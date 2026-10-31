"""Game Development: how games are designed, programmed and shipped.

How Games Are Made is the starting topic. Learners can work in an engine (Godot or Unity) and
learn the ideas every engine shares: the game loop, vectors and transforms, input, physics,
graphics, game AI and networking. Programming topics build on Foundations; pathfinding and
optimisation build on Computer Science Core.
"""

from seed.model import Domain, Topic, article, docs, video

TOPICS: tuple[Topic, ...] = (
    # --- Making games -----------------------------------------------------------------------
    Topic(
        "game_what_is_gamedev", "How Games Are Made",
        "What goes into a video game: the roles on a team (design, programming, art, audio), engines "
        "and frameworks, the loop of prototyping and playtesting, and the platforms games ship on.",
        1,
        (
            docs("MDN: Game development", "https://developer.mozilla.org/en-US/docs/Games"),
            article("Game Programming Patterns", "https://gameprogrammingpatterns.com/"),
        ),
    ),
    Topic(
        "game_design_basics", "Game Design Basics",
        "Designing play: mechanics, dynamics and aesthetics (MDA), core loops, goals and challenge, "
        "rewards and feedback, and why a designer thinks through every way a player might act.",
        2,
        (
            article("Hunicke, LeBlanc & Zubek: MDA framework (PDF)", "https://users.cs.northwestern.edu/~hunicke/MDA.pdf"),
            article("Liz England: The Door Problem", "https://lizengland.com/blog/the-door-problem/"),
        ),
    ),
    Topic(
        "game_loop", "The Game Loop",
        "The heart of every game: read input, update the world and draw a frame, many times a second; "
        "frame rate, delta time so movement doesn't depend on speed, and fixed time steps for physics.",
        2,
        (
            article("Game Programming Patterns: Game Loop", "https://gameprogrammingpatterns.com/game-loop.html"),
            article("Gaffer On Games: Fix Your Timestep!", "https://gafferongames.com/post/fix_your_timestep/"),
            docs("MDN: Anatomy of a video game", "https://developer.mozilla.org/en-US/docs/Games/Anatomy"),
        ),
    ),
    Topic(
        "game_vectors", "Vectors & Game Maths",
        "The maths behind movement: vectors for position, velocity and direction, length and "
        "normalising, the dot product for angles and facing, and a little trigonometry for rotation.",
        2,
        (
            docs("Godot docs: Vector math", "https://docs.godotengine.org/en/stable/tutorials/math/vector_math.html"),
            docs("Godot docs: Advanced vector math", "https://docs.godotengine.org/en/stable/tutorials/math/vectors_advanced.html"),
        ),
    ),
    Topic(
        "game_engines", "Game Engines",
        "What an engine gives you: a scene editor, rendering, physics, audio and export to many "
        "platforms; entities built from components; and choosing between Godot, Unity and Unreal.",
        2,
        (
            video("Unreal in 100 Seconds (Fireship)", "https://www.youtube.com/watch?v=DXDe-2BC4cE"),
            article("Game Programming Patterns: Component", "https://gameprogrammingpatterns.com/component.html"),
            docs("Unreal Engine documentation", "https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-documentation"),
        ),
    ),
    Topic(
        "game_transforms", "Transforms & Coordinate Spaces",
        "Placing things in a world: translation, rotation and scale, transform matrices, parent and "
        "child objects, and converting between local, world and screen coordinates.",
        3,
        (
            docs("Godot docs: Matrices and transforms", "https://docs.godotengine.org/en/stable/tutorials/math/matrices_and_transforms.html"),
            article("LearnOpenGL: Transformations", "https://learnopengl.com/Getting-started/Transformations"),
        ),
    ),
    # --- Engines --------------------------------------------------------------------------------
    Topic(
        "game_godot", "Godot & GDScript",
        "Making games in the free, open-source Godot engine: nodes and scenes, scripts in GDScript, "
        "signals for reacting to events, and the _process and _physics_process callbacks.",
        3,
        (
            video("Godot in 100 Seconds (Fireship)", "https://www.youtube.com/watch?v=QKgTZWbwD1U"),
            docs("Godot docs: Nodes and scenes", "https://docs.godotengine.org/en/stable/getting_started/step_by_step/nodes_and_scenes.html"),
            docs("Godot docs: Your first 2D game", "https://docs.godotengine.org/en/stable/getting_started/first_2d_game/index.html"),
        ),
    ),
    Topic(
        "game_unity", "Unity & C#",
        "Making games in Unity: GameObjects and components, C# scripts with Start and Update, "
        "prefabs for reusable objects, and the order in which Unity calls your code each frame.",
        3,
        (
            video("Unity in 100 Seconds (Fireship)", "https://www.youtube.com/watch?v=iqlH4okiQqg"),
            docs("Unity Learn: Unity Essentials", "https://learn.unity.com/pathway/unity-essentials"),
            docs("Unity manual: Event function execution order", "https://docs.unity.com/en-us/engine/6000.6/manual/scripting/managing-update-order/execution-order"),
        ),
    ),
    # --- Building blocks of a game ---------------------------------------------------------------
    Topic(
        "game_input", "Player Input & Controls",
        "Turning key presses, mouse movement and gamepads into actions: polling versus input events, "
        "mapping actions to buttons so players can rebind them, and keeping controls responsive.",
        3,
        (
            docs("Godot docs: Input examples", "https://docs.godotengine.org/en/stable/tutorials/inputs/input_examples.html"),
            docs("MDN: Desktop mouse and keyboard controls", "https://developer.mozilla.org/en-US/docs/Games/Techniques/Control_mechanisms/Desktop_with_mouse_and_keyboard"),
            docs("MDN: Using the Gamepad API", "https://developer.mozilla.org/en-US/docs/Web/API/Gamepad_API/Using_the_Gamepad_API"),
        ),
    ),
    Topic(
        "game_physics", "Collision & Physics",
        "Making objects touch and move believably: bounding boxes and circles, detecting and resolving "
        "collisions, rigid bodies, gravity and forces, and triggers that detect without blocking.",
        3,
        (
            docs("MDN: 2D collision detection", "https://developer.mozilla.org/en-US/docs/Games/Techniques/2D_collision_detection"),
            docs("Godot docs: Physics introduction", "https://docs.godotengine.org/en/stable/tutorials/physics/physics_introduction.html"),
            article("Jeffrey Thompson: Collision detection", "https://www.jeffreythompson.org/collision-detection/"),
        ),
    ),
    Topic(
        "game_2d_graphics", "Sprites, Tilemaps & 2D Animation",
        "Drawing 2D games: sprites and sprite sheets, frame-by-frame animation, tilemaps for building "
        "levels from small tiles, layers and draw order, and a camera that follows the player.",
        3,
        (
            docs("Godot docs: 2D sprite animation", "https://docs.godotengine.org/en/stable/tutorials/2d/2d_sprite_animation.html"),
            docs("MDN: Tiles and tilemaps overview", "https://developer.mozilla.org/en-US/docs/Games/Techniques/Tilemaps"),
            docs("Godot docs: Using TileMaps", "https://docs.godotengine.org/en/stable/tutorials/2d/using_tilemaps.html"),
        ),
    ),
    Topic(
        "game_state_machines", "State Machines & Game States",
        "Keeping behaviour organised: finite state machines for a player who can idle, run, jump or "
        "fall, transitions between states, and game states such as menu, playing and paused.",
        3,
        (
            article("Game Programming Patterns: State", "https://gameprogrammingpatterns.com/state.html"),
            article("GDQuest: Make a finite state machine in Godot 4", "https://www.gdquest.com/tutorial/godot/design-patterns/finite-state-machine/"),
        ),
    ),
    Topic(
        "game_audio", "Sound & Music",
        "Bringing a game to life with sound: sound effects as feedback, music that sets the mood, "
        "mixing with buses and volume levels, positional audio, and loading sounds efficiently.",
        3,
        (
            docs("Godot docs: Audio buses", "https://docs.godotengine.org/en/stable/tutorials/audio/audio_buses.html"),
            docs("Unity manual: Audio overview", "https://docs.unity.com/en-us/engine/6000.6/manual/audio/overview"),
            docs("MDN: Audio for web games", "https://developer.mozilla.org/en-US/docs/Games/Techniques/Audio_for_Web_Games"),
        ),
    ),
    Topic(
        "game_feel", "Game Feel & Game UI",
        "Making a game satisfying to play: responsive controls, juice such as screen shake, particles "
        "and sound on every action, plus clear menus and a HUD that shows what matters.",
        3,
        (
            video("Juice it or lose it (Jonasson & Purho)", "https://www.youtube.com/watch?v=Fy0aCDmgnxg"),
            video("Why Does Celeste Feel So Good to Play? (Game Maker's Toolkit)", "https://www.youtube.com/watch?v=yorTG9at90g"),
            docs("Godot docs: User interface", "https://docs.godotengine.org/en/stable/tutorials/ui/index.html"),
        ),
    ),
    Topic(
        "game_level_design", "Level Design",
        "Building the spaces players move through: teaching a mechanic, then testing and twisting it, "
        "pacing and difficulty curves, guiding players without words, and blocking out levels first.",
        3,
        (
            video("Super Mario 3D World's 4 Step Level Design (Game Maker's Toolkit)", "https://www.youtube.com/watch?v=dBmIkEvEBtA"),
            article("The Level Design Book: Blockout", "https://book.leveldesignbook.com/process/blockout"),
        ),
    ),
    # --- Going further ----------------------------------------------------------------------------
    Topic(
        "game_3d_graphics", "3D Graphics & Shaders",
        "How 3D scenes become pixels: meshes made of triangles, cameras and projection, materials and "
        "lighting, the rendering pipeline on the GPU, and shaders that colour vertices and pixels.",
        4,
        (
            video("How do Video Game Graphics Work? (Branch Education)", "https://www.youtube.com/watch?v=C8YtdC8mxTU"),
            docs("Godot docs: Introduction to 3D", "https://docs.godotengine.org/en/stable/tutorials/3d/introduction_to_3d.html"),
            article("The Book of Shaders", "https://thebookofshaders.com/"),
        ),
    ),
    Topic(
        "game_ai", "Game AI & Pathfinding",
        "Making characters seem smart: state machines and behaviour trees for decisions, A* to find "
        "paths on a grid or navigation mesh, and steering towards a target or away from danger.",
        4,
        (
            video("A* Pathfinding: algorithm explanation (Sebastian Lague)", "https://www.youtube.com/watch?v=-L-WgKMFuhE"),
            article("Game Developer: Behavior trees for AI, how they work", "https://www.gamedeveloper.com/programming/behavior-trees-for-ai-how-they-work"),
            docs("Godot docs: Using NavigationAgents", "https://docs.godotengine.org/en/stable/tutorials/navigation/navigation_using_navigationagents.html"),
        ),
    ),
    Topic(
        "game_multiplayer", "Multiplayer & Netcode",
        "Playing together over a network: client-server versus peer-to-peer, an authoritative server "
        "to stop cheating, latency and packet loss, client-side prediction and interpolation.",
        4,
        (
            article("Gaffer On Games: What every programmer needs to know about game networking", "https://gafferongames.com/post/what_every_programmer_needs_to_know_about_game_networking/"),
            article("Gabriel Gambetta: Client-server game architecture", "https://www.gabrielgambetta.com/client-server-game-architecture.html"),
            video("Overwatch gameplay architecture and netcode (GDC)", "https://www.youtube.com/watch?v=W3aieHjyNvw"),
        ),
    ),
    Topic(
        "game_optimisation", "Performance & Optimisation",
        "Keeping a steady frame rate: the frame budget (about 16.7 ms at 60 frames per second), "
        "profiling before optimising, fewer draw calls, object pooling, and level of detail.",
        4,
        (
            docs("Godot docs: General optimization tips", "https://docs.godotengine.org/en/stable/tutorials/performance/general_optimization.html"),
            article("Game Programming Patterns: Object Pool", "https://gameprogrammingpatterns.com/object-pool.html"),
            docs("Unity manual: Unity Profiler", "https://docs.unity.com/en-us/engine/6000.6/manual/analysis/profiler"),
        ),
    ),
    Topic(
        "game_shipping", "Playtesting & Shipping",
        "Finishing a game: watching people play without helping them, acting on feedback, exporting "
        "builds for each platform, and publishing on stores such as itch.io and Steam.",
        4,
        (
            docs("Godot docs: Exporting projects", "https://docs.godotengine.org/en/stable/tutorials/export/exporting_projects.html"),
            docs("itch.io: Your first itch.io page", "https://itch.io/docs/creators/getting-started"),
            docs("Steamworks: Getting started", "https://partner.steamgames.com/doc/gettingstarted"),
        ),
    ),
)

