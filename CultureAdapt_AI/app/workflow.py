from pathlib import Path

from app.services.parser import extract_text
from app.services.continuity import run_continuity_checks
from app.services.image_generator import generate_mock_visual_card


class CultureAdaptWorkflow:

    def __init__(self, llm):
        self.llm = llm

    def extract(self, file_path):
        source = extract_text(file_path)
        extraction = self.llm.extract_screenplay(source)
        return source, extraction

    def plan(self, source, extraction, culture, dialect, region, setting, output_script, output_language="Hindi"):
        return self.llm.create_adaptation_plan(
            source,
            extraction,
            culture,
            dialect,
            region,
            setting,
            output_script,
            output_language,
        )

    def adapt(self, source, plan):
        return self.llm.rewrite_screenplay(source, plan)

    def verify(self, extraction):
        return run_continuity_checks(extraction)

    def generate_visual_pack(self, extraction, output_dir):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = []

        for character in extraction.characters:
            path = output_dir / f"{character.character_id}.png"
            generate_mock_visual_card(
                str(path),
                f"Character: {character.name}",
                character.role or "Role not specified",
                [
                    f"ID: {character.character_id}",
                    f"Age: {character.age or 'Unknown'}",
                    f"Dialect: {character.dialect or 'Not specified'}",
                ],
            )
            paths.append(str(path))

        for costume in extraction.costumes:
            path = output_dir / f"{costume.costume_id}.png"
            generate_mock_visual_card(
                str(path),
                f"Costume: {costume.name}",
                costume.costume_id,
                [
                    f"Garments: {', '.join(costume.garments) or 'Not specified'}",
                    f"Fabric: {', '.join(costume.fabrics) or 'Not specified'}",
                    f"Colours: {', '.join(costume.colors) or 'Not specified'}",
                ],
            )
            paths.append(str(path))

        for scene in extraction.scenes:
            path = output_dir / f"{scene.scene_id}.png"
            generate_mock_visual_card(
                str(path),
                f"Scene: {scene.scene_id}",
                scene.summary,
                [
                    f"Location: {scene.location_id}",
                    f"Time: {scene.time or 'Unknown'}",
                    f"Characters: {', '.join(scene.character_ids) or 'None'}",
                    f"Props: {', '.join(scene.prop_ids) or 'None'}",
                ],
            )
            paths.append(str(path))

        return paths
