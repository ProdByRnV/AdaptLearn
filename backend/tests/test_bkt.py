"""BKT unit tests (ARCHITECTURE.md sections 11 and 23).

Expected values were computed independently with exact fractions (Python's fractions.Fraction)
from the formulas in ARCHITECTURE.md, not by calling the code under test.
"""

import itertools
import subprocess
import sys
from pathlib import Path

import pytest

from services.bkt import (
    DEFAULT_P_GUESS,
    DEFAULT_P_KNOW,
    DEFAULT_P_LEARN,
    DEFAULT_P_SLIP,
    MASTERY_THRESHOLD,
    mastery_reached,
    update_bkt,
    update_bkt_sequence,
)

approx = lambda value: pytest.approx(value, abs=1e-9)  # noqa: E731

BACKEND_DIR = Path(__file__).resolve().parent.parent


# --- Defaults (PRD 6.4) -------------------------------------------------------------

def test_defaults_match_the_prd():
    assert (DEFAULT_P_KNOW, DEFAULT_P_LEARN, DEFAULT_P_GUESS, DEFAULT_P_SLIP) == (0.10, 0.40, 0.20, 0.10)
    assert MASTERY_THRESHOLD == 0.95


# --- Single updates with known values --------------------------------------------

def test_correct_answer_from_default():
    # posterior = 0.09 / (0.09 + 0.18) = 1/3; new = 1/3 + (2/3)(0.4) = 0.6 exactly
    assert update_bkt(0.10, True) == approx(0.6)


def test_wrong_answer_from_default():
    # posterior = 0.01 / (0.01 + 0.72) = 1/73; new = 1/73 + (72/73)(0.4)
    assert update_bkt(0.10, False) == approx(0.40821917808219177)


@pytest.mark.parametrize(
    ("p_know", "correct", "expected"),
    [
        (0.60, True, 0.9225806451612903),
        (0.95, True, 0.9930635838150289),
        (0.95, False, 0.8222222222222222),
    ],
)
def test_known_single_updates(p_know, correct, expected):
    assert update_bkt(p_know, correct) == approx(expected)


@pytest.mark.parametrize("p_know", [0.0, 0.05, 0.1, 0.3, 0.5, 0.77, 0.95, 0.999, 1.0])
@pytest.mark.parametrize("correct", [True, False])
def test_matches_the_architecture_formula(p_know, correct):
    learn, guess, slip = 0.4, 0.2, 0.1
    if correct:
        posterior = p_know * (1 - slip) / (p_know * (1 - slip) + (1 - p_know) * guess)
    else:
        posterior = p_know * slip / (p_know * slip + (1 - p_know) * (1 - guess))
    assert update_bkt(p_know, correct) == approx(posterior + (1 - posterior) * learn)


def test_custom_parameters_are_used():
    # p_learn=0: pure Bayes. 0.5*0.75 / (0.5*0.75 + 0.5*0.25) = 0.75
    assert update_bkt(0.5, True, p_learn=0.0, p_guess=0.25, p_slip=0.25) == approx(0.75)


# --- Sequences (3-question quiz) -------------------------------------------------

@pytest.mark.parametrize(
    ("answers", "expected"),
    [
        ("CCC", [0.6, 0.9225806452, 0.9890160183]),
        ("CCW", [0.6, 0.9225806452, 0.7589958159]),
        ("WCC", [0.4082191781, 0.8538071066, 0.9780068729]),
        ("CWC", [0.6, 0.4947368421, 0.8890173410]),
        ("WWC", [0.4082191781, 0.4476291955, 0.8708761442]),
        ("CWW", [0.6, 0.4947368421, 0.4654292343]),
        ("WWW", [0.4082191781, 0.4476291955, 0.4551879666]),
    ],
)
def test_known_three_answer_sequences(answers, expected):
    trajectory = update_bkt_sequence(0.10, [a == "C" for a in answers])
    assert trajectory == [pytest.approx(v, abs=1e-9) for v in expected]


def test_sequence_equals_repeated_single_updates():
    answers = [True, False, True, True, False]
    p, manual = 0.10, []
    for correct in answers:
        p = update_bkt(p, correct)
        manual.append(p)
    assert update_bkt_sequence(0.10, answers) == manual


