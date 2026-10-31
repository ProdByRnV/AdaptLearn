"""App Development: building mobile apps, natively for Android and iOS or across platforms.

How Mobile Apps Work is the starting topic. Learners can follow one platform (Kotlin, Swift, React
Native, Flutter or a progressive web app) and then the topics every app needs. The rest builds on
Foundations and, for React Native and PWAs, on Web Development.
"""

from seed.model import Domain, Topic, article, docs, video

TOPICS: tuple[Topic, ...] = (
    # --- Platforms and languages ----------------------------------------------------------------
    Topic(
        "app_mobile_landscape", "How Mobile Apps Work",
        "The mobile app world: Android and iOS, native versus cross-platform versus web apps, how an "
        "app is built, installed and sandboxed, and how app stores distribute it.",
        1,
        (
            docs("Android Developers: Application fundamentals", "https://developer.android.com/guide/components/fundamentals"),
            article("AWS: What is mobile application development?", "https://aws.amazon.com/mobile/mobile-application-development/"),
            docs("Apple: Develop apps for Apple platforms", "https://developer.apple.com/tutorials/app-dev-training"),
        ),
    ),
    Topic(
        "app_mobile_ux", "Designing for Mobile",
        "Designing for small touch screens: thumb-sized touch targets, one main task per screen, "
        "platform conventions from Apple's guidelines and Material Design, and accessible apps.",
        2,
        (
            docs("Apple Human Interface Guidelines", "https://developer.apple.com/design/human-interface-guidelines"),
            docs("Material Design 3", "https://m3.material.io/"),
            article("NN/g: Mobile user experience", "https://www.nngroup.com/articles/mobile-ux/"),
        ),
    ),
    Topic(
        "app_kotlin_basics", "Kotlin Basics",
        "The language of modern Android: val and var, type inference, null safety with ? and ?:, "
        "functions and lambdas, data classes, and when expressions.",
        2,
        (
            video("Kotlin in 100 Seconds (Fireship)", "https://www.youtube.com/watch?v=xT8oP0wy-A0"),
            docs("Kotlin docs: Tour of Kotlin", "https://kotlinlang.org/docs/kotlin-tour-welcome.html"),
            docs("Kotlin docs: Basic syntax", "https://kotlinlang.org/docs/basic-syntax.html"),
        ),
    ),
    Topic(
        "app_swift_basics", "Swift Basics",
        "The language of Apple platforms: let and var, optionals and unwrapping, structs and classes, "
        "enums with associated values, closures, and protocols.",
        2,
        (
            video("Swift in 100 Seconds (Fireship)", "https://www.youtube.com/watch?v=nAchMctX4YA"),
            docs("The Swift Programming Language: A Swift tour", "https://docs.swift.org/latest/documentation/the-swift-programming-language/guidedtour/"),
            docs("Swift.org: Getting started", "https://www.swift.org/getting-started/"),
        ),
    ),
    Topic(
        "app_android_compose", "Android with Jetpack Compose",
        "Building Android screens in Kotlin: composable functions, layouts with Column and Row, state "
        "that redraws the UI when it changes, and Android Studio previews.",
        3,
        (
            docs("Android Developers: Compose tutorial", "https://developer.android.com/develop/ui/compose/tutorial"),
            docs("Android Developers: State and Jetpack Compose", "https://developer.android.com/develop/ui/compose/state"),
            docs("Android Basics with Compose course", "https://developer.android.com/courses/android-basics-compose/course"),
        ),
    ),
    Topic(
        "app_swiftui", "iOS with SwiftUI",
        "Building iOS screens in Swift: views as structs, stacks and modifiers, @State and bindings "
        "that keep the UI in step with data, and Xcode previews.",
        3,
        (
            docs("Apple: Introducing SwiftUI", "https://developer.apple.com/tutorials/swiftui"),
            docs("Apple: SwiftUI documentation", "https://developer.apple.com/documentation/swiftui"),
            article("Hacking with Swift: 100 Days of SwiftUI", "https://www.hackingwithswift.com/100/swiftui"),
        ),
    ),
    Topic(
        "app_react_native", "React Native",
        "One JavaScript code base for Android and iOS: React components that render native views, "
        "core components such as View and Text, styling, and getting started with Expo.",
        3,
        (
            video("React Native in 100 Seconds (Fireship)", "https://www.youtube.com/watch?v=gvkqT_Uoahw"),
            docs("React Native docs: Introduction", "https://reactnative.dev/docs/getting-started"),
            docs("Expo documentation", "https://docs.expo.dev/"),
        ),
    ),
    Topic(
        "app_flutter", "Flutter & Dart",
        "Google's cross-platform toolkit: the Dart language, everything as a widget, stateless and "
        "stateful widgets, hot reload, and one code base drawn the same on every platform.",
        3,
        (
            video("Flutter in 100 Seconds (Fireship)", "https://www.youtube.com/watch?v=lHhRhPV--G0"),
            docs("Flutter learning pathway", "https://docs.flutter.dev/learn/pathway"),
            docs("Dart: Introduction to Dart", "https://dart.dev/language"),
        ),
    ),
    Topic(
        "app_pwa", "Progressive Web Apps",
        "Web apps that install like native ones: the web app manifest, service workers for offline "
        "use and caching, installability, and what PWAs can and can't do on each platform.",
        3,
        (
            docs("web.dev: Learn PWA", "https://web.dev/learn/pwa"),
            docs("MDN: Progressive web apps", "https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps"),
            docs("MDN: Service Worker API", "https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API"),
        ),
    ),
    # --- What every app needs -------------------------------------------------------------------
    Topic(
        "app_navigation", "Screens & Navigation",
        "Moving between screens: stack navigation and the back button, tab bars and navigation bars, "
        "passing data to a screen, and deep links that open a specific screen.",
        3,
        (
            docs("Android Developers: Navigation", "https://developer.android.com/guide/navigation"),
            docs("React Navigation: Getting started", "https://reactnavigation.org/docs/getting-started"),
            docs("Apple HIG: Tab bars", "https://developer.apple.com/design/human-interface-guidelines/tab-bars"),
        ),
    ),
    Topic(
        "app_lifecycle", "App Lifecycle & Background Work",
        "What happens when users switch away: foreground and background states, the system ending "
        "apps to free memory, saving and restoring state, and limits on background work.",
        3,
        (
            docs("Android Developers: The activity lifecycle", "https://developer.android.com/guide/components/activities/activity-lifecycle"),
            docs("Apple: Managing your app's life cycle", "https://developer.apple.com/documentation/uikit/managing-your-app-s-life-cycle"),
            docs("Android Developers: Background tasks overview", "https://developer.android.com/develop/background-work/background-tasks"),
        ),
    ),
    Topic(
        "app_networking", "Networking & APIs in Apps",
        "Talking to servers from an app: HTTP requests off the main thread, parsing JSON, loading and "
        "error states, slow or missing connections, and timeouts and retries.",
        3,
        (
            docs("Android Developers: Connect to the network", "https://developer.android.com/develop/connectivity/network-ops/connecting"),
            docs("Flutter cookbook: Fetch data from the internet", "https://docs.flutter.dev/cookbook/networking/fetch-data"),
            docs("React Native docs: Networking", "https://reactnative.dev/docs/network"),
        ),
    ),
    Topic(
        "app_local_storage", "Local Storage & Offline Data",
        "Keeping data on the device: small settings in key-value storage, structured data in SQLite "
        "through Room or SwiftData, files, and offline-first apps that sync later.",
        3,
        (
            docs("Android Developers: Data and file storage overview", "https://developer.android.com/training/data-storage"),
            docs("Android Developers: Save data with Room", "https://developer.android.com/training/data-storage/room"),
            docs("Android Developers: Build an offline-first app", "https://developer.android.com/topic/architecture/data-layer/offline-first"),
        ),
    ),
    Topic(
        "app_permissions_privacy", "Permissions & Privacy",
        "Respecting users' data: runtime permissions for the camera, location and contacts, asking at "
        "the moment they're needed, coping with a refusal, and app store privacy labels.",
        3,
        (
            docs("Android Developers: Permissions on Android", "https://developer.android.com/guide/topics/permissions/overview"),
            docs("Apple: Requesting access to protected resources", "https://developer.apple.com/documentation/uikit/requesting-access-to-protected-resources"),
            docs("Apple: App privacy details", "https://developer.apple.com/app-store/app-privacy-details/"),
        ),
    ),
    Topic(
        "app_architecture", "State & App Architecture",
        "Structuring an app so it stays manageable: separate UI and data layers, view models that "
        "survive screen rotation, unidirectional data flow, and a single source of truth.",
        4,
        (
            docs("Android Developers: Guide to app architecture", "https://developer.android.com/topic/architecture"),
            docs("Android Developers: ViewModel overview", "https://developer.android.com/topic/libraries/architecture/viewmodel"),
            docs("Flutter: Architecting Flutter apps", "https://docs.flutter.dev/app-architecture"),
        ),
    ),
    Topic(
        "app_notifications", "Push Notifications",
        "Reaching users when the app is closed: device tokens, push services such as FCM and APNs, "
        "asking permission, notification channels, and not overwhelming people.",
        4,
        (
            docs("Firebase Cloud Messaging", "https://firebase.google.com/docs/cloud-messaging"),
            docs("Apple: User Notifications", "https://developer.apple.com/documentation/usernotifications"),
            docs("Android Developers: About notifications", "https://developer.android.com/develop/ui/views/notifications"),
        ),
    ),
    Topic(
        "app_testing", "Testing Mobile Apps",
        "Checking an app works on many devices: unit tests, UI tests with Espresso, XCTest or Flutter "
        "widget tests, emulators and simulators versus real devices, and screen-size coverage.",
        4,
        (
            docs("Android Developers: Fundamentals of testing", "https://developer.android.com/training/testing/fundamentals"),
            docs("Apple: XCTest", "https://developer.apple.com/documentation/xctest"),
            docs("Flutter: Testing Flutter apps", "https://docs.flutter.dev/testing/overview"),
        ),
    ),
    Topic(
        "app_performance", "Performance & Battery",
        "Keeping apps fast and light: fast start-up, smooth scrolling without dropped frames, keeping "
        "work off the main thread, image and memory use, and saving battery and data.",
        4,
        (
            docs("Android Developers: App performance guide", "https://developer.android.com/topic/performance/overview"),
            docs("Apple: Improving app responsiveness", "https://developer.apple.com/documentation/xcode/improving-app-responsiveness"),
            docs("Flutter: Performance", "https://docs.flutter.dev/perf"),
        ),
    ),
    Topic(
        "app_security", "Mobile App Security",
        "Protecting users and their data: secrets in the Keychain or Keystore, HTTPS with proper "
        "certificate checks, never shipping API keys in the app, and the OWASP MASVS checklist.",
        4,
        (
            docs("OWASP MASVS", "https://mas.owasp.org/MASVS/"),
            docs("Android Developers: Security checklist", "https://developer.android.com/privacy-and-security/security-tips"),
            docs("Apple: Keychain services", "https://developer.apple.com/documentation/security/keychain-services"),
        ),
    ),
    Topic(
        "app_publishing", "Publishing to App Stores",
        "Shipping to users: signing builds, version numbers, beta testing with TestFlight and Play "
        "testing tracks, store listings and review guidelines, and staged rollouts.",
        4,
        (
            docs("Android Developers: Publish your app", "https://developer.android.com/studio/publish"),
            docs("Apple: App Review Guidelines", "https://developer.apple.com/app-store/review/guidelines/"),
            docs("Apple: TestFlight", "https://developer.apple.com/testflight/"),
        ),
    ),
)

