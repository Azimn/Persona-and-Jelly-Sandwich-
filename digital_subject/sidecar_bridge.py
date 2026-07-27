from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from .engine import SubjectEngine
from .models import Action, Event


@dataclass(frozen=True, slots=True)
class SidecarFrame:
    """Read-only organism context supplied to a subjective controller."""

    subject_id: str
    cartridge_id: str
    tick: int
    observation: dict
    current_self_state: dict
    retrieved_history: tuple[str, ...]
    active_pressures: tuple[tuple[str, float], ...]
    active_needs: tuple[tuple[str, float], ...]
    relationship_context: dict
    self_narrative: tuple[str, ...]
    legal_actions: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def build_sidecar_frame(
    engine: SubjectEngine,
    event: Event,
    *,
    legal_actions: Iterable[Action] | None = None,
) -> SidecarFrame:
    """Expose lived context without granting the sidecar state authority.

    The sidecar may rank or select conduct from ``legal_actions``. It cannot
    directly change needs, memories, relationships, identity, or world facts.
    """

    allowed = tuple(legal_actions or Action)
    memories = engine._retrieve_memories(event.tags, 4)  # bounded read-only handoff
    relationship = engine.state.relationships.get(event.source)
    relationship_context = asdict(relationship) if relationship is not None else {}
    return SidecarFrame(
        subject_id=engine.state.subject_id,
        cartridge_id=engine.state.cartridge_id,
        tick=engine.state.tick,
        observation={
            "kind": event.kind,
            "source": event.source,
            "description": event.description,
            "target": event.target,
            "intensity": event.intensity,
            "valence": event.valence,
            "tags": event.tags,
        },
        current_self_state={
            "experience": engine.state.current_experience,
            "activity": engine.state.current_activity.value,
            "location": engine.state.location,
            "sensorium": dict(engine.state.sensorium),
        },
        retrieved_history=tuple(memory.summary for memory in memories),
        active_pressures=tuple(engine._triage_pressures()),
        active_needs=tuple(engine._triage_needs()),
        relationship_context=relationship_context,
        self_narrative=tuple(
            claim.proposition
            for claim in sorted(engine.state.narrative.values(), key=lambda item: item.confidence, reverse=True)[:4]
        ),
        legal_actions=tuple(action.value for action in allowed),
    )


def validate_sidecar_choice(frame: SidecarFrame, chosen: str | Action) -> Action:
    """Apply the host legal-action gate without mutating organism state."""

    action = chosen if isinstance(chosen, Action) else Action(str(chosen))
    if action.value not in frame.legal_actions:
        raise ValueError(f"sidecar chose illegal action: {action.value}")
    return action
