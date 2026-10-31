"""Checks curriculum content before it ships: the rules a reviewer would apply, run by a machine.

Offline (always): the curriculum validator, topic descriptions, resource lists, the fallback
question bank (every question through the same validation as AI questions) and the shape of the
prerequisite graph. Online (--online): every resource link is opened, and every video is looked up
through its site's oEmbed endpoint, which says whether it still exists and can be embedded.

Usage, from backend/ with the venv active:
    python -m seed.check_content                      # every domain, offline
    python -m seed.check_content --online             # also open every link and video
    python -m seed.check_content --domain foundations # one domain (repeat for several)

Errors must be fixed; warnings point at something worth a look. Exit status 1 when there are errors.
"""

import argparse
import re
import sys
from collections import defaultdict
from collections.abc import Iterable, Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import quote, urlsplit

import httpx
from pydantic import ValidationError

from schemas.quiz import QUESTIONS_PER_QUIZ, QuizContent, QuizQuestion, normalise
from seed.curriculum import DOMAINS, CurriculumError, validate_curriculum
from seed.fallback_questions import FALLBACK_QUESTIONS
from seed.model import Domain, Resource, Topic

DESCRIPTION_LENGTH = (60, 300)
PLACEHOLDER = re.compile(r"\b(todo|tbd|tba|fixme|lorem ipsum|xxx)\b", re.IGNORECASE)
CATCH_ALL = re.compile(r"\b(all|none|both|neither) of the (above|options|answers)\b", re.IGNORECASE)
# An answer this much longer than every wrong option gives itself away.
STANDS_OUT_RATIO = 1.6
STANDS_OUT_CHARS = 15
ISOLATED_DOMAIN_SIZE = 4
VIDEO_HOSTS = {"youtube.com", "youtu.be", "vimeo.com"}
YOUTUBE_ID = re.compile(r"^[\w-]{11}$")

Level = Literal["error", "warning"]


@dataclass(frozen=True)
class Finding:
    level: Level
    where: str  # a topic or domain id
    message: str

    def __str__(self) -> str:
        return f"{self.level.upper():8} {self.where}: {self.message}"


def _host(url: str) -> str:
    host = (urlsplit(url).hostname or "").lower()
    return host.removeprefix("www.").removeprefix("m.")


def youtube_video_id(url: str) -> str | None:
    """The id of a single YouTube video (watch?v=, youtu.be/ or /shorts/ links), else None."""
    parts = urlsplit(url)
    host = _host(url)
    if host == "youtu.be":
        candidate = parts.path.strip("/")
    elif host == "youtube.com" and parts.path == "/watch":
        candidate = dict(p.split("=", 1) for p in parts.query.split("&") if "=" in p).get("v", "")
    elif host == "youtube.com" and parts.path.startswith("/shorts/"):
        candidate = parts.path.removeprefix("/shorts/").strip("/")
    else:
        return None
    return candidate if YOUTUBE_ID.match(candidate) else None


# --- Offline -----------------------------------------------------------------------------

def check_static(
    domains: tuple[Domain, ...] = DOMAINS,
    fallback: Mapping[str, list[dict[str, Any]]] = FALLBACK_QUESTIONS,
    only: Iterable[str] | None = None,
) -> list[Finding]:
    """Every offline rule. `only` limits topic rules to the topics defined in those domains; the
    validator and graph rules always look at the whole curriculum, since edges cross domains."""
    findings: list[Finding] = []
    try:
        validate_curriculum(domains)
    except CurriculumError as exc:
        lines = str(exc).splitlines()[1:]
        findings += [Finding("error", "curriculum", line.strip()) for line in lines]

    all_topics = [t for d in domains for t in d.topics]
    selected = set(only) if only is not None else {d.id for d in domains}
    topics = [t for d in domains if d.id in selected for t in d.topics]

    findings += _description_findings(topics, all_topics)
    findings += _resource_findings(topics, all_topics)
    findings += _fallback_findings(topics, all_topics, fallback, check_unknown=only is None)
    findings += _graph_findings(domains, selected)
    return findings


def _description_findings(topics: list[Topic], all_topics: list[Topic]) -> list[Finding]:
    findings = []
    low, high = DESCRIPTION_LENGTH
    by_text = defaultdict(list)
    for t in all_topics:
        by_text[normalise(t.description)].append(t.id)
    for t in topics:
        length = len(t.description.strip())
        if not low <= length <= high:
            findings.append(Finding("error", t.id, f"description is {length} characters; keep it between {low} and {high}"))
        if not t.description.rstrip().endswith("."):
            findings.append(Finding("error", t.id, "description should be a full sentence ending with a full stop"))
        for text in (t.name, t.description, *(r.title for r in t.resources)):
            if PLACEHOLDER.search(text):
                findings.append(Finding("error", t.id, f"placeholder text: {text!r}"))
        others = [i for i in by_text[normalise(t.description)] if i != t.id]
        if others:
            findings.append(Finding("error", t.id, f"same description as {', '.join(others)}"))
    return findings


