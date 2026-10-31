"""Foundations: groundwork that most technical paths build on.

Git Basics is defined here and shared with Web Development. Its three original topics stay
starting topics (no prerequisites), so Web Development's starting topics don't change.
"""

from seed.model import Domain, Topic, article, docs, video

TOPICS: tuple[Topic, ...] = (
    # --- Computers and data ------------------------------------------------------------
    Topic(
        "how_computers_work", "How Computers Work",
        "What is inside a computer and how it runs programs: the CPU fetching and executing "
        "instructions, memory (RAM) versus storage, input and output devices, and the operating "
        "system in between.",
        1,
        (
            article("BBC Bitesize: The CPU and the fetch-execute cycle", "https://www.bbc.co.uk/bitesize/guides/zws8d2p/revision/1"),
            video("The Central Processing Unit (CPU): Crash Course Computer Science #7", "https://www.youtube.com/watch?v=FZGugFqdr60"),
        ),
    ),
    Topic(
        "binary_data_representation", "Binary & Data Representation",
        "How computers store everything as bits: counting in binary, bytes and their multiples, "
        "hexadecimal as a shorthand, and how text becomes numbers through character encodings such "
        "as ASCII and UTF-8.",
        1,
        (
            article("SparkFun: Binary", "https://learn.sparkfun.com/tutorials/binary/all"),
            article("BBC Bitesize: How computers see the world", "https://www.bbc.co.uk/bitesize/guides/z26rcdm/revision/1"),
            video("Characters, Symbols and the Unicode Miracle (Computerphile)", "https://www.youtube.com/watch?v=MijmeoH9LT4"),
        ),
    ),
    Topic(
        "data_formats", "Data Formats: JSON, CSV & YAML",
        "How programs exchange structured data as text: JSON objects and arrays, CSV rows and "
        "columns, and YAML's indentation-based configuration files, with the rules each format has "
        "for strings, numbers and nesting.",
        2,
        (
            docs("MDN: Working with JSON", "https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Scripting/JSON"),
            docs("RFC 4180: the CSV format", "https://datatracker.ietf.org/doc/html/rfc4180"),
            article("freeCodeCamp: What is YAML?", "https://www.freecodecamp.org/news/what-is-yaml-the-yml-file-format/"),
        ),
    ),
    # --- Programming groundwork --------------------------------------------------------
    Topic(
        "programming_concepts", "Programming Concepts",
        "The ideas every programming language shares: values and variables, data types, conditions "
        "that choose what runs, loops that repeat, and functions that package steps under a name.",
        1,
        (
            article("CS50x: Lecture 0 notes", "https://cs50.harvard.edu/x/2024/notes/0/"),
            article("BBC Bitesize: Data types", "https://www.bbc.co.uk/bitesize/guides/zh66pbk/revision/1"),
            video("Programming Basics: Statements & Functions: Crash Course Computer Science #12", "https://www.youtube.com/watch?v=l26oaHV7D40"),
        ),
    ),
    Topic(
        "algorithmic_thinking", "Algorithmic Thinking",
        "Turning a problem into precise steps: breaking it into smaller parts, writing pseudocode, "
        "tracing an algorithm by hand, and comparing approaches such as linear and binary search by "
        "how the work grows with the input.",
        2,
        (
            article("BBC Bitesize: What is computational thinking?", "https://www.bbc.co.uk/bitesize/guides/zp92mp3/revision/1"),
            article("CS50x: Lecture 3 notes (algorithms)", "https://cs50.harvard.edu/x/2024/notes/3/"),
            video("What's an algorithm? (TED-Ed)", "https://www.youtube.com/watch?v=6hfOvs8pY1k"),
        ),
    ),
    # --- Working with a computer -------------------------------------------------------
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
        "operating_system_basics", "Operating System Basics",
        "What the operating system does for programs: running processes and sharing the CPU, "
        "managing memory, organising files with owners and permissions, user accounts, and "
        "environment variables such as PATH.",
        2,
        (
            video("Operating Systems: Crash Course Computer Science #18", "https://www.youtube.com/watch?v=26QPDBe-NB8"),
            article("Red Hat: Linux file permissions explained", "https://www.redhat.com/en/blog/linux-file-permissions-explained"),
            article("MIT Missing Semester: Command-line Environment", "https://missing.csail.mit.edu/2020/command-line/"),
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
    # --- Networks and safety -----------------------------------------------------------
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
        "security_basics", "Security Basics",
        "Everyday habits that keep accounts and devices safe: long unique passwords kept in a password "
        "manager, multi-factor authentication, spotting phishing, installing updates promptly, and "
        "what the HTTPS padlock does and does not mean.",
        1,
        (
            article("NCSC: Top tips for staying secure online", "https://www.ncsc.gov.uk/collection/top-tips-for-staying-secure-online"),
            article("EFF Surveillance Self-Defense: Creating strong passwords", "https://ssd.eff.org/module/creating-strong-passwords"),
            article("NCSC: Phishing scams, how to spot and report them", "https://www.ncsc.gov.uk/collection/phishing-scams"),
        ),
    ),
)

PREREQUISITES: tuple[tuple[str, str], ...] = (
    ("how_computers_work", "binary_data_representation"),
    ("binary_data_representation", "data_formats"),
    ("programming_concepts", "algorithmic_thinking"),
    ("how_computers_work", "operating_system_basics"),
    ("command_line_basics", "operating_system_basics"),
    ("how_the_internet_works", "security_basics"),
)

FOUNDATIONS = Domain(
    id="foundations",
    name="Foundations",
    description=(
        "The groundwork most technical paths build on: how computers work and store data, "
        "programming ideas and algorithmic thinking, the terminal and operating system, Git, "
        "data formats, how the internet works, and staying safe online."
    ),
    topics=TOPICS,
    prerequisites=PREREQUISITES,
)
