"""Phase 25: sample AI quizzes for review (python -m seed.sample_quizzes), with a fake Groq."""

import io

import groq
import httpx
import pytest

from config import get_settings
from seed import sample_quizzes
from seed.curriculum import DOMAIN_BY_ID
from seed.sample_quizzes import DailyLimitReached, main, topic_info, with_rate_limits
from test_answer_check import check
from test_quiz import api_status_error


def rate_limited(retry_after: str) -> groq.APIStatusError:
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(429, request=request, headers={"retry-after": retry_after})
    return groq.APIStatusError("HTTP 429", response=response, body=None)


@pytest.fixture()
def report(tmp_path):
    return tmp_path / "review.md"


def run(args, sleeps=None) -> tuple[int, str]:
    out = io.StringIO()
    code = main(args, out, sleep=(sleeps.append if sleeps is not None else lambda s: None))
    return code, out.getvalue()


def test_topic_info_comes_from_the_curriculum_files():
    git = next(t for t in DOMAIN_BY_ID["foundations"].topics if t.id == "git_basics")
    info = topic_info(git)
    assert (info.name, info.difficulty, info.home_domain) == ("Git Basics", 1, "foundations")
    assert info.domains == ["foundations", "web-development"]


def test_a_domain_is_sampled_and_written_up_for_review(fake_llm, report):
    fake_llm.check_script = [check(([0], True), ([0, 2], True, "C works too."), ([0], True))]
    sleeps = []
    code, out = run(["--domain", "foundations", "--out", str(report), "--pause", "7"], sleeps)
    assert code == 0
    assert len(fake_llm.calls) == 10 and len(fake_llm.check_calls) == 10
    assert sleeps == [7] * 9  # between topics, not before the first
    assert "how_computers_work: 3 questions, 1 rejected" in out
    text = report.read_text(encoding="utf-8")
    assert text.startswith("# Sample AI quizzes: Foundations")
    assert "10 topics, 30 questions, 1 rejected by the answer check." in text
    assert "## How Computers Work (`how_computers_work`, level 1)" in text
    assert "- A (key): Right answer 0" in text and "- B: Wrong A0" in text
    assert "Explanation: Because answer 0 is right." in text
    assert "Answer check: **REJECTED** (correct: A, C; sound: True). C works too." in text
    assert text.count("Answer check: passed") == 29


def test_the_prompt_is_the_one_learners_get(fake_llm, report):
    run(["--domain", "foundations", "--topic", "git_basics", "--out", str(report)])
    system, user = fake_llm.calls[0]["messages"]
    assert system["content"] == sample_quizzes.llm_quiz.SYSTEM_PROMPT
    assert "Domain: Foundations" in user["content"] and "Topic: Git Basics" in user["content"]


def test_only_the_chosen_topics_are_sampled(fake_llm, report):
    code, _ = run(["--domain", "foundations", "--topic", "git_basics", "--out", str(report)])
    assert code == 0 and len(fake_llm.calls) == 1
    assert "## Git Basics" in report.read_text(encoding="utf-8")


def test_an_invalid_quiz_is_retried_and_problems_are_reported(fake_llm, report):
    fake_llm.script = ["not json", "still not", "never json"]
    code, out = run(["--domain", "foundations", "--topic", "git_basics", "--out", str(report)])
    assert code == 0 and len(fake_llm.calls) == 3 and fake_llm.check_calls == []
    assert "**Problem:** invalid quiz: not valid JSON" in report.read_text(encoding="utf-8")


def test_a_failed_check_is_reported_and_questions_shown_unchecked(fake_llm, report):
    fake_llm.check_script = ["nonsense"]
    run(["--domain", "foundations", "--topic", "git_basics", "--out", str(report)])
    text = report.read_text(encoding="utf-8")
    assert "**Problem:** answer check failed" in text
    assert text.count("Answer check: not run") == 3


def test_a_per_minute_limit_is_waited_out(fake_llm, report):
    fake_llm.script = [rate_limited("12")]
    sleeps = []
    code, _ = run(["--domain", "foundations", "--topic", "git_basics", "--out", str(report)], sleeps)
    assert code == 0 and sleeps == [13]
    assert len(fake_llm.calls) == 2


def test_a_daily_limit_stops_the_run_and_keeps_what_was_done(fake_llm, report):
    fake_llm.script = [fake_llm.last_quiz, rate_limited("3600")]
    code, out = run(["--domain", "foundations", "--out", str(report)])
    assert code == 1
    assert "a daily limit is reached; 9 topic(s) not sampled" in out
    text = report.read_text(encoding="utf-8")
    assert "**Stopped early:**" in text and "## How Computers Work" in text and "## Binary & Data Representation" not in text


def test_other_groq_errors_are_recorded_and_the_run_goes_on(fake_llm, report):
    fake_llm.script = [api_status_error(503)]
    code, out = run(["--domain", "foundations", "--out", str(report)])
    assert code == 0
    assert "how_computers_work: 0 questions, 0 rejected - Groq error" in out
    assert "binary_data_representation: 3 questions" in out


def test_rate_limit_helper_gives_up_after_one_wait():
    calls = []

    def call():
        calls.append(1)
        raise rate_limited("1")

    with pytest.raises(groq.APIStatusError):
        with_rate_limits(call, sleep=lambda s: None)
    assert len(calls) == 2
    with pytest.raises(DailyLimitReached):
        with_rate_limits(lambda: (_ for _ in ()).throw(rate_limited("86400")), sleep=lambda s: None)


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["--domain", "astrology"], "Unknown domain 'astrology'"),
        (["--domain", "foundations", "--topic", "css_basics"], "Not defined in foundations: css_basics"),
    ],
)
def test_bad_arguments(fake_llm, args, message):
    code, out = run(args)
    assert code == 2 and message in out
    assert fake_llm.calls == []


def test_without_a_key_there_is_nothing_to_sample(monkeypatch):
    monkeypatch.setattr(get_settings(), "groq_api_key", "")
    code, out = run(["--domain", "foundations"])
    assert code == 2 and "GROQ_API_KEY is not set" in out


def test_the_default_report_goes_to_the_ignored_review_folder(fake_llm, monkeypatch, tmp_path):
    monkeypatch.setattr(sample_quizzes, "DEFAULT_DIR", tmp_path / "content-review")
    code, out = run(["--domain", "foundations", "--topic", "git_basics"])
    assert code == 0
    files = list((tmp_path / "content-review").glob("foundations-*.md"))
    assert len(files) == 1 and str(files[0]) in out
    assert sample_quizzes.DEFAULT_DIR.name == "content-review"
