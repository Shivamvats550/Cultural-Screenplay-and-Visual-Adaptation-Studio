import sys
from pathlib import Path

# Add project root directory to sys.path so 'app' package imports work
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.llm.gemini_provider import GeminiProvider
from app.workflow import CultureAdaptWorkflow

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    workflow = CultureAdaptWorkflow(GeminiProvider())

    source, extraction = workflow.extract("sample_data/sample_screenplay.txt")

    print("TITLE:", extraction.title)
    print("CHARACTERS:", [c.name for c in extraction.characters])
    print("SCENES:", [s.scene_id for s in extraction.scenes])

    plan = workflow.plan(
        source,
        extraction,
        culture="Rajasthani",
        dialect="Marwari",
        region="Rajasthan",
        setting="Rural",
        output_script="Devanagari",
        output_language="Hindi",
    )

    print(plan.model_dump_json(indent=2, ensure_ascii=False))

    print(workflow.verify(extraction))

if __name__ == "__main__":
    main()
