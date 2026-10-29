"""Quiz integrity scoring (Phase 12.5, proctoring layers 1 and 2).

Pure functions with no database or framework imports, like services/bkt.py.

Every submitted quiz starts at 100 and loses points for each integrity signal:
  - browser events reported by the quiz page (layer 2): tab switches, leaving fullscreen,
    copy/paste attempts, a second screen, ...
  - signals the server derives itself (layer 1): answers faster than the question could be
    read, gaps in the page's heartbeat, or no heartbeat at all (monitoring not running).
A score of VERIFIED_THRESHOLD or more is "verified" and the attempt counts. Anything lower is
"flagged": the attempt is recorded but does not change mastery, progress or unlocks.
"""

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from itertools import pairwise
from datetime import datetime

VERIFIED_THRESHOLD = 80
MIN_PLAUSIBLE_ANSWER_SECONDS = 3.0
HEARTBEAT_INTERVAL_SECONDS = 5
MAX_HEARTBEAT_GAP_SECONDS = 15

# Events the quiz page may report. The page should send window_blur only when the tab stays
# visible (e.g. another app was clicked); switching tabs is reported as tab_hidden.
CLIENT_EVENT_TYPES: tuple[str, ...] = (
    "heartbeat",
    "tab_hidden",
    "window_blur",
    "fullscreen_exit",
    "copy_attempt",
    "paste_attempt",
    "context_menu",
    "multiple_screens",
)

VERDICT_VERIFIED = "verified"
VERDICT_FLAGGED = "flagged"
VERDICT_ABANDONED = "abandoned"  # a newer quiz replaced this one before it was submitted
VERDICTS: tuple[str, ...] = (VERDICT_VERIFIED, VERDICT_FLAGGED, VERDICT_ABANDONED)


@dataclass(frozen=True)
class Rule:
    penalty: int
    message: str
    once: bool = False  # penalise at most once per quiz


RULES: dict[str, Rule] = {
    # Reported by the browser (layer 2)
    "tab_hidden": Rule(10, "Switched to another tab"),
    "window_blur": Rule(5, "Switched to another window"),
    "fullscreen_exit": Rule(15, "Left fullscreen"),
    "copy_attempt": Rule(10, "Tried to copy question text"),
    "paste_attempt": Rule(10, "Tried to paste"),
    "context_menu": Rule(5, "Opened the right-click menu"),
    "multiple_screens": Rule(20, "A second screen was detected", once=True),
    # Derived by the server (layer 1)
    "fast_answer": Rule(10, f"Answered in under {MIN_PLAUSIBLE_ANSWER_SECONDS:g} seconds"),
    "heartbeat_gap": Rule(15, f"The quiz page stopped reporting for over {MAX_HEARTBEAT_GAP_SECONDS} seconds"),
    "monitoring_missing": Rule(50, "The quiz page never reported that monitoring was running", once=True),
}


@dataclass(frozen=True)
class AnswerTiming:
    served_at: datetime
    answered_at: datetime


@dataclass(frozen=True)
class IntegrityResult:
    score: int
    verdict: str
    counted: bool
    reasons: list[dict] = field(default_factory=list)


def heartbeat_gaps(heartbeats: Iterable[datetime], window_start: datetime, window_end: datetime) -> int:
    """Number of silences longer than MAX_HEARTBEAT_GAP_SECONDS within [window_start, window_end]."""
    if window_end <= window_start:
        return 0
    inside = sorted(t for t in heartbeats if window_start <= t <= window_end)
    points = [window_start, *inside, window_end]
    return sum(1 for a, b in pairwise(points) if (b - a).total_seconds() > MAX_HEARTBEAT_GAP_SECONDS)


def score_integrity(
    client_events: Iterable[str],
    heartbeats: Iterable[datetime],
    answers: Iterable[AnswerTiming],
    window_start: datetime | None,
    window_end: datetime | None,
) -> IntegrityResult:
    """Score one quiz attempt.

    client_events: event types reported by the page (heartbeats excluded).
    heartbeats: server receive times of the page's heartbeats.
    answers: serve/answer times of the questions that were answered.
    window_start/window_end: when the first question was served and the last one closed;
        heartbeat gaps are only measured inside this window.
    """
    heartbeats = list(heartbeats)
    counts = Counter(event for event in client_events if event in RULES)
    counts["fast_answer"] = sum(
        1 for a in answers if (a.answered_at - a.served_at).total_seconds() < MIN_PLAUSIBLE_ANSWER_SECONDS
    )
    if not heartbeats:
        counts["monitoring_missing"] = 1
    elif window_start is not None and window_end is not None:
        counts["heartbeat_gap"] = heartbeat_gaps(heartbeats, window_start, window_end)

    reasons = []
    for code, count in counts.items():
        if count <= 0:
            continue
        rule = RULES[code]
        penalty = rule.penalty * (1 if rule.once else count)
        reasons.append({"code": code, "count": count, "penalty": penalty, "message": rule.message})
    reasons.sort(key=lambda r: (-r["penalty"], r["code"]))

    score = max(0, 100 - sum(r["penalty"] for r in reasons))
    verified = score >= VERIFIED_THRESHOLD
    return IntegrityResult(
        score=score,
        verdict=VERDICT_VERIFIED if verified else VERDICT_FLAGGED,
        counted=verified,
        reasons=reasons,
    )


def rules_summary() -> list[dict]:
    """The rules as shown to learners before a quiz starts."""
    return [{"code": code, "penalty": rule.penalty, "message": rule.message} for code, rule in RULES.items()]
