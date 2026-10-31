"""Curated fallback questions for Computer Science Core. Code is Markdown; maths is LaTeX between \\( and \\)."""

from seed.questions import Bank, q

QUESTIONS: Bank = {
    # --- Algorithms and data structures -----------------------------------------------------
    "cs_complexity": [
        q("An algorithm loops over a list of n items and, for each item, loops over the whole list again. What "
          "is its time complexity?", "\\( O(n^2) \\)", ("\\( O(n) \\)", "\\( O(2n) \\)", "\\( O(\\log n) \\)"),
          "The inner loop runs n times for each of the n outer steps: \\( n \\times n = n^2 \\) steps."),
        q("Which grows fastest as n gets large?", "\\( O(2^n) \\)",
          ("\\( O(n^2) \\)", "\\( O(n \\log n) \\)", "\\( O(n^{10}) \\)"),
          "Exponential growth eventually overtakes any polynomial, however large its power."),
        q("Why is \\( O(2n) \\) written as \\( O(n) \\)?", "Big-O ignores constant factors and keeps the growth rate",
          ("Because 2n and n are always equal for whole numbers", "Because the 2 is moved into the input size n",
           "Because Big-O only counts loops, not steps"),
          "Doubling the work doesn't change how it grows: both grow linearly with n."),
    ],
    "cs_arrays_linked_lists": [
        q("Why is reading item k of an array \\( O(1) \\)?", "Its address can be calculated directly from k",
          ("The array is searched from both ends at once", "Arrays are always sorted, so k is found quickly",
           "Arrays keep a separate list of every item's name"),
          "Items sit next to each other in memory, so item k is at start + k × item size: one calculation, "
          "whatever the length."),
        q("You already hold a reference to a node in a singly linked list. How long does inserting a new node "
          "right after it take?", "\\( O(1) \\)", ("\\( O(n) \\)", "\\( O(\\log n) \\)", "\\( O(n^2) \\)"),
          "Only two links change. Finding the node in the first place would take \\( O(n) \\)."),
        q("A dynamic array, such as a Python list, doubles its capacity when full. What is the average cost of "
          "appending?", "\\( O(1) \\) on average (amortised)",
          ("\\( O(n) \\) every time", "\\( O(\\log n) \\) on average", "\\( O(n^2) \\) once it is full"),
          "Copying everything happens rarely, and doubling spreads that cost over many cheap appends."),
    ],
    "cs_stacks_queues": [
        q("Push 1, push 2 and push 3 onto a stack, then pop twice. What is left on the stack?", "1",
          ("3", "2", "1 and 2"),
          "A stack is last in, first out: the pops remove 3 and then 2."),
        q("Which structure suits a printer's jobs, handled in the order they arrive?", "A queue (first in, first out)",
          ("A stack (last in, first out)", "A binary search tree", "A hash table"),
          "A queue serves items in arrival order, which is fair for jobs waiting their turn."),
        q("Why can very deep recursion crash a program with a stack overflow?",
          "Each unfinished call keeps a frame on the call stack, which has a limit",
          ("Each recursive call copies the whole program into memory again",
           "The queue of pending calls fills up the computer's hard disk",
           "Recursive calls run on the graphics card, which has less memory"),
          "Every call waits on the call stack until it returns, so millions of nested calls exhaust the space "
          "(Python raises RecursionError first)."),
    ],
    "cs_hash_tables": [
        q("What is the average time to look up a key in a well-sized hash table?", "\\( O(1) \\)",
          ("\\( O(n) \\)", "\\( O(\\log n) \\)", "\\( O(n \\log n) \\)"),
          "The hash points straight at a bucket holding only a few keys. Python dictionaries and sets work "
          "this way."),
        q("Two different keys hash to the same bucket. What is this called?", "A collision",
          ("An overflow", "A rehash", "A deadlock"),
          "Collisions are expected; chaining or probing stores both keys and tells them apart."),
        q("Why do hash tables resize when the load factor gets too high?",
          "Too many keys per bucket make lookups slow down",
          ("Hash functions stop working once the table is half full", "Resizing sorts the keys so they print in order",
           "The table runs out of possible hash values"),
          "The load factor is keys per bucket. More buckets keep chains short, so lookups stay close to "
          "constant time."),
    ],
    "cs_recursion": [
        q("What happens if a recursive function never reaches a base case?",
          "It keeps calling itself until the stack overflows",
          ("It returns None after the first call", "Python turns it into a loop automatically",
           "It runs once and then stops by itself"),
          "The base case is what stops the recursion. Without it, calls pile up until the call stack runs out."),
        q("What does this print?\n\n```python\ndef f(n):\n    if n == 0:\n        return 0\n    return n + f(n - 1)\n\n"
          "print(f(4))\n```", "`10`", ("`4`", "`24`", "`0`"),
          "f(4) = 4 + f(3) = 4 + 3 + 2 + 1 + 0 = 10. 24 would be 4 factorial."),
        q("Merge sort splits a list in half, sorts each half recursively and merges the results. What is this "
          "strategy called?", "Divide and conquer",
          ("Dynamic programming", "Greedy choice", "Backtracking"),
          "Divide and conquer splits a problem into independent smaller ones and combines their answers."),
    ],
    "cs_sorting": [
        q("What is the worst-case time of merge sort?", "\\( O(n \\log n) \\)",
          ("\\( O(n^2) \\)", "\\( O(n) \\)", "\\( O(\\log n) \\)"),
          "It always halves the list (about \\( \\log n \\) levels) and merges n items at each level."),
        q("Quicksort always picks the first element as its pivot. On which input does it hit its worst case?",
          "A list that is already sorted",
          ("A list of random numbers", "A list with all different values", "A list of exactly two items"),
          "On sorted input every split leaves one side empty, giving \\( O(n^2) \\). Random or median-of-three "
          "pivots avoid this."),
        q("A stable sort orders people by age. What does stable mean?",
          "People with equal ages keep their original order",
          ("The sort never uses more memory than the list", "The sort takes the same time on every input",
           "The sort can't crash on a list of any size"),
          "Stability lets you sort by one key and then another; Python's sorted is stable."),
    ],
    "cs_trees": [
        q("In a binary search tree, where are values smaller than a node stored?", "In its left subtree",
          ("In its right subtree", "In its parent", "In a separate list"),
          "Every value in the left subtree is smaller and every value in the right subtree larger, which "
          "makes searching a matter of going left or right."),
        q("What does an in-order traversal of a binary search tree produce?", "The values in sorted order",
          ("The values level by level", "The root's value first, then the leaves",
           "The values in the order they were inserted"),
          "In-order visits the left subtree, then the node, then the right subtree, which for a BST is "
          "ascending order."),
        q("The values 1, 2, 3, 4 and 5 are inserted in that order into a plain binary search tree. What results?",
          "A chain where lookups take \\( O(n) \\)",
          ("A balanced tree where lookups take \\( O(\\log n) \\)", "A tree with all five values in the root",
           "An error, because sorted input isn't allowed"),
          "Each value is larger than the last, so each becomes a right child: effectively a linked list. "
          "Self-balancing trees such as AVL trees prevent this."),
    ],
    "cs_heaps": [
        q("In a min-heap, where is the smallest value?", "At the root",
          ("In the last leaf", "In the left child of the root", "Anywhere: heaps aren't ordered"),
          "Every parent is no larger than its children, so the minimum is always at the top."),
        q("How long does removing the minimum from a binary min-heap of n items take?", "\\( O(\\log n) \\)",
          ("\\( O(1) \\)", "\\( O(n) \\)", "\\( O(n \\log n) \\)"),
          "Reading the minimum is \\( O(1) \\), but removing it means moving the last item to the root and "
          "sifting it down the tree's height."),
        q("A heap is stored in an array starting at index 0. What is the index of the left child of the node at "
          "index i?", "\\( 2i + 1 \\)", ("\\( 2i \\)", "\\( i + 1 \\)", "\\( i / 2 \\)"),
          "With 0-based indexes the children of i are at \\( 2i + 1 \\) and \\( 2i + 2 \\), so no pointers are "
          "needed."),
    ],
    "cs_graphs": [
        q("Which traversal finds the fewest edges from a start vertex to every other vertex in an unweighted "
          "graph?", "Breadth-first search", ("Depth-first search", "Sorting the vertices", "A random walk"),
          "BFS explores in rings of increasing distance, so it reaches each vertex first by a shortest path."),
        q("Breadth-first search uses which data structure to decide what to visit next?", "A queue",
          ("A stack", "A heap ordered by name", "A hash table only"),
          "A queue visits vertices in the order they were discovered. Depth-first search uses a stack (or "
          "recursion)."),
        q("A graph has 1,000 vertices but only 3,000 edges. Which representation usually uses less memory?",
          "An adjacency list", ("An adjacency matrix", "Both use exactly the same", "A list of every possible pair"),
          "A list stores only existing edges (about 3,000 entries); a matrix needs 1,000 × 1,000 cells."),
    ],
    "cs_shortest_paths": [
        q("Why does Dijkstra's algorithm use a priority queue?",
          "To pick the unvisited vertex with the smallest distance quickly",
          ("To store the edges in the order they were added", "To remember which vertices have been visited twice",
           "To sort the final path from end back to start"),
          "Each step settles the closest unsettled vertex; a heap finds it in \\( O(\\log n) \\) instead of "
          "scanning them all."),
        q("When can Dijkstra's algorithm give a wrong answer?", "When some edges have negative weights",
          ("When the graph has cycles", "When edges have different weights", "When there are more than 100 vertices"),
          "It assumes a settled distance can't improve later, which a negative edge can break. Bellman-Ford "
          "handles negative weights."),
        q("What makes A* search faster than Dijkstra's algorithm for finding a route to one goal?",
          "A heuristic estimate steers it towards the goal",
          ("It ignores the edge weights entirely", "It searches every vertex in parallel",
           "It only works on graphs without cycles"),
          "A* ranks vertices by distance so far plus an estimate of the distance left (such as straight-line "
          "distance), so it explores fewer vertices."),
    ],
    "cs_greedy": [
        q("Coins are worth 1, 3 and 4. To make 6, a greedy method always takes the largest coin that fits. What "
          "happens?", "It uses three coins (4, 1, 1) where two (3, 3) would do",
          ("It finds the best answer, two coins (3, 3)", "It can't make 6 and gives up", "It uses two coins (4, 2)"),
          "Greedy choices aren't always optimal; this coin system needs dynamic programming to find the best "
          "answer."),
        q("To choose the most activities that don't overlap, which greedy rule gives the best answer?",
          "Pick the activity that finishes earliest, then repeat",
          ("Pick the shortest activity, then repeat", "Pick the activity that starts earliest, then repeat",
           "Pick the activity with the fewest overlaps, then repeat"),
          "Finishing earliest leaves the most room for the rest, and can be proven optimal; the other rules "
          "have counter-examples."),
        q("Which classic problem does a greedy algorithm solve correctly?",
          "Finding a minimum spanning tree (Kruskal's algorithm)",
          ("The 0/1 knapsack problem", "The travelling salesperson problem", "The longest common subsequence"),
          "Kruskal's algorithm adds the cheapest edge that doesn't form a cycle, which is proven optimal. The "
          "others need other methods."),
    ],
    "cs_dynamic_programming": [
        q("Why is the naive recursive Fibonacci function slow?",
          "It recomputes the same values exponentially many times",
          ("It uses floating-point numbers that are slow to add", "Python limits recursion to ten levels",
           "It sorts the sequence before each step"),
          "fib(n) calls fib(n - 1) and fib(n - 2), which call the same smaller values again and again."),
        q("What is memoisation?", "Storing results of calls so repeated calls are instant",
          ("Writing the algorithm out in pseudocode first", "Splitting the input into two halves each time",
           "Choosing the best local option at each step"),
          "Caching each subproblem's answer (e.g. with functools.cache) makes Fibonacci \\( O(n) \\)."),
        q("Which two properties make a problem a good fit for dynamic programming?",
          "Overlapping subproblems and optimal substructure",
          ("Sorted input and a unique answer", "A graph with no cycles and positive weights",
           "Independent subproblems and a greedy choice"),
          "Subproblems must repeat (so storing them helps) and the best answer must be built from best answers "
          "to subproblems."),
    ],
    "cs_complexity_classes": [
        q("What does it mean that a problem is in NP?", "A proposed solution can be checked in polynomial time",
          ("It can't be solved by any computer program", "It needs exponential time on every input",
           "It can be solved in polynomial time with no exceptions"),
          "NP is about verifying answers quickly. Whether every such problem can also be solved quickly is the "
          "P versus NP question."),
        q("If someone found a polynomial-time algorithm for one NP-complete problem, what would follow?",
          "Every problem in NP could be solved in polynomial time",
          ("Only that one problem would become easy", "NP-complete problems would no longer be in NP",
           "Every problem would become solvable by computers"),
          "Every NP problem can be converted into any NP-complete one, so solving one quickly would show that "
          "P = NP. Undecidable problems would stay unsolvable."),
        q("A delivery firm must plan a route through 500 stops, a travelling-salesperson problem. What is the "
          "practical approach?", "Use a heuristic that finds a good route, not a proven best",
          ("Try every possible route to guarantee the best one", "Wait until P versus NP is solved",
           "Sort the stops alphabetically and visit them in order"),
          "Checking every route is hopeless (about 500! orders); heuristics and approximation algorithms give "
          "good routes fast."),
    ],
    # --- Systems ----------------------------------------------------------------------------------
    "cs_computer_architecture": [
        q("Why does a CPU have caches?", "Main memory is far slower than the CPU, so recent data is kept close",
          ("Caches store files permanently when the power is off", "Caches let the CPU run programs without any memory",
           "Caches hold a backup copy in case main memory fails"),
          "Reading RAM takes many CPU cycles; small, fast caches keep recently used data and its neighbours "
          "near the cores."),
        q("Which of these is fastest for the CPU to access?", "A CPU register",
          ("Main memory (RAM)", "An SSD", "A network drive"),
          "The memory hierarchy runs from registers and caches (fastest, smallest) to RAM, then disks, then the "
          "network."),
        q("Why does looping over an array in order usually run faster than jumping around it at random?",
          "Neighbouring items arrive in the cache together",
          ("The CPU can only read memory addresses in order", "Random access needs the operating system's permission",
           "Arrays are copied to disk when accessed randomly"),
          "Memory is loaded in cache lines, so reading in order uses each loaded line fully; random jumps keep "
          "missing the cache."),
    ],
    "cs_processes_threads": [
        q("What is the key difference between two processes and two threads of one process?",
          "Threads share one process's memory; processes each have their own",
          ("Processes share memory; threads each get their own separate copy",
           "Threads can only run on computers with a single CPU core",
           "Processes are a Windows feature; threads are a Linux feature"),
          "Sharing memory makes threads cheap to communicate with, and also why they need locks. Processes are "
          "isolated by the operating system."),
        q("What is a context switch?", "Saving one task's state and loading another's to run it",
          ("Moving a program from one computer to another", "Switching the keyboard between open windows",
           "Changing a variable's type while the program runs"),
          "The OS saves registers and other state of the running thread and restores another's, which takes a "
          "little time each switch."),
        q("Why does the scheduler give each process short time slices?",
          "So many programs appear to run at once and stay responsive",
          ("So the CPU can rest between slices and stay cool", "So each program finishes in exactly the same time",
           "So programs can't use more than one slice of memory"),
          "Switching every few milliseconds shares the CPU fairly, so no single program can hold it for long."),
    ],
    "cs_memory_management": [
        q("In a language such as C, where are a function's local variables usually stored?", "On the stack",
          ("On the heap, always", "In the CPU's cache only", "On the disk"),
          "Each call gets a stack frame for its locals, freed automatically when it returns. Heap memory "
          "outlives the call and must be managed."),
        q("What does a garbage collector do?", "Frees memory that the program can no longer reach",
          ("Deletes temporary files from the disk", "Removes unused variables from the source code",
           "Compresses memory so programs use less of it"),
          "Languages such as Python and Java reclaim objects nothing refers to any more, so programmers don't "
          "free memory by hand."),
        q("What does virtual memory give each process?", "Its own address space, mapped to physical memory by the OS",
          ("A copy of every other process's memory to read", "Unlimited memory that never needs the disk",
           "Direct access to the physical memory chips"),
          "Each process sees its own addresses; the OS and hardware translate them, keeping processes apart and "
          "letting pages move to disk when RAM is short."),
    ],
    "cs_concurrency": [
        q("Two threads each run `count += 1` 1,000 times on a shared counter with no lock. Why can the result be "
          "less than 2,000?", "The read-add-write steps can interleave, losing updates",
          ("Threads can't run at the same time on one CPU", "Each thread gets its own copy of the counter",
           "Integers can't be changed by more than one thread"),
          "Both threads can read the same value and write back the same result: a race condition. A lock makes "
          "the update atomic."),
        q("Which of these is one of the conditions that must all hold for a deadlock?",
          "Circular wait: each thread waits for a lock the next one holds",
          ("Every thread runs on its own separate CPU core", "The program uses more threads than it has locks",
           "Locks are released as soon as they are acquired"),
          "Deadlock needs mutual exclusion, hold and wait, no pre-emption and circular wait; breaking any one "
          "prevents it."),
        q("How does always acquiring locks in one fixed global order help?",
          "It rules out circular wait, so deadlock can't happen",
          ("It makes every lock faster to acquire", "It lets two threads hold the same lock at once",
           "It removes the need for locks altogether"),
          "If every thread takes lock A before lock B, no thread can hold B while waiting for A."),
    ],
    "cs_networking": [
        q("Which is true of TCP compared with UDP?", "TCP delivers bytes reliably and in order; UDP doesn't",
          ("UDP delivers reliably and in order; TCP doesn't", "TCP is only for web pages; UDP for everything else",
           "Both guarantee delivery; UDP is just newer"),
          "TCP retransmits and reorders, at some cost in delay; UDP sends independent datagrams, which suits "
          "video calls and games."),
        q("What does a port number identify?", "Which program on a computer the data is for",
          ("Which computer on the internet to send it to", "Which cable the data travels along",
           "The order of packets in a message"),
          "The IP address finds the machine and the port finds the program, such as 443 for HTTPS."),
        q("What does TLS add to a TCP connection?", "Encryption and proof of the server's identity",
          ("Faster delivery by skipping lost packets", "A shorter address for the server",
           "Compression of images before sending"),
          "TLS encrypts the data and uses certificates to show you are talking to the real server; it is the "
          "S in HTTPS."),
    ],
    "cs_compilers_interpreters": [
        q("What does a compiler do?", "Translates a whole program into another form before it runs",
          ("Runs each line of source code as soon as it is read", "Checks a program for bugs and fixes them automatically",
           "Stores the program's output in a log file"),
          "A compiler produces machine code or bytecode ahead of time; an interpreter executes the program "
          "directly."),
        q("What does CPython do with a .py file before running it?",
          "Compiles it to bytecode, which its virtual machine runs",
          ("Compiles it straight to machine code for the CPU", "Converts it to C source code and compiles that",
           "Runs the text line by line with no other step"),
          "CPython compiles source to bytecode (cached in __pycache__) and its interpreter loop executes it."),
        q("What is usually the first stage of a compiler or interpreter?", "Lexing: breaking the text into tokens",
          ("Optimising the machine code", "Linking libraries together", "Running the program's tests"),
          "The lexer turns characters into tokens such as names, numbers and symbols; the parser then builds a "
          "syntax tree from them."),
    ],
}
