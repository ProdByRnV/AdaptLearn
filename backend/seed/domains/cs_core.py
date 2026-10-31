"""Computer Science Core: data structures and algorithms, and how computers, systems and networks work.

Big-O & Complexity is the starting topic. The systems topics build on Foundations (binary, operating
system basics, how the internet works, programming concepts).
"""

from seed.model import Domain, Topic, article, docs, video

TOPICS: tuple[Topic, ...] = (
    # --- Algorithms and data structures -----------------------------------------------------
    Topic(
        "cs_complexity", "Big-O & Complexity",
        "Describing how an algorithm's time and memory grow with its input: Big-O notation, common "
        "growth rates from O(1) to O(2^n), best, worst and average cases, and comparing algorithms.",
        2,
        (
            video("Big-O notation in 5 minutes (Michael Sambol)", "https://www.youtube.com/watch?v=__vX2sjlpXU"),
            article("Big-O cheat sheet", "https://www.bigocheatsheet.com/"),
            article("freeCodeCamp: What is Big O notation?", "https://www.freecodecamp.org/news/big-o-notation-why-it-matters-and-why-it-doesnt-1674cfa8a23c/"),
        ),
    ),
    Topic(
        "cs_arrays_linked_lists", "Arrays & Linked Lists",
        "Two ways to store a sequence: contiguous arrays with fast indexing, and linked lists with "
        "cheap insertion, the cost of each operation, and dynamic arrays that grow.",
        2,
        (
            article("VisuAlgo: Linked lists, stacks and queues", "https://visualgo.net/en/list"),
            article("Open Data Structures (free book)", "https://opendatastructures.org/"),
        ),
    ),
    Topic(
        "cs_stacks_queues", "Stacks & Queues",
        "Last-in-first-out stacks and first-in-first-out queues: their operations, how they are "
        "built, and where they appear, from undo history and the call stack to task queues.",
        2,
        (
            video("Data Structures Easy to Advanced Course (freeCodeCamp)", "https://www.youtube.com/watch?v=RBSGKlAvoiM"),
        ),
    ),
    Topic(
        "cs_hash_tables", "Hash Tables",
        "Constant-time lookups on average: hash functions, buckets, collisions handled by chaining or "
        "open addressing, the load factor and resizing.",
        2,
        (
            article("VisuAlgo: Hash tables", "https://visualgo.net/en/hashtable"),
        ),
    ),
    Topic(
        "cs_recursion", "Recursion",
        "Functions that call themselves: base cases and recursive cases, the call stack, divide and "
        "conquer, and when recursion runs too deep.",
        2,
        (
            article("VisuAlgo: Recursion trees", "https://visualgo.net/en/recursion"),
        ),
    ),
    Topic(
        "cs_sorting", "Sorting Algorithms",
        "Putting items in order: selection and insertion sort, merge sort and quicksort, their "
        "time complexities, stability, and why O(n log n) is the limit for comparison sorts.",
        3,
        (
            article("VisuAlgo: Sorting", "https://visualgo.net/en/sorting"),
        ),
    ),
    Topic(
        "cs_trees", "Trees & Binary Search Trees",
        "Hierarchical data: tree vocabulary, binary search trees and their ordered lookups, "
        "in-order, pre-order and post-order traversal, and why balance matters.",
        3,
        (
            article("VisuAlgo: Binary search trees and AVL trees", "https://visualgo.net/en/bst"),
        ),
    ),
    Topic(
        "cs_heaps", "Heaps & Priority Queues",
        "Always knowing the smallest (or largest) item: binary heaps stored in arrays, inserting and "
        "removing in O(log n), and priority queues built on them.",
        3,
        (
            article("VisuAlgo: Binary heaps", "https://visualgo.net/en/heap"),
        ),
    ),
    Topic(
        "cs_graphs", "Graphs & Traversal",
        "Modelling connections: vertices and edges, directed and weighted graphs, adjacency lists and "
        "matrices, and exploring them with breadth-first and depth-first search.",
        3,
        (
            article("VisuAlgo: Graph traversal (DFS and BFS)", "https://visualgo.net/en/dfsbfs"),
            video("Algorithms Course: Graph Theory (freeCodeCamp)", "https://www.youtube.com/watch?v=09_LlHjoEiY"),
        ),
    ),
    Topic(
        "cs_shortest_paths", "Shortest Paths",
        "Finding the cheapest route: breadth-first search for unweighted graphs, Dijkstra's "
        "algorithm with a priority queue, why it fails with negative weights, and A* search.",
        4,
        (
            article("Red Blob Games: Introduction to the A* algorithm", "https://www.redblobgames.com/pathfinding/a-star/introduction.html"),
            article("CP-Algorithms: Dijkstra's algorithm", "https://cp-algorithms.com/graph/dijkstra.html"),
            article("VisuAlgo: Single-source shortest paths", "https://visualgo.net/en/sssp"),
        ),
    ),
    Topic(
        "cs_greedy", "Greedy Algorithms",
        "Making the best local choice at each step: when that gives the best overall answer (interval "
        "scheduling, minimum spanning trees) and when it doesn't (some coin systems).",
        3,
        (
            article("CP-Algorithms (algorithm reference)", "https://cp-algorithms.com/"),
        ),
    ),
    Topic(
        "cs_dynamic_programming", "Dynamic Programming",
        "Solving problems by reusing answers to overlapping subproblems: memoisation and bottom-up "
        "tables, and classic examples such as Fibonacci, coin change and longest common subsequence.",
        4,
        (
            article("CP-Algorithms: Introduction to dynamic programming", "https://cp-algorithms.com/dynamic_programming/intro-to-dp.html"),
            video("Dynamic Programming: Learn to solve algorithmic problems (freeCodeCamp)", "https://www.youtube.com/watch?v=oBt53YbR9Kk"),
        ),
    ),
    Topic(
        "cs_complexity_classes", "P, NP & Hard Problems",
        "Problems no fast algorithm is known for: the classes P and NP, NP-complete problems such as "
        "the travelling salesperson, what P versus NP asks, and what to do in practice.",
        4,
        (
            video("P vs. NP and the Computational Complexity Zoo (hackerdashery)", "https://www.youtube.com/watch?v=YX40hbAHx3s"),
        ),
    ),
    # --- Systems ----------------------------------------------------------------------------------
    Topic(
        "cs_computer_architecture", "Computer Architecture",
        "How a processor runs programs: instructions and machine code, registers, the memory "
        "hierarchy from cache to disk, and why caches and pipelining make programs faster.",
        2,
        (
            video("Instructions & Programs: Crash Course Computer Science #8", "https://www.youtube.com/watch?v=zltgXvg6r3k"),
            video("Advanced CPU Designs: Crash Course Computer Science #9", "https://www.youtube.com/watch?v=rtAlC5J1U40"),
            article("Nand2Tetris: Build a computer from first principles", "https://www.nand2tetris.org/"),
        ),
    ),
    Topic(
        "cs_processes_threads", "Processes, Threads & Scheduling",
        "How an operating system runs many programs: processes and their isolation, threads sharing "
        "one process's memory, context switches, and how the scheduler shares the CPU.",
        3,
        (
            docs("Operating Systems: Three Easy Pieces, Processes", "https://pages.cs.wisc.edu/~remzi/OSTEP/cpu-intro.pdf"),
            docs("Operating Systems: Three Easy Pieces, Threads", "https://pages.cs.wisc.edu/~remzi/OSTEP/threads-intro.pdf"),
        ),
    ),
    Topic(
        "cs_memory_management", "Memory Management",
        "Where a program's data lives: the stack and the heap, allocation and garbage collection, "
        "memory leaks, and virtual memory giving each process its own address space.",
        3,
        (
            docs("Operating Systems: Three Easy Pieces, Address spaces", "https://pages.cs.wisc.edu/~remzi/OSTEP/vm-intro.pdf"),
            article("Operating Systems: Three Easy Pieces (free book)", "https://pages.cs.wisc.edu/~remzi/OSTEP/"),
        ),
    ),
    Topic(
        "cs_concurrency", "Concurrency, Locks & Deadlock",
        "Correct programs with several threads: race conditions, critical sections and locks, "
        "deadlock and the conditions that cause it, and how to avoid it.",
        4,
        (
            docs("Operating Systems: Three Easy Pieces, Locks", "https://pages.cs.wisc.edu/~remzi/OSTEP/threads-locks.pdf"),
            docs("Operating Systems: Three Easy Pieces, Concurrency bugs", "https://pages.cs.wisc.edu/~remzi/OSTEP/threads-bugs.pdf"),
        ),
    ),
    Topic(
        "cs_networking", "Computer Networks & Protocols",
        "How data crosses networks: the layered model, IP addresses and ports, TCP's reliable "
        "connections versus UDP's speed, the TCP handshake, and how TLS secures a connection.",
        3,
        (
            article("High Performance Browser Networking: Building blocks of TCP", "https://hpbn.co/building-blocks-of-tcp/"),
            article("High Performance Browser Networking: Building blocks of UDP", "https://hpbn.co/building-blocks-of-udp/"),
            article("High Performance Browser Networking: Transport Layer Security", "https://hpbn.co/transport-layer-security-tls/"),
        ),
    ),
    Topic(
        "cs_compilers_interpreters", "Compilers & Interpreters",
        "How source code becomes something a machine runs: lexing and parsing, compiling to machine "
        "code or bytecode, interpreters and virtual machines, and just-in-time compilation.",
        3,
        (
            article("Crafting Interpreters: A map of the territory", "https://craftinginterpreters.com/a-map-of-the-territory.html"),
        ),
    ),
)

