from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from .models import Event


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


@dataclass(slots=True)
class EpistemicRecord:
    id: str
    tick: int
    source: str
    objective_record: str
    perceived_record: str
    interpretation: str
    confidence: float
    tags: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    status: str = "provisional"
    revised_by: str | None = None


@dataclass(slots=True)
class Expectation:
    id: str
    proposition: str
    created_tick: int
    due_tick: int | None
    confidence: float
    source_record_ids: tuple[str, ...] = ()
    status: str = "pending"
    outcome: str | None = None
    prediction_error: float | None = None
    resolved_tick: int | None = None


@dataclass(slots=True)
class Commitment:
    id: str
    actor: str
    description: str
    beneficiary: str
    created_tick: int
    due_tick: int | None
    importance: float
    evidence_ids: tuple[str, ...] = ()
    status: str = "open"
    outcome: str | None = None
    resolved_tick: int | None = None


@dataclass(slots=True)
class ReflectionInsight:
    id: str
    kind: str
    proposition: str
    confidence: float
    evidence_ids: tuple[str, ...]
    created_tick: int
    trigger: str


@dataclass(slots=True)
class ContinuityState:
    schema_version: int = 1
    epistemic_records: list[EpistemicRecord] = field(default_factory=list)
    expectations: dict[str, Expectation] = field(default_factory=dict)
    commitments: dict[str, Commitment] = field(default_factory=dict)
    insights: list[ReflectionInsight] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> "ContinuityState":
        raw = raw or {}
        return cls(
            schema_version=int(raw.get("schema_version", 1)),
            epistemic_records=[
                EpistemicRecord(
                    **{
                        **item,
                        "tags": tuple(item.get("tags", ())),
                        "evidence_ids": tuple(item.get("evidence_ids", ())),
                    }
                )
                for item in raw.get("epistemic_records", [])
            ],
            expectations={
                key: Expectation(
                    **{
                        **item,
                        "source_record_ids": tuple(item.get("source_record_ids", ())),
                    }
                )
                for key, item in raw.get("expectations", {}).items()
            },
            commitments={
                key: Commitment(
                    **{
                        **item,
                        "evidence_ids": tuple(item.get("evidence_ids", ())),
                    }
                )
                for key, item in raw.get("commitments", {}).items()
            },
            insights=[
                ReflectionInsight(
                    **{
                        **item,
                        "evidence_ids": tuple(item.get("evidence_ids", ())),
                    }
                )
                for item in raw.get("insights", [])
            ],
        )


