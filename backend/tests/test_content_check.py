"""Phase 25: the content checker (python -m seed.check_content).

Offline rules run against the real curriculum (which must stay free of errors) and against small
made-up domains that break one rule each. Online checks use a fake network: no test opens a real link.
"""

import io
from dataclasses import replace

import httpx
import pytest

from seed import check_content
from seed.check_content import Finding, check_link, check_online, check_static, check_video, youtube_video_id
from seed.curriculum import DOMAINS
from seed.fallback_questions import FALLBACK_QUESTIONS
from seed.model import Domain, Topic, article, docs, video

DESC = "A clear description of what this topic covers, long enough to be useful."


def q(question: str, answer: str = "Right", wrong=("Wrong one", "Wrong two", "Wrong three"), explanation="Because.") -> dict:
    return {"question": question, "options": [answer, *wrong], "correct": 0, "explanation": explanation}


def bank(topic_id: str) -> list[dict]:
    return [q(f"{topic_id} question {n}?") for n in range(3)]


def topic(topic_id: str, difficulty: int = 1, **changes) -> Topic:
    base = Topic(topic_id, topic_id.replace("_", " ").title(), DESC, difficulty, (docs("Docs", f"https://example.com/{topic_id}"),))
    return replace(base, **changes)


def domain(*topics: Topic, edges=(), domain_id="pytest-a", shared=()) -> Domain:
    return Domain(domain_id, "Pytest A", "A test domain.", topics, tuple(edges), tuple(shared))


def run(domains, fallback=None, only=None) -> list[Finding]:
    if fallback is None:
        fallback = {t.id: bank(t.id) for d in domains for t in d.topics}
    return check_static(tuple(domains), fallback, only)


def messages(findings, level=None) -> list[str]:
    return [f"{f.where}: {f.message}" for f in findings if level is None or f.level == level]


# --- The real curriculum --------------------------------------------------------------------

def test_the_real_curriculum_has_no_errors():
    errors = messages(check_static(), "error")
    assert errors == []


def test_a_clean_made_up_curriculum_has_no_findings():
    two = topic("a_two", description=DESC + " Two.")
    assert run([domain(topic("a_one"), two, edges=[("a_one", "a_two")])]) == []


# --- Descriptions --------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("description", "expected"),
    [
        ("Too short.", "description is 10 characters; keep it between 60 and 300"),
        ("x" * 299 + ".", "description is 300 characters"),  # 300 is fine...
        ("x" * 300 + ".", "description is 301 characters; keep it between 60 and 300"),
        (DESC.rstrip("."), "description should be a full sentence ending with a full stop"),
        (DESC[:-1] + " - TODO.", "placeholder text"),
    ],
)
def test_description_rules(description, expected):
    found = messages(run([domain(topic("a_one", description=description))]), "error")
    if expected == "description is 300 characters":
        assert found == []
    else:
        assert any(expected in m for m in found), found


def test_two_topics_with_the_same_description_are_flagged():
    found = messages(run([domain(topic("a_one"), topic("a_two"))]), "error")
    assert "a_one: same description as a_two" in found and "a_two: same description as a_one" in found


# --- Resources -----------------------------------------------------------------------------

YT = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


@pytest.mark.parametrize(
    ("resources", "expected"),
    [
        ((docs("A", "https://example.com/a"), docs("B", "https://example.com/a")), "lists https://example.com/a twice"),
        ((video("Talk", "https://example.com/talk"),), "'Talk' is marked as a video but isn't on YouTube or Vimeo"),
        ((article("Clip", YT),), "'Clip' is on a video site but marked as article"),
        ((video("Channel", "https://www.youtube.com/@somechannel"),), "'Channel' isn't a link to a single YouTube video"),
        ((video("Playlist", "https://www.youtube.com/playlist?list=PL123"),), "isn't a link to a single YouTube video"),
        ((docs("TBD", "https://example.com/x"),), "placeholder text: 'TBD'"),
    ],
)
def test_resource_rules(resources, expected):
    found = messages(run([domain(topic("a_one", resources=resources))]), "error")
    assert any(expected in m for m in found), found