PREREQUISITES: tuple[tuple[str, str], ...] = (
    ("game_what_is_gamedev", "game_design_basics"),
    ("game_what_is_gamedev", "game_loop"),
    ("programming_concepts", "game_loop"),
    ("game_what_is_gamedev", "game_vectors"),
    ("game_what_is_gamedev", "game_engines"),
    ("game_vectors", "game_transforms"),

    ("game_engines", "game_godot"),
    ("programming_concepts", "game_godot"),
    ("game_engines", "game_unity"),
    ("programming_concepts", "game_unity"),

    ("game_loop", "game_input"),
    ("game_loop", "game_physics"),
    ("game_vectors", "game_physics"),
    ("game_loop", "game_2d_graphics"),
    ("game_loop", "game_state_machines"),
    ("game_engines", "game_audio"),
    ("game_design_basics", "game_feel"),
    ("game_input", "game_feel"),
    ("game_design_basics", "game_level_design"),

    ("game_transforms", "game_3d_graphics"),
    ("game_state_machines", "game_ai"),
    ("game_vectors", "game_ai"),
    ("cs_graphs", "game_ai"),
    ("game_input", "game_multiplayer"),
    ("how_the_internet_works", "game_multiplayer"),
    ("game_2d_graphics", "game_optimisation"),
    ("game_physics", "game_optimisation"),
    ("cs_complexity", "game_optimisation"),
    ("game_level_design", "game_shipping"),
    ("game_feel", "game_shipping"),
)

GAME_DEVELOPMENT = Domain(
    id="game-development",
    name="Game Development",
    description=(
        "Making video games: game design, the game loop and the maths of movement, engines such as "
        "Godot and Unity, input, physics, 2D and 3D graphics, sound, game AI, multiplayer, and "
        "playtesting and shipping."
    ),
    topics=TOPICS,
    prerequisites=PREREQUISITES,
)
