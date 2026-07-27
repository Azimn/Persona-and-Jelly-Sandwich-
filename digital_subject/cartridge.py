from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import Action, Habit, Preference, SubjectState


class CartridgeError(ValueError):
    pass


_ALLOWED_DIALOGUE_GROUPS = {
    "answer", "ask", "deflect", "conceal", "remain_silent", "repair", "challenge",
    "approach", "withdraw", "observe", "rest", "explore", "seek_contact",
    "self_soothe", "wait", "greeting", "return", "need", "memory", "identity",
}
_ALLOWED_SLOTS = {"name", "topic", "memory", "experience", "relationship", "need", "activity"}


@dataclass(frozen=True)
class ActivityProfile:
    action: Action
    trigger: str
    need_effects: dict[str, float]
    pressure_effects: dict[str, float]
    experience: str
    tags: tuple[str, ...]
    base_weight: float = 0.25


@dataclass(frozen=True)
class Cartridge:
    cartridge_id: str
    display_name: str
    identity: dict[str, Any]
    need_setpoints: dict[str, float]
    need_rates: dict[str, float]
    sensory_sensitivity: dict[str, float]
    preferences: tuple[Preference, ...]
    habits: tuple[Habit, ...]
    activities: tuple[ActivityProfile, ...]
    relationship_defaults: dict[str, float]
    dialogue: dict[str, tuple[str, ...]]
    reflection_interval: int = 12

    def create_state(self, subject_id: str) -> SubjectState:
        state = SubjectState(subject_id, self.display_name, cartridge_id=self.cartridge_id)
        state.need_setpoints.update(self.need_setpoints)
        state.needs.update(self.need_setpoints)
        state.preferences = {p.key: Preference(p.key, p.target, p.valence, p.confidence, p.learned, p.updated_tick) for p in self.preferences}
        state.habits = {h.key: Habit(h.key, h.trigger, h.action, h.strength, h.cooldown, h.last_used_tick) for h in self.habits}
        return state


def _require_table(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key)
    if not isinstance(value, dict):
        raise CartridgeError(f"missing required [{key}] table")
    return value


def _float_map(raw: Any, label: str) -> dict[str, float]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise CartridgeError(f"{label} must be a table")
    result: dict[str, float] = {}
    for key, value in raw.items():
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise CartridgeError(f"{label}.{key} must be numeric") from exc
        if not -1.0 <= number <= 1.0:
            raise CartridgeError(f"{label}.{key} must be within [-1, 1]")
        result[str(key)] = number
    return result


def _validate_template(text: str, group: str) -> None:
    import string
    fields = {name for _, name, _, _ in string.Formatter().parse(text) if name}
    unknown = fields - _ALLOWED_SLOTS
    if unknown:
        raise CartridgeError(f"dialogue.{group} uses unsupported slot: {sorted(unknown)[0]}")


def load_cartridge(path: str | Path) -> Cartridge:
    try:
        with open(path, "rb") as handle:
            raw = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise CartridgeError(f"could not load cartridge: {exc}") from exc

    metadata = _require_table(raw, "metadata")
    identity = _require_table(raw, "identity")
    cartridge_id = str(metadata.get("cartridge_id", "")).strip()
    display_name = str(metadata.get("display_name", "")).strip()
    if not cartridge_id or not display_name:
        raise CartridgeError("metadata.cartridge_id and metadata.display_name are required")

    homeostasis = _require_table(raw, "homeostasis")
    setpoints = _float_map(homeostasis.get("setpoints"), "homeostasis.setpoints")
    rates = _float_map(homeostasis.get("rates"), "homeostasis.rates")
    sensory = _float_map(raw.get("sensory", {}).get("sensitivity", {}), "sensory.sensitivity")
    relationship_defaults = _float_map(raw.get("relationships", {}).get("defaults", {}), "relationships.defaults")

    preferences: list[Preference] = []
    for index, item in enumerate(raw.get("preferences", [])):
        if not isinstance(item, dict):
            raise CartridgeError(f"preferences[{index}] must be a table")
        key = str(item.get("key", "")).strip()
        target = str(item.get("target", "")).strip()
        if not key or not target:
            raise CartridgeError(f"preferences[{index}] requires key and target")
        preferences.append(Preference(key, target, float(item.get("valence", 0.0)), float(item.get("confidence", 0.5))))

    habits: list[Habit] = []
    for index, item in enumerate(raw.get("habits", [])):
        if not isinstance(item, dict):
            raise CartridgeError(f"habits[{index}] must be a table")
        try:
            action = Action(str(item["action"]))
        except (KeyError, ValueError) as exc:
            raise CartridgeError(f"habits[{index}] has unsupported action") from exc
        habits.append(Habit(str(item.get("key", f"habit_{index}")), str(item.get("trigger", "")), action, float(item.get("strength", 0.5)), int(item.get("cooldown", 0))))

    activities: list[ActivityProfile] = []
    for index, item in enumerate(raw.get("activities", [])):
        if not isinstance(item, dict):
            raise CartridgeError(f"activities[{index}] must be a table")
        try:
            action = Action(str(item["action"]))
        except (KeyError, ValueError) as exc:
            raise CartridgeError(f"activities[{index}] has unsupported action") from exc
        activities.append(ActivityProfile(
            action=action,
            trigger=str(item.get("trigger", "always")),
            need_effects=_float_map(item.get("need_effects", {}), f"activities[{index}].need_effects"),
            pressure_effects=_float_map(item.get("pressure_effects", {}), f"activities[{index}].pressure_effects"),
            experience=str(item.get("experience", "I pass the time.")),
            tags=tuple(str(tag) for tag in item.get("tags", [])),
            base_weight=float(item.get("base_weight", 0.25)),
        ))

    dialogue_raw = raw.get("dialogue", {})
    if not isinstance(dialogue_raw, dict):
        raise CartridgeError("dialogue must be a table")
    dialogue: dict[str, tuple[str, ...]] = {}
    for group, values in dialogue_raw.items():
        if group not in _ALLOWED_DIALOGUE_GROUPS:
            raise CartridgeError(f"unsupported dialogue group: {group}")
        if not isinstance(values, list) or not values or not all(isinstance(v, str) and v.strip() for v in values):
            raise CartridgeError(f"dialogue.{group} must be a nonempty string list")
        for value in values:
            _validate_template(value, group)
        dialogue[group] = tuple(values)

    return Cartridge(
        cartridge_id=cartridge_id,
        display_name=display_name,
        identity=identity,
        need_setpoints=setpoints,
        need_rates=rates,
        sensory_sensitivity=sensory,
        preferences=tuple(preferences),
        habits=tuple(habits),
        activities=tuple(activities),
        relationship_defaults=relationship_defaults,
        dialogue=dialogue,
        reflection_interval=max(4, int(raw.get("reflection", {}).get("interval", 12))),
    )
