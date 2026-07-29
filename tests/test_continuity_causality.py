from pathlib import Path

from digital_subject.cartridge import load_cartridge
from digital_subject.continuity import SubjectContinuity
from digital_subject.continuity_influence import derive_continuity_influence
from digital_subject.enhanced_host import PersistentContinuityHost
from digital_subject.models import Action, Event


ROOT = Path(__file__).resolve().parents[1]


def _host(tmp_path, name: str) -> PersistentContinuityHost:
    cartridge = load_cartridge(ROOT / "cartridges" / "seed_subject.toml")
    host = PersistentContinuityHost.open(
        cartridge,
        tmp_path / f"{name}.json",
        runtime_path=tmp_path / f"{name}.runtime.json",
        continuity_path=tmp_path / f"{name}.continuity.json",
        clock=lambda: 1000.0,
        auto_catch_up=False,
    )
    # Keep present bodily needs below the historical pressure threshold so the
    # test isolates continuity rather than fatigue, hunger, or curiosity.
    host.engine.state.needs.update(
        {
            "energy": 0.95,
            "fatigue": 0.05,
            "hunger": 0.05,
            "thirst": 0.05,
            "comfort": 0.95,
            "pain": 0.0,
            "warmth": 0.95,
            "restlessness": 0.05,
            "curiosity": 0.25,
            "loneliness": 0.05,
            "safety": 0.95,
            "focus": 0.95,
            "satisfaction": 0.95,
        }
    )
    return host


def test_broken_commitment_creates_bounded_guarded_influence():
    continuity = SubjectContinuity()
    commitment = continuity.create_commitment(
        "jay",
        "Jay will return.",
        tick=1,
        importance=1.0,
    )
    continuity.resolve_commitment(
        commitment.id,
        outcome="Jay did not return.",
        kept=False,
        tick=4,
    )
    influence = derive_continuity_influence(
        continuity,
        Event("greeting", "jay", "Jay says hello."),
        tick=5,
    )
    deltas = dict(influence.pressure_deltas)
    assert influence.concern_key == "fear"
    assert "broken_or_overdue_commitment" in influence.reasons
    assert 0.0 < deltas["fear"] <= 0.20
    assert -0.20 <= deltas["trust"] < 0.0


def test_same_event_produces_different_conduct_after_different_histories(tmp_path):
    neutral = _host(tmp_path, "neutral")
    disappointed = _host(tmp_path, "disappointed")

    commitment = disappointed.continuity.create_commitment(
        "jay",
        "Jay will return when promised.",
        tick=1,
        importance=1.0,
    )
    disappointed.continuity.resolve_commitment(
        commitment.id,
        outcome="Jay failed to return.",
        kept=False,
        tick=4,
    )

    present_event = Event(
        "greeting",
        "jay",
        "Jay returns and says hello.",
        intensity=0.25,
        valence=0.0,
        tags=("jay", "contact"),
    )
    neutral_packet = neutral.observe(present_event)
    disappointed_packet = disappointed.observe(present_event)

    assert neutral_packet.intention is not disappointed_packet.intention
    assert disappointed_packet.intention in {
        Action.WITHDRAW,
        Action.CONCEAL,
        Action.REMAIN_SILENT,
    }
    influence = disappointed_packet.private_content["continuity_influence"]
    assert "broken_or_overdue_commitment" in influence["reasons"]


def test_continuity_influence_does_not_select_action_directly(tmp_path):
    host = _host(tmp_path, "bounded")
    commitment = host.continuity.create_commitment(
        "jay",
        "Jay will answer.",
        tick=1,
        importance=0.8,
    )
    host.continuity.resolve_commitment(
        commitment.id,
        outcome="No answer arrived.",
        kept=False,
        tick=3,
    )
    packet = host.observe(Event("greeting", "jay", "Jay says hello.", intensity=0.2))
    influence = packet.private_content["continuity_influence"]
    assert "action" not in influence
    assert set(influence) == {
        "source",
        "pressure_deltas",
        "concern_key",
        "concern_urgency",
        "reasons",
    }