def _resource_findings(topics: list[Topic], all_topics: list[Topic]) -> list[Finding]:
    findings = []
    users = defaultdict(list)
    for t in all_topics:
        for r in t.resources:
            users[r.url].append(t.id)
    for t in topics:
        urls = [r.url for r in t.resources]
        for url in sorted({u for u in urls if urls.count(u) > 1}):
            findings.append(Finding("error", t.id, f"lists {url} twice"))
        for r in t.resources:
            findings += _resource_type_findings(t.id, r)
            others = [i for i in users[r.url] if i != t.id]
            if others:
                findings.append(Finding("warning", t.id, f"{r.url} is also a resource of {', '.join(others)}"))
    return findings


def _resource_type_findings(topic_id: str, r: Resource) -> list[Finding]:
    on_video_site = _host(r.url) in VIDEO_HOSTS
    if r.type == "video" and not on_video_site:
        return [Finding("error", topic_id, f"{r.title!r} is marked as a video but isn't on YouTube or Vimeo")]
    if r.type != "video" and on_video_site:
        return [Finding("error", topic_id, f"{r.title!r} is on a video site but marked as {r.type}")]
    if on_video_site and _host(r.url) != "vimeo.com" and youtube_video_id(r.url) is None:
        return [Finding("error", topic_id, f"{r.title!r} isn't a link to a single YouTube video: {r.url}")]
    return []


def _fallback_findings(
    topics: list[Topic], all_topics: list[Topic], fallback: Mapping[str, list[dict[str, Any]]], check_unknown: bool
) -> list[Finding]:
    findings = []
    known = {t.id for t in all_topics}
    if check_unknown:
        for topic_id in sorted(set(fallback) - known):
            findings.append(Finding("error", topic_id, "has fallback questions but isn't in the curriculum"))
    owner = {}
    for topic_id, items in fallback.items():
        for item in items:
            owner.setdefault(normalise(str(item.get("question", ""))), []).append(topic_id)
    for t in topics:
        items = fallback.get(t.id, [])
        if len(items) < QUESTIONS_PER_QUIZ:
            findings.append(Finding("error", t.id, f"has {len(items)} fallback questions; needs {QUESTIONS_PER_QUIZ}"))
        valid = []
        for n, item in enumerate(items, start=1):
            try:
                question = QuizQuestion.model_validate(item)
            except ValidationError as exc:
                reasons = "; ".join(e["msg"] for e in exc.errors()[:3])
                findings.append(Finding("error", t.id, f"fallback question {n} is invalid: {reasons}"))
                continue
            valid.append(question)
            findings += _question_findings(t.id, n, question)
            others = [i for i in owner[normalise(question.question)] if i != t.id]
            if others:
                findings.append(Finding("error", t.id, f"fallback question {n} is also asked for {', '.join(others)}"))
        if len(valid) >= QUESTIONS_PER_QUIZ:
            try:
                QuizContent.model_validate({"questions": [q.model_dump() for q in valid[:QUESTIONS_PER_QUIZ]]})
            except ValidationError as exc:
                findings.append(Finding("error", t.id, f"fallback questions: {exc.errors()[0]['msg']}"))
    return findings


def _question_findings(topic_id: str, n: int, q: QuizQuestion) -> list[Finding]:
    # Maths delimiters, distinct options and the rest are already checked by QuizQuestion.
    findings = []
    if any(CATCH_ALL.search(o) for o in q.options):
        findings.append(Finding("error", topic_id, f"fallback question {n} uses an all/none-of-the-above option"))
    answer = len(q.options[q.correct])
    longest_wrong = max(len(o) for i, o in enumerate(q.options) if i != q.correct)
    if answer > STANDS_OUT_RATIO * longest_wrong and answer - longest_wrong > STANDS_OUT_CHARS:
        findings.append(Finding(
            "warning", topic_id,
            f"fallback question {n}: the answer stands out by length ({answer} characters, the longest wrong "
            f"option {longest_wrong})",
        ))
    return findings


