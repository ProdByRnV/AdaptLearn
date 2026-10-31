"""UI/UX Design: designing products that are useful, usable and good to look at.

What Is UI/UX Design? is the starting topic. Designing for Mobile is defined in App Development and
shared here; it builds on Usability Heuristics & UX Laws. Handing designs over to developers builds on
CSS Basics from Web Development.
"""

from seed.model import Domain, Topic, article, docs, video

TOPICS: tuple[Topic, ...] = (
    # --- Understanding users ------------------------------------------------------------------
    Topic(
        "ux_what_is", "What Is UI/UX Design?",
        "The difference between user experience (UX) and user interface (UI) design, user-centred "
        "design, and the design process from discovering the problem to delivering a solution.",
        1,
        (
            article("NN/g: The definition of user experience", "https://www.nngroup.com/articles/definition-user-experience/"),
            video("Don Norman: The term \"UX\" (NN/g)", "https://www.youtube.com/watch?v=9BdtGjoIN4E"),
            article("Design Council: The Double Diamond", "https://www.designcouncil.org.uk/resources/the-double-diamond/"),
        ),
    ),
    Topic(
        "ux_user_research", "User Research",
        "Learning what people need before designing: interviews, surveys, field studies and analytics, "
        "what people say versus what they do, writing research questions, and avoiding leading ones.",
        2,
        (
            article("NN/g: When to use which UX research methods", "https://www.nngroup.com/articles/which-ux-research-methods/"),
            docs("GOV.UK Service Manual: User research", "https://www.gov.uk/service-manual/user-research"),
            article("NN/g: User interviews 101", "https://www.nngroup.com/articles/user-interviews/"),
        ),
    ),
    Topic(
        "ux_personas_journeys", "Personas & Journey Maps",
        "Turning research into shared understanding: personas based on real data, user journeys and "
        "journey maps of goals, steps and feelings, and spotting the pain points to design for.",
        2,
        (
            article("NN/g: Personas make users memorable", "https://www.nngroup.com/articles/persona/"),
            article("NN/g: Journey mapping 101", "https://www.nngroup.com/articles/journey-mapping-101/"),
            article("NN/g: User journeys vs. user flows", "https://www.nngroup.com/articles/user-journeys-vs-user-flows/"),
        ),
    ),
    Topic(
        "ux_information_architecture", "Information Architecture",
        "Organising content so people can find it: grouping and labelling, site maps, navigation, and "
        "testing structures with card sorting and tree testing.",
        2,
        (
            article("NN/g: Information architecture vs. navigation", "https://www.nngroup.com/articles/ia-vs-navigation/"),
            article("NN/g: Card sorting", "https://www.nngroup.com/articles/card-sorting-definition/"),
            article("NN/g: Tree testing", "https://www.nngroup.com/articles/tree-testing/"),
        ),
    ),
    Topic(
        "ux_heuristics", "Usability Heuristics & UX Laws",
        "Rules of thumb for usable interfaces: Nielsen's ten heuristics such as visibility of status "
        "and error prevention, and laws such as Fitts's law and Hick's law.",
        2,
        (
            article("NN/g: 10 usability heuristics for user interface design", "https://www.nngroup.com/articles/ten-usability-heuristics/"),
            article("Laws of UX", "https://lawsofux.com/"),
            article("NN/g: Fitts's law and its applications in UX", "https://www.nngroup.com/articles/fitts-law/"),
        ),
    ),
    # --- Visual design ------------------------------------------------------------------------
    Topic(
        "ux_visual_hierarchy", "Visual Hierarchy & Layout",
        "Guiding the eye: size, contrast and position to show what matters most, Gestalt principles "
        "such as proximity and similarity, alignment, white space, and layout grids.",
        2,
        (
            article("NN/g: Visual hierarchy in UX", "https://www.nngroup.com/articles/visual-hierarchy-ux-definition/"),
            article("IxDF: Gestalt principles", "https://ixdf.org/literature/topics/gestalt-principles"),
            article("NN/g: 5 principles of visual design in UX", "https://www.nngroup.com/articles/principles-visual-design/"),
        ),
    ),
    Topic(
        "ux_typography", "Typography",
        "Making text easy to read: choosing typefaces, a type scale for headings and body text, line "
        "length and line height, font weights, and pairing no more than a couple of fonts.",
        2,
        (
            article("Butterick's Practical Typography", "https://practicaltypography.com/"),
            docs("Material Design 3: Typography", "https://m3.material.io/styles/typography/overview"),
        ),
    ),
    Topic(
        "ux_colour", "Colour in Interfaces",
        "Using colour with purpose: a palette with primary, neutral and status colours, colour to show "
        "meaning and state, enough contrast for text, and light and dark themes.",
        2,
        (
            docs("Material Design 3: Color system", "https://m3.material.io/styles/color/system/overview"),
            article("WebAIM: Contrast and color accessibility", "https://webaim.org/articles/contrast/"),
            docs("WebAIM: Contrast checker", "https://webaim.org/resources/contrastchecker/"),
        ),
    ),
    Topic(
        "ux_wireframing", "Sketching & Wireframing",
        "Exploring layouts quickly: paper sketches, low-fidelity wireframes that leave out colour and "
        "detail, wireflows that link screens, and getting feedback before polishing anything.",
        2,
        (
            article("Figma: What is wireframing?", "https://www.figma.com/resource-library/what-is-wireframing/"),
            article("Balsamiq: What is a wireframe?", "https://balsamiq.com/blog/what-are-wireframes/"),
            article("NN/g: Wireflows", "https://www.nngroup.com/articles/wireflows/"),
        ),
    ),
    # --- Designing interactions ---------------------------------------------------------------
    Topic(
        "ux_interaction_design", "Interaction Design",
        "Designing how an interface responds: affordances and signifiers, feedback for every action, "
        "states such as hover, focus, disabled, loading and error, and motion that explains changes.",
        3,
        (
            article("IxDF: What is interaction design?", "https://ixdf.org/literature/topics/interaction-design"),
            article("NN/g: Microinteractions in user experience", "https://www.nngroup.com/articles/microinteractions/"),
            docs("Material Design 3: Motion", "https://m3.material.io/styles/motion/overview/how-it-works"),
        ),
    ),
    Topic(
        "ux_accessible_design", "Accessible Design",
        "Designing for everyone, including disabled people: sufficient contrast, not relying on colour "
        "alone, visible focus, clear text, captions, and the WCAG principles behind them.",
        3,
        (
            article("WebAIM: Introduction to web accessibility", "https://webaim.org/intro/"),
            article("GOV.UK: Dos and don'ts on designing for accessibility", "https://accessibility.blog.gov.uk/2016/09/02/dos-and-donts-on-designing-for-accessibility/"),
            docs("Microsoft Inclusive Design", "https://inclusive.microsoft.design/"),
        ),
    ),
    Topic(
        "ux_figma", "Designing in Figma",
        "Working in a design tool: frames and layers, auto layout that resizes with its content, "
        "reusable components and variants, and sharing files for comments.",
        3,
        (
            docs("Figma: Guide to auto layout", "https://help.figma.com/hc/en-us/articles/360040451373-Guide-to-auto-layout-in-Figma"),
            docs("Figma: Guide to components", "https://help.figma.com/hc/en-us/articles/360038662654-Guide-to-components-in-Figma"),
            docs("Penpot user guide (open-source alternative)", "https://help.penpot.app/user-guide/"),
        ),
    ),
    Topic(
        "ux_prototyping", "Prototyping",
        "Making designs you can click through: low- and high-fidelity prototypes, linking screens and "
        "adding transitions, and choosing the cheapest prototype that answers the question.",
        3,
        (
            article("NN/g: UX prototypes, low fidelity vs. high fidelity", "https://www.nngroup.com/articles/ux-prototype-hi-lo-fidelity/"),
            docs("GOV.UK Service Manual: Making prototypes", "https://www.gov.uk/service-manual/design/making-prototypes"),
            docs("Figma: Guide to prototyping", "https://help.figma.com/hc/en-us/articles/360040314193-Guide-to-prototyping-in-Figma"),
        ),
    ),
    Topic(
        "ux_writing_forms", "UX Writing & Forms",
        "Words and forms that help people finish tasks: clear labels and buttons, helpful error "
        "messages, asking only what you need, and laying out forms that are quick to fill in.",
        3,
        (
            article("NN/g: Error-message guidelines", "https://www.nngroup.com/articles/error-message-guidelines/"),
            article("NN/g: Website forms usability, top 10 recommendations", "https://www.nngroup.com/articles/web-form-design/"),
            docs("GOV.UK Service Manual: Writing for user interfaces", "https://www.gov.uk/service-manual/design/writing-for-user-interfaces"),
        ),
    ),
    # --- Testing and delivering ---------------------------------------------------------------
    Topic(
        "ux_usability_testing", "Usability Testing",
        "Watching real people use a design: realistic tasks, thinking aloud, moderated and "
        "unmoderated sessions, why about five users find most problems, and reporting findings.",
        3,
        (
            article("NN/g: Usability testing 101", "https://www.nngroup.com/articles/usability-testing-101/"),
            article("NN/g: Why you only need to test with 5 users", "https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/"),
            docs("GOV.UK Service Manual: Using moderated usability testing", "https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing"),
        ),
    ),
    Topic(
        "ux_ethics", "Ethical Design & Deceptive Patterns",
        "Designing in users' interests: recognising deceptive patterns such as hidden costs, forced "
        "continuity and confirmshaming, respecting privacy and consent, and the laws against them.",
        3,
        (
            article("NN/g: Deceptive patterns in UX", "https://www.nngroup.com/articles/deceptive-patterns/"),
            article("Deceptive Patterns (Harry Brignull)", "https://deceptive.design/"),
            docs("EDPB: Guidelines on deceptive design patterns", "https://www.edpb.europa.eu/documents/guideline/guidelines-032022-on-deceptive-design-patterns-in-social-media-platform_en"),
        ),
    ),
    Topic(
        "ux_design_systems", "Design Systems",
        "Designing consistently at scale: design tokens for colour, type and spacing, a library of "
        "components with documented usage, atomic design, and examples such as GOV.UK and Carbon.",
        4,
        (
            article("NN/g: Design systems 101", "https://www.nngroup.com/articles/design-systems-101/"),
            article("Brad Frost: Atomic design methodology", "https://atomicdesign.bradfrost.com/chapter-2/"),
            docs("IBM Carbon Design System", "https://www.carbondesignsystem.com/"),
        ),
    ),
    Topic(
        "ux_metrics", "Measuring UX",
        "Putting numbers on experience: task success rate and time on task, the System Usability Scale "
        "(SUS), qualitative versus quantitative studies, and A/B tests that compare two designs.",
        4,
        (
            article("NN/g: Success rate, the simplest usability metric", "https://www.nngroup.com/articles/success-rate-the-simplest-usability-metric/"),
            article("MeasuringU: Measuring usability with the SUS", "https://measuringu.com/sus/"),
            article("NN/g: A/B testing 101", "https://www.nngroup.com/articles/ab-testing/"),
        ),
    ),
    Topic(
        "ux_handoff", "Design Handoff to Developers",
        "Getting designs built as intended: specs for spacing, sizes and states, design tokens shared "
        "with code, inspecting designs in developer tools such as Figma's Dev Mode, and reviewing builds.",
        4,
        (
            docs("Figma: Guide to Dev Mode", "https://help.figma.com/hc/en-us/articles/15023124644247-Guide-to-Dev-Mode-in-Figma"),
            docs("Design Tokens Community Group", "https://www.designtokens.org/"),
            docs("GOV.UK Design System", "https://design-system.service.gov.uk/"),
        ),
    ),
)