PREREQUISITES: tuple[tuple[str, str], ...] = (
    ("cs_complexity", "cs_arrays_linked_lists"),
    ("cs_arrays_linked_lists", "cs_stacks_queues"),
    ("cs_arrays_linked_lists", "cs_hash_tables"),
    ("cs_complexity", "cs_recursion"),
    ("cs_recursion", "cs_sorting"),
    ("cs_arrays_linked_lists", "cs_sorting"),
    ("cs_recursion", "cs_trees"),
    ("cs_arrays_linked_lists", "cs_trees"),
    ("cs_trees", "cs_heaps"),
    ("cs_stacks_queues", "cs_graphs"),
    ("cs_recursion", "cs_graphs"),
    ("cs_graphs", "cs_shortest_paths"),
    ("cs_heaps", "cs_shortest_paths"),
    ("cs_sorting", "cs_greedy"),
    ("cs_recursion", "cs_dynamic_programming"),
    ("cs_hash_tables", "cs_dynamic_programming"),
    ("cs_greedy", "cs_complexity_classes"),
    ("cs_dynamic_programming", "cs_complexity_classes"),

    ("binary_data_representation", "cs_computer_architecture"),
    ("operating_system_basics", "cs_processes_threads"),
    ("cs_computer_architecture", "cs_processes_threads"),
    ("cs_processes_threads", "cs_memory_management"),
    ("cs_processes_threads", "cs_concurrency"),
    ("how_the_internet_works", "cs_networking"),
    ("cs_processes_threads", "cs_networking"),
    ("programming_concepts", "cs_compilers_interpreters"),
    ("cs_computer_architecture", "cs_compilers_interpreters"),
)

CS_CORE = Domain(
    id="cs-core",
    name="Computer Science Core",
    description=(
        "The ideas under all software: complexity, data structures and algorithms from lists to "
        "graphs and dynamic programming, and how processors, operating systems, networks and "
        "compilers work."
    ),
    topics=TOPICS,
    prerequisites=PREREQUISITES,
)
