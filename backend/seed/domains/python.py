"""Python: the language from a first script to classes, packages, tests, async code and web APIs.

Three prerequisites come from Foundations: the terminal (for virtual environments), data formats
(for files) and how the internet works (for web APIs). Python Basics itself has none, so a
learner can start the language straight away.
"""

from seed.model import Domain, Topic, article, docs, video

TOPICS: tuple[Topic, ...] = (
    # --- The language -------------------------------------------------------------------
    Topic(
        "python_basics", "Python Basics",
        "Writing and running Python: the interactive prompt and script files, variables, numbers "
        "and arithmetic (including / versus //), strings, print() and input(), comments, and why "
        "indentation matters.",
        1,
        (
            docs("Python tutorial: An informal introduction to Python", "https://docs.python.org/3/tutorial/introduction.html"),
            docs("Python tutorial: Using the Python interpreter", "https://docs.python.org/3/tutorial/interpreter.html"),
            video("Python in 100 Seconds", "https://www.youtube.com/watch?v=x7X9w_GIm1s"),
        ),
    ),
    Topic(
        "python_control_flow", "Control Flow",
        "Choosing and repeating code in Python: if, elif and else, comparison and boolean operators, "
        "truthy and falsy values, while loops, for loops over range() and other sequences, and break "
        "and continue.",
        1,
        (
            docs("Python tutorial: More control flow tools", "https://docs.python.org/3/tutorial/controlflow.html"),
            video("Python for Beginners: Learn Python in 1 Hour (Programming with Mosh)", "https://www.youtube.com/watch?v=kqtD5dpn9C8"),
        ),
    ),
    Topic(
        "python_strings", "Working with Strings",
        "Text in Python: indexing and slicing, common string methods (split, join, strip, replace, "
        "upper), f-strings for formatting values, and why strings can't be changed in place.",
        1,
        (
            docs("Python tutorial: Input and output (formatting)", "https://docs.python.org/3/tutorial/inputoutput.html"),
            docs("Python docs: Built-in types (string methods)", "https://docs.python.org/3/builtins/stdtypes.html"),
            video("Python Tutorial for Beginners 2: Strings (Corey Schafer)", "https://www.youtube.com/watch?v=k9TUPpGqYTo"),
        ),
    ),
    Topic(
        "python_functions", "Functions",
        "Defining and calling functions: parameters and return values, default and keyword "
        "arguments, *args and **kwargs, None as the result of a function with no return, and "
        "variable scope (local, enclosing, global and built-in).",
        2,
        (
            video("Python Tutorial for Beginners 8: Functions (Corey Schafer)", "https://www.youtube.com/watch?v=9Os0o3wzS_I"),
            video("Python Tutorial: Variable Scope and the LEGB rule (Corey Schafer)", "https://www.youtube.com/watch?v=QVdf0LgmICw"),
        ),
    ),
    # --- Data structures ------------------------------------------------------------------
    Topic(
        "python_lists_tuples", "Lists & Tuples",
        "Ordered collections: creating, indexing and slicing lists, changing them with append, "
        "insert, pop and sort, the difference between copying a list and sharing it, and tuples as "
        "fixed records with unpacking.",
        2,
        (
            docs("Python tutorial: Data structures", "https://docs.python.org/3/tutorial/datastructures.html"),
            video("Python Tutorial for Beginners 4: Lists, Tuples, and Sets (Corey Schafer)", "https://www.youtube.com/watch?v=W8KRzm-HUcc"),
        ),
    ),
    Topic(
        "python_dicts_sets", "Dictionaries & Sets",
        "Key-value lookups with dictionaries (adding, updating, get() with a default, looping over "
        "items()), sets for unique values and fast membership tests, and which values can be "
        "dictionary keys.",
        2,
        (
            video("Python Tutorial for Beginners 5: Dictionaries (Corey Schafer)", "https://www.youtube.com/watch?v=daefaLgNkw0"),
            docs("Python docs: Glossary (hashable, mapping, iterable)", "https://docs.python.org/3/glossary.html"),
        ),
    ),
    Topic(
        "python_comprehensions", "Comprehensions",
        "Building lists, dictionaries and sets in a single expression with comprehensions, filtering "
        "with if, and generator expressions that produce values one at a time instead of building a "
        "whole list.",
        2,
        (
            article("Python Morsels: List comprehensions", "https://www.pythonmorsels.com/what-are-list-comprehensions/"),
            video("Python Tutorial: Comprehensions (Corey Schafer)", "https://www.youtube.com/watch?v=3dt4OGnU5sM"),
        ),
    ),
    # --- Programs and projects --------------------------------------------------------------
    Topic(
        "python_modules", "Modules & Imports",
        "Splitting code across files: import and from ... import, aliases, how Python finds modules, "
        "packages, and the if __name__ == \"__main__\" check for code that should only run as a "
        "script.",
        2,
        (
            docs("Python tutorial: Modules", "https://docs.python.org/3/tutorial/modules.html"),
            video("Python Tutorial for Beginners 9: Import Modules (Corey Schafer)", "https://www.youtube.com/watch?v=CqvZ3vGoGs0"),
        ),
    ),
    Topic(
        "python_virtual_environments", "pip & Virtual Environments",
        "Installing packages with pip into a virtual environment made with venv, so each project "
        "has its own dependencies: creating and activating one, and recording exact versions in "
        "requirements.txt.",
        2,
        (
            docs("Python tutorial: Virtual environments and packages", "https://docs.python.org/3/tutorial/venv.html"),
            docs("Python Packaging User Guide: pip and venv", "https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/"),
            video("Python Virtual Environments: Full Tutorial for Beginners (Tech With Tim)", "https://www.youtube.com/watch?v=Y21OR1OPC9A"),
        ),
    ),
    Topic(
        "python_standard_library", "The Standard Library",
        "Batteries included: everyday modules such as math, random, datetime, collections "
        "(Counter, defaultdict), pathlib, os and sys, and checking what Python already offers "
        "before installing a package.",
        2,
        (
            docs("Python tutorial: Brief tour of the standard library", "https://docs.python.org/3/tutorial/stdlib.html"),
            docs("Python docs: collections", "https://docs.python.org/3/library/collections.html"),
            docs("Python docs: datetime", "https://docs.python.org/3/library/datetime.html"),
        ),
    ),
    Topic(
        "python_files", "Files, JSON & CSV",
        "Reading and writing files with open() inside a with block, file modes, building paths with "
        "pathlib, and loading and saving data with the json and csv modules.",
        2,
        (
            video("Python Tutorial: File Objects (Corey Schafer)", "https://www.youtube.com/watch?v=Uh2ebFW8OYM"),
            docs("Python docs: json", "https://docs.python.org/3/library/json.html"),
            docs("Python docs: csv", "https://docs.python.org/3/library/csv.html"),
        ),
    ),
    Topic(
        "python_exceptions", "Errors & Exceptions",
        "Reading tracebacks, handling exceptions with try, except, else and finally, catching "
        "specific exception types, raising errors with raise, and defining your own exception "
        "classes.",
        2,
        (
            docs("Python tutorial: Errors and exceptions", "https://docs.python.org/3/tutorial/errors.html"),
            docs("Python docs: Built-in exceptions", "https://docs.python.org/3/builtins/exceptions.html"),
        ),
    ),
    Topic(
        "python_type_hints", "Type Hints",
        "Annotating variables, parameters and return values (int, list[str], dict[str, int], "
        "str | None), what hints do and do not do when a program runs, and checking them with a tool "
        "such as mypy.",
        2,
        (
            docs("mypy: Getting started", "https://mypy.readthedocs.io/en/stable/getting_started.html"),
            docs("mypy: Type hints cheat sheet", "https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html"),
        ),
    ),
    # --- Objects and advanced functions -----------------------------------------------------
    Topic(
        "python_oop", "Classes & Objects",
        "Defining classes with __init__ and methods, what self refers to, instance versus class "
        "attributes, special methods such as __repr__ and __eq__, and properties.",
        3,
        (
            docs("Python tutorial: Classes", "https://docs.python.org/3/tutorial/classes.html"),
            video("Python OOP Tutorial 1: Classes and Instances (Corey Schafer)", "https://www.youtube.com/watch?v=ZDa-Z5JzLYM"),
            video("Python OOP Tutorial 6: Property Decorators (Corey Schafer)", "https://www.youtube.com/watch?v=jCzT9XFZ5bw"),
        ),
    ),
    Topic(
        "python_inheritance", "Inheritance & Composition",
        "Building on existing classes: subclasses, overriding methods, calling the parent with "
        "super(), isinstance(), abstract base classes, and when to prefer composition (one object "
        "holding another) over inheritance.",
        3,
        (
            video("Python OOP Tutorial 4: Inheritance (Corey Schafer)", "https://www.youtube.com/watch?v=RSl87lqOXDE"),
            docs("Python docs: abc (abstract base classes)", "https://docs.python.org/3/library/abc.html"),
        ),
    ),
    Topic(
        "python_iterators_generators", "Iterators & Generators",
        "How for loops work underneath: iterables and iterators, iter() and next(), generator "
        "functions that yield values on demand, and building blocks from itertools.",
        3,
        (
            docs("Python docs: Functional programming HOWTO", "https://docs.python.org/3/howto/functional.html"),
            video("Python Tutorial: Generators (Corey Schafer)", "https://www.youtube.com/watch?v=bD05uGo_sVI"),
            video("Python Tutorial: Itertools Module (Corey Schafer)", "https://www.youtube.com/watch?v=Qu3dThVy6KQ"),
        ),
    ),
    Topic(
        "python_decorators", "Decorators & Closures",
        "Functions as values, inner functions that remember variables from the enclosing function "
        "(closures), nonlocal, and decorators: the @ syntax for wrapping a function to add "
        "behaviour, with functools.wraps to keep its name.",
        3,
        (
            video("Programming Terms: Closures (Corey Schafer)", "https://www.youtube.com/watch?v=swU3c34d2NQ"),
            video("Python Tutorial: Decorators (Corey Schafer)", "https://www.youtube.com/watch?v=FsAPt_9Bf3U"),
            docs("Python docs: functools", "https://docs.python.org/3/library/functools.html"),
        ),
    ),
    # --- Working code -------------------------------------------------------------------------
    Topic(
        "python_testing", "Testing with pytest",
        "Writing automated tests with pytest: the test files and functions it discovers, plain "
        "assert statements, checking errors with pytest.raises, fixtures for shared setup, and "
        "parametrize for many cases.",
        3,
        (
            docs("pytest: Get started", "https://docs.pytest.org/en/stable/getting-started.html"),
            docs("pytest: How to use fixtures", "https://docs.pytest.org/en/stable/how-to/fixtures.html"),
        ),
    ),
    Topic(
        "python_http_requests", "Calling Web APIs",
        "Talking to web APIs from Python with the requests library: GET and POST, query parameters "
        "and headers, reading JSON responses, checking status codes, and always setting a timeout.",
        3,
        (
            docs("Requests: Quickstart", "https://requests.readthedocs.io/en/latest/user/quickstart/"),
            video("Python Requests Tutorial (Corey Schafer)", "https://www.youtube.com/watch?v=tb8gHvYlCFs"),
        ),
    ),
    Topic(
        "python_async", "Async Python",
        "Concurrency with asyncio: coroutines defined with async def, await, the event loop, running "
        "tasks together with asyncio.gather or a TaskGroup, and why async helps with waiting on I/O "
        "but not with heavy computation.",
        4,
        (
            docs("Python docs: Coroutines and tasks", "https://docs.python.org/3/library/asyncio-task.html"),
            video("Next-Level Concurrent Programming in Python with Asyncio (ArjanCodes)", "https://www.youtube.com/watch?v=GpqAQxH1Afc"),
        ),
    ),
)

