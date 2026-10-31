"""Cybersecurity: protecting systems, data and people, taught from the defender's side.

Security Basics is defined in Foundations and shared here. Every topic is about how attacks work at a
high level and how to prevent, detect and respond to them; quizzes for this domain get an extra
defensive-only rule (services/llm_quiz.py, DOMAIN_RULES).
"""

from seed.model import Domain, Topic, article, docs, video

TOPICS: tuple[Topic, ...] = (
    # --- Principles and threats -------------------------------------------------------------
    Topic(
        "sec_principles", "Security Principles",
        "The ideas behind every security decision: confidentiality, integrity and availability, least "
        "privilege, defence in depth, secure defaults, and weighing risk by likelihood and impact.",
        1,
        (
            docs("NCSC: Secure design principles", "https://www.ncsc.gov.uk/collection/cyber-security-design-principles"),
            article("IBM: What is cybersecurity?", "https://www.ibm.com/think/topics/cybersecurity"),
            video("Cybersecurity: Crash Course Computer Science #31", "https://www.youtube.com/watch?v=bPVaOlJ6ln0"),
        ),
    ),
    Topic(
        "sec_threats_attacks", "Threats & Common Attacks",
        "Who attacks and how, at a high level: malware such as ransomware and worms, phishing and "
        "other social engineering, password attacks, denial of service, and the warning signs of each.",
        2,
        (
            article("IBM: What is a cyberattack?", "https://www.ibm.com/think/topics/cyber-attack"),
            docs("MITRE ATT&CK: knowledge base of attacker behaviour", "https://attack.mitre.org/"),
        ),
    ),
    Topic(
        "sec_cryptography", "Cryptography Basics",
        "The building blocks of secure systems: symmetric and public-key encryption, hash functions, "
        "message authentication codes and digital signatures, what each protects, and why you should "
        "never invent your own.",
        2,
        (
            video("Cryptography: Crash Course Computer Science #33", "https://www.youtube.com/watch?v=jhXCTbFnK8o"),
            video("7 Cryptography Concepts EVERY Developer Should Know (Fireship)", "https://www.youtube.com/watch?v=NuyzuNBFWxQ"),
            article("Crypto 101 (free book)", "https://www.crypto101.io/"),
        ),
    ),
    Topic(
        "sec_pki_tls", "Certificates, PKI & TLS",
        "How a browser knows it is talking to the right server: certificates, certificate authorities "
        "and chains of trust, the TLS handshake, and issuing and renewing certificates automatically.",
        3,
        (
            article("How HTTPS Works (illustrated)", "https://howhttps.works/"),
            docs("Let's Encrypt: How it works", "https://letsencrypt.org/how-it-works/"),
            video("SSL, TLS, HTTPS Explained (ByteByteGo)", "https://www.youtube.com/watch?v=j9QmMEWmcfo"),
        ),
    ),
    Topic(
        "sec_identity_access", "Identity & Access Management",
        "Controlling who can do what: authentication versus authorisation, factors and multi-factor "
        "authentication, storing passwords safely, single sign-on, and role-based access control.",
        3,
        (
            article("IBM: What is identity and access management?", "https://www.ibm.com/think/topics/identity-access-management"),
            docs("OWASP: Multifactor authentication cheat sheet", "https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html"),
            docs("OWASP: Authorisation cheat sheet", "https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html"),
        ),
    ),
    Topic(
        "sec_threat_modelling", "Threat Modelling",
        "Finding what could go wrong before it does: mapping data flows and trust boundaries, listing "
        "threats with STRIDE, and deciding which risks to fix, reduce, accept or transfer.",
        3,
        (
            docs("OWASP: Threat modelling cheat sheet", "https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html"),
        ),
    ),
    # --- Protecting systems -------------------------------------------------------------------
    Topic(
        "sec_network_security", "Network Security",
        "Protecting networks and the traffic on them: firewalls, network segmentation, VPNs, intrusion "
        "detection and prevention systems, secure Wi-Fi, and the zero-trust approach.",
        3,
        (
            article("IBM: What is network security?", "https://www.ibm.com/think/topics/network-security"),
            docs("NCSC: 10 Steps to Cyber Security", "https://www.ncsc.gov.uk/collection/10-steps"),
        ),
    ),
    Topic(
        "sec_web_security", "Web Application Security",
        "The commonest weaknesses in web apps and how to prevent them: the OWASP Top 10, broken access "
        "control, injection, cross-site scripting, cross-site request forgery and security headers.",
        3,
        (
            docs("OWASP Top 10", "https://owasp.org/www-project-top-ten/"),
            docs("MDN: Web security", "https://developer.mozilla.org/en-US/docs/Web/Security"),
            docs("OWASP: Cross-site scripting prevention cheat sheet", "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html"),
        ),
    ),
    Topic(
        "sec_secure_coding", "Secure Coding Practices",
        "Writing code that is hard to misuse: validating input, parameterised queries, encoding output, "
        "safe error messages, keeping secrets out of source code, and keeping dependencies up to date.",
        3,
        (
            docs("OWASP Proactive Controls", "https://owasp.org/www-project-proactive-controls/"),
            docs("OWASP: Input validation cheat sheet", "https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html"),
            docs("OWASP: Secrets management cheat sheet", "https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html"),
        ),
    ),
    Topic(
        "sec_system_hardening", "System Hardening & Patching",
        "Reducing what can be attacked on a computer or server: removing unused software and services, "
        "secure configuration baselines, prompt patching, endpoint protection and tested backups.",
        3,
        (
            docs("CIS Benchmarks (secure configuration guides)", "https://www.cisecurity.org/cis-benchmarks"),
            docs("NCSC: Device security guidance", "https://www.ncsc.gov.uk/collection/device-security-guidance"),
        ),
    ),
    Topic(
        "sec_vulnerability_management", "Vulnerability Management",
        "Finding and fixing weaknesses continuously: CVE identifiers, CVSS severity scores, vulnerability "
        "scanning, prioritising what is actually exploited, and responsible disclosure.",
        3,
        (
            article("IBM: What is vulnerability management?", "https://www.ibm.com/think/topics/vulnerability-management"),
            docs("NCSC: Vulnerability management", "https://www.ncsc.gov.uk/collection/vulnerability-management"),
            docs("FIRST: CVSS v4.0 user guide", "https://www.first.org/cvss/user-guide"),
        ),
    ),
    # --- Detection and response ---------------------------------------------------------------
    Topic(
        "sec_logging_monitoring", "Logging, Monitoring & Detection",
        "Noticing an attack in progress: what to log and what never to log, collecting logs centrally, "
        "SIEM systems, writing useful alerts, and handling false positives.",
        3,
        (
            docs("OWASP: Logging cheat sheet", "https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html"),
            article("IBM: What is SIEM?", "https://www.ibm.com/think/topics/siem"),
        ),
    ),
    Topic(
        "sec_incident_response", "Incident Response",
        "Handling a security incident: preparation, detection and analysis, containment, eradication "
        "and recovery, communicating, and learning lessons afterwards.",
        4,
        (
            docs("NIST SP 800-61 Rev. 3: Incident response recommendations", "https://csrc.nist.gov/pubs/sp/800/61/r3/final"),
            docs("NCSC: Incident management", "https://www.ncsc.gov.uk/collection/incident-management"),
            article("IBM: What is incident response?", "https://www.ibm.com/think/topics/incident-response"),
        ),
    ),
    Topic(
        "sec_forensics", "Digital Forensics Basics",
        "Investigating what happened: preserving evidence, the chain of custody, collecting the most "
        "volatile data first, verifying copies with hashes, and building a timeline.",
        4,
        (
            article("IBM: What is digital forensics?", "https://www.ibm.com/think/topics/digital-forensics"),
        ),
    ),
    Topic(
        "sec_penetration_testing", "Penetration Testing & Ethical Hacking",
        "Testing defences with permission: written authorisation, scope and rules of engagement, how a "
        "test differs from a vulnerability scan, red and blue teams, and reporting findings.",
        4,
        (
            docs("NCSC: Penetration testing", "https://www.ncsc.gov.uk/guidance/penetration-testing"),
            article("IBM: What is penetration testing?", "https://www.ibm.com/think/topics/penetration-testing"),
        ),
    ),
    Topic(
        "sec_cloud_security", "Cloud Security",
        "Staying secure on someone else's infrastructure: the shared responsibility model, misconfigured "
        "storage, identity as the perimeter, encryption at rest and in transit, and cloud audit logs.",
        4,
        (
            docs("AWS: Shared responsibility model", "https://aws.amazon.com/compliance/shared-responsibility-model/"),
            docs("NCSC: Cloud security guidance", "https://www.ncsc.gov.uk/collection/cloud"),
            article("IBM: What is cloud security?", "https://www.ibm.com/think/topics/cloud-security"),
        ),
    ),
    Topic(
        "sec_privacy_compliance", "Privacy, Risk & Compliance",
        "Security as an organisation's duty: personal data and data protection principles such as GDPR's, "
        "risk assessments, security policies, and frameworks such as the NIST CSF and CIS Controls.",
        3,
        (
            docs("ICO: A guide to the data protection principles", "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/"),
            docs("NIST Cybersecurity Framework", "https://www.nist.gov/cyberframework"),
            docs("CIS Critical Security Controls", "https://www.cisecurity.org/controls"),
        ),
    ),
)

