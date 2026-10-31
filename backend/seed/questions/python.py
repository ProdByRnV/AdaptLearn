"""Curated fallback questions for Python. Code is written as Markdown (`inline` or a fenced block)."""

from seed.questions import Bank, q

QUESTIONS: Bank = {
    # --- The language -------------------------------------------------------------------
    "python_basics": [
        q("What does `7 // 2` evaluate to in Python?", "`3`", ("`3.5`", "`4`", "`1`"),
          "`//` is floor division: it divides and rounds down to a whole number, so 7 // 2 is 3. `/` always "
          "gives a float (3.5) and `%` gives the remainder (1)."),
        q("What type does `input()` return, even when the user types 42?", "`str`", ("`int`", "`float`", "`bool`"),
          "input() always returns the text that was typed. Convert it yourself, e.g. `int(input())`, when you "
          "need a number."),
        q('What does `print("3" + "4")` show?', "`34`", ("`7`", "`3 4`", "An error: strings can't be added"),
          "`+` on two strings joins them, so the result is the string 34. Use `int()` on each to add them as "
          "numbers."),
    ],
    "python_control_flow": [
        q("Which numbers does `for i in range(2, 6): print(i)` print?", "2, 3, 4, 5",
          ("2, 3, 4, 5, 6", "3, 4, 5", "2 and 6 only"),
          "range(start, stop) starts at start and stops before stop, so range(2, 6) gives 2, 3, 4 and 5."),
        q("What does `break` do inside a loop?", "Ends the loop straight away",
          ("Skips to the next iteration", "Pauses the loop until Enter is pressed", "Ends the whole program"),
          "break leaves the innermost loop immediately. continue is the one that skips the rest of the current "
          "iteration and moves on to the next."),
        q('What does this print?\n\n```python\nx = 0\nif x:\n    print("yes")\nelse:\n    print("no")\n```',
          "`no`", ("`yes`", "Nothing", "An error: x is not a bool"),
          "An if statement tests truthiness. 0, empty strings and empty collections, and None are falsy, so "
          "the else branch runs."),
    ],
    "python_strings": [
        q('Given `s = "python"`, what is `s[1:4]`?', '`"yth"`', ('`"pyt"`', '`"ytho"`', '`"pyth"`'),
          "Indexes start at 0 and a slice stops before its end index, so s[1:4] takes the characters at 1, 2 "
          "and 3: y, t and h."),
        q('What does `"a,b,,c".split(",")` return?', "`['a', 'b', '', 'c']`",
          ("`['a', 'b', 'c']`", "`['a,b,,c']`", "`['a', 'b', ',', 'c']`"),
          "With a separator given, split keeps an empty string wherever two separators are next to each "
          "other. Only split() with no argument drops empty pieces."),
        q('After `s = "cat"`, what happens when you run `s[0] = "b"`?',
          "A TypeError, because strings can't be changed",
          ('`s` becomes `"bat"`', 'A new string is returned and `s` is unchanged', '`s` becomes `"bcat"`'),
          "Strings are immutable, so assigning to an index raises TypeError. Build a new string instead, "
          'e.g. `s = "b" + s[1:]`.'),
    ],
    "python_functions": [
        q("What does a Python function return if it ends without a `return` statement?", "`None`",
          ("`0`", "An empty string", "The value of its last line"),
          "A function with no return statement, or a bare `return`, gives back None."),
        q("What does this print?\n\n```python\ndef add(item, items=[]):\n    items.append(item)\n    return items\n\n"
          "add(1)\nprint(add(2))\n```",
          "`[1, 2]`", ("`[2]`", "`[1]`", "An error: items is not defined"),
          "A default value is created once, when the def runs, so every call without items shares the same "
          "list. Use `items=None` and create a new list inside the function instead."),
        q('Given `def greet(name, greeting="Hello"):`, which call is an error?', '`greet(greeting="Hi", "Ada")`',
          ('`greet("Ada")`', '`greet("Ada", "Hi")`', '`greet(greeting="Hi", name="Ada")`'),
          "Positional arguments must come before keyword arguments, so that call is a SyntaxError. The others "
          "are valid: keyword arguments can be in any order."),
    ],
    # --- Data structures ------------------------------------------------------------------
    "python_lists_tuples": [
        q("What does this print?\n\n```python\na = [1, 2, 3]\nb = a\nb.append(4)\nprint(a)\n```",
          "`[1, 2, 3, 4]`", ("`[1, 2, 3]`", "`[4]`", "`[1, 2, 3, [4]]`"),
          "b = a doesn't copy the list: both names refer to the same list, so a change through b shows "
          "through a. Use `a.copy()` or `list(a)` for a separate copy."),
        q("What is the difference between `sorted(nums)` and `nums.sort()`?",
          "sorted() returns a new list; .sort() sorts nums in place",
          ("sorted() sorts in place; .sort() returns a new list",
           "sorted() only works on numbers; .sort() on any list",
           "None: one is just an older name for the other"),
          "sorted() works on any iterable and returns a new sorted list. list.sort() changes the list itself "
          "and returns None."),
        q("What does `x, y = (10, 20)` do?", "Sets x to 10 and y to 20",
          ("Sets both x and y to (10, 20)", "Sets x to (10, 20) and y to None", "Raises an error: tuples can't be unpacked"),
          "Unpacking assigns each item of the tuple to the matching name on the left. The counts must match."),
    ],
    "python_dicts_sets": [
        q('What does `d.get("missing", 0)` return when `d` has no key `"missing"`?', "`0`",
          ("`None`", "It raises a KeyError", '`"missing"`'),
          "get returns the default you pass when the key is absent (None if you pass none). Only `d[\"missing\"]` "
          "raises KeyError."),
        q("What is `len({1, 2, 2, 3, 3, 3})`?", "`3`", ("`6`", "`4`", "`1`"),
          "A set keeps one copy of each value, so the set is {1, 2, 3}, which has 3 items."),
        q("Which of these can be used as a dictionary key?", "`(1, 2)`", ("`[1, 2]`", "`{1, 2}`", '`{"a": 1}`'),
          "Keys must be hashable. Tuples of hashable values are, but lists, sets and dictionaries can change, "
          "so they are not hashable and raise TypeError as keys."),
    ],
    "python_comprehensions": [
        q("What is `[n * n for n in range(5) if n % 2 == 0]`?", "`[0, 4, 16]`",
          ("`[0, 1, 4, 9, 16]`", "`[4, 16]`", "`[1, 9]`"),
          "range(5) gives 0 to 4; the if keeps the even ones (0, 2 and 4), and each is squared."),
        q('What does `{w: len(w) for w in ["hi", "hey"]}` produce?', "`{'hi': 2, 'hey': 3}`",
          ("`[2, 3]`", "`{2: 'hi', 3: 'hey'}`", "`{'hi', 'hey'}`"),
          "A dictionary comprehension builds key: value pairs; here each word maps to its length."),
        q("Why write `sum(x * x for x in nums)` rather than `sum([x * x for x in nums])`?",
          "It doesn't build the whole list in memory first",
          ("It gives a more precise result for floats", "The list version raises an error with sum()",
           "A generator expression can be reused many times"),
          "A generator expression hands sum one value at a time instead of building a list first. The result "
          "is the same; a generator can only be used once."),
    ],
    # --- Programs and projects --------------------------------------------------------------
    "python_modules": [
        q("What is the value of `__name__` in a file run directly with `python app.py`?", '`"__main__"`',
          ('`"app"`', '`"app.py"`', "`None`"),
          'The file run as the program is named "__main__". When the same file is imported, __name__ is its '
          "module name (app), which is what the `if __name__ == \"__main__\":` check relies on."),
        q("After `import math`, how do you call its square root function?", "`math.sqrt(16)`",
          ("`sqrt(16)`", "`math->sqrt(16)`", "`import.sqrt(16)`"),
          "import math binds the module to the name math, and its functions are reached with a dot. "
          "`from math import sqrt` would let you write sqrt(16)."),
        q("Why is `from module import *` discouraged?",
          "It hides where names come from and can overwrite existing ones",
          ("It imports the module twice and slows start-up", "It only works for modules in the standard library",
           "It makes the imported functions read-only"),
          "Star imports pull in many names at once, so readers can't tell where a name was defined and one "
          "module's name can silently replace another's."),
    ],
    "python_virtual_environments": [
        q("Why give each project its own virtual environment?", "So each project can have its own package versions",
          ("So Python code runs faster inside it", "To keep the project's source code private",
           "So the project can run without Python installed"),
          "Packages installed into a virtual environment don't affect other projects or the system Python, so "
          "two projects can depend on different versions of the same package."),
        q("Which command creates a virtual environment in a folder named `.venv`?", "`python -m venv .venv`",
          ("`pip install venv .venv`", "`python venv create .venv`", "`pip freeze > .venv`"),
          "The venv module in the standard library creates environments: python -m venv followed by the "
          "folder. You then activate it before installing packages."),
        q("What does `pip freeze > requirements.txt` do?",
          "Saves the installed packages and their exact versions to a file",
          ("Locks the environment so no new packages can be installed", "Installs every package listed in the file",
           "Deletes packages that are not listed in the file"),
          "pip freeze lists installed packages as name==version, and > writes that list to the file. "
          "`pip install -r requirements.txt` installs them elsewhere."),
    ],
    "python_standard_library": [
        q('What does `Counter("banana").most_common(1)` return?', "`[('a', 3)]`",
          ("`('a', 3)`", "`[('b', 1)]`", "`{'a': 3}`"),
          "Counter counts each item; most_common(n) returns a list of the n most common (item, count) pairs. "
          "a appears 3 times in banana."),
        q("What does a `defaultdict(list)` do when you read a key it doesn't have yet?",
          "Adds the key with an empty list and returns it",
          ("Raises a KeyError like a normal dict", "Returns None without adding the key",
           "Returns a list of every existing key"),
          "defaultdict calls its factory (here list) to create a value for a missing key, so "
          "`d[k].append(x)` works without checking first."),
        q("Which call gives a random whole number from 1 to 6, including both ends?", "`random.randint(1, 6)`",
          ("`random.randrange(1, 6)`", "`random.random(1, 6)`", "`random.choice(1, 6)`"),
          "randint includes both ends. randrange(1, 6) stops before 6, random() takes no arguments and "
          "returns a float, and choice takes one sequence."),
    ],
    "python_files": [
        q("Why open files in a `with` block, as in `with open(path) as f:`?",
          "The file is closed automatically, even if an error occurs",
          ("It opens the file faster than calling open() alone", "It stops other programs from reading the file",
           "It reads the whole file into memory at once"),
          "The with statement closes the file when the block ends, whether it finishes normally or with an "
          "exception, so files aren't left open."),
        q('What does `open("notes.txt", "w")` do if notes.txt already exists?',
          "Empties it, so writing replaces the old contents",
          ("Adds new writes to the end of the existing contents", "Raises an error because the file exists",
           "Opens it read-only"),
          'Mode "w" truncates an existing file. "a" appends to the end, and "x" raises FileExistsError if the '
          "file is already there."),
        q("Which function turns a Python dictionary into a JSON string?", "`json.dumps()`",
          ("`json.loads()`", "`json.load()`", "`str()`"),
          "dumps (dump string) serialises to a JSON string; loads and load go the other way, from a string "
          "and a file. str() gives Python's own notation, with single quotes, which isn't JSON."),
    ],
    "python_exceptions": [
        q("In try / except / else / finally, when does the `else` block run?",
          "Only when the try block raised no exception",
          ("Only when an exception was caught", "Every time, after the finally block",
           "Only when an exception was not caught"),
          "else runs after try succeeds without an exception; finally runs in every case, and runs last."),
        q('What does `int("abc")` raise?', "`ValueError`", ("`TypeError`", "`SyntaxError`", "`KeyError`"),
          "int accepts a string, so the type is fine, but this string's value isn't a number, which is a "
          "ValueError."),
        q("Why is a bare `except:` (catching everything) usually a bad idea?",
          "It also hides bugs and catches Ctrl+C (KeyboardInterrupt)",
          ("It makes the program run noticeably slower", "It only catches errors from the standard library",
           "It can only be used once in each program"),
          "A bare except catches every exception, including typos such as NameError and the KeyboardInterrupt "
          "from Ctrl+C. Catch the specific exceptions you expect instead."),
    ],
    "python_type_hints": [
        q('What does this print?\n\n```python\ndef double(n: int) -> int:\n    return n * 2\n\nprint(double("hi"))\n```',
          "`hihi`", ('A TypeError, because "hi" is not an int', "`4`", "`None`"),
          "Python doesn't enforce type hints when the program runs. A type checker such as mypy would report "
          "the call, but Python simply runs \"hi\" * 2."),
        q("Which annotation means a string or None?", "`str | None`", ("`str & None`", "`[str, None]`", "`str?`"),
          "The | operator builds a union of types (Python 3.10 and later); `Optional[str]` from typing means "
          "the same."),
        q("Which annotation describes a list of integers?", "`list[int]`", ("`list(int)`", "`int[]`", "`list<int>`"),
          "Built-in collections take their item types in square brackets, e.g. list[int] and dict[str, int]."),
    ],
    # --- Objects and advanced functions -----------------------------------------------------
    "python_oop": [
        q("In a method `def area(self):`, what is `self`?", "The object the method was called on",
          ("The class the method is defined in", "A keyword that Python reserves for methods",
           "A copy of the object made for the call"),
          "Calling `box.area()` passes box as the first argument, which by convention is named self. It is "
          "the object itself, not a copy, and self isn't a keyword."),
        q('What does this print?\n\n```python\nclass Dog:\n    tricks = []\n\n    def add(self, trick):\n'
          '        self.tricks.append(trick)\n\na, b = Dog(), Dog()\na.add("sit")\nprint(b.tricks)\n```',
          "`['sit']`", ("`[]`", "An AttributeError", "`None`"),
          "tricks is a class attribute, so every Dog shares one list. Create per-object data in __init__ "
          "(`self.tricks = []`)."),
        q("Which special method gives the text the interactive prompt shows when you evaluate an object?",
          "`__repr__`", ("`__init__`", "`__str__`", "`__show__`"),
          "The prompt displays repr(obj), which calls __repr__. print() and str() use __str__, falling back "
          "to __repr__ when it isn't defined."),
    ],
    "python_inheritance": [
        q("What does `super().__init__(name)` do inside a subclass's `__init__`?",
          "Runs the parent class's __init__ with name",
          ("Creates a second object of the parent class", "Replaces the subclass with its parent",
           "Calls the subclass's own __init__ again"),
          "super() gives access to the parent class's methods for the same object, so the parent can set up "
          "its part of the object."),
        q("`Animal` defines `speak()`, and its subclass `Cat` defines `speak()` too. Which runs for `Cat().speak()`?",
          "Cat's speak()", ("Animal's speak()", "Both, Animal's first", "Neither: Python raises an error"),
          "A method defined in the subclass overrides the parent's. Cat's version can still call the parent's "
          "with super().speak()."),
        q("When is composition usually a better fit than inheritance?",
          "When an object has another (a car has an engine)",
          ("When an object is a kind of another (a car is a vehicle)", "When the classes must share every method",
           "Whenever the classes live in different files"),
          "Inheritance models is-a relationships; composition, where one object holds another, models has-a "
          "relationships and keeps classes loosely coupled."),
    ],
    "python_iterators_generators": [
        q("What does calling a generator function (one that contains `yield`) return?",
          "A generator object; none of its code has run yet",
          ("The first value it yields", "A list of every value it yields", "None, once the function finishes"),
          "The body only starts running when you ask the generator for a value, e.g. with next() or a for loop."),
        q("What does this print?\n\n```python\ndef count():\n    yield 1\n    yield 2\n\ng = count()\n"
          "print(list(g), list(g))\n```",
          "`[1, 2] []`", ("`[1, 2] [1, 2]`", "`[1] [2]`", "An error: g was already used"),
          "A generator can be consumed only once. The first list() takes every value; the second finds it "
          "exhausted and gets an empty list."),
        q("What happens when `next()` is called on an iterator that has no values left?",
          "It raises StopIteration",
          ("It returns None", "It starts again from the first value", "It returns the last value again"),
          "StopIteration signals the end; for loops catch it to know when to stop. next(it, default) returns "
          "the default instead."),
    ],
    "python_decorators": [
        q("Writing `@timer` above `def load():` is the same as which line after the definition?",
          "`load = timer(load)`", ("`load = load(timer)`", "`timer = timer(load)`", "`load = timer()`"),
          "A decorator is called with the function and its return value replaces the name, so @timer means "
          "load = timer(load)."),
        q("Why use `functools.wraps` inside a decorator?",
          "So the wrapper keeps the original function's name and docstring",
          ("So the wrapped function runs faster when called", "So the decorator can only be applied once",
           "So the function's arguments are type-checked"),
          "Without it, the decorated function reports the wrapper's name and docstring, which confuses "
          "debugging and documentation tools."),
        q("What does this print?\n\n```python\ndef make_counter():\n    count = 0\n\n    def step():\n"
          "        nonlocal count\n        count += 1\n        return count\n\n    return step\n\n"
          "c = make_counter()\nc()\nprint(c())\n```",
          "`2`", ("`1`", "`0`", "An UnboundLocalError"),
          "step is a closure: it keeps the count variable from make_counter alive between calls, and nonlocal "
          "lets it change that variable. The second call returns 2."),
    ],
    # --- Working code -------------------------------------------------------------------------
    "python_testing": [
        q("By default, which tests does pytest collect?",
          "test_*.py or *_test.py files and functions named test...",
          ("Functions whose docstring contains the word test", "Only the functions listed in a pytest.ini file",
           "Every function in every Python file of the project"),
          "pytest looks for files named test_*.py or *_test.py and runs the functions in them whose names "
          "start with test (and test methods in classes named Test...)."),
        q('Which test checks that `int("x")` raises ValueError?', '`with pytest.raises(ValueError): int("x")`',
          ('`assert int("x") == ValueError`', '`assert raises(int("x"))`', '`pytest.expect(ValueError, int("x"))`'),
          "pytest.raises passes only if the code inside the with block raises that exception. None of the "
          "other lines catch the ValueError (and pytest has no raises or expect function to call that way), "
          "so each test would fail with an error."),
        q("What is a pytest fixture for?",
          "Providing shared setup, such as test data, to tests that ask for it",
          ("Marking a test that should be skipped on some operating systems",
           "Repeating one test many times to measure how long it takes",
           "Fixing failing tests by updating their expected values"),
          "A test asks for a fixture by naming it as a parameter; pytest runs the fixture and passes in what it "
          "returns, and can clean up afterwards."),
    ],
    "python_http_requests": [
        q("What does `response.raise_for_status()` do?", "Raises an error if the status is 4xx or 5xx",
          ("Prints the status code of the response", "Retries the request until it succeeds",
           "Returns True when the status is 200"),
          "requests doesn't treat 404 or 500 as errors by itself; raise_for_status raises HTTPError for them "
          "and does nothing for a successful response."),
        q("Why pass `timeout=` to `requests.get()`?",
          "Without it, a request can wait forever for a server that never replies",
          ("requests refuses to send a request that has no timeout set",
           "It makes the server answer faster by giving it a deadline",
           "It caches the response for that many seconds"),
          "requests has no timeout by default, so a server that stops responding can hang the program. A "
          "timeout makes it raise an exception instead."),
        q("How do you send the query string `?q=python&page=2` with requests?",
          '`requests.get(url, params={"q": "python", "page": 2})`',
          ('`requests.get(url, json={"q": "python", "page": 2})`',
           '`requests.get(url, headers={"q": "python", "page": 2})`',
           '`requests.get(url, data={"q": "python", "page": 2})`'),
          "params is encoded into the URL's query string. json and data put the values in the request body, "
          "and headers sends them as HTTP headers."),
    ],
    "python_async": [
        q("What does calling an `async def` function, such as `fetch()`, return without `await`?",
          "A coroutine object; its body hasn't run yet",
          ("The function's return value", "A thread that is already running", "None, after the function finishes"),
          "A coroutine runs only when it is awaited or scheduled as a task. Python warns if one is never awaited."),
        q("Two coroutines each `await asyncio.sleep(1)`. About how long does `await asyncio.gather(a(), b())` take?",
          "About 1 second", ("About 2 seconds", "Almost no time", "It never finishes"),
          "gather runs both concurrently on the event loop: while one waits, the other waits too, so the "
          "waits overlap."),
        q("For which kind of work does asyncio help most?", "Waiting on many network requests at once",
          ("Heavy number-crunching that keeps the CPU busy", "Making one calculation finish sooner",
           "Running code on several CPU cores at once"),
          "asyncio switches between tasks while they wait for I/O, on a single thread. CPU-heavy work needs "
          "processes (or other tools) to use several cores."),
    ],
}