class SubjectContinuity:
    """Small subject-owned ledger for interpretation, prediction, and obligation.

    This subsystem is deterministic and model-independent. External import tools may
    prepare records, but only validated records enter this runtime state.
    """

    def __init__(
        self,
        state: ContinuityState | None = None,
        *,
        record_limit: int = 256,
        insight_limit: int = 64,
    ) -> None:
        self.state = state or ContinuityState()
        self.record_limit = max(16, int(record_limit))
        self.insight_limit = max(8, int(insight_limit))

    def observe(
        self,
        event: Event,
        *,
        tick: int,
        interpretation: str,
        evidence_ids: tuple[str, ...] = (),
    ) -> EpistemicRecord:
        metadata = event.metadata if isinstance(event.metadata, dict) else {}
        objective = str(metadata.get("objective_record") or event.description)
        perceived = str(metadata.get("perceived_record") or event.description)
        confidence = _clamp(metadata.get("interpretation_confidence", 0.55))
        record = EpistemicRecord(
            id=str(uuid.uuid4()),
            tick=int(tick),
            source=str(event.source),
            objective_record=objective,
            perceived_record=perceived,
            interpretation=str(metadata.get("interpretation") or interpretation),
            confidence=confidence,
            tags=tuple(dict.fromkeys(str(tag) for tag in event.tags)),
            evidence_ids=tuple(dict.fromkeys(str(value) for value in evidence_ids)),
        )
        self.state.epistemic_records.append(record)
        self.state.epistemic_records = self.state.epistemic_records[-self.record_limit :]
        self._apply_metadata(event, record)
        self._apply_event_conventions(event, record)
        self._maybe_reflect(record)
        return record

    def revise_record(
        self,
        record_id: str,
        *,
        interpretation: str,
        evidence_id: str,
        confidence: float,
        tick: int,
    ) -> EpistemicRecord:
        original = self._record(record_id)
        revision = EpistemicRecord(
            id=str(uuid.uuid4()),
            tick=int(tick),
            source="revision",
            objective_record=original.objective_record,
            perceived_record=original.perceived_record,
            interpretation=str(interpretation),
            confidence=_clamp(confidence),
            tags=tuple(dict.fromkeys((*original.tags, "revision"))),
            evidence_ids=tuple(dict.fromkeys((*original.evidence_ids, str(evidence_id), original.id))),
            status="revised",
        )
        original.status = "superseded"
        original.revised_by = revision.id
        self.state.epistemic_records.append(revision)
        self.state.epistemic_records = self.state.epistemic_records[-self.record_limit :]
        self._add_insight(
            "revised_belief",
            f"Later evidence changed how I understand: {original.objective_record}",
            _clamp(confidence),
            (original.id, revision.id, str(evidence_id)),
            int(tick),
            "contradiction_or_correction",
        )
        return revision

    def create_expectation(
        self,
        proposition: str,
        *,
        tick: int,
        due_tick: int | None = None,
        confidence: float = 0.5,
        evidence_ids: tuple[str, ...] = (),
        expectation_id: str | None = None,
    ) -> Expectation:
        item = Expectation(
            id=expectation_id or str(uuid.uuid4()),
            proposition=str(proposition),
            created_tick=int(tick),
            due_tick=None if due_tick is None else int(due_tick),
            confidence=_clamp(confidence),
            source_record_ids=tuple(dict.fromkeys(str(value) for value in evidence_ids)),
        )
        self.state.expectations[item.id] = item
        return item

    def resolve_expectation(
        self,
        expectation_id: str,
        *,
        outcome: str,
        confirmed: bool,
        tick: int,
    ) -> Expectation:
        item = self.state.expectations[expectation_id]
        item.status = "confirmed" if confirmed else "violated"
        item.outcome = str(outcome)
        item.prediction_error = _clamp((1.0 - item.confidence) if confirmed else item.confidence)
        item.resolved_tick = int(tick)
        self._add_insight(
            "prediction_result",
            (
                f"My expectation was supported: {item.proposition}"
                if confirmed
                else f"What happened contradicted my expectation: {item.proposition}"
            ),
            _clamp(0.45 + item.prediction_error * 0.45),
            item.source_record_ids,
            int(tick),
            "prediction_error",
        )
        return item

    def create_commitment(
        self,
        actor: str,
        description: str,
        *,
        beneficiary: str = "self",
        tick: int,
        due_tick: int | None = None,
        importance: float = 0.5,
        evidence_ids: tuple[str, ...] = (),
        commitment_id: str | None = None,
    ) -> Commitment:
        item = Commitment(
            id=commitment_id or str(uuid.uuid4()),
            actor=str(actor),
            description=str(description),
            beneficiary=str(beneficiary),
            created_tick=int(tick),
            due_tick=None if due_tick is None else int(due_tick),
            importance=_clamp(importance),
            evidence_ids=tuple(dict.fromkeys(str(value) for value in evidence_ids)),
        )
        self.state.commitments[item.id] = item
        return item

    def resolve_commitment(
        self,
        commitment_id: str,
        *,
        outcome: str,
        kept: bool,
        tick: int,
    ) -> Commitment:
        item = self.state.commitments[commitment_id]
        item.status = "kept" if kept else "broken"
        item.outcome = str(outcome)
        item.resolved_tick = int(tick)
        self._add_insight(
            "commitment_result",
            (
                f"{item.actor} followed through on: {item.description}"
                if kept
                else f"{item.actor} did not follow through on: {item.description}"
            ),
            _clamp(0.45 + item.importance * 0.45),
            item.evidence_ids,
            int(tick),
            "commitment_resolution",
        )
        return item

    def advance_deadlines(self, tick: int) -> None:
        current = int(tick)
        for item in self.state.expectations.values():
            if item.status == "pending" and item.due_tick is not None and current > item.due_tick:
                item.status = "expired"
                item.resolved_tick = current
                item.prediction_error = item.confidence
        for item in self.state.commitments.values():
            if item.status == "open" and item.due_tick is not None and current > item.due_tick:
                item.status = "overdue"

    def summary(self) -> dict[str, Any]:
        return {
            "record_count": len(self.state.epistemic_records),
            "open_expectations": [
                asdict(item) for item in self.state.expectations.values() if item.status == "pending"
            ],
            "open_commitments": [
                asdict(item) for item in self.state.commitments.values() if item.status in {"open", "overdue"}
            ],
            "recent_insights": [asdict(item) for item in self.state.insights[-8:]],
        }

    def _apply_metadata(self, event: Event, record: EpistemicRecord) -> None:
        metadata = event.metadata if isinstance(event.metadata, dict) else {}
        expectation = metadata.get("expectation")
        if isinstance(expectation, dict) and expectation.get("proposition"):
            self.create_expectation(
                str(expectation["proposition"]),
                tick=record.tick,
                due_tick=expectation.get("due_tick"),
                confidence=float(expectation.get("confidence", 0.5)),
                evidence_ids=(record.id,),
                expectation_id=expectation.get("id"),
            )
        commitment = metadata.get("commitment")
        if isinstance(commitment, dict) and commitment.get("description"):
            self.create_commitment(
                str(commitment.get("actor", event.source)),
                str(commitment["description"]),
                beneficiary=str(commitment.get("beneficiary", "self")),
                tick=record.tick,
                due_tick=commitment.get("due_tick"),
                importance=float(commitment.get("importance", event.intensity)),
                evidence_ids=(record.id,),
                commitment_id=commitment.get("id"),
            )
        resolution = metadata.get("resolve_expectation")
        if isinstance(resolution, dict) and resolution.get("id") in self.state.expectations:
            self.resolve_expectation(
                str(resolution["id"]),
                outcome=str(resolution.get("outcome", event.description)),
                confirmed=bool(resolution.get("confirmed", False)),
                tick=record.tick,
            )
        resolution = metadata.get("resolve_commitment")
        if isinstance(resolution, dict) and resolution.get("id") in self.state.commitments:
            self.resolve_commitment(
                str(resolution["id"]),
                outcome=str(resolution.get("outcome", event.description)),
                kept=bool(resolution.get("kept", False)),
                tick=record.tick,
            )

    def _apply_event_conventions(self, event: Event, record: EpistemicRecord) -> None:
        if event.kind == "promise_made":
            self.create_commitment(
                event.source,
                event.description,
                tick=record.tick,
                importance=event.intensity,
                evidence_ids=(record.id,),
            )
        elif event.kind in {"promise_kept", "promise_broken"}:
            candidates = [
                item
                for item in self.state.commitments.values()
                if item.actor == event.source and item.status in {"open", "overdue"}
            ]
            if candidates:
                latest = max(candidates, key=lambda item: item.created_tick)
                self.resolve_commitment(
                    latest.id,
                    outcome=event.description,
                    kept=event.kind == "promise_kept",
                    tick=record.tick,
                )

    def _maybe_reflect(self, record: EpistemicRecord) -> None:
        if not record.tags:
            return
        recent = self.state.epistemic_records[-24:]
        matches = [
            item
            for item in recent
            if item.id != record.id and set(item.tags).intersection(record.tags)
        ]
        if len(matches) < 2:
            return
        tag = next((tag for tag in record.tags if sum(tag in item.tags for item in matches) >= 2), None)
        if tag is None:
            return
        evidence = tuple(item.id for item in (*matches[-4:], record))
        key = ("recurring_pattern", tag, evidence[-1])
        if any(
            item.kind == key[0] and tag in item.proposition and item.evidence_ids == evidence
            for item in self.state.insights
        ):
            return
        self._add_insight(
            "recurring_pattern",
            f"Experiences involving {tag.replace('_', ' ')} have become a recurring part of my history.",
            _clamp(0.40 + len(evidence) * 0.08),
            evidence,
            record.tick,
            "repetition",
        )

    def _add_insight(
        self,
        kind: str,
        proposition: str,
        confidence: float,
        evidence_ids: tuple[str, ...],
        tick: int,
        trigger: str,
    ) -> ReflectionInsight:
        item = ReflectionInsight(
            id=str(uuid.uuid4()),
            kind=str(kind),
            proposition=str(proposition),
            confidence=_clamp(confidence),
            evidence_ids=tuple(dict.fromkeys(str(value) for value in evidence_ids)),
            created_tick=int(tick),
            trigger=str(trigger),
        )
        self.state.insights.append(item)
        self.state.insights = self.state.insights[-self.insight_limit :]
        return item

    def _record(self, record_id: str) -> EpistemicRecord:
        for item in self.state.epistemic_records:
            if item.id == record_id:
                return item
        raise KeyError(record_id)
