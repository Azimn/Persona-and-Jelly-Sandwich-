from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from .cartridge import ActivityProfile, Cartridge
from .models import (
    Action, Association, Belief, Concern, Consequence, Event, Experience,
    ExpressionPacket, Habit, Memory, NarrativeClaim, OwnedEvent, Preference,
    Relationship, SubjectState,
)
from .rules import EVENT_RULES, EXPRESSION_CONSTRAINTS, INHIBITION, NEED_ACTIONS, PRESSURE_ACTIONS, PRESSURE_RETENTION


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def clamp_signed(value: float) -> float:
    return max(-1.0, min(1.0, value))


class SubjectEngine:
    def __init__(self, state: SubjectState, cartridge: Cartridge, *, memory_limit: int = 128, association_limit: int = 32, top_k: int = 4) -> None:
        if state.cartridge_id != cartridge.cartridge_id:
            raise ValueError("state and cartridge identities do not match")
        self.state = state
        self.cartridge = cartridge
        self.memory_limit = memory_limit
        self.association_limit = association_limit
        self.top_k = top_k

    @classmethod
    def from_cartridge(cls, cartridge: Cartridge, subject_id: str = "subject-001") -> "SubjectEngine":
        return cls(cartridge.create_state(subject_id), cartridge)

    def step(self, event: Event) -> ExpressionPacket:
        self._advance_time(1)
        owned = self._own_event(event)
        self._apply_event(owned)
        self._update_world_presence(event)
        self._learn_preference(owned)
        self._update_relationship(owned)
        self._maybe_reflect(force=event.intensity >= 0.8)
        needs = self._triage_needs()
        pressures = self._triage_pressures()
        intention = self._choose_intention(event, needs, pressures)
        leak = self._compute_leak_risk(owned, needs, pressures)
        packet = self._make_packet(owned, intention, needs, pressures, self._bucket(leak))
        self.state.last_intention = intention
        self.state.current_activity = intention
        return packet

    def live(self, ticks: int = 1) -> list[Experience]:
        experiences: list[Experience] = []
        for _ in range(max(0, ticks)):
            self._advance_time(1)
            activity = self._select_idle_activity()
            experience = self._perform_activity(activity)
            experiences.append(experience)
            self._maybe_reflect()
        return experiences

    def idle_tick(self, ticks: int = 1) -> None:
        self.live(ticks)

    def apply_consequence(self, consequence: Consequence) -> None:
        self._advance_time(1)
        kind = "success" if consequence.success is True else "failure" if consequence.success is False else "consequence"
        rule = EVENT_RULES.get(kind)
        if rule:
            scale = max(0.25, abs(consequence.valence))
            for key, amount in rule.pressure_deltas.items():
                self._adjust_pressure(key, amount * scale)
            for key, amount in rule.need_deltas.items():
                self._adjust_need(key, amount * scale)
        if consequence.source not in {"world", "self", "system"}:
            relationship = self._relationship(consequence.source)
            relationship.trust = clamp(relationship.trust + consequence.valence * 0.04)
            relationship.comfort = clamp(relationship.comfort + consequence.valence * 0.03)
        if consequence.success is False:
            self.state.unresolved.append(consequence.description)
            self.state.unresolved = self.state.unresolved[-24:]
        memory = Memory(
            str(uuid.uuid4()), consequence.description, self._consequence_meaning(consequence),
            tuple(dict.fromkeys(("consequence", consequence.action.value, *consequence.tags))),
            clamp(0.45 + abs(consequence.valence) * 0.4), clamp(abs(consequence.valence)),
            self.state.tick, self.state.tick,
        )
        self._store_memory(memory)
        self.state.last_consequence = consequence
        self._maybe_reflect(force=abs(consequence.valence) >= 0.7)

    def record_expression(self, text: str) -> None:
        self.state.last_expression = text

    def debug_snapshot(self) -> dict:
        return {
            "tick": self.state.tick,
            "subject": self.state.display_name,
            "current_experience": self.state.current_experience,
            "current_activity": self.state.current_activity.value,
            "needs": {k: round(v, 4) for k, v in sorted(self.state.needs.items())},
            "top_needs": [(k, round(v, 4)) for k, v in self._triage_needs()],
            "pressures": {k: round(v, 4) for k, v in sorted(self.state.pressures.items())},
            "top_pressures": [(k, round(v, 4)) for k, v in self._triage_pressures()],
            "sensorium": {k: round(v, 4) for k, v in sorted(self.state.sensorium.items())},
            "preferences": {k: {"target": p.target, "valence": round(p.valence, 4), "confidence": round(p.confidence, 4), "learned": p.learned} for k, p in self.state.preferences.items()},
            "relationships": {k: {field: round(getattr(r, field), 4) for field in ("trust", "comfort", "respect", "interest", "attachment", "affection", "safety", "familiarity", "obligation", "uncertainty")} for k, r in self.state.relationships.items()},
            "narrative": {k: {"proposition": n.proposition, "confidence": round(n.confidence, 4), "valence": round(n.valence, 4)} for k, n in self.state.narrative.items()},
            "beliefs": {k: {"proposition": b.proposition, "confidence": round(b.confidence, 4), "valence": round(b.valence, 4)} for k, b in self.state.beliefs.items()},
            "unresolved": list(self.state.unresolved),
            "memory_count": len(self.state.memories),
            "life_log": [asdict(e) for e in self.state.life_log[-8:]],
            "last_intention": self.state.last_intention.value if self.state.last_intention else None,
            "last_expression": self.state.last_expression,
            "last_consequence": asdict(self.state.last_consequence) if self.state.last_consequence else None,
        }

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.state.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path, cartridge: Cartridge) -> "SubjectEngine":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        state = SubjectState(
            raw["subject_id"], raw["display_name"], cartridge_id=raw.get("cartridge_id", cartridge.cartridge_id),
            tick=raw.get("tick", 0), location=raw.get("location", "unknown"), present_others=raw.get("present_others", []),
            needs=raw.get("needs", {}), need_setpoints=raw.get("need_setpoints", {}), pressures=raw.get("pressures", {}),
            pressure_baselines=raw.get("pressure_baselines", {}), sensorium=raw.get("sensorium", {}),
        )
        state.beliefs = {k: Belief(**v) for k, v in raw.get("beliefs", {}).items()}
        state.concerns = {k: Concern(**v) for k, v in raw.get("concerns", {}).items()}
        state.memories = [Memory(**v) for v in raw.get("memories", [])]
        state.associations = [Association(**v) for v in raw.get("associations", [])]
        state.preferences = {k: Preference(**v) for k, v in raw.get("preferences", {}).items()}
        state.habits = {k: Habit(**{**v, "action": Action(v["action"])}) for k, v in raw.get("habits", {}).items()}
        state.relationships = {k: Relationship(**v) for k, v in raw.get("relationships", {}).items()}
        state.narrative = {k: NarrativeClaim(**{**v, "evidence_memory_ids": tuple(v.get("evidence_memory_ids", ()))}) for k, v in raw.get("narrative", {}).items()}
        state.unresolved = raw.get("unresolved", [])
        state.life_log = [Experience(**{**v, "tags": tuple(v.get("tags", ()))}) for v in raw.get("life_log", [])]
        state.current_activity = Action(raw.get("current_activity", "wait"))
        state.current_experience = raw.get("current_experience", "I am present.")
        if raw.get("last_intention"):
            state.last_intention = Action(raw["last_intention"])
        state.last_expression = raw.get("last_expression")
        if raw.get("last_consequence"):
            c = raw["last_consequence"]
            state.last_consequence = Consequence(**{**c, "action": Action(c["action"]), "tags": tuple(c.get("tags", ()))})
        state.last_contact_tick = raw.get("last_contact_tick", 0)
        return cls(state, cartridge)

    def _advance_time(self, ticks: int) -> None:
        for _ in range(ticks):
            self.state.tick += 1
            self._advance_homeostasis()
            self._decay_private_state()
            self._apply_sensorium()
            self._advance_social_absence()

    def _advance_homeostasis(self) -> None:
        rates = self.cartridge.need_rates
        for key, rate in rates.items():
            self._adjust_need(key, rate)
        fatigue = self.state.needs.get("fatigue", 0.0)
        self._adjust_need("energy", -0.002 - fatigue * 0.002)
        self._adjust_need("focus", -fatigue * 0.002)
        self._adjust_need("restlessness", 0.001 + self.state.needs.get("curiosity", 0.0) * 0.001)
        if self.state.present_others:
            self._adjust_need("loneliness", -0.004)
        else:
            self._adjust_need("loneliness", 0.002)

    def _decay_private_state(self) -> None:
        for key, value in list(self.state.pressures.items()):
            baseline = self.state.pressure_baselines.get(key, 0.0)
            retention = PRESSURE_RETENTION.get(key, 0.98)
            self.state.pressures[key] = clamp(baseline + (value - baseline) * retention)
        for concern in self.state.concerns.values():
            concern.urgency = clamp(concern.urgency * concern.persistence)
        self.state.concerns = {k: c for k, c in self.state.concerns.items() if c.urgency >= 0.02}
        for memory in self.state.memories:
            memory.strength = clamp(memory.strength * (0.9998 if memory.kind == "narrative" else 0.9992))
        for association in self.state.associations:
            association.strength = clamp(association.strength * 0.999)

    def _apply_sensorium(self) -> None:
        sensitivity = self.cartridge.sensory_sensitivity
        noise = self.state.sensorium.get("noise", 0.0) * sensitivity.get("noise", 0.5)
        clutter = self.state.sensorium.get("clutter", 0.0) * sensitivity.get("clutter", 0.5)
        temperature = self.state.sensorium.get("temperature", 0.5)
        self._adjust_need("comfort", -(noise + clutter) * 0.002)
        self._adjust_need("focus", -noise * 0.002)
        self._adjust_need("warmth", (temperature - 0.5) * sensitivity.get("temperature", 0.5) * 0.004)
        novelty = self.state.sensorium.get("novelty", 0.0)
        self._adjust_need("curiosity", novelty * sensitivity.get("novelty", 0.5) * 0.002)
        self.state.sensorium["novelty"] = clamp(novelty * 0.97)

    def _advance_social_absence(self) -> None:
        if self.state.tick - self.state.last_contact_tick > 10:
            self._adjust_need("loneliness", 0.0015)
        for relationship in self.state.relationships.values():
            if self.state.tick - relationship.last_contact_tick > 24:
                relationship.uncertainty = clamp(relationship.uncertainty + 0.0008)

    def _own_event(self, event: Event) -> OwnedEvent:
        rule = EVENT_RULES.get(event.kind)
        matched = self._retrieve_memories(event.tags, 4)
        relevance = clamp(event.intensity + (0.15 if event.target == "self" else 0.0) + 0.04 * len(matched))
        surprise = clamp(abs(event.actual_valence - event.expected_valence)) if event.expected_valence is not None and event.actual_valence is not None else clamp(event.intensity * 0.35)
        meaning = str(event.metadata.get("first_person_meaning") or (rule.meaning if rule else f"This event concerns me: {event.description}"))
        for memory in matched:
            memory.last_recalled_tick = self.state.tick
            memory.recall_count += 1
            memory.strength = clamp(memory.strength + 0.025)
        self._record_experience("event", meaning, relevance, event.tags)
        return OwnedEvent(event, meaning, relevance, surprise, tuple(m.id for m in matched))

    def _apply_event(self, owned: OwnedEvent) -> None:
        event = owned.event
        rule = EVENT_RULES.get(event.kind)
        if rule:
            scale = event.intensity * (1.0 + owned.surprise * 0.4)
            for key, amount in rule.pressure_deltas.items():
                self._adjust_pressure(key, amount * scale)
            for key, amount in rule.need_deltas.items():
                self._adjust_need(key, amount * scale)
            if rule.concern:
                urgency = clamp(0.25 + event.intensity * 0.55 + owned.surprise * 0.2)
                current = self.state.concerns.get(rule.concern)
                if current:
                    current.urgency = clamp(current.urgency + urgency * 0.35)
                    current.last_updated_tick = self.state.tick
                else:
                    self.state.concerns[rule.concern] = Concern(rule.concern, owned.first_person_meaning, urgency, 0.985, self.state.tick)
                if event.kind in {"ignored", "accusation", "sensitive_topic", "betrayal", "failure", "silence"}:
                    self.state.unresolved.append(owned.first_person_meaning)
                    self.state.unresolved = self.state.unresolved[-24:]
            if rule.belief_key and rule.belief_text:
                self._update_belief(rule.belief_key, rule.belief_text, 0.12 * event.intensity, rule.belief_valence)
        self._apply_environment_metadata(event.metadata)
        charge = clamp(abs(event.valence) + event.intensity * 0.7 + owned.surprise * 0.2)
        self._store_memory(Memory(str(uuid.uuid4()), event.description, owned.first_person_meaning, event.tags, clamp(0.3 + event.intensity * 0.45 + owned.surprise * 0.25), charge, self.state.tick, self.state.tick))
        self._update_associations(event.tags)

    def _apply_environment_metadata(self, metadata: dict) -> None:
        sensory = metadata.get("sensorium", {})
        if isinstance(sensory, dict):
            for key, value in sensory.items():
                try:
                    self.state.sensorium[str(key)] = clamp(float(value))
                except (TypeError, ValueError):
                    continue
        if "location" in metadata:
            self.state.location = str(metadata["location"])

    def _update_world_presence(self, event: Event) -> None:
        person = str(event.metadata.get("person_id", event.source))
        if event.kind == "person_arrived" and person not in self.state.present_others:
            self.state.present_others.append(person)
        elif event.kind == "person_left" and person in self.state.present_others:
            self.state.present_others.remove(person)
        if event.source not in {"world", "self", "system", "environment"}:
            self.state.last_contact_tick = self.state.tick

    def _learn_preference(self, owned: OwnedEvent) -> None:
        event = owned.event
        signal = event.actual_valence if event.actual_valence is not None else event.valence
        if signal == 0.0:
            return
        for tag in event.tags:
            key = f"learned:{tag}"
            existing = self.state.preferences.get(key)
            delta = signal * event.intensity * 0.12
            if existing:
                existing.valence = clamp_signed(existing.valence + delta * (1.0 - existing.confidence * 0.5))
                existing.confidence = clamp(existing.confidence + abs(delta) * 0.25)
                existing.updated_tick = self.state.tick
            else:
                self.state.preferences[key] = Preference(key, tag, clamp_signed(delta), clamp(0.25 + abs(delta)), True, self.state.tick)

    def _relationship(self, person_id: str) -> Relationship:
        if person_id not in self.state.relationships:
            defaults = self.cartridge.relationship_defaults
            self.state.relationships[person_id] = Relationship(person_id, **{k: defaults[k] for k in defaults if k in Relationship.__dataclass_fields__})
        return self.state.relationships[person_id]

    def _update_relationship(self, owned: OwnedEvent) -> None:
        source = owned.event.source
        if source in {"world", "self", "system", "environment"}:
            return
        relationship = self._relationship(source)
        rule = EVENT_RULES.get(owned.event.kind)
        if rule:
            for key, delta in rule.relationship_deltas.items():
                if hasattr(relationship, key):
                    setattr(relationship, key, clamp(getattr(relationship, key) + delta * owned.event.intensity))
        relationship.familiarity = clamp(relationship.familiarity + 0.01 + owned.event.intensity * 0.01)
        relationship.interest = clamp(relationship.interest + self.state.needs.get("curiosity", 0.0) * 0.003)
        relationship.attachment = clamp(relationship.attachment + max(0.0, relationship.trust - 0.5) * 0.005)
        relationship.last_contact_tick = self.state.tick

    def _triage_needs(self) -> list[tuple[str, float]]:
        scored: list[tuple[str, float]] = []
        low_is_bad = {"energy", "comfort", "warmth", "safety", "focus", "satisfaction"}
        for key, value in self.state.needs.items():
            urgency = 1.0 - value if key in low_is_bad else value
            if key in {"hunger", "thirst", "pain", "fatigue", "loneliness"}:
                urgency = value
            scored.append((key, clamp(urgency)))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:self.top_k]

    def _triage_pressures(self) -> list[tuple[str, float]]:
        scored: list[tuple[str, float]] = []
        for key, value in self.state.pressures.items():
            magnitude = abs(value - self.state.pressure_baselines.get(key, 0.0))
            if key == "self_story_stability":
                magnitude = 1.0 - value
            scored.append((key, clamp(magnitude)))
        scored.extend((f"concern:{c.key}", c.urgency) for c in self.state.concerns.values())
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:self.top_k]

    def _choose_intention(self, event: Event, needs: list[tuple[str, float]], pressures: list[tuple[str, float]]) -> Action:
        if event.kind in {"apology"}:
            return Action.REPAIR
        dominant_pressure = pressures[0] if pressures else ("trust", 0.0)
        dominant_need = needs[0] if needs else ("curiosity", 0.0)
        if dominant_pressure[1] >= dominant_need[1] + 0.12:
            key = dominant_pressure[0].replace("concern:", "")
            options = PRESSURE_ACTIONS.get(key, (Action.ANSWER, Action.ASK, Action.DEFLECT))
        else:
            options = NEED_ACTIONS.get(dominant_need[0], (Action.ANSWER, Action.ASK, Action.OBSERVE))
        habit = self._matching_habit(dominant_need[0], dominant_pressure[0])
        if habit and habit.strength >= 0.65 and self.state.tick - habit.last_used_tick > habit.cooldown:
            habit.last_used_tick = self.state.tick
            return habit.action
        if self.state.pressures.get("trust", 0.5) < 0.25 and Action.CONCEAL in options:
            return Action.CONCEAL
        return options[0]

    def _matching_habit(self, need_key: str, pressure_key: str) -> Habit | None:
        candidates = [h for h in self.state.habits.values() if h.trigger in {need_key, pressure_key, pressure_key.replace("concern:", "")}]
        return max(candidates, key=lambda h: h.strength, default=None)

    def _select_idle_activity(self) -> ActivityProfile | None:
        needs = self._triage_needs()
        pressures = self._triage_pressures()
        dominant_need = needs[0][0] if needs else "curiosity"
        dominant_pressure = pressures[0][0].replace("concern:", "") if pressures else ""
        scored: list[tuple[float, ActivityProfile]] = []
        for activity in self.cartridge.activities:
            score = activity.base_weight
            if activity.trigger in {"always", dominant_need, dominant_pressure}:
                score += 0.60
            habit = self._matching_habit(dominant_need, dominant_pressure)
            if habit and habit.action == activity.action:
                score += habit.strength * 0.35
            score += self._stable_jitter(activity.action.value, self.state.tick) * 0.001
            scored.append((score, activity))
        return max(scored, key=lambda item: item[0])[1] if scored else None

    def _perform_activity(self, activity: ActivityProfile | None) -> Experience:
        if activity is None:
            self.state.current_activity = Action.WAIT
            return self._record_experience("idle", "I wait while my condition continues to change.", 0.15, ("wait",))
        self.state.current_activity = activity.action
        for key, delta in activity.need_effects.items():
            self._adjust_need(key, delta)
        for key, delta in activity.pressure_effects.items():
            self._adjust_pressure(key, delta)
        experience = self._record_experience("activity", activity.experience, 0.25 + self._triage_needs()[0][1] * 0.35, activity.tags)
        if experience.intensity >= 0.55 or self.state.tick % 8 == 0:
            self._store_memory(Memory(str(uuid.uuid4()), activity.experience, activity.experience, activity.tags, 0.30, experience.intensity * 0.5, self.state.tick, self.state.tick, kind="activity"))
        return experience

    def _maybe_reflect(self, force: bool = False) -> None:
        if not force and self.state.tick % self.cartridge.reflection_interval != 0:
            return
        recent = self.state.memories[-24:]
        if len(recent) < 3:
            return
        tag_scores: dict[str, list[Memory]] = {}
        for memory in recent:
            for tag in memory.tags:
                tag_scores.setdefault(tag, []).append(memory)
        repeated = [(tag, memories) for tag, memories in tag_scores.items() if len(memories) >= 3]
        if repeated:
            tag, memories = max(repeated, key=lambda item: (len(item[1]), sum(m.emotional_charge for m in item[1])))
            avg = sum(self._memory_valence(m) for m in memories) / len(memories)
            proposition = self._narrative_sentence(tag, avg)
            key = f"pattern:{tag}"
            evidence = tuple(m.id for m in memories[-5:])
            current = self.state.narrative.get(key)
            confidence = clamp(0.35 + len(memories) * 0.08)
            if current:
                current.confidence = clamp(max(current.confidence, confidence) + 0.02)
                current.valence = clamp_signed((current.valence + avg) / 2)
                current.evidence_memory_ids = evidence
                current.updated_tick = self.state.tick
            else:
                self.state.narrative[key] = NarrativeClaim(key, proposition, confidence, clamp_signed(avg), evidence, self.state.tick)
                self._store_memory(Memory(str(uuid.uuid4()), proposition, f"I formed a conclusion about my life: {proposition}", ("narrative", tag), 0.75, abs(avg), self.state.tick, self.state.tick, kind="narrative"))

    @staticmethod
    def _memory_valence(memory: Memory) -> float:
        negative = {"betrayal", "accusation", "ignored", "failure", "pain", "threat"}
        positive = {"kindness", "praise", "promise", "repair", "success", "comfort"}
        tags = set(memory.tags)
        if tags & negative:
            return -memory.emotional_charge
        if tags & positive:
            return memory.emotional_charge
        return 0.0

    @staticmethod
    def _narrative_sentence(tag: str, valence: float) -> str:
        readable = tag.replace("_", " ")
        if valence > 0.15:
            return f"Experiences involving {readable} have generally made my life feel safer or more worthwhile."
        if valence < -0.15:
            return f"Experiences involving {readable} have repeatedly carried risk or hurt for me."
        return f"Experiences involving {readable} keep returning, though I have not settled what they mean."

    def _compute_leak_risk(self, owned: OwnedEvent, needs: list[tuple[str, float]], pressures: list[tuple[str, float]]) -> float:
        pressure_key, pressure_magnitude = pressures[0] if pressures else ("trust", 0.0)
        pressure_key = pressure_key.replace("concern:", "")
        need_magnitude = needs[0][1] if needs else 0.0
        inhibition_weakness = 1.0 - INHIBITION.get(pressure_key, 0.5)
        depletion = 1.0 + (1.0 - self.state.needs.get("energy", 0.5)) * 0.65 + self.state.needs.get("fatigue", 0.0) * 0.35
        trigger = 1.0 + owned.self_relevance * 0.25 + owned.surprise * 0.25
        return clamp(max(pressure_magnitude * inhibition_weakness, need_magnitude * 0.25) * depletion * trigger)

    @staticmethod
    def _bucket(value: float) -> str:
        return "low" if value < 0.31 else "medium" if value < 0.66 else "high"

    def _make_packet(self, owned: OwnedEvent, intention: Action, needs: list[tuple[str, float]], pressures: list[tuple[str, float]], leak_bucket: str) -> ExpressionPacket:
        memories = tuple(m.summary for m in self._memories_by_ids(owned.matched_memory_ids))
        beliefs = tuple(b.proposition for b in sorted(self.state.beliefs.values(), key=lambda x: x.confidence, reverse=True)[:3])
        narrative = tuple(n.proposition for n in sorted(self.state.narrative.values(), key=lambda x: x.confidence, reverse=True)[:3])
        relationship = self.state.relationships.get(owned.event.source)
        stance = self._relationship_stance(relationship) if relationship else ()
        posture = tuple(self._posture_line(k, v) for k, v in pressures)
        private = {"owned_meaning": owned.first_person_meaning, "self_relevance": owned.self_relevance, "surprise": owned.surprise, "sensorium": dict(self.state.sensorium)}
        return ExpressionPacket(self.state.subject_id, self.state.display_name, intention, posture, tuple(needs), tuple(pressures), stance, self.state.current_experience, leak_bucket, EXPRESSION_CONSTRAINTS[leak_bucket], memories, beliefs, narrative, self.cartridge.dialogue, private)

    @staticmethod
    def _relationship_stance(relationship: Relationship) -> tuple[str, ...]:
        result = []
        if relationship.trust >= 0.65:
            result.append("trusting")
        elif relationship.trust <= 0.25:
            result.append("distrustful")
        if relationship.comfort >= 0.65:
            result.append("comfortable")
        if relationship.attachment >= 0.55:
            result.append("attached")
        if relationship.uncertainty >= 0.65:
            result.append("uncertain")
        return tuple(result or ("measured",))

    @staticmethod
    def _posture_line(name: str, magnitude: float) -> str:
        label = name.replace("concern:", "").replace("_", " ")
        level = "dominant" if magnitude >= 0.66 else "active" if magnitude >= 0.31 else "present"
        return f"{label}: {level}"

    def _record_experience(self, kind: str, text: str, intensity: float, tags: Iterable[str]) -> Experience:
        experience = Experience(self.state.tick, kind, text, clamp(intensity), tuple(tags))
        self.state.current_experience = text
        self.state.life_log.append(experience)
        self.state.life_log = self.state.life_log[-64:]
        return experience

    def _adjust_need(self, key: str, delta: float) -> None:
        self.state.needs[key] = clamp(self.state.needs.get(key, self.state.need_setpoints.get(key, 0.5)) + delta)

    def _adjust_pressure(self, key: str, delta: float) -> None:
        self.state.pressures[key] = clamp(self.state.pressures.get(key, self.state.pressure_baselines.get(key, 0.0)) + delta)

    def _update_belief(self, key: str, proposition: str, confidence_delta: float, valence: float) -> None:
        if key in self.state.beliefs:
            belief = self.state.beliefs[key]
            belief.confidence = clamp(belief.confidence + confidence_delta)
            belief.valence = clamp_signed((belief.valence + valence) / 2)
            belief.updated_tick = self.state.tick
        else:
            self.state.beliefs[key] = Belief(key, proposition, clamp(0.35 + confidence_delta), clamp_signed(valence), self.state.tick)

    def _store_memory(self, memory: Memory) -> None:
        self.state.memories.append(memory)
        if len(self.state.memories) > self.memory_limit:
            self.state.memories.sort(key=lambda m: (m.kind == "narrative", m.strength + m.emotional_charge * 0.25, m.last_recalled_tick), reverse=True)
            self.state.memories = self.state.memories[:self.memory_limit]

    def _retrieve_memories(self, tags: Iterable[str], limit: int) -> list[Memory]:
        tag_set = set(tags)
        scored: list[tuple[float, Memory]] = []
        for memory in self.state.memories:
            overlap = len(tag_set.intersection(memory.tags))
            association_bonus = sum(a.strength for a in self.state.associations if (a.left in tag_set and a.right in memory.tags) or (a.right in tag_set and a.left in memory.tags))
            if not overlap and not association_bonus:
                continue
            recency = 1.0 / (1.0 + max(0, self.state.tick - memory.last_recalled_tick))
            score = overlap * 0.45 + association_bonus * 0.20 + memory.strength * 0.25 + memory.emotional_charge * 0.08 + recency * 0.02
            scored.append((score, memory))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [memory for _, memory in scored[:limit]]

    def _memories_by_ids(self, ids: Iterable[str]) -> list[Memory]:
        wanted = set(ids)
        return [memory for memory in self.state.memories if memory.id in wanted]

    def _update_associations(self, tags: tuple[str, ...]) -> None:
        unique = tuple(dict.fromkeys(tags))
        for index, left in enumerate(unique):
            for right in unique[index + 1:]:
                existing = next((a for a in self.state.associations if {a.left, a.right} == {left, right}), None)
                if existing:
                    existing.strength = clamp(existing.strength + 0.08)
                    existing.last_used_tick = self.state.tick
                else:
                    self.state.associations.append(Association(left, right, 0.25, self.state.tick))
        if len(self.state.associations) > self.association_limit:
            self.state.associations.sort(key=lambda a: (a.strength, a.last_used_tick), reverse=True)
            self.state.associations = self.state.associations[:self.association_limit]

    @staticmethod
    def _consequence_meaning(consequence: Consequence) -> str:
        if consequence.success is True:
            return "My action changed the situation in the direction I intended."
        if consequence.success is False:
            return "My action failed, and I must now live with that failure."
        return "My action changed the situation in a way I did not fully control."

    @staticmethod
    def _stable_jitter(*parts: object) -> int:
        digest = hashlib.blake2b("|".join(map(str, parts)).encode("utf-8"), digest_size=2).digest()
        return int.from_bytes(digest, "big") % 101
