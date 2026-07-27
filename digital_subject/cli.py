from __future__ import annotations

import argparse
import json
from pathlib import Path

from .cartridge import load_cartridge
from .engine import SubjectEngine
from .models import Consequence, Event
from .renderers import TemplateRenderer, packet_to_prompt


ROOT = Path(__file__).resolve().parents[1]


def build_demo_engine() -> SubjectEngine:
    cartridge = load_cartridge(ROOT / "cartridges" / "seed_subject.toml")
    return SubjectEngine.from_cartridge(cartridge, "subject-001")


def run_demo() -> None:
    engine = build_demo_engine()
    renderer = TemplateRenderer()
    print("INITIAL LIFE")
    engine.live(18)
    print(json.dumps(engine.debug_snapshot(), indent=2, default=str))

    sequence = [
        Event("person_arrived", "jay", "Jay enters the room.", intensity=0.45, valence=0.2, tags=("jay", "arrival", "contact"), metadata={"person_id": "jay", "sensorium": {"social_presence": 1.0, "novelty": 0.4}}),
        Event("greeting", "jay", "Jay greets me.", intensity=0.35, valence=0.3, tags=("jay", "contact")),
        Event("kindness", "jay", "Jay asks whether I have been all right.", intensity=0.60, valence=0.6, tags=("jay", "kindness", "care")),
        Event("ignored", "jay", "Jay does not answer my question.", intensity=0.60, valence=-0.4, tags=("jay", "silence")),
        Event("apology", "jay", "Jay apologizes for becoming distracted.", intensity=0.65, valence=0.5, tags=("jay", "repair", "care")),
    ]
    for event in sequence:
        packet = engine.step(event)
        expression = renderer.render(packet, topic=event.description)
        engine.record_expression(expression)
        engine.apply_consequence(Consequence(packet.intention, f"The interaction continued after I said: {expression}", True, 0.25, event.tags, source=event.source))
        engine.live(3)
        print(f"\nEVENT: {event.description}")
        print(f"EXPRESSION: {expression}")
        print(f"EXPERIENCE: {engine.state.current_experience}")

    packet = engine.step(Event("greeting", "jay", "Jay returns later.", intensity=0.30, valence=0.2, tags=("jay", "contact")))
    print("\nCOMPACT LLM HANDOFF")
    print(packet_to_prompt(packet, "You seem different. What happened while I was gone?"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", default="demo", choices=["demo"])
    args = parser.parse_args()
    if args.command == "demo":
        run_demo()


if __name__ == "__main__":
    main()