PREREQUISITES: tuple[tuple[str, str], ...] = (
    ("app_mobile_landscape", "app_mobile_ux"),
    ("app_mobile_landscape", "app_kotlin_basics"),
    ("programming_concepts", "app_kotlin_basics"),
    ("app_mobile_landscape", "app_swift_basics"),
    ("programming_concepts", "app_swift_basics"),
    ("app_kotlin_basics", "app_android_compose"),
    ("app_swift_basics", "app_swiftui"),
    ("app_mobile_landscape", "app_react_native"),
    ("react_fundamentals", "app_react_native"),
    ("app_mobile_landscape", "app_flutter"),
    ("programming_concepts", "app_flutter"),
    ("app_mobile_landscape", "app_pwa"),
    ("responsive_design", "app_pwa"),
    ("async_javascript", "app_pwa"),

    ("app_mobile_ux", "app_navigation"),
    ("app_mobile_landscape", "app_lifecycle"),
    ("operating_system_basics", "app_lifecycle"),
    ("app_mobile_landscape", "app_networking"),
    ("how_the_internet_works", "app_networking"),
    ("data_formats", "app_networking"),
    ("app_mobile_landscape", "app_local_storage"),
    ("sql_basics", "app_local_storage"),
    ("app_mobile_landscape", "app_permissions_privacy"),
    ("security_basics", "app_permissions_privacy"),
    ("app_navigation", "app_architecture"),
    ("app_networking", "app_architecture"),
    ("app_local_storage", "app_architecture"),
    ("app_networking", "app_notifications"),
    ("app_permissions_privacy", "app_notifications"),
    ("app_architecture", "app_testing"),
    ("app_lifecycle", "app_performance"),
    ("app_networking", "app_performance"),
    ("app_local_storage", "app_security"),
    ("app_networking", "app_security"),
    ("app_permissions_privacy", "app_security"),
    ("app_testing", "app_publishing"),
)

APP_DEVELOPMENT = Domain(
    id="app-development",
    name="App Development",
    description=(
        "Building mobile apps: native Android with Kotlin and iOS with Swift, cross-platform with React "
        "Native and Flutter, progressive web apps, and what every app needs from networking and storage "
        "to testing and publishing."
    ),
    topics=TOPICS,
    prerequisites=PREREQUISITES,
)
