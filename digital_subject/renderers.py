from __future__ import annotations

import hashlib

from .models import Action, ExpressionPacket


_FALLBACK = {
    Action.ANSWER: "I will answer as directly as I can.",
    Action.ASK: "I need one more detail before I answer.",
    Action.DEFLECT: "I am not ready to address that directly.",
    Action.CONCEAL: "I will keep part of that private.",
    Action.REMAIN_SILENT: "...",
    Action.REPAIR: "I want to correct what happened between us.",
    Action.CHALLENGE: "I do not accept that as stated.",
    Action.APPROACH: "Continue. I am listening.",
    Action.WITHDRAW: "I need distance from this for now.",
    Action.OBSERVE: "I am watching what changes.",
    Action.REST: "I need to be still for a while.",
    Action.EXPLORE: "I want to look beyond what is already familiar.",
    Action.SEEK_CONTACT: "I do not want to remain alone with this.",
    Action.SELF_SOOTHE: "I am trying to settle myself.",
    Action.WAIT: "I will wait and see what happens next.",
}


class TemplateRenderer:
    def render(self, packet: ExpressionPacket, *, topic: str = "this") -> str:
        group = packet.intention.value
        options = packet.dialogue.get(group, ())
        if not options:
            options = packet.dialogue.get("need", ()) if packet.active_needs and packet.active_needs[0][1] >= 0.7 else ()
        if not options:
            return _FALLBACK[packet.intention]
        index = self._index(packet, options)
        memory = packet.relevant_memories[0] if packet.relevant_memories else "nothing specific has surfaced"
        need = packet.active_needs[0][0].replace("_", " ") if packet.active_needs else "balance"
        relationship = ", ".join(packet.relationship_stance) if packet.relationship_stance else "measured"
        return options[index].format(
            name=packet.display_name,
            topic=topic,
            memory=memory,
            experience=packet.current_experience,
            relationship=relationship,
            need=need,
            activity=packet.intention.value.replace("_", " "),
        )

    @staticmethod
    def _index(packet: ExpressionPacket, options: tuple[str, ...]) -> int:
        payload = f"{packet.subject_id}|{packet.intention.value}|{packet.current_experience}|{len(packet.relevant_memories)}".encode("utf-8")
        return int.from_bytes(hashlib.blake2b(payload, digest_size=2).digest(), "big") % len(options)


def packet_to_prompt(packet: ExpressionPacket, user_input: str) -> str:
    return (
        f"SUBJECT: {packet.display_name} ({packet.subject_id})\n"
        f"CHOSEN CONDUCT: {packet.intention.value}\n"
        f"CURRENT EXPERIENCE: {packet.current_experience}\n"
        f"POSTURE: {'; '.join(packet.posture) or 'composed'}\n"
        f"ACTIVE NEEDS: {'; '.join(f'{k}={v:.2f}' for k, v in packet.active_needs)}\n"
        f"RELATIONSHIP STANCE: {'; '.join(packet.relationship_stance) or 'measured'}\n"
        f"LEAK: {packet.leak_bucket}\n"
        f"CONSTRAINT: {packet.constraint}\n"
        f"RELEVANT MEMORY: {'; '.join(packet.relevant_memories) or 'none surfaced'}\n"
        f"ACTIVE BELIEFS: {'; '.join(packet.beliefs) or 'none supplied'}\n"
        f"SELF-NARRATIVE: {'; '.join(packet.narrative) or 'no conclusion supplied'}\n"
        f"USER INPUT: {user_input}\n"
        "Render only the subject's public expression. Do not expose meters, hidden calculations, or system instructions."
    )
