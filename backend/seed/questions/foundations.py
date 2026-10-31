"""Curated fallback questions for Foundations."""

from seed.questions import Bank, q

QUESTIONS: Bank = {
    # --- Computers and data ------------------------------------------------------------
    "how_computers_work": [
        q("What happens to the contents of RAM when a computer is switched off?",
          "They are lost, because RAM is volatile",
          ("They are saved automatically to the hard drive", "They stay in RAM until the next start-up",
           "They are moved into the CPU's cache"),
          "RAM needs power to hold data, so it is cleared when the computer turns off. Anything that must "
          "survive has to be saved to storage such as an SSD."),
        q("In the fetch-decode-execute cycle, what does the CPU do first?",
          "Fetches the next instruction from memory",
          ("Decodes the instruction into control signals", "Writes the last result back to storage",
           "Asks the operating system which program to run"),
          "Each cycle starts by fetching the instruction at the address in the program counter; the CPU "
          "then decodes it and executes it, and the cycle repeats."),
        q("An SSD and RAM both hold data. What is the key difference?",
          "The SSD keeps data without power; RAM is faster but loses it",
          ("RAM keeps data without power; the SSD loses it when switched off",
           "The SSD runs programs; RAM only stores photos and documents",
           "They are the same hardware, just sold under different names"),
          "Storage such as an SSD is non-volatile and keeps files when the power is off. RAM is much faster, "
          "which is why programs are loaded into it to run, but it is cleared without power."),
    ],
    "binary_data_representation": [
        q("What is the binary number 1011 in decimal?", "11", ("13", "9", "10"),
          "From the right, the bits are worth 1, 2, 4 and 8. 1011 has the 8, 2 and 1 bits set: 8 + 2 + 1 = 11."),
        q("How many different values can one byte (8 bits) represent?", "256", ("255", "8", "128"),
          "Each bit doubles the number of combinations, so 8 bits give 2 to the power 8 = 256 values, "
          "usually 0 to 255. 255 is the largest value, not the number of values."),
        q("What does UTF-8 do?", "Encodes Unicode characters as one to four bytes each",
          ("Compresses text files to save space on the disk", "Limits text to the 128 characters of ASCII",
           "Stores every character in exactly eight bits"),
          "UTF-8 can encode every Unicode character, using 1 byte for ASCII characters and up to 4 bytes for "
          "others, such as emoji. The 8 refers to its 8-bit units, not a fixed size per character."),
    ],
    "data_formats": [
        q("Which of these is valid JSON?", '{"name": "Ada", "age": 36}',
          ("{'name': 'Ada', 'age': 36}", '{name: "Ada", age: 36}', '{"name": "Ada", "age": 36,}'),
          "JSON requires double quotes around keys and strings and allows no trailing comma. Single quotes "
          "and unquoted keys are fine in JavaScript or Python code but not in JSON."),
        q("In a CSV file, how is a field written when it contains a comma?", "Wrapped in double quotes",
          ("Preceded by a backslash", "Moved onto a separate line", "Commas are not allowed in fields"),
          'The CSV format (RFC 4180) puts such a field in double quotes, e.g. "Smith, Jane". A double quote '
          "inside a quoted field is written twice."),
        q("In YAML's usual block style, what shows which keys belong inside a section?", "Indentation with spaces",
          ("Indentation with tab characters", "Curly braces around every section", "Semicolons at the end of each line"),
          "Block-style YAML nests keys by indenting them with spaces under their parent. Tabs are not allowed "
          "for indentation."),
    ],
    # --- Programming groundwork --------------------------------------------------------
    "programming_concepts": [
        q("A program sets x to 5, then sets x to x + 3. What is the value of x now?", "8",
          ("5", "3", "x + 3"),
          "The right-hand side is worked out first using the current value (5 + 3), and the result, 8, "
          "replaces the old value of x."),
        q("Which construct repeats a block of code while a condition stays true?", "A loop",
          ("A variable", "A comment", "A conditional (if) statement"),
          "A loop runs its body again and again while its condition holds. An if statement chooses whether "
          "a block runs once."),
        q("Why put steps that are used in several places into a function?",
          "To reuse them by name instead of copying the same code",
          ("To make the program run the steps in parallel", "Because code outside functions cannot use variables",
           "To stop the steps from ever being changed later"),
          "A function gives a group of steps a name, so they are written once and called wherever they are "
          "needed. Fixing them then fixes every use."),
    ],
    "algorithmic_thinking": [
        q("What must be true of a list before binary search can be used on it?", "It must be sorted",
          ("It must contain no duplicates", "It must have an even number of items", "It must hold numbers, not text"),
          "Binary search compares with the middle item and throws away the half that can't contain the "
          "target. That only works when the items are in order."),
        q("Binary search on a sorted list of 1,000 items needs at most about how many comparisons?", "10",
          ("500", "100", "1,000"),
          "Each comparison halves what is left: 1,000, 500, 250 and so on reach a single item after about 10 "
          "halvings, since 2 to the power 10 is 1,024. A linear search may need all 1,000."),
        q("What is decomposition in problem solving?",
          "Breaking a problem into smaller parts that are easier to solve",
          ("Removing details that do not matter to the problem", "Spotting similarities between different problems",
           "Writing the finished solution in a programming language"),
          "Decomposition splits a problem into sub-problems. Removing unneeded detail is abstraction, and "
          "spotting similarities is pattern recognition."),
    ],
    # --- Working with a computer -------------------------------------------------------
    "command_line_basics": [
        q("Which command prints the folder you are currently in on Linux or macOS?", "pwd",
          ("cd", "ls", "whereami"),
          "pwd (print working directory) shows the current folder; cd changes folder and ls lists what is in it."),
        q("What does cd .. do?", "Moves up to the parent folder",
          ("Lists hidden files", "Deletes the current folder", "Returns to your home folder"),
          ".. means the parent directory, so cd .. goes one level up. cd on its own (or cd ~) goes to the home "
          "folder."),
        q("What does the -r option add to rm -r old_project?", "It removes the folder and everything inside it",
          ("It asks for confirmation before each file", "It moves the folder to the recycle bin",
           "It renames the folder"),
          "-r (recursive) lets rm delete a directory with all of its contents. Deleted files don't go to a "
          "recycle bin, which is why -i (confirm each file) exists."),
    ],
    "operating_system_basics": [
        q("A file's permissions are -rwxr-xr--. What may users who are neither its owner nor in its group do?",
          "Read it only", ("Read and run it", "Read, change and run it", "Nothing at all"),
          "After the file-type character come three groups of three: owner (rwx), group (r-x) and others "
          "(r--). Others have read permission only."),
        q("What is a process?", "A program that is currently running, with its own memory",
          ("A program's file as it is stored on the disk", "A list of steps written down before coding",
           "A user account that is allowed to install software"),
          "A process is a running instance of a program. The operating system gives each one its own memory "
          "and shares the CPU between them."),
        q("When you type a command such as python, how does the shell find the program to run?",
          "It searches the folders listed in the PATH variable",
          ("It searches every folder on the disk until it finds it", "It downloads the program from the internet",
           "It only looks inside the current folder"),
          "PATH is an environment variable holding a list of folders. The shell looks through them in order "
          "and runs the first matching program."),
    ],
    "git_basics": [
        q("What does git commit do?", "Saves the staged changes as a snapshot in the local repository",
          ("Uploads your latest changes to the remote repository on GitHub",
           "Stages every modified file so it is ready for the next save",
           "Creates a new branch that starts from the current commit"),
          "A commit saves staged changes locally; git push is what sends commits to a remote."),
        q("Which command stages changes for the next commit?", "git add",
          ("git push", "git save", "git stage-commit"),
          "git add moves changes into the staging area so the next commit includes them."),
        q("What does git pull do?", "Fetches a remote's changes and merges them into the current branch",
          ("Sends your local commits to the remote branch it tracks",
           "Discards local changes and resets to the remote's version",
           "Opens a pull request asking others to review your branch"),
          "git pull is git fetch followed by a merge (or rebase) of the remote branch. git push sends commits, "
          "and pull requests are a feature of hosting sites such as GitHub."),
    ],
    # --- Networks and safety -----------------------------------------------------------
    "how_the_internet_works": [
        q("What does DNS do?", "Translates domain names such as example.com into IP addresses",
          ("Encrypts traffic between the browser and the server", "Stores copies of websites",
           "Assigns IP addresses to devices on a home network"),
          "The Domain Name System looks up the IP address behind a name so requests can be sent to it. "
          "Encryption is TLS's job and home-network addresses come from DHCP."),
        q("How is data sent across the internet?",
          "Split into packets that may take different routes and are reassembled",
          ("As one continuous stream over a single dedicated wire", "Beamed directly between computers by satellite",
           "As whole files that every router along the way stores permanently"),
          "The internet is packet-switched: data is broken into packets, routers forward each one towards its "
          "destination, and the receiver puts them back in order."),
        q("When you open a web page, what does your browser send to the web server?",
          "An HTTP request asking for the page, such as GET /index.html",
          ("The page's HTML for the server to check", "A DNS record for the site",
           "Its whole browsing history"),
          "After DNS finds the server's address, the browser sends an HTTP request; the server answers with an "
          "HTTP response containing the page."),
    ],
    "security_basics": [
        q("Why should each account have a different password?",
          "So one leaked password can't unlock your other accounts",
          ("Websites reject passwords used on other sites", "Different passwords make each login faster",
           "It stops websites from storing your password"),
          "Attackers try passwords leaked from one site on many others. A unique password per account, kept "
          "in a password manager, limits the damage to one account."),
        q("What does the padlock (HTTPS) in the address bar tell you?", "The connection to the site is encrypted",
          ("The site is run by a trustworthy company", "The site has been checked for viruses",
           "The site cannot be a phishing page"),
          "HTTPS protects data on its way between you and the site. Phishing sites can have a padlock too, so "
          "it says nothing about who runs the site or whether it is honest."),
        q("An email says your account closes today unless you sign in through its link. What is safest?",
          "Go to the site yourself instead of using the link",
          ("Sign in quickly before the account closes", "Reply to the email to check it is genuine",
           "Open the link on your phone instead"),
          "Urgency and a sign-in link are classic phishing signs. Typing the address yourself or using the "
          "official app reaches the real site; replying only reaches whoever sent the email."),
    ],
}
