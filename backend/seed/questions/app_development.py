"""Curated fallback questions for App Development. Code is Markdown."""

from seed.questions import Bank, q

QUESTIONS: Bank = {
    # --- Platforms and languages ----------------------------------------------------------------
    "app_mobile_landscape": [
        q("What is a cross-platform framework such as Flutter or React Native for?",
          "Building Android and iOS apps from one code base",
          ("Running Android apps inside a web browser", "Converting iOS apps into desktop programs",
           "Hosting an app's server in the cloud"),
          "Cross-platform frameworks let one team share most code between platforms, instead of writing "
          "separate Kotlin and Swift apps."),
        q("Which languages are used to build native apps for Android and iOS today?",
          "Kotlin for Android and Swift for iOS", ("Swift for Android and Kotlin for iOS", "Python for both platforms",
                                                   "HTML for Android and CSS for iOS"),
          "Google recommends Kotlin for Android and Apple's Swift is the main language for iOS. Java and "
          "Objective-C are older options."),
        q("What does it mean that mobile apps are sandboxed?",
          "Each app is kept apart from other apps' data unless allowed",
          ("Apps can only run while connected to Wi-Fi", "Apps are tested in a simulator before release",
           "Every app shares one storage area on the device"),
          "The operating system isolates each app's files and memory. Reaching other data, such as photos or "
          "contacts, needs the user's permission."),
    ],
    "app_mobile_ux": [
        q("Why should buttons in a mobile app be at least about 44-48 points (dp) across?",
          "So they are easy to tap accurately with a finger", ("So the app loads faster", "So the app passes store review",
                                                               "So the text inside fits on one line"),
          "Apple recommends at least 44×44 points and Material Design 48×48 dp, roughly the size of a "
          "fingertip, to avoid mis-taps."),
        q("Why do Android and iOS apps often look slightly different even when they do the same thing?",
          "Each platform has its own design conventions users expect",
          ("Android screens can't display the same colours", "iOS apps aren't allowed to use buttons",
           "Android apps must use only text, not icons"),
          "Following Apple's Human Interface Guidelines and Material Design makes an app feel familiar to "
          "users of each platform."),
        q("What makes an app more usable with a screen reader such as TalkBack or VoiceOver?",
          "Giving icons and images meaningful text labels", ("Using smaller fonts to fit more on screen",
                                                             "Replacing all text with icons",
                                                             "Turning off animations on every screen"),
          "Screen readers read out labels. An icon button without a content description is announced only as "
          "\"button\"."),
    ],
    "app_kotlin_basics": [
        q("In Kotlin, what is the difference between `val` and `var`?",
          "A `val` can't be reassigned; a `var` can", ("A `val` is a number; a `var` is text", "A `var` can't be reassigned; a `val` can",
                                                       "There is no difference between them"),
          "`val` declares a read-only reference and `var` a mutable one. Prefer `val` unless the value must "
          "change."),
        q("If `name` is a `String?` that is null, what does `name?.length ?: 0` give?", "`0`",
          ("`null`", "It throws a NullPointerException", "`-1`"),
          "`?.` returns null instead of calling `length` on null, and the Elvis operator `?:` then supplies "
          "the default `0`."),
        q("What does marking a class with `data` give you in Kotlin?",
          "Generated `equals`, `hashCode`, `toString` and `copy`",
          ("A class that stores its data in a database", "A class whose fields can never be null",
           "Automatic saving of the object to a file"),
          "Data classes are for holding values: the compiler writes the boilerplate methods from the "
          "primary constructor's properties."),
    ],
    "app_swift_basics": [
        q("In Swift, what does a `?` after a type, as in `String?`, mean?",
          "The value may be a string or nil", ("The value is a string that can't change",
                                               "The value is checked at compile time", "The value is a list of strings"),
          "An optional either holds a value or is `nil`. Swift makes you unwrap it before use, which prevents "
          "many crashes."),
        q("What is the main difference between a struct and a class in Swift?",
          "Structs are copied when assigned; classes are shared references",
          ("Structs can have methods and initialisers, but classes can't", "Classes can't have properties",
           "Structs are only allowed in SwiftUI"),
          "Assigning a struct makes an independent copy. Assigning a class instance makes another reference "
          "to the same object."),
        q("What does `guard let user = user else { return }` do?",
          "Exits early if `user` is nil, otherwise unwraps it", ("Creates a new user if one is missing",
                                                                 "Crashes the app if `user` is nil",
                                                                 "Makes `user` impossible to change"),
          "`guard let` unwraps an optional for the rest of the scope, or runs the `else` block, which must "
          "leave the scope."),
    ],
    "app_android_compose": [
        q("What marks a Kotlin function as a piece of Jetpack Compose UI?", "The `@Composable` annotation",
          ("The `@Override` annotation", "Returning a `View` object", "Naming it with a `UI` prefix"),
          "Composable functions describe UI. Compose calls them again (recomposes) when the state they read "
          "changes."),
        q("What does `var count by remember { mutableStateOf(0) }` give a composable?",
          "State that survives recomposition and updates the UI when it changes",
          ("A value saved permanently to the device", "A constant that can never change",
           "A variable shared by every app on the phone"),
          "`mutableStateOf` makes Compose track the value, and `remember` keeps it across recompositions. "
          "Use `rememberSaveable` to survive rotation too."),
        q("Which composable arranges its children one above another?", "`Column`",
          ("`Row`", "`Box`", "`Spacer`"),
          "`Column` places children vertically, `Row` horizontally, and `Box` stacks them on top of each "
          "other."),
    ],
    "app_swiftui": [
        q("What does `@State private var count = 0` do in a SwiftUI view?",
          "Stores a value the view owns and redraws when it changes", ("Saves the value to the device's storage",
                                                                       "Makes the value readable by other apps",
                                                                       "Declares a value that can never change"),
          "SwiftUI watches `@State` properties and recomputes the view's `body` whenever one changes."),
        q("What does `$count` pass to a child view such as `Toggle` or `TextField`?",
          "A binding that lets the child read and change the value", ("A read-only copy of the value at that moment in time",
                                                                       "The value converted into text",
                                                                       "The memory address of the value"),
          "The `$` prefix gives a `Binding`, a two-way connection to the state, so the control can update "
          "it."),
        q("Which SwiftUI container lays out views side by side horizontally?", "`HStack`",
          ("`VStack`", "`ZStack`", "`List`"),
          "`HStack` arranges views horizontally, `VStack` vertically, and `ZStack` overlays them."),
    ],
    "app_react_native": [
        q("In React Native, where must text such as \"Hello\" be placed?", "Inside a `<Text>` component",
          ("Directly inside a `<View>`", "Inside a `<p>` element", "Inside a `<div>` element"),
          "React Native renders native views, not HTML. Strings must be wrapped in `<Text>`, and HTML tags "
          "like `<div>` don't exist."),
        q("What is the default `flexDirection` of a layout in React Native?", "`column`",
          ("`row`", "`row-reverse`", "`grid`"),
          "Unlike CSS on the web, where flex containers default to `row`, React Native lays children out in a "
          "column by default."),
        q("What does Expo add when building a React Native app?",
          "Tools and libraries that make building and testing easier",
          ("A separate language that replaces JavaScript", "A requirement to write native Swift code",
           "A web server that hosts the app's screens"),
          "Expo provides a ready set of native modules, a development app for running code on a phone, and "
          "build services."),
    ],
    "app_flutter": [
        q("In Flutter, what is almost everything on screen built from?", "Widgets",
          ("Activities", "Storyboards", "HTML elements"),
          "Flutter UIs are trees of widgets, from layout such as `Row` and `Column` to text, buttons and "
          "padding."),
        q("When should a Flutter widget be a `StatefulWidget` rather than a `StatelessWidget`?",
          "When it holds data that changes while it is on screen", ("When it is shown on more than one screen",
                                                                    "When it contains more than one child",
                                                                    "When it needs to display an image"),
          "A `StatefulWidget` keeps a `State` object, and calling `setState` tells Flutter to rebuild with "
          "the new data."),
        q("What does hot reload do during Flutter development?",
          "Shows code changes in the running app, usually keeping its state",
          ("Restarts the phone and installs the new code from scratch",
           "Publishes the latest build of the app to both app stores",
           "Clears all of the app's saved data and settings on the device"),
          "Hot reload injects updated code into the running app in about a second, so you can tweak the UI "
          "without losing your place."),
    ],
    "app_pwa": [
        q("What lets a progressive web app work offline?", "A service worker that serves cached files",
          ("A web app manifest file", "A larger browser cache setting", "Installing it from an app store"),
          "A service worker sits between the page and the network and can answer requests from a cache when "
          "there is no connection."),
        q("What is the web app manifest for?",
          "Describing the app's name, icons and how it opens when installed",
          ("Listing every file and folder the web server stores on disk", "Storing the user's login details",
           "Making the site load without JavaScript"),
          "The manifest is a JSON file the browser reads to install the app with the right name, icon, theme "
          "colour and display mode."),
        q("Why must service workers be served over HTTPS (except on localhost)?",
          "They can intercept every request, so they must come from a trusted origin",
          ("HTTPS makes the service worker start and run noticeably faster", "HTTP pages can't store any files at all",
           "Browsers only install apps from app stores"),
          "A service worker controls a site's network traffic, so browsers only register one from a secure "
          "origin to stop it being tampered with."),
    ],
    # --- What every app needs -------------------------------------------------------------------
    "app_navigation": [
        q("In stack navigation, what happens when the user goes back?",
          "The top screen is removed, revealing the one below", ("A new copy of the previous screen is created",
                                                                 "The app returns to the home screen",
                                                                 "Every screen in the stack is closed"),
          "Opening a screen pushes it onto the stack and going back pops it, returning to the previous screen "
          "as it was."),
        q("When is a bottom tab bar the best choice?",
          "Switching between a few top-level sections", ("Showing a long list of settings",
                                                          "Moving through the steps of a form",
                                                          "Showing a single error message"),
          "Tab bars give one-tap access to three to five main sections that users switch between often."),
        q("What is a deep link?", "A link that opens a specific screen inside an app",
          ("A link hidden in the app's source code", "A link to the app's store page",
           "A link that works only on Wi-Fi"),
          "A deep link, such as one in an email or notification, takes the user straight to the relevant "
          "screen instead of the app's home."),
    ],
    "app_lifecycle": [
        q("By default, what happens to an Android activity when the screen is rotated?",
          "It is destroyed and created again", ("It keeps running with no changes", "The whole app is closed",
                                                "The phone restarts the app from the store"),
          "Rotation is a configuration change, so the activity is recreated. State must be kept, for example "
          "in a ViewModel or saved state."),
        q("Why should an app save the user's unsaved work when it moves to the background?",
          "The system may end it later to free memory", ("Background apps lose their internet permission",
                                                         "The app store requires it for every app",
                                                         "Saving makes the app open faster"),
          "Mobile systems can stop background apps at any time. Saving state lets the app restore where the "
          "user left off."),
        q("Which Android API is meant for deferrable work that must eventually run, such as uploading logs?",
          "WorkManager", ("A plain background thread", "A `Toast`", "The activity's `onCreate`"),
          "WorkManager schedules work that survives app restarts and reboots, respecting constraints such as "
          "being on Wi-Fi or charging."),
    ],
    "app_networking": [
        q("What happens if an Android app makes a network request on the main thread?",
          "Android throws an exception to stop the UI freezing", ("The request runs faster than usual",
                                                                  "The request is sent twice for safety",
                                                                  "The app is uninstalled automatically"),
          "Android throws `NetworkOnMainThreadException`, because a slow request on the UI thread would make "
          "the app unresponsive."),
        q("While data is loading from a server, what should a well-built screen show?",
          "A loading indicator, then the data or an error with a retry", ("A blank screen until the data arrives",
                                                                          "Yesterday's date as a placeholder",
                                                                          "A message asking the user to restart"),
          "Showing loading, success and error states tells users what is happening and lets them recover "
          "from failures."),
        q("Why should mobile apps set timeouts on network requests?",
          "Phone connections can stall, and the app shouldn't wait forever",
          ("Servers reject requests without a timeout", "Timeouts make downloads smaller",
           "Timeouts are needed to use HTTPS"),
          "Mobile networks drop and slow down often. A timeout lets the app show an error or retry instead of "
          "hanging."),
    ],
    "app_local_storage": [
        q("What suits key-value storage such as DataStore or `UserDefaults` best?",
          "Small settings like the chosen theme", ("Thousands of chat messages", "Large photos and videos",
                                                   "Data shared with other apps"),
          "Key-value stores are for small, simple values. Structured or large data belongs in a database or "
          "in files."),
        q("What is Room on Android?", "A library that makes working with SQLite easier",
          ("A cloud database run by Google", "A tool for designing app screens", "A way to share files between apps"),
          "Room maps Kotlin classes to SQLite tables, checks queries at compile time, and works with "
          "coroutines and Flow."),
        q("What does an offline-first app do?",
          "Reads from local data first and syncs with the server when it can",
          ("Refuses to start without an internet connection", "Stores nothing on the device at all",
           "Downloads the whole server database every time"),
          "Treating the local database as the source of truth keeps the app usable offline. Changes sync "
          "later."),
    ],
    "app_permissions_privacy": [
        q("When is the best time to ask for camera permission?",
          "When the user taps the feature that needs the camera", ("As soon as the app is installed",
                                                                    "Before the user creates an account",
                                                                    "Every time the app is opened"),
          "Asking in context explains why the permission is needed, so users are more likely to agree and "
          "trust the app."),
        q("What should an app do if the user refuses location permission?",
          "Keep working, with that feature limited or explained", ("Close immediately and show an error message to the user",
                                                                    "Ask again every few seconds",
                                                                    "Use the location without asking"),
          "Apps should degrade gracefully, for example letting users type a city, and explain how to grant "
          "access later in Settings."),
        q("On iOS, what must an app include before it asks for camera access?",
          "A usage description explaining why it needs the camera", ("A paid developer certificate for cameras",
                                                                       "A separate camera app on the device",
                                                                       "The user's email address"),
          "The `NSCameraUsageDescription` text in Info.plist is shown in the permission prompt. Without it, "
          "the app is stopped when it asks."),
    ],
    "app_architecture": [
        q("Why keep screen state in an Android ViewModel?",
          "It survives configuration changes such as rotation", ("It saves the state to the cloud automatically",
                                                                 "It makes the screen draw twice as fast",
                                                                 "It lets other apps read the state"),
          "A ViewModel outlives the activity being recreated, so data isn't lost or reloaded on rotation."),
        q("In unidirectional data flow, how do state and events move?",
          "State flows down to the UI; events flow up from it",
          ("Events flow down to the UI; state flows up", "The UI edits the database directly",
           "Every screen keeps its own copy of the data"),
          "The UI displays state and sends user events to a state holder, which updates the state. One "
          "direction makes changes easy to follow."),
        q("Why separate an app's UI layer from its data layer?",
          "Each can be changed and tested without breaking the other",
          ("It is required for the app to compile", "It makes the app's download smaller",
           "It stops the app from needing a network"),
          "Keeping data fetching and storage out of screens means the UI can change freely and the data code "
          "can be tested on its own."),
    ],
    "app_notifications": [
        q("How does a server send a push notification to an Android phone?",
          "Through Firebase Cloud Messaging, using the device's token",
          ("By connecting directly to the phone's IP address", "By sending an SMS message to the phone",
           "By asking the user's mobile carrier"),
          "The app registers and gets a token. The server sends the message to FCM (or APNs on iOS), which "
          "delivers it to the device."),
        q("On Android 13 and later, what must an app have before it can show notifications?",
          "The user's runtime permission", ("A paid Google developer account", "An open network connection",
                                            "Permission from the mobile carrier"),
          "Since Android 13, `POST_NOTIFICATIONS` is a runtime permission, as on iOS, where apps must also "
          "ask."),
        q("Why should apps avoid sending too many push notifications?",
          "Users may turn them off or uninstall the app", ("Each notification costs the user money",
                                                           "Phones can only hold ten notifications",
                                                           "The app store limits them to one a day"),
          "Notifications interrupt people. Sending only timely, relevant ones keeps users willing to receive "
          "them."),
    ],
    "app_testing": [
        q("Why do teams write many more unit tests than full UI tests?",
          "Unit tests are faster and more reliable to run", ("UI tests can't run on emulators",
                                                             "Unit tests test the whole app at once",
                                                             "App stores reject apps with UI tests"),
          "Following the testing pyramid: many quick unit tests, fewer integration tests, and a small number "
          "of slower end-to-end UI tests."),
        q("Which tool is used for automated UI tests of native Android apps?", "Espresso",
          ("XCTest", "pytest", "Selenium IDE"),
          "Espresso drives Android UI in instrumented tests (Compose has its own test APIs). XCTest is "
          "Apple's equivalent for iOS."),
        q("Why test on real devices as well as emulators and simulators?",
          "Real hardware can differ in performance, sensors and screen sizes",
          ("Emulators can't run any tests at all", "App stores require photos of real devices",
           "Real devices run tests without code"),
          "Emulators are fast for everyday testing, but issues with memory, cameras or specific models only "
          "show up on real hardware."),
    ],
    "app_performance": [
        q("At 60 frames per second, roughly how long does the app have to draw each frame?",
          "About 16 milliseconds", ("About 1 second", "About 100 milliseconds", "About 1 millisecond"),
          "1000 ms / 60 ≈ 16.7 ms. Work that takes longer on the main thread causes dropped frames, felt as "
          "jank."),
        q("Why use a lazy list such as `LazyColumn`, `RecyclerView` or SwiftUI's `List` for long lists?",
          "It only creates the items currently on screen", ("It loads every item before showing any",
                                                            "It stores the list in the cloud",
                                                            "It makes each item's text smaller"),
          "Lazy lists create and recycle views as you scroll, so memory and start-up time don't grow with "
          "the list's length."),
        q("What usually drains a phone's battery fastest in an app?",
          "Frequent network, GPS or background work", ("Using dark colours in the UI", "Having many screens",
                                                       "Showing text in bold"),
          "Radios, location and waking the device are costly. Batching requests and deferring background "
          "work saves battery."),
    ],
    "app_security": [
        q("Why shouldn't a secret API key be built into a mobile app?",
          "Anyone can extract it from the installed app", ("It makes the app too large to install",
                                                           "Phones can't send API keys over HTTPS",
                                                           "App stores delete keys automatically"),
          "App packages can be unpacked and inspected. Secrets belong on a server, which the app calls with "
          "the user's own credentials."),
        q("Where should an app store a user's login token on iOS?", "In the Keychain",
          ("In a plain text file", "In `UserDefaults`", "In the app's source code"),
          "The Keychain encrypts its contents and is protected by the device. On Android, the Keystore plays "
          "a similar role."),
        q("A developer turns off HTTPS certificate checking to get past an error. What is the risk?",
          "Attackers on the network could read or change the app's traffic",
          ("The app will use more battery than before", "The server will refuse every request",
           "The app will fail its next update"),
          "Certificate validation proves the app is talking to the real server. Without it, a man-in-the-"
          "middle can intercept data."),
    ],
    "app_publishing": [
        q("What must happen to each new Android build uploaded to Google Play?",
          "Its `versionCode` must be higher than the last one", ("Its app name must change each time",
                                                                 "It must be signed with a new key every time",
                                                                 "It must be smaller than the last version"),
          "Play uses the integer `versionCode` to order releases. Updates must also be signed with the same "
          "app signing key."),
        q("What is TestFlight used for?", "Sending beta builds of an iOS app to testers",
          ("Measuring an app's flight-mode battery use", "Designing an app's store screenshots",
           "Testing websites in the Safari browser"),
          "TestFlight lets developers invite testers to install pre-release builds and send feedback before "
          "the App Store release."),
        q("What is a staged rollout?", "Releasing an update to a percentage of users first",
          ("Publishing the app in one country only, forever", "Releasing all features in one update",
           "Asking users to vote on each new version"),
          "Starting with a small share of users lets the team watch for crashes and halt the release before "
          "it reaches everyone."),
    ],
}
