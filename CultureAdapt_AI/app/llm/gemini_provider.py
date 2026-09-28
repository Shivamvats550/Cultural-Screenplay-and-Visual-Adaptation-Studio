import time
import json
from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.models import ExtractionResult, AdaptationPlan


def fix_truncated_json(raw: str) -> str:
    s = raw.strip()
    if not s:
        return "{}"

    quotes = 0
    in_esc = False
    for c in s:
        if in_esc:
            in_esc = False
        elif c == '\\':
            in_esc = True
        elif c == '"':
            quotes += 1

    if quotes % 2 != 0:
        s += '"'

    s = s.rstrip(', \t\r\n')

    stack = []
    in_str = False
    in_e = False
    for c in s:
        if in_e:
            in_e = False
        elif c == '\\':
            in_e = True
        elif c == '"':
            in_str = not in_str
        elif not in_str:
            if c in '{[':
                stack.append(c)
            elif c == '}' and stack and stack[-1] == '{':
                stack.pop()
            elif c == ']' and stack and stack[-1] == '[':
                stack.pop()

    for c in reversed(stack):
        if c == '{':
            s += '}'
        elif c == '[':
            s += ']'

    return s


class GeminiProvider:
    # Main LLM provider.
    # Hinglish: Ye class Gemini API se baat karti hai.

    def __init__(self, api_key=GEMINI_API_KEY, model=GEMINI_MODEL):
        if not api_key:
            raise ValueError("GEMINI_API_KEY missing. Add it to .env.")

        self.client = genai.Client(api_key=api_key)
        self.model = model

    def _generate_with_retry(self, contents, config=None):
        fallback_models = [
            self.model,
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.5-pro",
            "gemini-flash-latest",
        ]
        models_to_try = []
        for m in fallback_models:
            if m and m not in models_to_try:
                models_to_try.append(m)

        last_exception = None
        for current_model in models_to_try:
            for attempt in range(3):
                try:
                    kwargs = {"model": current_model, "contents": contents}
                    if config is not None:
                        kwargs["config"] = config
                    return self.client.models.generate_content(**kwargs)
                except Exception as exc:
                    last_exception = exc
                    err_msg = str(exc)
                    if "404" in err_msg or "NOT_FOUND" in err_msg:
                        # Model not found on this endpoint, try next fallback model
                        break
                    if "503" in err_msg or "UNAVAILABLE" in err_msg or "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                        time.sleep(1.5 * (attempt + 1))
                        continue
                    raise exc

        if last_exception:
            raise last_exception

    def extract_screenplay(self, screenplay_text: str) -> ExtractionResult:
        prompt = f'''
You are a screenplay extraction agent.

RULES
- Use ONLY information explicitly supported by the screenplay text. Do not infer or invent.
- Preserve scene order exactly as it appears.
- Merge obvious aliases (e.g. "JOHN", "John Smith", "MR. SMITH") into one character; list the variants in "aliases".
- IDs are lowercase snake_case, derived from the canonical name, and prefixed by type:
  char_john_smith, cost_john_smith_trench_coat, prop_revolver, scene_001.
  Scene IDs are sequential in order of appearance.
- If a detail is not stated, use null. Never guess.
- Costumes: only clothing or accessories worn/described. Props: only objects that are handled or plot-relevant.
- Every costume and prop must cite the scene(s) where it appears.

OUTPUT: valid JSON only, no commentary, matching this shape:
{{
  "title": string | null,
  "characters": [{{"id": str, "name": str, "aliases": [str], "description": str | null, "first_scene": str}}],
  "costumes": [{{"id": str, "character_id": str, "description": str, "scene_ids": [str]}}],
  "props": [{{"id": str, "name": str, "description": str | null, "scene_ids": [str], "used_by": [str]}}],
  "scenes": [{{"id": str, "heading": str, "location": str | null, "time_of_day": str | null,
              "character_ids": [str], "costume_ids": [str], "prop_ids": [str], "summary": str}}]
}}

SOURCE:
{screenplay_text}
'''

        response = self._generate_with_retry(
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ExtractionResult,
                max_output_tokens=8192,
            ),
        )

        if getattr(response, "parsed", None):
            return response.parsed

        try:
            return ExtractionResult.model_validate_json(response.text)
        except Exception:
            repaired_text = fix_truncated_json(response.text)
            return ExtractionResult.model_validate_json(repaired_text)

    def create_adaptation_plan(
        self,
        screenplay_text,
        extraction,
        culture,
        dialect,
        region,
        setting,
        output_script,
        output_language="Hindi",
    ) -> AdaptationPlan:

        prompt = f'''
You are a cultural screenplay adaptation planning agent.

TASK
Produce an adaptation PLAN. Do not rewrite the screenplay and do not translate word for word.

PRESERVE
Story logic, character relationships, and emotional arc.

CONSIDER
Dialect and idioms; kinship terms and honorifics; greetings and behaviour; gestures and
non-verbal behaviour; family roles; architecture; clothing; food; transport; props;
sound and atmosphere.

RULES
- Use ONLY the extraction and source for story facts. Do not add plot, characters or relationships.
- Reference every element by its existing ID from the extraction. Never create new IDs
  except for new adaptation entries, which use the prefix adapt_.
- Do not assert cultural facts you are not confident about. Set requires_review=true and
  explain the doubt in "review_reason".
- If the original element needs no change, set action="keep".
- Actions: keep | replace | modify | remove | add.
- Output valid JSON only, no commentary.

TARGET
Culture: {culture}
Dialect: {dialect}
Region: {region}
Setting: {setting}
Output script: {output_script}
Output language: {output_language}

OUTPUT SHAPE
{{
  "cultural_summary": str,
  "characters": [{{"character_id": str, "adapted_name": str | null, "kinship_terms": {{"<other_character_id>": str}},
                   "speech_style": str, "requires_review": bool, "review_reason": str | null}}],
  "costumes": [{{"costume_id": str, "action": str, "adapted_description": str | null, "rationale": str,
                 "requires_review": bool, "review_reason": str | null}}],
  "props": [{{"prop_id": str, "action": str, "adapted_description": str | null, "rationale": str,
              "requires_review": bool, "review_reason": str | null}}],
  "scenes": [{{"scene_id": str, "adapted_location": str | null, "architecture": str | null,
               "food": str | null, "transport": str | null, "gestures": [str],
               "greetings": [str], "sound_atmosphere": str | null,
               "dialogue_notes": [str], "requires_review": bool, "review_reason": str | null}}]
}}

EXTRACTION:
{extraction.model_dump_json(indent=2)}

SOURCE:
{screenplay_text}
'''

        response = self._generate_with_retry(
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AdaptationPlan,
                max_output_tokens=8192,
            ),
        )

        if getattr(response, "parsed", None):
            return response.parsed

        try:
            return AdaptationPlan.model_validate_json(response.text)
        except Exception:
            repaired_text = fix_truncated_json(response.text)
            return AdaptationPlan.model_validate_json(repaired_text)

    def rewrite_screenplay(self, screenplay_text, plan) -> str:
        prompt = f'''
Rewrite the screenplay using ONLY the approved adaptation plan.

Rules:
- Preserve scene order.
- Preserve character relationships.
- Preserve central conflict.
- Preserve emotional arc.
- Do not invent a new plot.
- Write dialogue and scene directions naturally in the target language ({getattr(plan, 'output_language', 'Hindi')}) and script ({plan.output_script}).
- Apply cultural decisions naturally.
- Avoid stereotypes.
- Do not add unsupported rituals.

APPROVED PLAN:
{plan.model_dump_json(indent=2)}

SOURCE:
{screenplay_text}
'''

        response = self._generate_with_retry(
            contents=prompt,
        )

        return response.text
