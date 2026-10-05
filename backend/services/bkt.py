"""Bayesian Knowledge Tracing (ARCHITECTURE.md section 11).

Pure functions with no database or framework imports, so they can be unit-tested in
isolation and reused anywhere. p_know is the estimated probability that the learner
knows the topic.

For each answer:
  1. Bayesian update - how likely is it they knew the topic, given this answer?
       correct: p_know*(1-p_slip) / (p_know*(1-p_slip) + (1-p_know)*p_guess)
       wrong:   p_know*p_slip     / (p_know*p_slip     + (1-p_know)*(1-p_guess))
  2. Learning transition - they may have learned it from attempting the question:
       p_know_new = posterior + (1 - posterior) * p_learn
"""

from collections.abc import Iterable

# PRD 6.4 defaults. Fixed for every user and topic; not varied per request.
DEFAULT_P_KNOW = 0.10
DEFAULT_P_LEARN = 0.40
DEFAULT_P_GUESS = 0.20
DEFAULT_P_SLIP = 0.10
MASTERY_THRESHOLD = 0.95


def _check_probability(name: str, value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1, got {value}")


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


def update_bkt(
    p_know: float,
    correct: bool,
    p_learn: float = DEFAULT_P_LEARN,
    p_guess: float = DEFAULT_P_GUESS,
    p_slip: float = DEFAULT_P_SLIP,
) -> float:
    """Return the new p_know after one answer."""
    for name, value in (("p_know", p_know), ("p_learn", p_learn), ("p_guess", p_guess), ("p_slip", p_slip)):
        _check_probability(name, value)

    if correct:
        evidence_if_known = p_know * (1 - p_slip)
        evidence_if_unknown = (1 - p_know) * p_guess
    else:
        evidence_if_known = p_know * p_slip
        evidence_if_unknown = (1 - p_know) * (1 - p_guess)

    total = evidence_if_known + evidence_if_unknown
    # Only possible at the extremes (e.g. p_know=0 with p_guess=0): the answer carries no
    # information, so the belief is unchanged before the learning step.
    posterior = evidence_if_known / total if total > 0 else p_know

    return _clamp(posterior + (1 - posterior) * p_learn)


def update_bkt_sequence(
    p_know: float,
    answers: Iterable[bool],
    p_learn: float = DEFAULT_P_LEARN,
    p_guess: float = DEFAULT_P_GUESS,
    p_slip: float = DEFAULT_P_SLIP,
) -> list[float]:
    """Apply update_bkt to each answer in order. Returns p_know after each answer.

    Order matters: the same score can end at different values depending on which answer
    was wrong (e.g. 2/3 from 0.10 ends near 0.76 if the last answer is wrong, 0.98 if the first is).
    """
    trajectory = []
    for correct in answers:
        p_know = update_bkt(p_know, correct, p_learn, p_guess, p_slip)
        trajectory.append(p_know)
    return trajectory


def mastery_reached(p_know: float) -> bool:
    return p_know >= MASTERY_THRESHOLD