def _graph_findings(domains: tuple[Domain, ...], selected: set[str]) -> list[Finding]:
    findings = []
    topics = {t.id: t for d in domains for t in d.topics}
    edges = [e for d in domains for e in d.prerequisites if e[0] in topics and e[1] in topics]
    needs = defaultdict(set)
    for source, target in edges:
        needs[target].add(source)
    home = {t.id: d.id for d in domains for t in d.topics}

    def reachable(start: str, skip_edge: tuple[str, str]) -> set[str]:
        """Topics `start` depends on, ignoring one direct edge."""
        seen, stack = set(), [p for p in needs[start] if (p, start) != skip_edge]
        while stack:
            node = stack.pop()
            if node not in seen:
                seen.add(node)
                stack.extend(needs[node])
        return seen

    for source, target in edges:
        if home[target] not in selected:
            continue
        if topics[source].difficulty > topics[target].difficulty:
            findings.append(Finding(
                "warning", target,
                f"prerequisite {source} is harder (level {topics[source].difficulty}) than the topic itself "
                f"(level {topics[target].difficulty})",
            ))
        if source in reachable(target, (source, target)):
            findings.append(Finding("warning", target, f"prerequisite {source} is already implied by another prerequisite"))

    for d in domains:
        if d.id not in selected or len(d.topic_ids) < ISOLATED_DOMAIN_SIZE:
            continue
        members = set(d.topic_ids)
        for topic_id in d.topic_ids:
            linked = (needs[topic_id] & members) or any(topic_id in needs[m] for m in members)
            if not linked:
                findings.append(Finding("warning", topic_id, f"isn't connected to any other topic in {d.id}"))
    return findings


# --- Online ------------------------------------------------------------------------------

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
REFUSED = {401, 403, 429, 999}  # sites that block automated visitors; someone has to look by hand


def check_link(client: httpx.Client, url: str) -> tuple[Level | None, str]:
    """(None, note) when the page opens; otherwise the level and what went wrong."""
    for attempt in (1, 2):
        try:
            with client.stream("GET", url) as response:
                status, final = response.status_code, str(response.url)
            break
        except httpx.HTTPError as exc:
            if attempt == 2:
                return "error", f"unreachable ({type(exc).__name__}): {url}"
    if status in (404, 410):
        return "error", f"dead link ({status}): {url}"
    if status in REFUSED:
        return "warning", f"the site refused an automated check ({status}); open it by hand: {url}"
    if status >= 400:
        return "warning", f"the site answered {status}; try again later: {url}"
    if urlsplit(final).path in ("", "/") and urlsplit(url).path not in ("", "/"):
        return "warning", f"redirects to the site's home page ({final}), so the page may be gone: {url}"
    return None, "ok"


def check_video(client: httpx.Client, url: str) -> tuple[Level | None, str]:
    """Look a YouTube or Vimeo video up through oEmbed: does it exist, and may it be embedded?"""
    if _host(url) == "vimeo.com":
        endpoint = f"https://vimeo.com/api/oembed.json?url={quote(url, safe='')}"
    else:
        endpoint = f"https://www.youtube.com/oembed?format=json&url={quote(url, safe='')}"
    try:
        response = client.get(endpoint)
    except httpx.HTTPError as exc:
        return "error", f"couldn't reach the video site ({type(exc).__name__}): {url}"
    if response.status_code == 200:
        title = response.json().get("title", "")
        return None, f"video found: {title}"
    if response.status_code in (401, 403):
        return "warning", f"the video exists but can't be embedded ({response.status_code}); still watchable: {url}"
    return "error", f"video unavailable, removed or private ({response.status_code}): {url}"


def check_online(topics: list[Topic], client: httpx.Client | None = None, workers: int = 8) -> list[Finding]:
    """Open every resource (videos through oEmbed), a few at a time."""
    own = client is None
    client = client or httpx.Client(
        follow_redirects=True, timeout=20, headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"}
    )
    jobs = [(t.id, r) for t in topics for r in t.resources]

    def run(job: tuple[str, Resource]) -> Finding | None:
        topic_id, r = job
        level, message = (check_video if r.type == "video" else check_link)(client, r.url)
        return Finding(level, topic_id, message) if level else None

    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            return [f for f in pool.map(run, jobs) if f]
    finally:
        if own:
            client.close()


# --- Command line ------------------------------------------------------------------------

def main(argv: list[str] | None = None, out=sys.stdout) -> int:
    parser = argparse.ArgumentParser(prog="python -m seed.check_content", description=__doc__.split("\n\n")[0])
    parser.add_argument("--online", action="store_true", help="also open every link and look up every video")
    parser.add_argument("--domain", action="append", metavar="ID", help="only this domain's topics (repeatable)")
    args = parser.parse_args(argv)

    known = {d.id for d in DOMAINS}
    unknown = sorted(set(args.domain or []) - known)
    if unknown:
        print(f"Unknown domain: {', '.join(unknown)} (domains: {', '.join(sorted(known))})", file=out)
        return 2

    findings = check_static(only=args.domain)
    topics = [t for d in DOMAINS if args.domain is None or d.id in args.domain for t in d.topics]
    resources = sum(len(t.resources) for t in topics)
    if args.online:
        findings += check_online(topics)

    order = {"error": 0, "warning": 1}
    for finding in sorted(findings, key=lambda f: (order[f.level], f.where)):
        print(finding, file=out)
    errors = sum(f.level == "error" for f in findings)
    warnings = len(findings) - errors
    checked = f"{len(topics)} topics, {resources} resources{' (opened)' if args.online else ''}"
    print(f"\nChecked {checked}: {errors} error(s), {warnings} warning(s).", file=out)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
