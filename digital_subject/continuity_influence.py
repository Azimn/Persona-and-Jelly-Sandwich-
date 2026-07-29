from __future__ import annotations

from dataclasses import dataclass

from .continuity import SubjectContinuity
from .models import Concern, Event, SubjectState


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


@dataclass(frozen=True, slots=True)
class ContinuityInfluence:
    """Bounded history-derived input to the existing engine synthesis path.

    This record never selects conduct. It only exposes pressures and concerns that
    the established engine may weigh alongside needs, habits, relationships, and
    the current event.
    """

    source: str
    pressure_deltas: tuple[tuple[str, float], ...]
    concern_key: str | None = None
    concern_description: str | None = None
    concern_urgency: float = 0.0
    reasons: tuple[str, ...] = ()


def derive_continuity_influence(
    continuity: SubjectContinuity,
    event: Event,
    *,
    tick: int,
) -> ContinuityInfluence:
    source = str(event.source)
    pressure: dict[str, float] = {}
    reasons: list[str] = []
    concern_key: str | None = None
    concern_description: str | None = None
    concern_urgency = 0.0

    related_commitments = [
        item for item in continuity.state.commitments.values() if item.actor == source
    ]
    broken = [item for item in related_commitments if item.status in {"broken", "overdue"}]
    kept = [item for item in related_commitments if item.status == "kept"]
    open_items = [item for item in related_commitments if item.status == "open"]

    if broken:
        weight = min(1.0, sum(item.importance for item in broken) / max(1, len(broken)))
        pressure["trust"] = pressure.get("trust", 0.0) - (0.08 + 0.12 * weight)
        pressure["fear"] = pressure.get("fear", 0.0) + (0.05 + 0.10 * weight)
        pressure["anger"] = pressure.get("anger", 0.0) + (0.03 + 0.07 * weight)
        concern_key = "unreliable_commitment"
        concern_description = f"{source} has failed to complete an important commitment to me."
        concern_urgency = 0.45 + 0.35 * weight
        reasons.append("broken_or_overdue_commitment")

    if kept:
        weight = min(1.0, sum(item.importance for item in kept[-3:]) / max(1, len(kept[-3:])))
        pressure["trust"] = pressure.get("trust", 0.0) + (0.04 + 0.08 * weight)
        pressure["fear"] = pressure.get("fear", 0.0) - (0.02 + 0.05 * weight)
        pressure["attachment"] = pressure.get("attachment", 0.0) + (0.02 + 0.04 * weight)
        reasons.append("kept_commitment")

    if open_items:
        due = [item for item in open_items if item.due_tick is not None]
        approaching = [item for item in due if item.due_tick is not None and item.due_tick - tick <= 2]
        if approaching:
            urgency = max(item.importance for item in approaching)
            pressure["arousal"] = pressure.get("arousal", 0.0) + 0.03 + 0.05 * urgency
            concern_key = concern_key or "anticipated_commitment"
            concern_description = concern_description or f"I am waiting to see whether {source} follows through."
            concern_urgency = max(concern_urgency, 0.30 + 0.30 * urgency)
            reasons.append("commitment_due_soon")

    related_expectations = [
        item
        for item in continuity.state.expectations.values()
        if source.lower() in item.proposition.lower()
    ]
    violated = [item for item in related_expectations if item.status in {"violated", "expired"}]
    confirmed = [item for item in related_expectations if item.status == "confirmed"]
    if violated:
        error = max(float(item.prediction_error or item.confidence) for item in violated[-3:])
        pressure["fear"] = pressure.get("fear", 0.0) + 0.04 + 0.08 * error
        pressure["self_story_stability"] = pressure.get("self_story_stability", 0.0) - 0.03 - 0.05 * error
        reasons.append("violated_expectation")
    if confirmed:
        support = max(1.0 - float(item.prediction_error or 0.0) for item in confirmed[-3:])
        pressure["trust"] = pressure.get("trust", 0.0) + 0.03 + 0.05 * support
        reasons.append("confirmed_expectation")

    source_records = [
        item for item in continuity.state.epistemic_records if item.source == source
    ][-12:]
    superseded = [item for item in source_records if item.status == "superseded"]
    if superseded:
        pressure["self_story_stability"] = pressure.get("self_story_stability", 0.0) + 0.02
        pressure["arousal"] = pressure.get("arousal", 0.0) - 0.02
        reasons.append("interpretation_revised")

    bounded = tuple(
        sorted(
            (key, max(-0.20, min(0.20, value)))
            for key, value in pressure.items()
            if abs(value) >= 0.001
        )
    )
    return ContinuityInfluence(
        source=source,
        pressure_deltas=bounded,
        concern_key=concern_key,
        concern_description=concern_description,
        concern_urgency=_clamp(concern_urgency),
        reasons=tuple(dict.fromkeys(reasons)),
    )


def apply_continuity_influence(
    state: SubjectState,
    influence: ContinuityInfluence,
    *,
    tick: int,
) -> None:
    """Apply bounded history pressure before the existing engine chooses conduct."""

    for key, delta in influence.pressure_deltas:
        current = float(state.pressures.get(key, state.pressure_baselines.get(key, 0.0)))
        state.pressures[key] = _clamp(current + delta)

    if influence.concern_key and influence.concern_description:
        current = state.concerns.get(influence.concern_key)
        if current is None:
            state.concerns[influence.concern_key] = Concern(
                influence.concern_key,
                influence.concern_description,
                influence.concern_urgency,
                0.985,
                int(tick),
            )
        else:
            current.urgency = _clamp(max(current.urgency, influence.concern_urgency))
            current.description = influence.concern_description
            current.last_updated_tick = int(tick)
