from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any

from .host import PersistentOrganismHost


@dataclass(frozen=True, slots=True)
class AwayReport:
    since_tick: int
    current_tick: int
    elapsed_ticks: int
    experience_count: int
    memory_count: int
    activity_counts: dict[str, int]
    notable_experiences: tuple[str, ...]
    current_experience: str
    current_activity: str
    top_needs: tuple[tuple[str, float], ...]
    compressed_ticks: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OrganismInspector:
    """Read-only inspection of organism, host runtime, and objective room."""

    @staticmethod
    def snapshot(host: PersistentOrganismHost) -> dict[str, Any]:
        engine_snapshot = deepcopy(host.engine.debug_snapshot())
        return {
            "organism": engine_snapshot,
            "runtime": deepcopy(host.runtime.to_dict()),
            "world": deepcopy(host.world.state.to_dict()),
        }

    @staticmethod
    def away_report(host: PersistentOrganismHost, since_tick: int | None = None) -> AwayReport:
        state = host.engine.state
        start = host.runtime.last_seen_tick if since_tick is None else max(0, int(since_tick))
        experiences = [item for item in getattr(state, "life_log", []) if int(getattr(item, "tick", 0)) > start]
        memories = [item for item in getattr(state, "memories", []) if int(getattr(item, "created_tick", 0)) > start]

        actions: Counter[str] = Counter()
        action_names = {
            "answer", "ask", "deflect", "conceal", "remain_silent", "repair", "challenge",
            "approach", "withdraw", "observe", "rest", "explore", "seek_contact", "self_soothe", "wait",
        }
        for item in experiences:
            tags = tuple(getattr(item, "tags", ()))
            action_tag = next((tag for tag in tags if isinstance(tag, str) and tag in action_names), None)
            actions[action_tag or str(getattr(item, "kind", "experience"))] += 1

        notable = [
            str(getattr(item, "first_person", ""))
            for item in experiences
            if float(getattr(item, "intensity", 0.0)) >= 0.35
        ][-8:]
        snapshot = host.engine.debug_snapshot()
        top_needs = tuple((str(key), float(value)) for key, value in snapshot.get("top_needs", [])[:4])
        last_catchup = host.runtime.last_catchup

        activity = getattr(state, "current_activity", "wait")
        activity_value = getattr(activity, "value", activity)
        return AwayReport(
            since_tick=start,
            current_tick=int(state.tick),
            elapsed_ticks=max(0, int(state.tick) - start),
            experience_count=len(experiences),
            memory_count=len(memories),
            activity_counts=dict(actions),
            notable_experiences=tuple(value for value in notable if value),
            current_experience=str(getattr(state, "current_experience", "I am present.")),
            current_activity=str(activity_value),
            top_needs=top_needs,
            compressed_ticks=int(last_catchup.get("compressed_ticks", 0)),
        )

    @staticmethod
    def render_text(report: AwayReport) -> str:
        lines = [
            f"Ticks since last inspection: {report.elapsed_ticks}",
            f"Experiences recorded: {report.experience_count}",
            f"Memories formed: {report.memory_count}",
            f"Current activity: {report.current_activity}",
            f"Current experience: {report.current_experience}",
        ]
        if report.top_needs:
            lines.append("Active needs: " + ", ".join(f"{key}={value:.2f}" for key, value in report.top_needs))
        if report.activity_counts:
            lines.append("Activity pattern: " + ", ".join(f"{key}×{value}" for key, value in sorted(report.activity_counts.items())))
        if report.notable_experiences:
            lines.append("Notable unattended experiences:")
            lines.extend(f"- {value}" for value in report.notable_experiences)
        if report.compressed_ticks:
            lines.append(f"Long absence compression: {report.compressed_ticks} ticks were not replayed moment by moment.")
        return "\n".join(lines)
