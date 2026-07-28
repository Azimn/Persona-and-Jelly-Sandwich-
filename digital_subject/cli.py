from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .cartridge import load_cartridge
from .engine import SubjectEngine
from .host import PersistentOrganismHost
from .inspector import OrganismInspector
from .models import Consequence, Event
from .renderers import TemplateRenderer, packet_to_prompt


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CARTRIDGE = ROOT / "cartridges" / "seed_subject.toml"


def build_demo_engine() -> SubjectEngine:
    cartridge = load_cartridge(DEFAULT_CARTRIDGE)
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


def _host(args: argparse.Namespace, *, auto_catch_up: bool = True) -> PersistentOrganismHost:
    cartridge = load_cartridge(args.cartridge)
    return PersistentOrganismHost.open(
        cartridge,
        args.state,
        runtime_path=args.runtime,
        subject_id=args.subject_id,
        tick_seconds=args.tick_seconds,
        max_catchup_ticks=args.max_catchup_ticks,
        auto_catch_up=auto_catch_up,
    )


def _print_status(host: PersistentOrganismHost, *, as_json: bool = False, mark_seen: bool = False) -> None:
    report = OrganismInspector.away_report(host)
    if as_json:
        print(json.dumps({"away": report.to_dict(), "snapshot": OrganismInspector.snapshot(host)}, indent=2, default=str))
    else:
        print(OrganismInspector.render_text(report))
    if mark_seen:
        host.mark_seen()


def _add_host_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cartridge", type=Path, default=DEFAULT_CARTRIDGE)
    parser.add_argument("--state", type=Path, default=Path("subject_state.json"))
    parser.add_argument("--runtime", type=Path, default=Path("subject_runtime.json"))
    parser.add_argument("--subject-id", default="subject-001")
    parser.add_argument("--tick-seconds", type=float, default=300.0)
    parser.add_argument("--max-catchup-ticks", type=int, default=288)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one persistent digital organism.")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("demo", help="Run the in-memory demonstration.")

    init_parser = subparsers.add_parser("init", help="Create persistent organism and room state.")
    _add_host_options(init_parser)

    status_parser = subparsers.add_parser("status", help="Catch up elapsed time and inspect what happened.")
    _add_host_options(status_parser)
    status_parser.add_argument("--json", action="store_true")

    tick_parser = subparsers.add_parser("tick", help="Advance a chosen number of organism ticks.")
    _add_host_options(tick_parser)
    tick_parser.add_argument("ticks", type=int)
    tick_parser.add_argument("--json", action="store_true")

    room_parser = subparsers.add_parser("room", help="Change objective room conditions.")
    _add_host_options(room_parser)
    room_parser.add_argument("--name")
    room_parser.add_argument("--light", type=float)
    room_parser.add_argument("--noise", type=float)
    room_parser.add_argument("--temperature", type=float)
    room_parser.add_argument("--clutter", type=float)
    room_parser.add_argument("--novelty", type=float)

    arrive_parser = subparsers.add_parser("arrive", help="Record that a person entered the room.")
    _add_host_options(arrive_parser)
    arrive_parser.add_argument("person_id")
    arrive_parser.add_argument("--name")

    leave_parser = subparsers.add_parser("leave", help="Record that a person left the room.")
    _add_host_options(leave_parser)
    leave_parser.add_argument("person_id")
    leave_parser.add_argument("--name")

    event_parser = subparsers.add_parser("event", help="Deliver an objective event and render the selected expression.")
    _add_host_options(event_parser)
    event_parser.add_argument("kind")
    event_parser.add_argument("source")
    event_parser.add_argument("description")
    event_parser.add_argument("--intensity", type=float, default=0.5)
    event_parser.add_argument("--valence", type=float, default=0.0)
    event_parser.add_argument("--tags", default="")

    args = parser.parse_args()
    command = args.command or "demo"
    if command == "demo":
        run_demo()
        return

    if command == "init":
        host = _host(args, auto_catch_up=False)
        host.save()
        _print_status(host, mark_seen=True)
        return

    host = _host(args)
    if command == "status":
        _print_status(host, as_json=args.json, mark_seen=True)
    elif command == "tick":
        host.run_ticks(args.ticks)
        _print_status(host, as_json=args.json)
    elif command == "room":
        values: dict[str, Any] = {
            key: value
            for key, value in {
                "name": args.name,
                "light": args.light,
                "noise": args.noise,
                "temperature": args.temperature,
                "clutter": args.clutter,
                "novelty": args.novelty,
            }.items()
            if value is not None
        }
        host.set_room(**values)
        _print_status(host)
    elif command == "arrive":
        host.arrive(args.person_id, args.name)
        _print_status(host)
    elif command == "leave":
        host.leave(args.person_id, args.name)
        _print_status(host)
    elif command == "event":
        tags = tuple(value.strip() for value in args.tags.split(",") if value.strip())
        event = Event(args.kind, args.source, args.description, intensity=args.intensity, valence=args.valence, tags=tags)
        packet = host.observe(event)
        text = TemplateRenderer().render(packet, topic=args.description)
        host.engine.record_expression(text)
        host.save()
        print(text)


if __name__ == "__main__":
    main()