@pytest.mark.parametrize(
    "url",
    [YT, "https://youtu.be/dQw4w9WgXcQ", "https://m.youtube.com/watch?v=dQw4w9WgXcQ&t=30",
     "https://www.youtube.com/shorts/dQw4w9WgXcQ", "https://vimeo.com/76979871"],
)
def test_single_videos_on_youtube_and_vimeo_are_fine(url):
    assert run([domain(topic("a_one", resources=(video("Video", url),)))]) == []


def test_youtube_video_ids():
    assert youtube_video_id(YT) == "dQw4w9WgXcQ"
    assert youtube_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert youtube_video_id("https://www.youtube.com/watch?v=short") is None
    assert youtube_video_id("https://example.com/watch?v=dQw4w9WgXcQ") is None


def test_a_link_shared_by_two_topics_is_a_warning():
    shared = (docs("Same", "https://example.com/same"),)
    found = run([domain(topic("a_one", resources=shared), topic("a_two", description=DESC + " Two.", resources=shared))])
    assert messages(found, "error") == []
    assert "a_one: https://example.com/same is also a resource of a_two" in messages(found, "warning")


# --- Fallback questions --------------------------------------------------------------------

def test_missing_or_too_few_fallback_questions():
    found = messages(run([domain(topic("a_one"))], fallback={}), "error")
    assert found == ["a_one: has 0 fallback questions; needs 3"]
    found = messages(run([domain(topic("a_one"))], fallback={"a_one": bank("a_one")[:2]}), "error")
    assert found == ["a_one: has 2 fallback questions; needs 3"]


def test_fallback_questions_for_a_topic_that_does_not_exist():
    fallback = {"a_one": bank("a_one"), "ghost": bank("ghost")}
    assert "ghost: has fallback questions but isn't in the curriculum" in messages(run([domain(topic("a_one"))], fallback))


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        (q("Dupes?", "Same", ("same", "Other", "Another")), "fallback question 1 is invalid: Value error, options must be distinct"),
        (q("What is \\( x^2 ?"), "fallback question 1 is invalid: Value error, maths opened with \\( is never closed"),
        (q("Which?", "All of the above"), "fallback question 1 uses an all/none-of-the-above option"),
        (q("Which?", "Right", ("None of the options", "B", "C")), "uses an all/none-of-the-above option"),
    ],
)
def test_each_fallback_question_is_validated(question, expected):
    fallback = {"a_one": [question, *bank("a_one")[1:]]}
    found = messages(run([domain(topic("a_one"))], fallback), "error")
    assert any(expected in m for m in found), found


def test_repeated_questions_within_a_topic_and_across_topics():
    same = q("Shared question?")
    found = messages(run([domain(topic("a_one"))], {"a_one": [same, same, bank("a_one")[2]]}), "error")
    assert "a_one: fallback questions: Value error, questions must be distinct" in found
    fallback = {"a_one": [same, *bank("a_one")[1:]], "a_two": [same, *bank("a_two")[1:]]}
    found = messages(run([domain(topic("a_one"), topic("a_two", description=DESC + " Two."))], fallback), "error")
    assert "a_one: fallback question 1 is also asked for a_two" in found


def test_an_answer_that_stands_out_by_length_is_a_warning():
    giveaway = q("Which?", "A long and detailed answer that is obviously the right one", ("Short", "Brief", "Tiny"))
    found = run([domain(topic("a_one"))], {"a_one": [giveaway, *bank("a_one")[1:]]})
    assert messages(found, "error") == []
    assert messages(found, "warning") == [
        "a_one: fallback question 1: the answer stands out by length (58 characters, the longest wrong option 5)"
    ]


