"""Curated fallback questions for Cybersecurity: conceptual and defensive. Code is Markdown."""

from seed.questions import Bank, q

QUESTIONS: Bank = {
    # --- Principles and threats -------------------------------------------------------------
    "sec_principles": [
        q("Ransomware encrypts a company's files so staff can no longer open them. Which part of the CIA triad "
          "is hit most directly?", "Availability",
          ("Confidentiality", "Integrity", "Non-repudiation"),
          "The data still exists and may not have been read or altered, but the people who need it can't use "
          "it, which is a loss of availability."),
        q("An intern's account can read every customer record, though the job needs only the support queue. "
          "Which principle does this break?", "Least privilege",
          ("Defence in depth", "Separation of duties", "Security through obscurity"),
          "Least privilege means giving each account only the access its job needs, so a stolen or misused "
          "account can do less harm."),
        q("Why does defence in depth use several independent layers of protection?",
          "So one failed control doesn't leave the system open",
          ("So each layer can be weaker and cheaper to run", "So attackers can't tell which layer stopped them",
           "So that no single team owns all of security"),
          "Every control fails sometimes. With layers such as a firewall, patching, MFA and monitoring, an "
          "attacker has to get past all of them, not just one."),
    ],
    "sec_threats_attacks": [
        q("An email that seems to come from your bank asks you to confirm your password through a link. What "
          "is this?", "Phishing",
          ("A denial-of-service attack", "A man-in-the-middle attack", "Ransomware"),
          "Phishing tricks people into giving away credentials or running something harmful. Check the sender "
          "and go to the site yourself instead of following the link."),
        q("What sets a worm apart from a virus?", "It spreads between computers on its own",
          ("It only damages files and never steals data", "It can only infect phones, never PCs",
           "It needs someone to open an attachment to spread"),
          "A virus attaches to files or programs and spreads when they're run or shared; a worm copies itself "
          "across networks without anyone's help."),
        q("Attackers try a few common passwords against thousands of different accounts. What is this called, "
          "and what defends against it best?", "Password spraying; multi-factor authentication",
          ("Brute force; making passwords expire monthly", "Phishing; a stricter spam filter",
           "SQL injection; parameterised queries"),
          "Spraying stays under per-account lockout limits by trying few passwords on many accounts. MFA "
          "stops a guessed password being enough, and banning common passwords helps too."),
    ],
    "sec_cryptography": [
        q("Which kind of encryption uses the same secret key to encrypt and to decrypt?", "Symmetric encryption",
          ("Public-key encryption", "Hashing", "A digital signature"),
          "Symmetric ciphers such as AES use one shared key. Public-key encryption uses a pair: a public key "
          "to encrypt and a private key to decrypt."),
        q("What does a cryptographic hash function such as SHA-256 provide?",
          "A fixed-size fingerprint that changes if the data changes",
          ("Encryption that the right key can reverse", "Proof of who sent a message, on its own",
           "Compression that keeps every byte of the data"),
          "A hash is one-way: you can't get the input back. It shows whether data has changed; proving who "
          "sent it needs a key, as in a MAC or a signature."),
        q("Alice signs a document with her private key. What can anyone with her public key check?",
          "That Alice signed it and it hasn't changed since",
          ("That nobody else has read the document", "That the document's contents are true",
           "That Alice can no longer change her key"),
          "A digital signature gives integrity and authenticity. It doesn't hide the contents: that needs "
          "encryption."),
    ],
    "sec_pki_tls": [
        q("What does a certificate authority (CA) vouch for when it signs a website's certificate?",
          "That the public key belongs to that domain",
          ("That the website is safe and free of malware", "That the company behind the site is honest",
           "That the site's server has been fully patched"),
          "A certificate binds a public key to a name. A phishing site can have a perfectly valid certificate "
          "for its own lookalike domain."),
        q("A site's certificate expired yesterday. What do visitors' browsers do?",
          "Show a warning and stop the page loading by default",
          ("Load the page and mark the connection as secure", "Quietly fall back to plain unencrypted HTTP",
           "Fetch a new certificate for the site automatically"),
          "Browsers refuse expired certificates. Automated renewal, as Let's Encrypt encourages, avoids this "
          "common outage."),
        q("During a TLS handshake, why is public-key cryptography used before switching to a symmetric key?",
          "Public keys agree a secret safely; symmetric ciphers are much faster",
          ("Symmetric keys can't be used over the internet at all", "Public-key encryption is too weak to protect data",
           "Browsers aren't allowed to store symmetric keys"),
          "The handshake authenticates the server and agrees a shared secret; the bulk of the data is then "
          "encrypted with a fast symmetric cipher such as AES."),
    ],
    "sec_identity_access": [
        q("Which pair is two different authentication factors?", "A password and a code from a phone app",
          ("A password and a security question", "A PIN and a password", "A fingerprint and a face scan"),
          "Factors are something you know, have or are. A password and a security question are both things "
          "you know; two biometrics are both things you are."),
        q("How should a web application store users' passwords?",
          "With a slow, salted hash such as Argon2 or bcrypt",
          ("Encrypted with AES, with the key kept in the code", "As a fast SHA-256 hash with no salt",
           "In plain text, in a table only admins can read"),
          "A slow salted hash makes stolen hashes expensive to crack and stops identical passwords having "
          "identical hashes. Encryption can be reversed by anyone who finds the key."),
        q("A user logs in successfully but is blocked from the admin page. Which step blocked them?",
          "Authorisation", ("Authentication", "Accounting", "Encryption"),
          "Authentication confirms who you are; authorisation decides what you're allowed to do."),
    ],
    "sec_threat_modelling": [
        q("In STRIDE, which threat is someone pretending to be another user?", "Spoofing",
          ("Tampering", "Repudiation", "Elevation of privilege"),
          "STRIDE: Spoofing identity, Tampering with data, Repudiation, Information disclosure, Denial of "
          "service and Elevation of privilege. Strong authentication counters spoofing."),
        q("What is a trust boundary in a data flow diagram?",
          "Where data passes between parts trusted to different degrees",
          ("The edge of the building that houses the servers", "The limit on how much data a user may upload",
           "The point at which the system's encryption ends"),
          "Data crossing a trust boundary, such as from a browser to your API, must be checked; threats tend "
          "to cluster there."),
        q("When is threat modelling most useful?", "While designing, and again when the design changes",
          ("Only after an attack has happened", "Only once the code is written and deployed",
           "Only for systems that handle payments"),
          "Design flaws are cheapest to fix before they're built. Revisiting the model as the system changes "
          "keeps it accurate."),
    ],
    # --- Protecting systems -------------------------------------------------------------------
    "sec_network_security": [
        q("What does a firewall do?", "Allows or blocks traffic according to rules",
          ("Encrypts all traffic leaving the network", "Removes malware from infected computers",
           "Gives every device a unique IP address"),
          "A firewall filters traffic by rules such as source, destination, port and protocol. Encryption and "
          "malware removal are other tools' jobs."),
        q("Why put the office printers, staff laptops and payment systems on separate network segments?",
          "To stop an attacker in one segment reaching the others easily",
          ("To make the internet connection faster for everyone", "To avoid needing passwords inside the network",
           "To let every device see every other device"),
          "Segmentation limits lateral movement: a compromised printer shouldn't be one hop from the "
          "payment systems."),
        q("What is the core idea of zero trust?",
          "Verify every request, wherever it comes from",
          ("Trust any device once it is inside the network", "Block every connection that comes from outside",
           "Rely on the firewall at the network's edge"),
          "Zero trust drops the idea of a trusted internal network: each request is authenticated and "
          "authorised on its own merits."),
    ],
    "sec_web_security": [
        q("A user's comment is shown on a page and its script runs in other visitors' browsers. Which weakness "
          "is this, and what prevents it?", "Cross-site scripting; encoding output for the context it's shown in",
          ("SQL injection; parameterised queries", "CSRF; requiring a longer session cookie",
           "Broken authentication; a stronger password policy"),
          "XSS happens when user input is treated as page code. Encoding output, using frameworks that escape "
          "by default and a Content Security Policy prevent it."),
        q("A user changes the number in `/invoices/1041` to `1042` and sees someone else's invoice. What is "
          "missing?", "An access check that the invoice belongs to the user",
          ("Encryption of the invoice number in the URL", "A CAPTCHA on the invoice page",
           "A rate limit on the invoice API"),
          "This is broken access control, top of the OWASP Top 10. Hiding or encrypting IDs doesn't fix it; "
          "the server must check ownership on every request."),
        q("What does a CSRF token protect against?",
          "Another site making the browser send unwanted requests",
          ("Attackers reading the session cookie", "Passwords being guessed too many times",
           "Data being read as it crosses the network"),
          "Cross-site request forgery rides on the browser's cookies. A secret token that another site can't "
          "read, plus SameSite cookies, shows the request came from your own pages."),
    ],
    "sec_secure_coding": [
        q("Why should a login form say \"Incorrect email or password\" instead of \"No account with that "
          "email\"?", "So it doesn't reveal which emails have accounts",
          ("Because shorter error messages load faster", "So users try a different email address",
           "Because detailed messages break screen readers"),
          "Revealing whether an account exists helps attackers build lists of targets. Error messages should "
          "help users without leaking information."),
        q("Where should an API key that a deployed app needs be kept?",
          "In a secrets manager or environment variable, not the code",
          ("In the source code, so every copy has it", "In a comment at the top of the main file",
           "In the README, so new developers can find it"),
          "Secrets in source code end up in Git history, backups and screenshots. Keep them out of the "
          "repository and rotate any that leak."),
        q("Which approach to validating input is generally safer?",
          "Allow only what is expected and reject the rest",
          ("Block a list of known bad characters", "Accept everything and check it later on",
           "Validate only in the browser's JavaScript"),
          "Allow-lists fail safe: anything unexpected is rejected. Deny-lists miss new tricks, and browser "
          "checks can be bypassed, so the server must validate too."),
    ],
    "sec_system_hardening": [
        q("What does hardening a server mainly involve?",
          "Removing unneeded services and setting secure configuration",
          ("Adding more memory so it is harder to crash", "Moving it to a stronger physical case",
           "Giving every user an administrator account"),
          "Each unused service or open port is something that could be attacked. Baselines such as the CIS "
          "Benchmarks list secure settings."),
        q("A critical security update for a widely used library is released. What is the sensible response?",
          "Test it and roll it out quickly, starting with exposed systems",
          ("Wait a year to see whether anyone gets attacked", "Install it only on new servers from now on",
           "Turn off automatic updates to avoid surprises"),
          "Attackers often exploit known flaws soon after patches appear. Prioritise systems exposed to the "
          "internet and those whose flaws are being exploited."),
        q("Why must backups be kept separately and their restores tested?",
          "Ransomware may encrypt reachable backups, and untested ones can fail",
          ("Because backups slow down the server they're on", "Because the law forbids backups on the same disk",
           "Because restoring is always faster from tape"),
          "An offline or immutable copy survives an attack on the main systems, and a restore test proves the "
          "backup actually works."),
    ],
    "sec_vulnerability_management": [
        q("What is a CVE?", "A public identifier for a specific known vulnerability",
          ("A score for how severe a vulnerability is", "A tool that scans networks for weaknesses",
           "A law requiring companies to report breaches"),
          "CVE IDs such as CVE-2021-44228 name vulnerabilities so everyone refers to the same one. Severity "
          "is scored separately, usually with CVSS."),
        q("Two flaws on internet-facing servers: one CVSS 9.1 with no known exploitation, one CVSS 7.5 being "
          "actively exploited. Which is usually fixed first?", "The 7.5 one that is being exploited",
          ("The 9.1 one, because its score is higher", "Neither until the scores are recalculated",
           "Whichever was discovered first"),
          "CVSS measures how bad a flaw could be; active exploitation shows it's being used now. Lists such "
          "as CISA's Known Exploited Vulnerabilities exist to help with this."),
        q("What is responsible (coordinated) disclosure?",
          "Reporting a flaw privately so it can be fixed before details go public",
          ("Publishing a flaw at once so everyone knows", "Selling details of a flaw to the highest bidder",
           "Keeping a found flaw secret indefinitely"),
          "The finder tells the vendor, agrees a timeline and publishes after a fix is available, protecting "
          "users in the meantime."),
    ],
    # --- Detection and response ---------------------------------------------------------------
    "sec_logging_monitoring": [
        q("Which of these should never be written to application logs?", "Users' passwords",
          ("Failed login attempts", "The time of each request", "Which account changed a setting"),
          "Logs are widely read and kept for a long time. Record security events, but never passwords, "
          "session tokens or full card numbers."),
        q("What does a SIEM system do?", "Collects logs from many sources and correlates them into alerts",
          ("Blocks network traffic that matches a rule", "Encrypts logs so attackers can't read them",
           "Scans source code for vulnerabilities"),
          "A SIEM brings logs together so related events, such as many failed logins then a success from a "
          "new country, can be spotted."),
        q("A detection rule fires hundreds of times a day, almost always on harmless activity. What is the "
          "risk?", "Analysts start ignoring it and miss a real attack",
          ("The SIEM will delete older logs to make room", "The rule will start blocking legitimate users",
           "There is no risk; more alerts are always safer"),
          "Alert fatigue is a real failure mode. Tune noisy rules so that alerts are rare enough to be "
          "investigated."),
    ],
    "sec_incident_response": [
        q("Malware is found on one laptop. What usually comes first: containment or eradication?",
          "Containment, such as isolating the laptop from the network",
          ("Eradication, by wiping the laptop at once", "Recovery, by restoring the laptop from backup",
           "Lessons learned, in a meeting about the cause"),
          "Containing an incident stops it spreading while you investigate; wiping first can destroy the "
          "evidence of what happened and how far it went."),
        q("Why prepare an incident response plan before anything goes wrong?",
          "So people know their roles, contacts and steps under pressure",
          ("Because insurers forbid responding without one", "So that incidents can't happen at all",
           "So the security team doesn't need to be told"),
          "Preparation is the first phase of the NIST incident response life cycle. Decisions made calmly in "
          "advance save time in a crisis."),
        q("What is the purpose of the lessons-learned review after an incident?",
          "To improve defences and the response process",
          ("To decide which employee to blame", "To close the incident ticket faster",
           "To delete the evidence that was collected"),
          "A blameless review finds what went wrong and what worked, then turns it into concrete changes."),
    ],
    "sec_forensics": [
        q("Why do investigators record a hash of a disk image when they take it?",
          "To show later that the evidence hasn't changed",
          ("To encrypt the evidence so no one else can read it", "To make the image smaller to store",
           "To find deleted files on the disk"),
          "Recomputing the hash later and getting the same value shows the copy is identical to the "
          "original, which matters if the evidence is challenged."),
        q("What is the chain of custody?", "A record of who handled evidence, when and why",
          ("The order in which systems were attacked", "The list of people allowed into the data centre",
           "The sequence of backups kept for a system"),
          "An unbroken record shows evidence wasn't tampered with, so it can be relied on, including in court."),
        q("Following the order of volatility, which is usually collected first from a running machine?",
          "The contents of memory (RAM)", ("Files on the hard disk", "Archived backup tapes", "Printed reports"),
          "Memory is lost when the machine is turned off, so it is captured before more persistent data such "
          "as disk contents."),
    ],
    "sec_penetration_testing": [
        q("What separates a penetration test from an attack?", "Written permission and an agreed scope",
          ("The tools used", "The time of day it is carried out", "Whether a vulnerability is found"),
          "The same techniques are legal and useful only with the system owner's written authorisation and "
          "rules of engagement that say what may be tested."),
        q("How does a penetration test differ from an automated vulnerability scan?",
          "A tester checks whether weaknesses can really be exploited and chained",
          ("A scan needs permission, but a penetration test doesn't", "A penetration test only checks for missing patches",
           "A scan is always more thorough than a person"),
          "Scanners list possible weaknesses, including false positives. Testers confirm real impact and find "
          "combinations and logic flaws that scanners miss."),
        q("In a security exercise, what does the blue team do?", "Defends: detects and responds to the attack",
          ("Plays the attacker", "Writes the rules of engagement", "Audits the company's finances"),
          "The red team plays the adversary; the blue team defends. A purple team approach has them work "
          "together to improve detection."),
    ],
    "sec_cloud_security": [
        q("Under the shared responsibility model, who is usually responsible for configuring access to a "
          "cloud storage bucket?", "The customer", ("The cloud provider", "The internet service provider",
                                                    "Nobody: buckets are private and can't be changed"),
          "The provider secures the underlying infrastructure; customers secure what they configure in it, "
          "including who can read their data."),
        q("Which mistake has exposed the most data in cloud breaches?",
          "Storage left readable by anyone on the internet",
          ("The provider's data centre being broken into", "Encryption that was too strong to manage",
           "Using more than one cloud region"),
          "Misconfiguration, such as public buckets and over-broad permissions, is the commonest cause. "
          "Block public access by default and audit permissions."),
        q("Why is identity often called the new perimeter in the cloud?",
          "Access is granted by identities and permissions, not network location",
          ("Because cloud servers have no network connections", "Because firewalls are banned in the cloud",
           "Because every user shares a single account"),
          "Cloud services are reachable over the internet, so stolen credentials or excessive permissions can "
          "matter more than any firewall."),
    ],
    "sec_privacy_compliance": [
        q("Under GDPR's data minimisation principle, what should an organisation collect?",
          "Only the personal data it needs for its stated purpose",
          ("As much data as possible in case it is useful", "Only data that has been encrypted",
           "Any data the user hasn't explicitly refused"),
          "Collecting less means less to protect and less harm if it leaks. Storage limitation adds that data "
          "should be kept only as long as needed."),
        q("In a risk assessment, which two things are usually combined to rate a risk?", "Likelihood and impact",
          ("Cost and speed", "Age and size of the system", "Number of users and number of servers"),
          "A likely, high-impact risk comes first. The organisation can then reduce, transfer (for example "
          "with insurance), avoid or accept each risk."),
        q("What are frameworks such as the NIST Cybersecurity Framework and the CIS Controls for?",
          "Organising and prioritising an organisation's security work",
          ("Encrypting data automatically", "Replacing the need for a security team",
           "Certifying that a system can't be breached"),
          "Frameworks give a shared structure (for NIST: govern, identify, protect, detect, respond and "
          "recover) and a way to measure progress; none guarantees safety."),
    ],
}