def test_empty_sequence():
    assert update_bkt_sequence(0.3, []) == []


def test_answer_order_matters_for_the_same_score():
    """Documented behaviour: 2/3 correct ends ~0.76 or ~0.98 depending on which answer was wrong."""
    last_wrong = update_bkt_sequence(0.10, [True, True, False])[-1]
    first_wrong = update_bkt_sequence(0.10, [False, True, True])[-1]
    assert last_wrong == approx(0.7589958159) and first_wrong == approx(0.9780068729)


def test_one_perfect_quiz_reaches_mastery_from_default():
    assert mastery_reached(update_bkt_sequence(0.10, [True, True, True])[-1])


def test_repeated_wrong_answers_converge_to_16_over_35():
    p = 0.10
    for _ in range(200):
        p = update_bkt(p, False)
    assert p == approx(16 / 35)


# --- Properties over a grid of inputs ---------------------------------------------

GRID = [0.0, 0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99, 1.0]


def test_result_always_within_0_and_1():
    """Every combination of the grid for all four parameters (13,122 updates)."""
    for p_know, p_learn, p_guess, p_slip in itertools.product(GRID, repeat=4):
        for correct in (True, False):
            result = update_bkt(p_know, correct, p_learn, p_guess, p_slip)
            assert 0.0 <= result <= 1.0, (p_know, correct, p_learn, p_guess, p_slip, result)


@pytest.mark.parametrize("p_know", GRID)
def test_correct_answer_never_lowers_p_know(p_know):
    assert update_bkt(p_know, True) >= p_know - 1e-12


@pytest.mark.parametrize("p_know", GRID)
def test_correct_beats_wrong_from_the_same_state(p_know):
    if 0 < p_know < 1:
        assert update_bkt(p_know, True) > update_bkt(p_know, False)


@pytest.mark.parametrize("p_know", GRID)
def test_learning_step_sets_a_floor_of_p_learn(p_know):
    """After any answer p_know >= p_learn, because posterior >= 0."""
    assert update_bkt(p_know, False) >= DEFAULT_P_LEARN - 1e-12


def test_certain_knowledge_stays_certain():
    assert update_bkt(1.0, True) == 1.0
    assert update_bkt(1.0, False) == 1.0


def test_zero_information_edge_case_does_not_divide_by_zero():
    # p_know=0 and p_guess=0: a correct answer is impossible under the model; belief unchanged before learning.
    assert update_bkt(0.0, True, p_learn=0.4, p_guess=0.0, p_slip=0.1) == approx(0.4)
    assert update_bkt(1.0, False, p_learn=0.0, p_guess=0.2, p_slip=0.0) == approx(1.0)


# --- Validation --------------------------------------------------------------------

@pytest.mark.parametrize("name", ["p_know", "p_learn", "p_guess", "p_slip"])
@pytest.mark.parametrize("bad", [-0.01, 1.01, float("inf")])
def test_rejects_out_of_range_probabilities(name, bad):
    params = {"p_know": 0.5, "p_learn": 0.4, "p_guess": 0.2, "p_slip": 0.1, name: bad}
    with pytest.raises(ValueError, match=name):
        update_bkt(params["p_know"], True, params["p_learn"], params["p_guess"], params["p_slip"])


def test_rejects_nan():
    with pytest.raises(ValueError):
        update_bkt(float("nan"), True)


# --- Mastery threshold ----------------------------------------------------------------

@pytest.mark.parametrize(
    ("p_know", "expected"),
    [(0.0, False), (0.5, False), (0.9499999, False), (0.95, True), (0.9500001, True), (1.0, True)],
)
def test_mastery_threshold(p_know, expected):
    assert mastery_reached(p_know) is expected


# --- Independence from database code (Phase 9 exit gate) -------------------------------

def test_bkt_imports_no_database_code():
    code = (
        "import sys; import services.bkt; "
        "loaded = [m for m in ('sqlalchemy', 'neo4j', 'psycopg2', 'fastapi', 'db', 'models') if m in sys.modules]; "
        "print(','.join(loaded))"
    )
    result = subprocess.run([sys.executable, "-c", code], cwd=BACKEND_DIR, capture_output=True, text=True, check=True)
    assert result.stdout.strip() == ""
