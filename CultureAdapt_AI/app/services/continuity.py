from app.models import ExtractionResult


def run_continuity_checks(extraction: ExtractionResult):
    report = []

    known_characters = {c.character_id for c in extraction.characters}
    known_costumes = {c.costume_id for c in extraction.costumes}

    for scene in extraction.scenes:
        for char_id in scene.character_ids:
            if char_id not in known_characters:
                report.append({
                    "status": "FAIL",
                    "scene_id": scene.scene_id,
                    "type": "missing_character",
                    "message": f"{char_id} is referenced but not defined.",
                })

        for costume_id in scene.costume_ids:
            if costume_id not in known_costumes:
                report.append({
                    "status": "FAIL",
                    "scene_id": scene.scene_id,
                    "type": "missing_costume",
                    "message": f"{costume_id} is referenced but not defined.",
                })

    for i in range(1, len(extraction.scenes)):
        previous = set(extraction.scenes[i - 1].prop_ids)
        current = set(extraction.scenes[i].prop_ids)

        for prop_id in previous - current:
            report.append({
                "status": "WARNING",
                "scene_id": extraction.scenes[i].scene_id,
                "type": "prop_disappearance",
                "message": f"{prop_id} disappeared; verify that the story explains it.",
            })

    if not report:
        report.append({
            "status": "PASS",
            "type": "continuity",
            "message": "No deterministic continuity problems found.",
        })

    return report
