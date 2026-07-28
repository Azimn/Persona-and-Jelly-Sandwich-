from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from .models import Event


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(slots=True)
class RoomState:
    room_id: str = "room-001"
    name: str = "The Room"
    light: float = 0.50
    noise: float = 0.15
    temperature: float = 0.55
    clutter: float = 0.15
    novelty: float = 0.10
    occupants: list[str] = field(default_factory=list)
    objects: list[str] = field(default_factory=list)
    auto_day_cycle: bool = True
    last_updated_at: float = 0.0

    def sensorium(self) -> dict[str, float]:
        return {
            "light": _clamp(self.light),
            "noise": _clamp(self.noise),
            "temperature": _clamp(self.temperature),
            "clutter": _clamp(self.clutter),
            "novelty": _clamp(self.novelty),
            "social_presence": 1.0 if self.occupants else 0.0,
        }

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> "RoomState":
        raw = raw or {}
        return cls(
            room_id=str(raw.get("room_id", "room-001")),
            name=str(raw.get("name", "The Room")),
            light=_clamp(raw.get("light", 0.50)),
            noise=_clamp(raw.get("noise", 0.15)),
            temperature=_clamp(raw.get("temperature", 0.55)),
            clutter=_clamp(raw.get("clutter", 0.15)),
            novelty=_clamp(raw.get("novelty", 0.10)),
            occupants=[str(value) for value in raw.get("occupants", [])],
            objects=[str(value) for value in raw.get("objects", [])],
            auto_day_cycle=bool(raw.get("auto_day_cycle", True)),
            last_updated_at=float(raw.get("last_updated_at", 0.0)),
        )


class RoomWorld:
    """Small objective room model.

    It owns ambient facts and presence. It never writes memories, beliefs, or
    relationships directly. Those changes occur only when the engine receives
    an observation or lives through time with the room's sensorium applied.
    """

    def __init__(self, state: RoomState | None = None) -> None:
        self.state = state or RoomState()

    def apply_to(self, engine: Any) -> None:
        engine.state.location = self.state.room_id
        engine.state.present_others = list(self.state.occupants)
        sensorium = getattr(engine.state, "sensorium", None)
        if isinstance(sensorium, dict):
            sensorium.update(self.state.sensorium())

    def advance_to(self, timestamp: float) -> None:
        self.state.last_updated_at = float(timestamp)
        if self.state.auto_day_cycle:
            moment = datetime.fromtimestamp(timestamp)
            hour = moment.hour + moment.minute / 60.0
            self.state.light = self._daylight(hour)
            target_noise = 0.08 if hour < 6.0 or hour >= 22.0 else 0.16
            self.state.noise = _clamp(self.state.noise * 0.85 + target_noise * 0.15)
        self.state.novelty = _clamp(self.state.novelty * 0.97)

    @staticmethod
    def _daylight(hour: float) -> float:
        if hour < 5.0:
            return 0.08
        if hour < 8.0:
            return 0.08 + (hour - 5.0) / 3.0 * 0.57
        if hour < 18.0:
            return 0.65
        if hour < 21.0:
            return 0.65 - (hour - 18.0) / 3.0 * 0.47
        return 0.08

    def set_conditions(
        self,
        *,
        light: float | None = None,
        noise: float | None = None,
        temperature: float | None = None,
        clutter: float | None = None,
        novelty: float | None = None,
        name: str | None = None,
        timestamp: float | None = None,
    ) -> Event:
        before = self.state.sensorium()
        if light is not None:
            self.state.light = _clamp(light)
        if noise is not None:
            self.state.noise = _clamp(noise)
        if temperature is not None:
            self.state.temperature = _clamp(temperature)
        if clutter is not None:
            self.state.clutter = _clamp(clutter)
        if novelty is not None:
            self.state.novelty = _clamp(novelty)
        if name is not None:
            self.state.name = str(name)
        if timestamp is not None:
            self.state.last_updated_at = float(timestamp)

        after = self.state.sensorium()
        changed = {key: after[key] - before.get(key, after[key]) for key in after}
        dominant = max(changed, key=lambda key: abs(changed[key]), default="novelty")
        delta = changed.get(dominant, 0.0)

        if dominant == "noise":
            kind = "noise" if delta >= 0 else "quiet"
            meaning = "The room has become noisier around me." if delta >= 0 else "The room has become quieter around me."
        elif dominant == "temperature":
            kind = "warm" if delta >= 0 else "cold"
            meaning = "The room feels warmer around me." if delta >= 0 else "The room feels colder around me."
        else:
            kind = "environment_change"
            meaning = f"The conditions in {self.state.name} have changed around me."

        return Event(
            kind=kind,
            source="environment",
            description=f"Conditions changed in {self.state.name}.",
            intensity=min(1.0, 0.20 + abs(delta)),
            valence=0.0,
            tags=("environment", "room", dominant),
            metadata={
                "sensorium": after,
                "location": self.state.room_id,
                "first_person_meaning": meaning,
            },
        )

    def person_arrived(self, person_id: str, display_name: str | None = None) -> Event:
        person_id = str(person_id).strip()
        if not person_id:
            raise ValueError("person_id is required")
        if person_id not in self.state.occupants:
            self.state.occupants.append(person_id)
        self.state.novelty = _clamp(self.state.novelty + 0.25)
        name = display_name or person_id
        return Event(
            kind="person_arrived",
            source=person_id,
            description=f"{name} entered {self.state.name}.",
            intensity=0.45,
            valence=0.10,
            tags=(person_id, "arrival", "presence"),
            metadata={
                "person_id": person_id,
                "sensorium": self.state.sensorium(),
                "location": self.state.room_id,
            },
        )

    def person_left(self, person_id: str, display_name: str | None = None) -> Event:
        person_id = str(person_id).strip()
        if not person_id:
            raise ValueError("person_id is required")
        if person_id in self.state.occupants:
            self.state.occupants.remove(person_id)
        self.state.novelty = _clamp(self.state.novelty + 0.15)
        name = display_name or person_id
        return Event(
            kind="person_left",
            source=person_id,
            description=f"{name} left {self.state.name}.",
            intensity=0.40,
            valence=-0.05,
            tags=(person_id, "departure", "absence"),
            metadata={
                "person_id": person_id,
                "sensorium": self.state.sensorium(),
                "location": self.state.room_id,
            },
        )
