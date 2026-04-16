from __future__ import annotations

import random
import re
from dataclasses import dataclass


CRISIS_PATTERNS = [
    r"\bkill myself\b",
    r"\bend my life\b",
    r"\bsuicid(?:e|al)\b",
    r"\bself[- ]harm\b",
    r"\bhurt myself\b",
    r"\bdon't want to live\b",
    r"\bwant to die\b",
    r"\bcan'?t go on\b",
]

NEGATIVE_WORDS = {
    "anxious",
    "anxiety",
    "sad",
    "depressed",
    "alone",
    "lonely",
    "angry",
    "stress",
    "stressed",
    "worried",
    "overwhelmed",
    "panic",
    "afraid",
    "tired",
    "hopeless",
    "hurt",
    "crying",
    "broken",
}

POSITIVE_WORDS = {
    "good",
    "better",
    "happy",
    "grateful",
    "relieved",
    "hopeful",
    "calm",
    "fine",
    "great",
    "okay",
    "ok",
}


@dataclass
class Analysis:
    is_crisis: bool
    emotion: str
    intent: str
    intensity: str


def _contains_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def analyze_message(message: str) -> Analysis:
    text = message.lower().strip()
    is_crisis = _contains_any(text, CRISIS_PATTERNS)

    if any(word in text for word in ["thanks", "thank you", "appreciate"]):
        intent = "gratitude"
    elif "?" in text or any(
        phrase in text
        for phrase in ["what should i do", "how do i", "can you help", "advice"]
    ):
        intent = "guidance"
    elif any(
        phrase in text
        for phrase in ["i feel", "i am feeling", "i've been feeling", "i'm feeling"]
    ):
        intent = "reflection"
    else:
        intent = "sharing"

    negative_hits = sum(1 for word in NEGATIVE_WORDS if word in text)
    positive_hits = sum(1 for word in POSITIVE_WORDS if word in text)

    if is_crisis:
        emotion = "crisis"
    elif negative_hits >= 2:
        emotion = "distressed"
    elif negative_hits == 1:
        emotion = "low"
    elif positive_hits >= 1:
        emotion = "positive"
    else:
        emotion = "mixed"

    emphasis_markers = text.count("!") + text.count("really") + text.count("very")
    if is_crisis or emphasis_markers >= 2 or negative_hits >= 3:
        intensity = "high"
    elif negative_hits >= 1 or positive_hits >= 1:
        intensity = "medium"
    else:
        intensity = "low"

    return Analysis(
        is_crisis=is_crisis,
        emotion=emotion,
        intent=intent,
        intensity=intensity,
    )


def generate_support_response(message: str) -> str:
    analysis = analyze_message(message)

    if analysis.is_crisis:
        return (
            "I'm really glad you said this out loud. If you might act on these thoughts "
            "or are not safe right now, please call your local emergency number immediately "
            "or go to the nearest emergency room. If you can, contact a trusted person right now "
            "and stay with them while you reach out for urgent human support."
        )

    opening = _pick_opening(analysis)
    reflection = _pick_reflection(analysis, message)
    next_step = _pick_next_step(analysis)

    parts = [opening, reflection, next_step]
    return " ".join(part for part in parts if part)


def _pick_opening(analysis: Analysis) -> str:
    if analysis.emotion == "distressed":
        return random.choice(
            [
                "That sounds really heavy to carry on your own.",
                "It makes sense that this feels like a lot right now.",
                "I can hear how draining this has been for you.",
            ]
        )
    if analysis.emotion == "low":
        return random.choice(
            [
                "I'm glad you shared that with me.",
                "Thank you for being open about how you're feeling.",
                "It helps to put this into words, and you just did that.",
            ]
        )
    if analysis.emotion == "positive":
        return random.choice(
            [
                "I'm glad there's some lightness in what you're sharing.",
                "That sounds like an important shift for you.",
                "It's good to hear that from you.",
            ]
        )
    return random.choice(
        [
            "I'm here with you.",
            "Thank you for bringing that here.",
            "We can take this one step at a time.",
        ]
    )


def _pick_reflection(analysis: Analysis, message: str) -> str:
    cleaned = re.sub(r"\s+", " ", message.strip())
    if len(cleaned) > 160:
        cleaned = cleaned[:157].rstrip() + "..."

    if analysis.intent == "gratitude":
        return "You don't have to carry everything perfectly to be making progress."
    if analysis.intent == "guidance":
        return (
            "It sounds like you're looking for something practical, not just reassurance."
        )
    if analysis.intent == "reflection":
        return f"What you're describing matters, and it deserves care: \"{cleaned}\""
    return "You don't need to solve everything at once for this moment to matter."


def _pick_next_step(analysis: Analysis) -> str:
    if analysis.intent == "guidance":
        return random.choice(
            [
                "A good first step is to name the main problem in one short sentence, then pick the smallest action you can do in the next 10 minutes.",
                "Try pausing for one slow breath, then ask yourself what feels most urgent and what can wait until later today.",
                "If it helps, we can break this into what you can control, what you can't control, and what support you need from someone else.",
            ]
        )
    if analysis.emotion in {"distressed", "low"}:
        return random.choice(
            [
                "For the next few minutes, try loosening your shoulders, unclenching your jaw, and taking five slow breaths before deciding what comes next.",
                "If you can, drink some water, sit somewhere a little quieter, and let your body settle before pushing yourself again.",
                "One gentle next step could be texting one trusted person or writing down the single thought that feels loudest right now.",
            ]
        )
    if analysis.emotion == "positive":
        return random.choice(
            [
                "Try to notice what helped, because that's something you can come back to later.",
                "Holding onto this moment matters, especially if things have felt hard recently.",
                "If you want, you can build on this by writing down what is going right today.",
            ]
        )
    return random.choice(
        [
            "If you want, keep going and tell me which part of this feels hardest right now.",
            "We can slow this down together and focus on one part at a time.",
            "If it helps, tell me what happened first and what feeling showed up after that.",
        ]
    )