def test_a_slightly_longer_answer_is_fine():
    fine = q("Which?", "A somewhat longer answer", ("Short answer here", "Brief one", "Tiny"))
    assert run([domain(topic("a_one"))], {"a_one": [fine, *bank("a_one")[1:]]}) == []


# --- The prerequisite graph ----------------------------------------------------------------

def test_invalid_curricula_report_the_validator_problems():
    found = messages(run([domain(topic("a_one"), topic("a_two"), edges=[("a_one", "a_two"), ("a_two", "a_one")])]))
    assert any(m.startswith("curriculum: prerequisite cycle") for m in found)


def test_a_prerequisite_harder_than_its_topic_is_a_warning():
    found = run([domain(topic("a_one", 3), topic("a_two", 1, description=DESC + " Two."), edges=[("a_one", "a_two")])])
    assert messages(found) == ["a_two: prerequisite a_one is harder (level 3) than the topic itself (level 1)"]


def test_a_prerequisite_already_implied_by_another_is_a_warning():
    topics = [topic(f"a_{n}", description=f"{DESC} {n}.") for n in ("one", "two", "three")]
    found = run([domain(*topics, edges=[("a_one", "a_two"), ("a_two", "a_three"), ("a_one", "a_three")])])
    assert messages(found) == ["a_three: prerequisite a_one is already implied by another prerequisite"]


def test_a_topic_unconnected_in_a_larger_domain_is_a_warning():
    topics = [topic(f"a_{n}", description=f"{DESC} {n}.") for n in ("one", "two", "three", "four")]
    found = run([domain(*topics, edges=[("a_one", "a_two"), ("a_two", "a_three")])])
    assert messages(found) == ["a_four: isn't connected to any other topic in pytest-a"]
    # Small domains (fewer than 4 topics) are often independent starters, so they are left alone.
    assert run([domain(*topics[:3], edges=[("a_one", "a_two")])]) == []


def test_only_limits_topic_rules_to_a_domain():
    a = domain(topic("a_one", description="Short."))
    b = Domain("pytest-b", "Pytest B", "Another.", (topic("b_one", description="Also short."),))
    found = run([a, b], only=["pytest-b"])
    assert [f.where for f in found] == ["b_one"]


# --- Online --------------------------------------------------------------------------------

def client_for(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (200, (None, "ok")),
        (404, ("error", "dead link (404): https://example.com/page")),
        (410, ("error", "dead link (410): https://example.com/page")),
        (403, ("warning", "the site refused an automated check (403); open it by hand: https://example.com/page")),
        (429, ("warning", "the site refused an automated check (429); open it by hand: https://example.com/page")),
        (503, ("warning", "the site answered 503; try again later: https://example.com/page")),
    ],
)
def test_links_are_opened(status, expected):
    with client_for(lambda request: httpx.Response(status)) as client:
        assert check_link(client, "https://example.com/page") == expected


def test_a_link_that_now_redirects_to_the_home_page_is_a_warning():
    def handler(request):
        if request.url.path == "/old-page":
            return httpx.Response(301, headers={"Location": "https://example.com/"})
        return httpx.Response(200)

    with client_for(handler) as client:
        level, message = check_link(client, "https://example.com/old-page")
    assert level == "warning" and "redirects to the site's home page" in message


def test_an_unreachable_link_is_tried_twice_then_an_error():
    calls = []

    def handler(request):
        calls.append(request.url)
        raise httpx.ConnectError("refused", request=request)

    with client_for(handler) as client:
        assert check_link(client, "https://example.com/page") == ("error", "unreachable (ConnectError): https://example.com/page")
    assert len(calls) == 2


def test_a_link_that_works_the_second_time_is_fine():
    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) == 1:
            raise httpx.ReadTimeout("slow", request=request)
        return httpx.Response(200)

    with client_for(handler) as client:
        assert check_link(client, "https://example.com/page") == (None, "ok")


