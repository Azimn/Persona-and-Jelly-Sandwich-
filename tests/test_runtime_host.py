from __future__ import annotations

import json
from pathlib import Path

from digital_subject.cartridge import load_cartridge
from digital_subject.host import PersistentOrganismHost
from digital_subject.inspector import OrganismInspector


ROOT = Path(__file__).resolve().parents[1]


class Clock:
    def __init__(self, value: float = 1_000.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def make_host(tmp_path: Path, clock: Clock, *, max_ticks: int = 12) -> PersistentOrganismHost:
    cartridge = load_cartridge(ROOT / "cartridges" / "seed_subject.toml")
    return PersistentOrganismHost.open(
        cartridge,
        tmp_path / "subject.json",
        runtime_path=tmp_path / "runtime.json",
        clock=clock,
        tick_seconds=60.0,
        max_catchup_ticks=max_ticks,
        auto_catch_up=False,
    )


def test_clock_catchup_advances_life_and_preserves_fraction(tmp_path):
    clock = Clock()
    host = make_host(tmp_path, clock)
    host.save()
    clock.advance(185.0)

    report = host.catch_up()

    assert report.requested_ticks == 3
    assert report.applied_ticks == 3
    assert report.remainder_seconds == 5.0
    assert host.engine.state.tick == 3
    assert report.experiences
    assert host.engine.state.last_expression is None


def test_long_absence_is_bounded_and_reported(tmp_path):
    clock = Clock()
    host = make_host(tmp_path, clock, max_ticks=4)
    host.save()
    clock.advance(600.0)

    report = host.catch_up()

    assert report.requested_ticks == 10
    assert report.applied_ticks == 4
    assert report.compressed_ticks == 6
    assert host.engine.state.tick == 4


def test_runtime_and_room_survive_reopen(tmp_path):
    clock = Clock()
    host = make_host(tmp_path, clock)
    host.set_room(noise=0.8, temperature=0.25, name="Workshop")
    host.arrive("jay", "Jay")
    tick = host.engine.state.tick

    reopened = PersistentOrganismHost.open(
        host.cartridge,
        host.state_path,
        runtime_path=host.runtime_path,
        clock=clock,
        tick_seconds=60.0,
        max_catchup_ticks=12,
        auto_catch_up=False,
    )

    assert reopened.engine.state.tick == tick
    assert reopened.world.state.name == "Workshop"
    assert reopened.world.state.noise == 0.8
    assert "jay" in reopened.world.state.occupants


def test_room_world_is_objective_and_applied_before_experience(tmp_path):
    clock = Clock()
    host = make_host(tmp_path, clock)

    host.set_room(light=0.2, clutter=0.7)

    assert host.engine.state.sensorium["light"] == 0.2
    assert host.engine.state.sensorium["clutter"] == 0.7
    host.run_ticks(1)
    assert host.engine.state.current_experience.startswith("I ")


def test_inspector_is_read_only_and_reports_unattended_life(tmp_path):
    clock = Clock()
    host = make_host(tmp_path, clock)
    host.run_ticks(3)
    before_state = json.dumps(host.engine.state.to_dict(), sort_keys=True)
    before_runtime = json.dumps(host.runtime.to_dict(), sort_keys=True)

    report = OrganismInspector.away_report(host, since_tick=0)
    snapshot = OrganismInspector.snapshot(host)

    assert report.elapsed_ticks == 3
    assert report.experience_count == 3
    assert report.notable_experiences
    assert snapshot["world"]["room_id"] == "room-001"
    assert json.dumps(host.engine.state.to_dict(), sort_keys=True) == before_state
    assert json.dumps(host.runtime.to_dict(), sort_keys=True) == before_runtime


def test_mark_seen_moves_only_inspection_cursor(tmp_path):
    clock = Clock()
    host = make_host(tmp_path, clock)
    host.run_ticks(2)
    subject_before = json.dumps(host.engine.state.to_dict(), sort_keys=True)

    host.mark_seen()

    assert host.runtime.last_seen_tick == host.engine.state.tick
    assert json.dumps(host.engine.state.to_dict(), sort_keys=True) == subject_before
