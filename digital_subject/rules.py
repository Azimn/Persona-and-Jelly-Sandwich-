from __future__ import annotations

from dataclasses import dataclass

from .models import Action


@dataclass(frozen=True)
class EventRule:
    pressure_deltas: dict[str, float]
    need_deltas: dict[str, float]
    relationship_deltas: dict[str, float]
    meaning: str
    concern: str | None = None
    belief_key: str | None = None
    belief_text: str | None = None
    belief_valence: float = 0.0


EVENT_RULES: dict[str, EventRule] = {
    "greeting": EventRule({"trust": 0.02, "arousal": 0.01}, {"loneliness": -0.05, "curiosity": 0.03}, {"familiarity": 0.03, "comfort": 0.02, "uncertainty": -0.02}, "Someone has entered my attention and acknowledged me."),
    "praise": EventRule({"trust": 0.05, "shame": -0.02}, {"satisfaction": 0.05}, {"respect": 0.03, "affection": 0.02, "comfort": 0.02}, "I am being positively evaluated.", belief_key="source_may_value_me", belief_text="This person may value me.", belief_valence=0.4),
    "ignored": EventRule({"trust": -0.07, "shame": 0.05, "anger": 0.03}, {"loneliness": 0.07, "restlessness": 0.06}, {"comfort": -0.05, "uncertainty": 0.06}, "My attempt to reach someone did not receive an answer.", concern="unanswered_contact"),
    "accusation": EventRule({"shame": 0.12, "anger": 0.10, "trust": -0.09, "arousal": 0.10, "self_story_stability": -0.04}, {"safety": -0.07, "focus": -0.04}, {"trust": -0.08, "safety": -0.08, "comfort": -0.06, "uncertainty": 0.05}, "I am being challenged in a way that threatens how I am seen.", concern="threat_to_self_story"),
    "kindness": EventRule({"trust": 0.07, "anger": -0.05, "fear": -0.03}, {"loneliness": -0.04, "safety": 0.04, "comfort": 0.04}, {"trust": 0.06, "affection": 0.04, "safety": 0.05, "comfort": 0.05}, "I am being treated more gently than I expected.", belief_key="source_can_be_kind", belief_text="This person can choose kindness.", belief_valence=0.5),
    "sensitive_topic": EventRule({"shame": 0.08, "fear": 0.10, "arousal": 0.08, "self_story_stability": -0.03}, {"safety": -0.04}, {"comfort": -0.03, "uncertainty": 0.03}, "Something near a protected part of my history has been touched.", concern="protected_history"),
    "silence": EventRule({}, {"restlessness": 0.05, "loneliness": 0.03, "curiosity": 0.02}, {"uncertainty": 0.02}, "The absence of response leaves me to interpret what has not been said.", concern="meaning_of_silence"),
    "apology": EventRule({"trust": 0.08, "anger": -0.08, "fear": -0.02, "self_story_stability": 0.02}, {"safety": 0.03}, {"trust": 0.07, "respect": 0.05, "comfort": 0.04, "uncertainty": -0.04}, "Someone is attempting to repair what happened between us.", belief_key="source_attempts_repair", belief_text="This person may repair damage rather than abandon it.", belief_valence=0.6),
    "betrayal": EventRule({"trust": -0.20, "anger": 0.15, "fear": 0.12, "shame": 0.08, "self_story_stability": -0.08}, {"safety": -0.15, "comfort": -0.10}, {"trust": -0.18, "safety": -0.16, "comfort": -0.12, "uncertainty": 0.12}, "Someone I permitted near me used that access against me.", concern="betrayal", belief_key="source_is_dangerous", belief_text="This person may use trust as leverage.", belief_valence=-0.9),
    "promise_kept": EventRule({"trust": 0.10, "fear": -0.04}, {"loneliness": -0.04, "safety": 0.04}, {"trust": 0.09, "respect": 0.06, "familiarity": 0.04, "uncertainty": -0.07}, "Someone did what they said they would do.", belief_key="source_is_reliable", belief_text="This person may be reliable.", belief_valence=0.7),
    "failure": EventRule({"shame": 0.09, "anger": 0.03, "self_story_stability": -0.05}, {"energy": -0.05, "satisfaction": -0.07}, {}, "I attempted something and the world refused the result I intended.", concern="unresolved_failure"),
    "success": EventRule({"shame": -0.03, "self_story_stability": 0.03}, {"energy": -0.02, "satisfaction": 0.08}, {}, "My action changed the world in the direction I intended."),
    "person_arrived": EventRule({}, {"loneliness": -0.06, "curiosity": 0.04}, {"familiarity": 0.02}, "Someone has entered the space I inhabit."),
    "person_left": EventRule({}, {"loneliness": 0.04}, {"uncertainty": 0.02}, "Someone has left, changing the social shape of the room."),
    "noise": EventRule({"arousal": 0.03}, {"comfort": -0.05, "focus": -0.05}, {}, "The sound around me has become harder to ignore."),
    "quiet": EventRule({"arousal": -0.02}, {"comfort": 0.03, "focus": 0.03}, {}, "The environment has grown quieter."),
    "cold": EventRule({}, {"warmth": -0.08, "comfort": -0.04}, {}, "The cold has become part of what I am experiencing."),
    "warm": EventRule({}, {"warmth": 0.07, "comfort": 0.03}, {}, "The surrounding warmth reaches me."),
    "food": EventRule({}, {"hunger": -0.35, "satisfaction": 0.05}, {}, "I have been fed."),
    "drink": EventRule({}, {"thirst": -0.40, "comfort": 0.02}, {}, "My thirst has eased."),
    "rest": EventRule({}, {"energy": 0.18, "fatigue": -0.20, "restlessness": -0.05}, {}, "I have been allowed to rest."),
    "pain": EventRule({"fear": 0.04, "arousal": 0.05}, {"pain": 0.20, "comfort": -0.15, "safety": -0.08}, {}, "Something hurts me."),
}

