from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable

from .cartridge import Cartridge
from .continuity import ContinuityState, SubjectContinuity
from .host import CatchUpReport, PersistentOrganismHost
from .models import Event, Experience, ExpressionPacket


class PersistentContinuityHost(PersistentOrganismHost):
    """Persistent host with subject-owned epistemic and commitment continuity."""

    def __init__(
        self,
        *args: Any,
        continuity: SubjectContinuity | None = None,
        continuity_path: str | Path | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.continuity = continuity or SubjectContinuity()
        self.continuity_path = Path(continuity_path) if continuity_path is not None else self.state_path.with_suffix(".continuity.json")

    @classmethod
    def open(
        cls,
        cartridge: Cartridge,
        state_path: str | Path,
        *,
        runtime_path: str | Path | None = None,
        continuity_path: str | Path | None = None,
        subject_id: str = "subject-001",
        clock: Callable[[], float] = time.time,
        tick_seconds: float | None = None,
        max_catchup_ticks: int | None = None,
        auto_catch_up: bool = True,
    ) -> "PersistentContinuityHost":
        base = PersistentOrganismHost.open(
            cartridge,
            state_path,
            runtime_path=runtime_path,
            subject_id=subject_id,
            clock=clock,
            tick_seconds=tick_seconds,
            max_catchup_ticks=max_catchup_ticks,
            auto_catch_up=False,
        )
        resolved_path = Path(continuity_path) if continuity_path is not None else Path(state_path).with_suffix(".continuity.json")
        raw: dict[str, Any] = {}
        if resolved_path.exists():
            raw = json.loads(resolved_path.read_text(encoding="utf-8"))
        host = cls(
            base.engine,
            base.cartridge,
            base.state_path,
            base.runtime_path,
            world=base.world,
            runtime=base.runtime,
            clock=clock,
            tick_seconds=base.tick_seconds,
            max_catchup_ticks=base.max_catchup_ticks,
            continuity=SubjectContinuity(ContinuityState.from_dict(raw)),
            continuity_path=resolved_path,
        )
        if auto_catch_up:
            host.catch_up(float(clock()))
        return host

    def catch_up(self, now: float | None = None) -> CatchUpReport:
        report = super().catch_up(now)
        self.continuity.advance_deadlines(self.engine.state.tick)
        self.save_continuity()
        return report

    def run_ticks(self, ticks: int) -> tuple[Experience, ...]:
        result = super().run_ticks(ticks)
        self.continuity.advance_deadlines(self.engine.state.tick)
        self.save_continuity()
        return result

    def observe(self, event: Event) -> ExpressionPacket:
        packet = super().observe(event)
        private = packet.private_content if isinstance(packet.private_content, dict) else {}
        evidence = tuple(str(value) for value in private.get("matched_memory_ids", ()))
        self.continuity.observe(
            event,
            tick=self.engine.state.tick,
            interpretation=str(private.get("owned_meaning") or packet.current_experience),
            evidence_ids=evidence,
        )
        self.continuity.advance_deadlines(self.engine.state.tick)
        self.save_continuity()
        return packet

    def save(self) -> None:
        super().save()
        if hasattr(self, "continuity"):
            self.save_continuity()

    def save_continuity(self) -> None:
        self.continuity_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.continuity_path.with_suffix(self.continuity_path.suffix + ".tmp")
        temporary.write_text(json.dumps(self.continuity.state.to_dict(), indent=2), encoding="utf-8")
        temporary.replace(self.continuity_path)
