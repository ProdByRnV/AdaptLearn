"""Generate a sample AI quiz for every topic of a domain and write them up for review.

Each topic gets one real quiz from Groq, made exactly as learners get it, then the answer check
(see services/llm_quiz.py). The report shows every question with its options, answer key and
explanation, and the check's verdict, so a reviewer can read a whole domain in one sitting.

Groq's free tier allows about 8,000 tokens a minute and 1,000 requests a day; a topic costs two
requests and about 2,500 tokens. The run pauses between topics, waits when Groq asks it to, and
stops cleanly (writing what it has) when the daily limit is reached.

Usage, from backend/ with the venv active and GROQ_API_KEY set:
    python -m seed.sample_quizzes --domain foundations
    python -m seed.sample_quizzes --domain web-development --topic css_grid --topic flexbox
    python -m seed.sample_quizzes --domain foundations --out ../content-review/foundations.md --pause 20
"""

import argparse
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from groq import APIConnectionError, APIStatusError, APITimeoutError

from config import get_settings
from schemas.quiz import QuizQuestion
from seed.curriculum import DOMAIN_BY_ID, DOMAINS
from seed.model import Topic
from services import llm_quiz
from services.topic_service import TopicInfo

DEFAULT_DIR = Path(__file__).resolve().parents[2] / "content-review"
GENERATE_ATTEMPTS = 3
# A Retry-After longer than this means a daily limit, not a per-minute one: stop instead of waiting.
LONGEST_WAIT_SECONDS = 120
LETTERS = "ABCD"


class DailyLimitReached(Exception):
    pass


@dataclass
class TopicSample:
    topic: Topic
    questions: list[QuizQuestion] = field(default_factory=list)
    checks: list[llm_quiz.AnswerCheck] = field(default_factory=list)
    problem: str = ""

    @property
    def rejected(self) -> int:
        return sum(not c.passes(q.correct) for q, c in zip(self.questions, self.checks, strict=False))


def topic_info(topic: Topic) -> TopicInfo:
    """What the quiz prompt needs, straight from the curriculum files (no databases)."""
    domains = sorted(d.id for d in DOMAINS if topic.id in d.topic_ids)
    home = next(d.id for d in DOMAINS if topic in d.topics)
    return TopicInfo(
        id=topic.id, name=topic.name, description=topic.description, difficulty=topic.difficulty,
        resources=[], prerequisites=[], prerequisite_names=[], home_domain=home, domains=domains,
        prerequisite_domains=[],
    )


def with_rate_limits(call, sleep=time.sleep):
    """Run a Groq call; on a 429 wait as long as Groq asks (once), unless that means a daily limit."""
    for attempt in (1, 2):
        try:
            return call()
        except APIStatusError as exc:
            if exc.status_code != 429 or attempt == 2:
                raise
            wait = float(exc.response.headers.get("retry-after", "30") or 30)
            if wait > LONGEST_WAIT_SECONDS:
                raise DailyLimitReached(f"Groq asks to wait {wait:.0f}s: a daily limit is reached") from exc
            sleep(wait + 1)
    raise AssertionError("unreachable")


def sample_topic(topic: Topic, domain_name: str, sleep=time.sleep) -> TopicSample:
    sample = TopicSample(topic)
    messages = [
        {"role": "system", "content": llm_quiz.SYSTEM_PROMPT},
        {"role": "user", "content": llm_quiz.build_user_prompt(topic_info(topic), domain_name)},
    ]
    for _ in range(GENERATE_ATTEMPTS):
        try:
            raw = with_rate_limits(lambda: llm_quiz.call_groq(messages, timeout=30), sleep)
            sample.questions = llm_quiz.parse_quiz(raw)
            break
        except llm_quiz.InvalidQuizOutput as exc:
            sample.problem = f"invalid quiz: {exc}"
        except APIStatusError as exc:
            if exc.status_code != 400:
                raise
            sample.problem = f"rejected by Groq: {exc}"
    else:
        return sample
    try:
        sample.checks = with_rate_limits(lambda: llm_quiz.check_answers(sample.questions, timeout=30), sleep)
        sample.problem = ""
    except (llm_quiz.InvalidQuizOutput, APIStatusError) as exc:
        if isinstance(exc, APIStatusError) and exc.status_code == 429:
            raise
        sample.problem = f"answer check failed: {exc}"
    return sample