PREREQUISITES: tuple[tuple[str, str], ...] = (
    ("ux_what_is", "ux_user_research"),
    ("ux_user_research", "ux_personas_journeys"),
    ("ux_what_is", "ux_information_architecture"),
    ("ux_what_is", "ux_heuristics"),
    ("ux_what_is", "ux_visual_hierarchy"),
    ("ux_visual_hierarchy", "ux_typography"),
    ("ux_visual_hierarchy", "ux_colour"),
    ("ux_information_architecture", "ux_wireframing"),

    ("ux_heuristics", "ux_interaction_design"),
    ("ux_colour", "ux_accessible_design"),
    ("ux_heuristics", "ux_accessible_design"),
    ("ux_wireframing", "ux_figma"),
    ("ux_visual_hierarchy", "ux_figma"),
    ("ux_figma", "ux_prototyping"),
    ("ux_interaction_design", "ux_prototyping"),
    ("ux_interaction_design", "ux_writing_forms"),

    ("ux_prototyping", "ux_usability_testing"),
    ("ux_user_research", "ux_usability_testing"),
    ("ux_heuristics", "ux_ethics"),
    ("ux_figma", "ux_design_systems"),
    ("ux_typography", "ux_design_systems"),
    ("ux_accessible_design", "ux_design_systems"),
    ("ux_usability_testing", "ux_metrics"),
    ("ux_design_systems", "ux_handoff"),
    ("css_basics", "ux_handoff"),
)

UI_UX_DESIGN = Domain(
    id="ui-ux-design",
    name="UI/UX Design",
    description=(
        "Designing products people can use and enjoy: user research, information architecture, "
        "usability principles, visual and interaction design, accessibility, prototyping in Figma, "
        "usability testing, and design systems."
    ),
    topics=TOPICS,
    prerequisites=PREREQUISITES,
    shared=("app_mobile_ux",),
)