PREREQUISITES: tuple[tuple[str, str], ...] = (
    ("python_basics", "python_control_flow"),
    ("python_basics", "python_strings"),
    ("python_control_flow", "python_functions"),
    ("python_control_flow", "python_lists_tuples"),
    ("python_lists_tuples", "python_dicts_sets"),
    ("python_dicts_sets", "python_comprehensions"),

    ("python_functions", "python_modules"),
    ("python_modules", "python_virtual_environments"),
    ("command_line_basics", "python_virtual_environments"),
    ("python_modules", "python_standard_library"),
    ("python_strings", "python_files"),
    ("python_dicts_sets", "python_files"),
    ("data_formats", "python_files"),
    ("python_functions", "python_exceptions"),
    ("python_functions", "python_type_hints"),
    ("python_dicts_sets", "python_type_hints"),

    ("python_functions", "python_oop"),
    ("python_oop", "python_inheritance"),
    ("python_comprehensions", "python_iterators_generators"),
    ("python_oop", "python_iterators_generators"),
    ("python_functions", "python_decorators"),

    ("python_exceptions", "python_testing"),
    ("python_virtual_environments", "python_testing"),
    ("python_files", "python_http_requests"),
    ("python_virtual_environments", "python_http_requests"),
    ("how_the_internet_works", "python_http_requests"),
    ("python_exceptions", "python_async"),
    ("python_iterators_generators", "python_async"),
)

PYTHON = Domain(
    id="python",
    name="Python",
    description=(
        "Programming in Python from a first script: data structures, functions and classes, files "
        "and packages, testing, then async code and web APIs. The base for data science, AI and "
        "automation."
    ),
    topics=TOPICS,
    prerequisites=PREREQUISITES,
)