@pytest.mark.parametrize(
    ("status", "level"),
    [(200, None), (401, "warning"), (403, "warning"), (404, "error"), (400, "error")],
)
def test_youtube_videos_are_looked_up_through_oembed(status, level):
    seen = []

    def handler(request):
        seen.append(request.url)
        return httpx.Response(status, json={"title": "Git in 100 seconds"} if status == 200 else None)

    with client_for(handler) as client:
        found_level, message = check_video(client, YT)
    assert found_level == level
    assert seen[0].host == "www.youtube.com" and seen[0].path == "/oembed"
    assert seen[0].params["url"] == YT and seen[0].params["format"] == "json"
    if status == 200:
        assert message == "video found: Git in 100 seconds"


def test_vimeo_videos_use_vimeos_oembed():
    seen = []

    def handler(request):
        seen.append(request.url)
        return httpx.Response(404)

    with client_for(handler) as client:
        assert check_video(client, "https://vimeo.com/1")[0] == "error"
    assert seen[0].host == "vimeo.com" and seen[0].path == "/api/oembed.json"


def test_an_unreachable_video_site_is_an_error():
    def handler(request):
        raise httpx.ConnectError("down", request=request)

    with client_for(handler) as client:
        assert check_video(client, YT)[0] == "error"


def test_check_online_opens_every_resource_and_reports_only_problems():
    topics = [
        topic("a_one", resources=(docs("Fine", "https://example.com/fine"), docs("Gone", "https://example.com/gone"))),
        topic("a_two", resources=(video("Clip", YT),)),
    ]
    opened = []

    def handler(request):
        opened.append(str(request.url))
        if request.url.path == "/gone":
            return httpx.Response(404)
        return httpx.Response(200, json={"title": "Clip"})

    with client_for(handler) as client:
        found = check_online(topics, client, workers=2)
    assert len(opened) == 3
    assert [(f.level, f.where) for f in found] == [("error", "a_one")]


# --- Command line ---------------------------------------------------------------------------

def test_the_command_reports_and_exits_0_without_errors():
    out = io.StringIO()
    assert check_content.main([], out) == 0
    text = out.getvalue()
    topics = sum(len(d.topics) for d in DOMAINS)
    assert f"Checked {topics} topics" in text and "0 error(s)" in text


def test_the_command_exits_1_on_errors_and_lists_errors_first(monkeypatch):
    found = [Finding("warning", "b", "look"), Finding("error", "a", "broken")]
    monkeypatch.setattr(check_content, "check_static", lambda only=None: found)
    out = io.StringIO()
    assert check_content.main([], out) == 1
    lines = out.getvalue().splitlines()
    assert lines[:2] == ["ERROR    a: broken", "WARNING  b: look"]
    assert "1 error(s), 1 warning(s)" in lines[-1]


def test_the_command_checks_one_domain_and_opens_links_only_when_asked(monkeypatch):
    calls = {}
    monkeypatch.setattr(check_content, "check_static", lambda only=None: calls.setdefault("only", only) and [])
    monkeypatch.setattr(check_content, "check_online", lambda topics: calls.setdefault("online", [t.id for t in topics]) and [])
    out = io.StringIO()
    assert check_content.main(["--domain", "foundations"], out) == 0
    assert calls == {"only": ["foundations"]}
    assert check_content.main(["--domain", "foundations", "--online"], out) == 0
    assert calls["online"] == ["command_line_basics", "how_the_internet_works", "git_basics"]
    assert "(opened)" in out.getvalue()


def test_the_command_rejects_an_unknown_domain():
    out = io.StringIO()
    assert check_content.main(["--domain", "astrology"], out) == 2
    assert "Unknown domain: astrology" in out.getvalue()


def test_the_real_fallback_bank_is_what_the_checker_reads():
    assert check_content.FALLBACK_QUESTIONS is FALLBACK_QUESTIONS
