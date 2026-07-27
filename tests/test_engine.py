from pathlib import Path

import pytest

from digital_subject.cartridge import CartridgeError, load_cartridge
from digital_subject.engine import SubjectEngine
from digital_subject.models import Action, Consequence, Event
from digital_subject.renderers import TemplateRenderer


ROOT = Path(__file__).resolve().parents[1]


def make_engine() -> SubjectEngine:
    cartridge = load_cartridge(ROOT / "cartridges" / "seed_subject.toml")
    return SubjectEngine.from_cartridge(cartridge, "test-subject")


def test_event_changes_same_persistent_subject():
    engine = make_engine()
    original_id = engine.state.subject_id
    before = dict(engine.state.pressures)
    packet = engine.step(Event("accusation", "user", "You are hiding something.", intensity=0.8, valence=-0.6, tags=("user", "accusation")))
    assert engine.state.subject_id == original_id
    assert engine.state.pressures["shame"] > before["shame"]
    assert packet.subject_id == original_id


def test_life_continues_without_prompt():
    engine = make_engine()
    before = dict(engine.state.needs)
    experiences = engine.live(12)
    assert engine.state.tick == 12
    assert len(experiences) == 12
    assert engine.state.needs != before
    assert engine.state.current_experience.startswith("I ")
    assert engine.state.last_expression is None


def test_high_fatigue_selects_rest_activity():
    engine = make_engine()
    engine.state.needs["fatigue"] = 0.95
    engine.state.needs["energy"] = 0.10
    experience = engine.live(1)[0]
    assert engine.state.current_activity is Action.REST
    assert "still" in experience.first_person.lower() or "strain" in experience.first_person.lower()


def test_relationship_is_multidimensional_and_changes():
    engine = make_engine()
    engine.step(Event("kindness", "jay", "Jay treats me gently.", intensity=0.8, valence=0.8, tags=("jay", "kindness")))
    relationship = engine.state.relationships["jay"]
    assert relationship.trust > engine.cartridge.relationship_defaults["trust"]
    assert relationship.comfort > engine.cartridge.relationship_defaults["comfort"]
    assert relationship.familiarity > engine.cartridge.relationship_defaults["familiarity"]


def test_experience_teaches_preference():
    engine = make_engine()
    engine.step(Event("music", "world", "Soft piano music begins.", intensity=0.7, valence=0.8, tags=("music", "piano")))
    assert engine.state.preferences["learned:music"].valence > 0
    assert engine.state.preferences["learned:music"].learned is True


def test_repeated_experience_forms_self_narrative():
    engine = make_engine()
    for _ in range(3):
        engine.step(Event("kindness", "jay", "Jay returns and chooses kindness.", intensity=0.8, valence=0.8, tags=("jay", "kindness", "care")))
    engine.live(10)
    assert engine.state.narrative
    assert any("jay" in claim.proposition.lower() or "kindness" in claim.proposition.lower() or "care" in claim.proposition.lower() for claim in engine.state.narrative.values())
    assert any(memory.kind == "narrative" for memory in engine.state.memories)


def test_consequence_becomes_autobiographical_memory():
    engine = make_engine()
    packet = engine.step(Event("greeting", "user", "Hello.", intensity=0.3, valence=0.2, tags=("user",)))
    consequence = Consequence(packet.intention, "The user answered my question.", True, 0.5, ("user", "reply"), source="user")
    engine.apply_consequence(consequence)
    assert any(memory.summary == consequence.description for memory in engine.state.memories)
    assert engine.state.last_consequence == consequence


def test_private_state_is_hidden_from_repr():
    packet = make_engine().step(Event("accusation", "user", "You lied.", intensity=0.7, valence=-0.7, tags=("lie", "user")))
    assert "owned_meaning" not in repr(packet)
    assert packet.private_content


def test_dialogue_comes_from_cartridge():
    engine = make_engine()
    packet = engine.step(Event("greeting", "user", "Hello.", intensity=0.3, tags=("user",)))
    text = TemplateRenderer().render(packet, topic="our first meeting")
    authored = {line for values in engine.cartridge.dialogue.values() for line in values}
    assert any(text == line.format(name=packet.display_name, topic="our first meeting", memory="nothing specific has surfaced", experience=packet.current_experience, relationship=", ".join(packet.relationship_stance), need=packet.active_needs[0][0].replace("_", " "), activity=packet.intention.value.replace("_", " ")) for line in authored if "{" not in line or True)


def test_save_and_load_preserve_life(tmp_path):
    engine = make_engine()
    engine.live(5)
    engine.step(Event("promise_kept", "jay", "Jay returned as promised.", intensity=0.8, valence=0.7, tags=("jay", "promise", "repair")))
    path = tmp_path / "subject.json"
    engine.save(path)
    loaded = SubjectEngine.load(path, engine.cartridge)
    assert loaded.state.subject_id == engine.state.subject_id
    assert loaded.state.tick == engine.state.tick
    assert loaded.state.needs == engine.state.needs
    assert loaded.state.relationships["jay"].trust == engine.state.relationships["jay"].trust
    assert len(loaded.state.life_log) == len(engine.state.life_log)


def test_cartridge_rejects_unknown_dialogue_slot(tmp_path):
    text = (ROOT / "cartridges" / "seed_subject.toml").read_text(encoding="utf-8")
    text = text.replace('"I will answer from what I have actually experienced, not from an invented history."', '"Hello {secret_meter}."')
    bad = tmp_path / "bad.toml"
    bad.write_text(text, encoding="utf-8")
    with pytest.raises(CartridgeError, match="unsupported slot"):
        load_cartridge(bad)


def test_two_cartridges_do_not_share_dialogue(tmp_path):
    source = (ROOT / "cartridges" / "seed_subject.toml").read_text(encoding="utf-8")
    alternate = source.replace('cartridge_id = "seed-subject-v1"', 'cartridge_id = "alternate-v1"').replace('display_name = "Subject One"', 'display_name = "Alternate"').replace('"I need stillness before I can give this proper attention."', '"Alternate rest phrase."')
    path = tmp_path / "alternate.toml"
    path.write_text(alternate, encoding="utf-8")
    first = make_engine()
    second_cartridge = load_cartridge(path)
    second = SubjectEngine.from_cartridge(second_cartridge, "alternate")
    first.state.needs["fatigue"] = 0.95
    first.state.needs["energy"] = 0.10
    second.state.needs["fatigue"] = 0.95
    second.state.needs["energy"] = 0.10
    first_packet = first.step(Event("greeting", "user", "Hello.", intensity=0.2))
    second_packet = second.step(Event("greeting", "user", "Hello.", intensity=0.2))
    first_text = TemplateRenderer().render(first_packet)
    second_text = TemplateRenderer().render(second_packet)
    assert first_text != "Alternate rest phrase."
    assert second_text == "Alternate rest phrase."


def test_sidecar_bridge_is_read_only_and_filters_actions():
    from digital_subject.sidecar_bridge import build_sidecar_frame, validate_sidecar_choice

    engine = make_engine()
    before = engine.state.to_dict()
    event = Event("greeting", "jay", "Jay says hello.", intensity=0.3, tags=("jay", "contact"))
    frame = build_sidecar_frame(engine, event, legal_actions=(Action.ANSWER, Action.ASK))
    assert engine.state.to_dict() == before
    assert validate_sidecar_choice(frame, "ask") is Action.ASK
    with pytest.raises(ValueError, match="illegal action"):
        validate_sidecar_choice(frame, "withdraw")
