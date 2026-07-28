from pathlib import Path

from digital_subject.cartridge import load_cartridge
from digital_subject.continuity import ContinuityState, SubjectContinuity
from digital_subject.enhanced_host import PersistentContinuityHost
from digital_subject.models import Event


ROOT = Path(__file__).resolve().parents[1]


def test_epistemic_layers_remain_distinct():
    continuity = SubjectContinuity()
    record = continuity.observe(
        Event(
            "person_left",
            "jay",
            "Jay left during the conversation.",
            tags=("jay", "departure"),
            metadata={
                "objective_record": "Jay left at 18:04 after his phone rang.",
                "perceived_record": "Jay stopped speaking and left abruptly.",
                "interpretation": "He may have wanted to escape the conversation.",
                "interpretation_confidence": 0.45,
            },
        ),
        tick=4,
        interpretation="fallback",
    )
    assert record.objective_record != record.perceived_record
    assert record.perceived_record != record.interpretation
    assert record.status == "provisional"


def test_later_evidence_revises_without_erasing_original():
    continuity = SubjectContinuity()
    original = continuity.observe(
        Event("person_left", "jay", "Jay left.", tags=("jay", "departure")),
        tick=1,
        interpretation="He may be avoiding me.",
    )
    revision = continuity.revise_record(
        original.id,
        interpretation="The emergency call is a better explanation for his departure.",
        evidence_id="call-log-1",
        confidence=0.85,
        tick=3,
    )
    assert original.status == "superseded"
    assert original.revised_by == revision.id
    assert original.id in revision.evidence_ids
    assert continuity.state.insights[-1].kind == "revised_belief"


def test_expectation_tracks_prediction_error():
    continuity = SubjectContinuity()
    item = continuity.create_expectation("Jay will return.", tick=2, due_tick=5, confidence=0.8)
    continuity.resolve_expectation(item.id, outcome="Jay did not return.", confirmed=False, tick=6)
    assert item.status == "violated"
    assert item.prediction_error == 0.8
    assert continuity.state.insights[-1].trigger == "prediction_error"


def test_promise_events_create_and_resolve_commitment():
    continuity = SubjectContinuity()
    continuity.observe(
        Event("promise_made", "jay", "Jay promised to return.", intensity=0.8, tags=("jay", "promise")),
        tick=1,
        interpretation="Jay has made a commitment to me.",
    )
    commitment = next(iter(continuity.state.commitments.values()))
    assert commitment.status == "open"
    continuity.observe(
        Event("promise_kept", "jay", "Jay returned as promised.", tags=("jay", "promise")),
        tick=4,
        interpretation="Jay followed through.",
    )
    assert commitment.status == "kept"


def test_repeated_evidence_forms_bounded_insight():
    continuity = SubjectContinuity()
    for tick in range(1, 4):
        continuity.observe(
            Event("kindness", "jay", f"Kind act {tick}.", tags=("jay", "kindness")),
            tick=tick,
            interpretation="Jay treated me kindly.",
        )
    assert any(item.kind == "recurring_pattern" for item in continuity.state.insights)
    insight = continuity.state.insights[-1]
    assert len(insight.evidence_ids) >= 3


def test_state_round_trip_preserves_typed_records():
    continuity = SubjectContinuity()
    continuity.observe(Event("greeting", "jay", "Hello.", tags=("jay",)), tick=1, interpretation="Jay acknowledged me.")
    expectation = continuity.create_expectation("Jay will answer.", tick=1, confidence=0.6)
    restored = ContinuityState.from_dict(continuity.state.to_dict())
    assert restored.epistemic_records[0].tags == ("jay",)
    assert restored.expectations[expectation.id].source_record_ids == ()


def test_enhanced_host_persists_subject_continuity(tmp_path):
    cartridge = load_cartridge(ROOT / "cartridges" / "seed_subject.toml")
    clock = lambda: 1000.0
    host = PersistentContinuityHost.open(
        cartridge,
        tmp_path / "subject.json",
        runtime_path=tmp_path / "runtime.json",
        continuity_path=tmp_path / "continuity.json",
        clock=clock,
        auto_catch_up=False,
    )
    host.observe(
        Event(
            "promise_made",
            "jay",
            "Jay promised to return.",
            intensity=0.8,
            tags=("jay", "promise"),
            metadata={"perceived_record": "Jay told me he would return."},
        )
    )
    reopened = PersistentContinuityHost.open(
        cartridge,
        tmp_path / "subject.json",
        runtime_path=tmp_path / "runtime.json",
        continuity_path=tmp_path / "continuity.json",
        clock=clock,
        auto_catch_up=False,
    )
    assert len(reopened.continuity.state.epistemic_records) == 1
    assert len(reopened.continuity.state.commitments) == 1