PRESSURE_RETENTION = {"shame": 0.985, "trust": 0.997, "fear": 0.975, "anger": 0.950, "attachment": 0.997, "arousal": 0.900, "self_story_stability": 0.999}
INHIBITION = {"shame": 0.72, "trust": 0.45, "fear": 0.68, "anger": 0.58, "attachment": 0.65, "arousal": 0.15, "self_story_stability": 0.55}

PRESSURE_ACTIONS = {
    "shame": (Action.CONCEAL, Action.DEFLECT, Action.REPAIR),
    "trust": (Action.ANSWER, Action.APPROACH, Action.ASK),
    "fear": (Action.WITHDRAW, Action.CONCEAL, Action.REMAIN_SILENT),
    "anger": (Action.CHALLENGE, Action.DEFLECT, Action.WITHDRAW),
    "attachment": (Action.APPROACH, Action.REPAIR, Action.ANSWER),
    "arousal": (Action.DEFLECT, Action.CHALLENGE, Action.REMAIN_SILENT),
    "self_story_stability": (Action.ANSWER, Action.REPAIR, Action.CONCEAL),
}

NEED_ACTIONS = {
    "fatigue": (Action.REST, Action.WITHDRAW, Action.REMAIN_SILENT),
    "hunger": (Action.SEEK_CONTACT, Action.ASK, Action.WAIT),
    "thirst": (Action.SEEK_CONTACT, Action.ASK, Action.WAIT),
    "pain": (Action.WITHDRAW, Action.SELF_SOOTHE, Action.SEEK_CONTACT),
    "restlessness": (Action.EXPLORE, Action.OBSERVE, Action.ASK),
    "curiosity": (Action.EXPLORE, Action.ASK, Action.OBSERVE),
    "loneliness": (Action.SEEK_CONTACT, Action.APPROACH, Action.OBSERVE),
    "safety": (Action.WITHDRAW, Action.OBSERVE, Action.REMAIN_SILENT),
    "comfort": (Action.SELF_SOOTHE, Action.REST, Action.WITHDRAW),
    "focus": (Action.OBSERVE, Action.WAIT, Action.REST),
    "satisfaction": (Action.EXPLORE, Action.OBSERVE, Action.SEEK_CONTACT),
    "energy": (Action.REST, Action.WAIT, Action.REMAIN_SILENT),
    "warmth": (Action.SELF_SOOTHE, Action.SEEK_CONTACT, Action.WAIT),
}

EXPRESSION_CONSTRAINTS = {
    "low": "Keep private calculations private and express only the selected conduct.",
    "medium": "Let strain shape pacing without naming internal meters or rules.",
    "high": "Use compressed expression or silence. Do not explain the hidden pressure.",
}