PREREQUISITES: tuple[tuple[str, str], ...] = (
    ("sec_principles", "sec_threats_attacks"),
    ("security_basics", "sec_threats_attacks"),
    ("sec_principles", "sec_cryptography"),
    ("binary_data_representation", "sec_cryptography"),
    ("sec_cryptography", "sec_pki_tls"),
    ("how_the_internet_works", "sec_pki_tls"),
    ("sec_cryptography", "sec_identity_access"),
    ("sec_threats_attacks", "sec_threat_modelling"),
    ("sec_principles", "sec_privacy_compliance"),

    ("sec_threats_attacks", "sec_network_security"),
    ("sec_threats_attacks", "sec_web_security"),
    ("sec_web_security", "sec_secure_coding"),
    ("programming_concepts", "sec_secure_coding"),
    ("sec_threats_attacks", "sec_system_hardening"),
    ("operating_system_basics", "sec_system_hardening"),
    ("sec_system_hardening", "sec_vulnerability_management"),

    ("sec_network_security", "sec_logging_monitoring"),
    ("sec_system_hardening", "sec_logging_monitoring"),
    ("sec_logging_monitoring", "sec_incident_response"),
    ("sec_incident_response", "sec_forensics"),
    ("sec_vulnerability_management", "sec_penetration_testing"),
    ("sec_network_security", "sec_penetration_testing"),
    ("sec_web_security", "sec_penetration_testing"),
    ("sec_identity_access", "sec_cloud_security"),
    ("sec_network_security", "sec_cloud_security"),
    ("cloud_computing_basics", "sec_cloud_security"),
)

CYBERSECURITY = Domain(
    id="cybersecurity",
    name="Cybersecurity",
    description=(
        "Protecting systems, data and people, from the defender's side: security principles and "
        "cryptography, securing networks, web apps and servers, finding and fixing weaknesses, and "
        "detecting and responding to incidents."
    ),
    topics=TOPICS,
    prerequisites=PREREQUISITES,
    shared=("security_basics",),
)
