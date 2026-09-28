import sys
from pathlib import Path

# Add project root directory to sys.path so 'app' package imports work
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.models import Character, Costume, Prop, Scene, ExtractionResult
from app.services.continuity import run_continuity_checks


def test_missing_character():
    x = ExtractionResult(
        title="Test",
        characters=[Character(character_id="CHAR_01", name="Amar")],
        scenes=[
            Scene(
                scene_id="SC01",
                location_id="LOC01",
                summary="Test",
                character_ids=["CHAR_UNKNOWN"],
            )
        ],
    )

    report = run_continuity_checks(x)
    assert any(r["type"] == "missing_character" for r in report)


def test_missing_costume():
    x = ExtractionResult(
        title="Test",
        costumes=[Costume(costume_id="COST_01", name="Kurta")],
        scenes=[
            Scene(
                scene_id="SC01",
                location_id="LOC01",
                summary="Test",
                costume_ids=["COST_UNKNOWN"],
            )
        ],
    )

    report = run_continuity_checks(x)
    assert any(r["type"] == "missing_costume" for r in report)


def test_prop_disappearance():
    x = ExtractionResult(
        title="Test",
        props=[Prop(prop_id="PROP_LETTER", name="Letter")],
        scenes=[
            Scene(
                scene_id="SC01",
                location_id="LOC01",
                summary="Letter appears",
                prop_ids=["PROP_LETTER"],
            ),
            Scene(
                scene_id="SC02",
                location_id="LOC01",
                summary="Next scene",
                prop_ids=[],
            ),
        ],
    )

    report = run_continuity_checks(x)
    assert any(r["type"] == "prop_disappearance" for r in report)