def render(domain_name: str, samples: list[TopicSample], stopped: str = "") -> str:
    settings = get_settings()
    questions = sum(len(s.questions) for s in samples)
    rejected = sum(s.rejected for s in samples)
    lines = [
        f"# Sample AI quizzes: {domain_name}",
        "",
        f"Generated {datetime.now():%Y-%m-%d %H:%M} with {settings.groq_model} "
        f"(answer check at {settings.groq_check_reasoning_effort or 'default'} effort).",
        f"{len(samples)} topics, {questions} questions, {rejected} rejected by the answer check.",
    ]
    if stopped:
        lines += ["", f"**Stopped early:** {stopped}"]
    for s in samples:
        lines += ["", f"## {s.topic.name} (`{s.topic.id}`, level {s.topic.difficulty})"]
        if s.problem:
            lines += ["", f"**Problem:** {s.problem}"]
        for n, q in enumerate(s.questions, start=1):
            check = s.checks[n - 1] if n <= len(s.checks) else None
            lines += ["", f"### Question {n}", "", q.question, ""]
            lines += [f"- {LETTERS[i]}{' (key)' if i == q.correct else ''}: {option}" for i, option in enumerate(q.options)]
            lines += ["", f"Explanation: {q.explanation}"]
            if check is None:
                lines += ["", "Answer check: not run"]
            else:
                verdict = "passed" if check.passes(q.correct) else "**REJECTED**"
                said = ", ".join(LETTERS[i] for i in sorted(set(check.correct))) or "none"
                lines += ["", f"Answer check: {verdict} (correct: {said}; sound: {check.sound}). {check.reason}"]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None, out=sys.stdout, sleep=time.sleep) -> int:
    parser = argparse.ArgumentParser(prog="python -m seed.sample_quizzes", description=__doc__.split("\n\n")[0])
    parser.add_argument("--domain", required=True, metavar="ID", help="the domain to sample")
    parser.add_argument("--topic", action="append", metavar="ID", help="only these topics (repeatable)")
    parser.add_argument("--out", type=Path, help="report file (default: content-review/<domain>-<time>.md)")
    parser.add_argument("--pause", type=float, default=15, help="seconds between topics (default 15)")
    args = parser.parse_args(argv)

    if not get_settings().groq_api_key.strip():
        print("GROQ_API_KEY is not set; there is nothing to sample.", file=out)
        return 2
    domain = DOMAIN_BY_ID.get(args.domain)
    if domain is None:
        print(f"Unknown domain {args.domain!r} (domains: {', '.join(DOMAIN_BY_ID)})", file=out)
        return 2
    own = {t.id: t for t in domain.topics}
    unknown = sorted(set(args.topic or []) - set(own))
    if unknown:
        print(f"Not defined in {domain.id}: {', '.join(unknown)}", file=out)
        return 2
    topics = [own[i] for i in args.topic] if args.topic else list(domain.topics)

    samples: list[TopicSample] = []
    stopped = ""
    for n, topic in enumerate(topics):
        if n:
            sleep(args.pause)
        try:
            samples.append(sample_topic(topic, domain.name, sleep))
        except DailyLimitReached as exc:
            stopped = f"{exc}; {len(topics) - n} topic(s) not sampled"
            break
        except (APIStatusError, APIConnectionError, APITimeoutError) as exc:
            samples.append(TopicSample(topic, problem=f"Groq error: {exc}"))
        print(f"{topic.id}: {len(samples[-1].questions)} questions, {samples[-1].rejected} rejected"
              f"{' - ' + samples[-1].problem if samples[-1].problem else ''}", file=out)

    path = args.out or DEFAULT_DIR / f"{domain.id}-{datetime.now():%Y%m%d-%H%M}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(domain.name, samples, stopped), encoding="utf-8")
    print(f"Report written to {path}" + (f" ({stopped})" if stopped else ""), file=out)
    return 1 if stopped else 0


if __name__ == "__main__":
    raise SystemExit(main())
