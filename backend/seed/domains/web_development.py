"""Web Development: the 30 topics and prerequisite edges from ARCHITECTURE.md sections 7-8.

Git Basics is defined in Foundations and shared here.
"""

from seed.model import Domain, Topic, article, docs, video

TOPICS: tuple[Topic, ...] = (
    # --- HTML & CSS -----------------------------------------------------------
    Topic(
        "html_basics", "HTML Basics",
        "The structure of a web page: elements, tags, attributes, headings, links, images and lists.",
        1,
        (
            docs("MDN: HTML", "https://developer.mozilla.org/en-US/docs/Web/HTML"),
            article("web.dev: Learn HTML", "https://web.dev/learn/html"),
            video("HTML in 100 Seconds", "https://www.youtube.com/watch?v=ok-plXXHlWw"),
        ),
    ),
    Topic(
        "semantic_html", "Semantic HTML",
        "Choosing elements by meaning (header, nav, main, article, section, footer) so pages are "
        "understandable to browsers, search engines and assistive technology.",
        1,
        (
            article("web.dev: Semantic HTML", "https://web.dev/learn/html/semantic-html"),
            docs("MDN: Semantics", "https://developer.mozilla.org/en-US/docs/Glossary/Semantics"),
        ),
    ),
    Topic(
        "forms_accessibility", "Forms & Accessibility",
        "Building forms with labels, input types and validation, and making pages usable with a "
        "keyboard and screen readers.",
        2,
        (
            article("web.dev: Learn Forms", "https://web.dev/learn/forms"),
            article("web.dev: Learn Accessibility", "https://web.dev/learn/accessibility"),
            docs("MDN: Web forms", "https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Forms"),
        ),
    ),
    Topic(
        "css_basics", "CSS Basics",
        "Styling pages with selectors, the cascade, specificity, the box model, colours and typography.",
        1,
        (
            docs("MDN: CSS", "https://developer.mozilla.org/en-US/docs/Web/CSS"),
            article("web.dev: Learn CSS", "https://web.dev/learn/css"),
            video("CSS in 100 Seconds", "https://www.youtube.com/watch?v=OEV8gMkCHXQ"),
        ),
    ),
    Topic(
        "flexbox", "Flexbox",
        "One-dimensional layout with flex containers and items: direction, wrapping, alignment and "
        "distributing space.",
        2,
        (
            article("CSS-Tricks: A Complete Guide to Flexbox", "https://css-tricks.com/snippets/css/a-guide-to-flexbox/"),
            docs("MDN: Flexbox", "https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Flexbox"),
            article("Flexbox Froggy (interactive game)", "https://flexboxfroggy.com/"),
        ),
    ),
    Topic(
        "css_grid", "CSS Grid",
        "Two-dimensional layout with rows, columns, tracks, gaps and named grid areas.",
        2,
        (
            article("CSS-Tricks: A Complete Guide to CSS Grid", "https://css-tricks.com/complete-guide-css-grid-layout/"),
            docs("MDN: Grids", "https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Grids"),
            article("Grid Garden (interactive game)", "https://cssgridgarden.com/"),
        ),
    ),
    Topic(
        "responsive_design", "Responsive Design",
        "Layouts that adapt to any screen using media queries, fluid units, flexible images and a "
        "mobile-first approach.",
        2,
        (
            article("web.dev: Learn Responsive Design", "https://web.dev/learn/design"),
            docs("MDN: Responsive design", "https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Responsive_Design"),
        ),
    ),
    # --- JavaScript -------------------------------------------------------------
    Topic(
        "javascript_fundamentals", "JavaScript Fundamentals",
        "Variables, data types, operators, conditionals and loops: the core syntax of JavaScript.",
        1,
        (
            article("javascript.info: JavaScript Fundamentals", "https://javascript.info/first-steps"),
            docs("MDN: JavaScript Guide", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide"),
            video("JavaScript in 100 Seconds", "https://www.youtube.com/watch?v=DHjqpvDnNGE"),
        ),
    ),
    Topic(
        "functions_scope", "Functions & Scope",
        "Declaring and calling functions, parameters and return values, arrow functions, scope, "
        "hoisting and closures.",
        2,
        (
            article("javascript.info: Functions", "https://javascript.info/function-basics"),
            article("javascript.info: Variable scope, closure", "https://javascript.info/closure"),
            docs("MDN: Functions", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Functions"),
        ),
    ),
    Topic(
        "arrays_objects", "Arrays & Objects",
        "Storing and transforming data with arrays and objects: array methods like map, filter and "
        "reduce, destructuring and the spread syntax.",
        2,
        (
            article("javascript.info: Objects", "https://javascript.info/object"),
            article("javascript.info: Array methods", "https://javascript.info/array-methods"),
            docs("MDN: Array", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array"),
        ),
    ),
    Topic(
        "dom_manipulation", "DOM Manipulation",
        "Selecting, creating, changing and removing page elements from JavaScript through the "
        "Document Object Model.",
        2,
        (
            article("javascript.info: Document", "https://javascript.info/document"),
            docs("MDN: Document Object Model (DOM)", "https://developer.mozilla.org/en-US/docs/Web/API/Document_Object_Model"),
        ),
    ),
    Topic(
        "browser_events", "Browser Events",
        "Responding to user actions with event listeners, the event object, bubbling, delegation "
        "and preventing default behaviour.",
        2,
        (
            article("javascript.info: Introduction to browser events", "https://javascript.info/introduction-browser-events"),
            docs("MDN: Introduction to events", "https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Scripting/Events"),
        ),
    ),
    Topic(
        "async_javascript", "Async JavaScript",
        "Handling work that finishes later: the event loop, callbacks, promises and async/await.",
        3,
        (
            article("javascript.info: Promises, async/await", "https://javascript.info/async"),
            docs("MDN: Asynchronous JavaScript", "https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Async_JS"),
            video("The Async Await Episode I Promised", "https://www.youtube.com/watch?v=vn3tm0quoqE"),
        ),
    ),
    Topic(
        "fetch_http_apis", "Fetch & HTTP APIs",
        "Calling web APIs with fetch: HTTP methods, status codes, headers, JSON bodies and error handling.",
        3,
        (
            docs("MDN: Using the Fetch API", "https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch"),
            docs("MDN: An overview of HTTP", "https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview"),
            article("javascript.info: Fetch", "https://javascript.info/fetch"),
        ),
    ),
    Topic(
        "es_modules", "ES Modules",
        "Splitting code into files with import and export, default versus named exports, and how "
        "modules load in the browser.",
        2,
        (
            article("javascript.info: Modules, introduction", "https://javascript.info/modules-intro"),
            docs("MDN: JavaScript modules", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules"),
        ),
    ),
    # --- Tooling & backend -----------------------------------------------------
    Topic(
        "nodejs_basics", "Node.js Basics",
        "Running JavaScript outside the browser: the Node.js runtime, core modules, the file system "
        "and the event loop on the server.",
        2,
        (
            docs("Node.js: Introduction to Node.js", "https://nodejs.org/learn/getting-started/introduction-to-nodejs"),
            docs("Node.js API documentation", "https://nodejs.org/docs/latest/api/"),
        ),
    ),
    Topic(
        "npm_packages", "npm & Packages",
        "Managing dependencies with npm: package.json, installing packages, semantic versioning and "
        "npm scripts.",
        2,
        (
            docs("npm Docs: About npm", "https://docs.npmjs.com/about-npm"),
            docs("npm Docs: package.json", "https://docs.npmjs.com/cli/configuring-npm/package-json"),
            docs("Node.js: An introduction to the npm package manager", "https://nodejs.org/learn/getting-started/an-introduction-to-the-npm-package-manager"),
        ),
    ),
    Topic(
        "express_basics", "Express.js Basics",
        "Building web servers with Express: routes, request and response objects, middleware and "
        "serving JSON.",
        3,
        (
            docs("Express: Hello world", "https://expressjs.com/en/starter/hello-world/"),
            docs("Express: Routing", "https://expressjs.com/en/guide/routing/"),
            docs("MDN: Express web framework", "https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/Express_Nodejs"),
        ),
    ),
    Topic(
        "rest_api_design", "REST API Design",
        "Designing clean HTTP APIs: resources, URLs, methods, status codes, request validation and "
        "consistent error responses.",
        3,
        (
            article("Microsoft: Web API design best practices", "https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design"),
            docs("MDN: HTTP request methods", "https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods"),
            video("RESTful APIs in 100 Seconds", "https://www.youtube.com/watch?v=-MTSQjw5DrM"),
        ),
    ),
    Topic(
        "authentication_basics", "Authentication Basics",
        "Securing apps: password hashing, sessions versus tokens, JWTs, protecting routes and common "
        "security pitfalls.",
        4,
        (
            article("OWASP: Authentication Cheat Sheet", "https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html"),
            article("OWASP: Password Storage Cheat Sheet", "https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html"),
            article("Introduction to JSON Web Tokens", "https://www.jwt.io/introduction"),
        ),
    ),
    # --- Databases ---------------------------------------------------------------
    Topic(
        "sql_basics", "SQL Basics",
        "Querying relational data with SELECT, WHERE, ORDER BY, JOIN and GROUP BY, and changing it "
        "with INSERT, UPDATE and DELETE.",
        2,
        (
            article("SQLBolt: Interactive SQL lessons", "https://sqlbolt.com/"),
            video("SQL Explained in 100 Seconds", "https://www.youtube.com/watch?v=zsjvFFKOm3c"),
        ),
    ),
    Topic(
        "postgresql_basics", "PostgreSQL Basics",
        "Working with PostgreSQL: creating tables, data types, constraints, indexes and connecting "
        "from an application.",
        3,
        (
            docs("PostgreSQL Tutorial (official docs)", "https://www.postgresql.org/docs/current/tutorial.html"),
            article("PostgreSQL Tutorial", "https://neon.com/postgresql/tutorial"),
            video("PostgreSQL in 100 Seconds", "https://www.youtube.com/watch?v=n2Fluyr3lbc"),
        ),
    ),
    # --- React -----------------------------------------------------------------
    Topic(
        "react_fundamentals", "React Fundamentals",
        "Building user interfaces from components with JSX, rendering lists and conditionally "
        "showing content.",
        2,
        (
            docs("React: Quick Start", "https://react.dev/learn"),
            docs("React: Thinking in React", "https://react.dev/learn/thinking-in-react"),
            video("React in 100 Seconds", "https://www.youtube.com/watch?v=Tn6-PIqc4UM"),
        ),
    ),
    Topic(
        "props_state", "Props & State",
        "Passing data into components with props, keeping component memory with state, and lifting "
        "state up to share it.",
        2,
        (
            docs("React: Passing Props to a Component", "https://react.dev/learn/passing-props-to-a-component"),
            docs("React: State, a Component's Memory", "https://react.dev/learn/state-a-components-memory"),
            docs("React: Sharing State Between Components", "https://react.dev/learn/sharing-state-between-components"),
        ),
    ),
    Topic(
        "react_hooks", "React Hooks",
        "Using built-in hooks such as useState, useEffect, useRef, useMemo and useContext, and "
        "writing custom hooks.",
        3,
        (
            docs("React: Built-in Hooks", "https://react.dev/reference/react/hooks"),
            docs("React: Reusing Logic with Custom Hooks", "https://react.dev/learn/reusing-logic-with-custom-hooks"),
            video("10 React Hooks Explained", "https://www.youtube.com/watch?v=TNhaISOUy6Q"),
        ),
    ),
    Topic(
        "react_router", "React Router",
        "Client-side routing in single-page apps: routes, links, URL parameters, nested layouts and "
        "redirects.",
        3,
        (
            docs("React Router documentation", "https://reactrouter.com/home"),
        ),
    ),
    Topic(
        "react_api_integration", "API Integration in React",
        "Fetching data in React apps: loading and error states, effects, cancelling requests and "
        "keeping server data in sync.",
        3,
        (
            docs("React: Synchronizing with Effects", "https://react.dev/learn/synchronizing-with-effects"),
            docs("React: You Might Not Need an Effect", "https://react.dev/learn/you-might-not-need-an-effect"),
            docs("TanStack Query overview", "https://tanstack.com/query/latest/docs/framework/react/overview"),
        ),
    ),
    # --- Shipping --------------------------------------------------------------
    Topic(
        "testing_basics", "Testing Basics",
        "Writing automated tests: unit versus integration tests, assertions, mocking, and testing UI "
        "components the way users use them.",
        4,
        (
            docs("Vitest: Getting Started", "https://vitest.dev/guide/"),
            docs("React Testing Library: Introduction", "https://testing-library.com/docs/react-testing-library/intro/"),
            docs("Jest: Getting Started", "https://jestjs.io/docs/getting-started"),
        ),
    ),
    Topic(
        "deployment_basics", "Deployment Basics",
        "Shipping apps to production: builds, environment variables, hosting frontends and APIs, "
        "managed databases and HTTPS.",
        4,
        (
            docs("MDN: Publishing your website", "https://developer.mozilla.org/en-US/docs/Learn_web_development/Getting_started/Your_first_website/Publishing_your_website"),
            docs("Vercel: Getting started", "https://vercel.com/docs/getting-started-with-vercel"),
            docs("Railway documentation", "https://docs.railway.com/"),
        ),
    ),
)

# (prerequisite, dependent): the left topic must be completed before the right one unlocks.
PREREQUISITES: tuple[tuple[str, str], ...] = (
    ("html_basics", "semantic_html"),
    ("semantic_html", "forms_accessibility"),
    ("html_basics", "css_basics"),
    ("css_basics", "flexbox"),
    ("css_basics", "css_grid"),
    ("flexbox", "responsive_design"),
    ("css_grid", "responsive_design"),

    ("javascript_fundamentals", "functions_scope"),
    ("javascript_fundamentals", "arrays_objects"),
    ("functions_scope", "dom_manipulation"),
    ("arrays_objects", "dom_manipulation"),
    ("dom_manipulation", "browser_events"),
    ("functions_scope", "async_javascript"),
    ("async_javascript", "fetch_http_apis"),
    ("javascript_fundamentals", "es_modules"),

    ("git_basics", "nodejs_basics"),
    ("javascript_fundamentals", "nodejs_basics"),
    ("nodejs_basics", "npm_packages"),
    ("npm_packages", "express_basics"),
    ("express_basics", "rest_api_design"),
    ("rest_api_design", "authentication_basics"),

    ("sql_basics", "postgresql_basics"),
    ("rest_api_design", "postgresql_basics"),

    ("javascript_fundamentals", "react_fundamentals"),
    ("html_basics", "react_fundamentals"),
    ("css_basics", "react_fundamentals"),
    ("react_fundamentals", "props_state"),
    ("props_state", "react_hooks"),
    ("react_hooks", "react_router"),
    ("fetch_http_apis", "react_api_integration"),
    ("react_hooks", "react_api_integration"),
    ("react_router", "react_api_integration"),

    ("rest_api_design", "testing_basics"),
    ("react_api_integration", "testing_basics"),
    ("postgresql_basics", "testing_basics"),

    ("testing_basics", "deployment_basics"),
    ("authentication_basics", "deployment_basics"),
)

WEB_DEVELOPMENT = Domain(
    id="web-development",
    name="Web Development",
    description=(
        "Building websites and web apps: HTML and CSS, JavaScript and React on the front end, "
        "Node.js, APIs and databases on the back end, then testing and shipping."
    ),
    topics=TOPICS,
    prerequisites=PREREQUISITES,
    shared=("git_basics",),
)
