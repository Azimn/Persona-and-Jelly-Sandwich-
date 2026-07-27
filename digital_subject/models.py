from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Action(str, Enum):
    ANSWER = "answer"
    ASK = "ask"
    DEFLECT = "deflect"
    CONCEAL = "conceal"
    REMAIN_SILENT = "remain_silent"
    REPAIR = "repair"
    CHALLENGE = "challenge"
    APPROACH = "approach"
    WITHDRAW = "withdraw"
    OBSERVE = "observe"
    REST = "rest"
    EXPLORE = "explore"
    SEEK_CONTACT = "seek_contact"
    SELF_SOOTHE = "self_soothe"
    WAIT = "wait"


@dataclass(slots=True)
class Event:
    kind: str
    source: str
    description: str
    target: str = "self"
    intensity: float = 0.5
    valence: float = 0.0
    tags: tuple[str, ...] = ()
    expected_valence: float | None = None
    actual_valence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class OwnedEvent:
    event: Event
    first_person_meaning: str
    self_relevance: float
    surprise: float
    matched_memory_ids: tuple[str, ...] = ()


@dataclass(slots=True)
class Memory:
    id: str
    summary: str
    meaning: str
    tags: tuple[str, ...]
    strength: float
    emotional_charge: float
    created_tick: int
    last_recalled_tick: int
    recall_count: int = 0
    kind: str = "episode"


@dataclass(slots=True)
class Belief:
    key: str
    proposition: str
    confidence: float
    valence: float = 0.0
    updated_tick: int = 0


@dataclass(slots=True)
class Concern:
    key: str
    description: str
    urgency: float
    persistence: float
    last_updated_tick: int = 0


@dataclass(slots=True)
class Association:
    left: str
    right: str
    strength: float
    last_used_tick: int


@dataclass(slots=True)
class Preference:
    key: str
    target: str
    valence: float
    confidence: float
    learned: bool = False
    updated_tick: int = 0


@dataclass(slots=True)
class Habit:
    key: str
    trigger: str
    action: Action
    strength: float
    cooldown: int = 0
    last_used_tick: int = -10_000


@dataclass(slots=True)
class Relationship:
    person_id: str
    trust: float = 0.35
    comfort: float = 0.30
    respect: float = 0.35
    interest: float = 0.35
    attachment: float = 0.15
    affection: float = 0.10
    safety: float = 0.45
    familiarity: float = 0.05
    obligation: float = 0.00
    uncertainty: float = 0.60
    last_contact_tick: int = 0


@dataclass(slots=True)
class NarrativeClaim:
    key: str
    proposition: str
    confidence: float
    valence: float
    evidence_memory_ids: tuple[str, ...]
    updated_tick: int


@dataclass(slots=True)
class Consequence:
    action: Action
    description: str
    success: bool | None
    valence: float
    tags: tuple[str, ...] = ()
    world_changes: dict[str, Any] = field(default_factory=dict)
    source: str = "world"


@dataclass(slots=True)
class Experience:
    tick: int
    kind: str
    first_person: str
    intensity: float
    tags: tuple[str, ...] = ()


@dataclass(slots=True)
class ExpressionPacket:
    subject_id: str
    display_name: str
    intention: Action
    posture: tuple[str, ...]
    active_needs: tuple[tuple[str, float], ...]
    top_pressures: tuple[tuple[str, float], ...]
    relationship_stance: tuple[str, ...]
    current_experience: str
    leak_bucket: str
    constraint: str
    relevant_memories: tuple[str, ...]
    beliefs: tuple[str, ...]
    narrative: tuple[str, ...]
    dialogue: dict[str, tuple[str, ...]] = field(default_factory=dict, repr=False)
    private_content: dict[str, Any] = field(default_factory=dict, repr=False)


DEFAULT_NEEDS = {
    "energy": 0.80,
    "fatigue": 0.15,
    "hunger": 0.10,
    "thirst": 0.10,
    "comfort": 0.70,
    "pain": 0.00,
    "warmth": 0.60,
    "restlessness": 0.20,
    "curiosity": 0.35,
    "loneliness": 0.15,
    "safety": 0.75,
    "focus": 0.65,
    "satisfaction": 0.55,
}

DEFAULT_PRESSURES = {
    "shame": 0.10,
    "trust": 0.50,
    "fear": 0.15,
    "anger": 0.10,
    "attachment": 0.20,
    "arousal": 0.25,
    "self_story_stability": 0.85,
}

DEFAULT_SENSORIUM = {
    "light": 0.50,
    "noise": 0.20,
    "temperature": 0.55,
    "novelty": 0.15,
    "social_presence": 0.00,
    "clutter": 0.15,
}


@dataclass
class SubjectState:
    subject_id: str
    display_name: str
    cartridge_id: str = "neutral"
    tick: int = 0
    location: str = "unknown"
    present_others: list[str] = field(default_factory=list)
    needs: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_NEEDS))
    need_setpoints: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_NEEDS))
    pressures: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_PRESSURES))
    pressure_baselines: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_PRESSURES))
    sensorium: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_SENSORIUM))
    beliefs: dict[str, Belief] = field(default_factory=dict)
    concerns: dict[str, Concern] = field(default_factory=dict)
    memories: list[Memory] = field(default_factory=list)
    associations: list[Association] = field(default_factory=list)
    preferences: dict[str, Preference] = field(default_factory=dict)
    habits: dict[str, Habit] = field(default_factory=dict)
    relationships: dict[str, Relationship] = field(default_factory=dict)
    narrative: dict[str, NarrativeClaim] = field(default_factory=dict)
    unresolved: list[str] = field(default_factory=list)
    life_log: list[Experience] = field(default_factory=list)
    current_activity: Action = Action.WAIT
    current_experience: str = "I am present."
    last_intention: Action | None = None
    last_expression: str | None = None
    last_consequence: Consequence | None = None
    last_contact_tick: int = 0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["current_activity"] = self.current_activity.value
        if self.last_intention is not None:
            data["last_intention"] = self.last_intention.value
        if self.last_consequence is not None:
            data["last_consequence"]["action"] = self.last_consequence.action.value
        for habit in data["habits"].values():
            habit["action"] = habit["action"].value if isinstance(habit["action"], Action) else habit["action"]
        return data
