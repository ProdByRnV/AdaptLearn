"""Foundations: groundwork that most technical paths build on.

A starter set; the domain grows in a later phase. Git Basics is defined here and shared with
Web Development.
"""

from seed.model import Domain, Topic, article, docs, video

TOPICS: tuple[Topic, ...] = (
    Topic(
        "command_line_basics", "Command Line Basics",
        "Working in a terminal: moving between folders, listing, creating, copying, moving and deleting "
        "files, running programs with options, and reading their output and error messages.",
        1,
        (
            docs("MDN: Command line crash course", "https://developer.mozilla.org/en-US/docs/Learn_web_development/Getting_started/Environment_setup/Command_line"),
            article("Ubuntu: The Linux command line for beginners", "https://ubuntu.com/tutorials/command-line-for-beginners"),
            article("MIT Missing Semester: The Shell", "https://missing.csail.mit.edu/2020/course-shell/"),
        ),
    ),
    Topic(
        "how_the_internet_works", "How the Internet Works",
        "How computers reach each other: IP addresses, packets and routers, DNS turning names into "
        "addresses, and how a browser requests a page from a server over HTTP.",
        1,
        (
            docs("MDN: How does the Internet work?", "https://developer.mozilla.org/en-US/docs/Learn_web_development/Howto/Web_mechanics/How_does_the_Internet_work"),
            docs("MDN: How the web works", "https://developer.mozilla.org/en-US/docs/Learn_web_development/Getting_started/Web_standards/How_the_web_works"),
        ),
    ),
    Topic(
        "git_basics", "Git Basics",
        "Version control with Git: repositories, commits, branches, merging and working with remotes.",
        1,
        (
            docs("Pro Git: Getting Started", "https://git-scm.com/book/en/v2/Getting-Started-About-Version-Control"),
            article("Learn Git Branching (interactive)", "https://learngitbranching.js.org/"),
            video("Git Explained in 100 Seconds", "https://www.youtube.com/watch?v=hwP7WQkmECE"),
        ),
    ),
)

FOUNDATIONS = Domain(
    id="foundations",
    name="Foundations",
    description=(
        "The groundwork most technical paths build on: working in a terminal, tracking your work "
        "with Git, and how computers talk to each other over the internet."
    ),
    topics=TOPICS,
)
