"""Curated fallback questions for Cloud & DevOps. Code is Markdown."""

from seed.questions import Bank, q

QUESTIONS: Bank = {
    # --- Working practices and servers ------------------------------------------------------
    "devops_culture": [
        q("Why does DevOps favour many small releases over a few large ones?",
          "Small changes are easier to test, review and roll back",
          ("Small releases need no testing at all", "Large releases are not allowed by cloud providers",
           "Users prefer to see the version number change often"),
          "When a small change breaks something, the cause is obvious and the fix is quick. Big releases "
          "bundle many risks together."),
        q("Which of these is one of the four DORA software delivery metrics?", "Deployment frequency",
          ("Lines of code written per day", "Number of servers running", "Hours worked by the team"),
          "DORA's metrics include deployment frequency, lead time for changes, change failure rate and time "
          "to restore service, measuring both speed and stability."),
        q("In a DevOps team, who is responsible for the software running well in production?",
          "The whole team that builds it, together with operations",
          ("Only the operations team, after hand-over", "Only the developer who wrote the last change",
           "Only the customers who report problems"),
          "\"You build it, you run it\": shared ownership means the people who write the code also see and "
          "fix how it behaves in production."),
    ],
    "devops_linux_admin": [
        q("Which command starts the `nginx` service now and makes it start at every boot?",
          "`sudo systemctl enable --now nginx`",
          ("`sudo systemctl start nginx`", "`sudo systemctl status nginx`", "`sudo systemctl reload nginx`"),
          "`enable` creates the links that start the service at boot and `--now` also starts it immediately. "
          "`start` alone doesn't survive a reboot."),
        q("Why log in to servers with SSH keys rather than passwords?",
          "Keys can't be guessed and are never typed into the server",
          ("Keys make the connection faster than passwords", "Passwords don't work over SSH at all",
           "Keys let anyone log in without an account"),
          "A private key stays on your machine and is far too long to guess. Disabling password logins then "
          "stops password-guessing attempts."),
        q("What does `sudo` let an authorised user do?", "Run a single command as another user, usually root",
          ("Switch off the firewall permanently", "Log in to any server on the network",
           "Install software without downloading it"),
          "`sudo` grants temporary, logged elevated rights for one command, so admins don't need to stay "
          "logged in as root."),
    ],
    "devops_shell_scripting": [
        q("In Bash, what does an exit status of `0` mean?", "The command succeeded",
          ("The command failed", "The command is still running", "The command printed no output"),
          "By convention 0 means success and any other number means a kind of failure. `$?` holds the last "
          "command's exit status."),
        q("Why do many scripts start with `set -euo pipefail`?",
          "To stop on errors and unset variables instead of carrying on",
          ("To make the script run faster by skipping checks", "To print every command before it runs",
           "To run the whole script as the root user"),
          "`-e` exits when a command fails, `-u` treats unset variables as errors and `pipefail` makes a "
          "pipeline fail if any part of it fails. `-x` is the option that prints commands."),
        q("A file is called `my report.txt`. Why should a script write `\"$file\"` rather than `$file`?",
          "Without quotes, the space splits it into two arguments",
          ("Without quotes, Bash can't read the variable", "Quotes make the variable read-only",
           "Quotes convert the value to lowercase"),
          "Unquoted variables undergo word splitting and filename expansion. Quoting keeps the value as one "
          "argument."),
    ],
    "devops_git_workflows": [
        q("What is a pull request for?", "Proposing a branch's changes for review before merging",
          ("Downloading the latest changes from the server", "Deleting a branch that is no longer needed",
           "Undoing the most recent commit on main"),
          "A pull request shows the diff, runs checks and collects review comments before the branch is "
          "merged. Downloading changes is `git pull`, a different thing."),
        q("What characterises trunk-based development?", "Everyone merges small changes into main at least daily",
          ("Each feature lives on its own branch for months", "Only one developer may commit at a time",
           "Releases are made from long-running release branches only"),
          "Short-lived branches, or none, keep integration continuous and avoid painful merges. Unfinished "
          "work is hidden behind feature flags."),
        q("What should a code reviewer focus on most?",
          "Whether the change is correct, clear and safe",
          ("Whether the author used their favourite editor", "How many lines the change adds",
           "Whether the commit was made during working hours"),
          "Review catches bugs, design problems and security issues and spreads knowledge. Formatting is best "
          "left to automatic tools."),
    ],
    # --- Delivery pipelines ---------------------------------------------------------------------
    "devops_ci": [
        q("What is the main goal of continuous integration?",
          "Find integration problems early by merging and testing often",
          ("Deploy every commit straight to production", "Replace code review with automated tests",
           "Keep each developer's work separate for as long as possible"),
          "Integrating at least daily with an automated build and tests means conflicts and bugs show up "
          "while they are small. Deploying every change is continuous deployment."),
        q("The main branch's build has just failed. What does good CI practice say to do?",
          "Fix it, or revert the change, before anything else",
          ("Keep merging, and fix it at the end of the week", "Turn off the failing tests",
           "Delete the CI pipeline until it passes"),
          "A broken main branch blocks everyone and hides new failures. Restoring a green build is the team's "
          "top priority."),
        q("In GitHub Actions, where is a workflow defined?", "In a YAML file under `.github/workflows/`",
          ("In the repository's README", "In a settings page that can't be versioned",
           "In a `Dockerfile` at the root of the repository"),
          "Workflows are code: YAML files in the repository, versioned and reviewed like everything else."),
    ],
    "devops_cd": [
        q("What is the difference between continuous delivery and continuous deployment?",
          "Delivery keeps every change releasable; deployment releases each one automatically",
          ("Delivery is for websites; deployment is for mobile and desktop apps", "Deployment skips tests that delivery runs first",
           "They are two names for exactly the same practice"),
          "With continuous delivery a person decides when to release a ready build; continuous deployment "
          "sends every change that passes the pipeline to production."),
        q("In a blue-green deployment, how is the new version released?",
          "Traffic is switched from the old environment to the new one",
          ("The old servers are upgraded one by one in place", "Users are asked to download the new version",
           "The new version runs only at night"),
          "Two identical environments run side by side; switching back is instant if the new one misbehaves."),
        q("What is a canary release?", "Sending a small share of users to the new version first",
          ("Releasing only on test servers that users never see", "Releasing all changes at once to everyone",
           "Releasing a version with its logging turned off"),
          "If errors or latency rise for the small group, the release is stopped before most users are "
          "affected."),
    ],
    "devops_containers": [
        q("What is the difference between a Docker image and a container?",
          "An image is a read-only template; a container is a running instance of it",
          ("An image runs on Linux; a container runs on Windows", "A container is a compressed copy of an image",
           "They are two names for the same thing"),
          "You build an image once and can start many containers from it, each with its own writable layer."),
        q("How do containers differ from virtual machines?",
          "Containers share the host's kernel; each VM runs its own operating system",
          ("Containers each boot a full kernel; VMs share the host's one", "Virtual machines start much faster than containers do",
           "Only one container can run on each computer at a time"),
          "Sharing the kernel makes containers lighter and quicker to start; VMs give stronger isolation at a "
          "higher cost."),
        q("Why copy `requirements.txt` and install dependencies before copying the rest of the code in a "
          "Dockerfile?", "So the dependency layer is reused from the cache when only code changes",
          ("Because Docker reads files in alphabetical order", "Because code must never be copied into an image",
           "So the image can run without a base image"),
          "Each instruction makes a layer, and a layer is rebuilt only if it or an earlier one changes. "
          "Ordering by how often things change keeps builds fast."),
    ],
    "devops_kubernetes": [
        q("What is the smallest deployable unit in Kubernetes?", "A pod",
          ("A node", "A container image", "A namespace"),
          "A pod wraps one or more containers that share a network address and storage. Deployments create "
          "and replace pods for you."),
        q("A Deployment asks for 3 replicas and one pod crashes. What does Kubernetes do?",
          "Starts a new pod to get back to 3",
          ("Waits for an administrator to restart it", "Scales the Deployment down to 2",
           "Stops the other two pods as well"),
          "Kubernetes keeps comparing the actual state with the desired state and corrects any difference: "
          "this is its self-healing."),
        q("Why put a Kubernetes Service in front of a set of pods?",
          "To give them a stable address while pods come and go",
          ("To store the pods' data permanently", "To build the container images for them",
           "To encrypt the pods' container images"),
          "Pods are replaced and get new IP addresses; a Service keeps one name and spreads traffic across "
          "whichever pods are healthy."),
    ],
    "devops_iac": [
        q("What does `terraform plan` do?", "Shows what changes would be made, without making them",
          ("Creates all the resources immediately", "Deletes every resource that Terraform manages",
           "Downloads the cloud provider's documentation"),
          "`plan` compares the configuration with the recorded state and real infrastructure; `apply` makes "
          "the changes."),
        q("What is configuration drift?",
          "Real infrastructure gradually differing from its definition",
          ("A server physically moving between data centres", "Code that runs more slowly over time",
           "Logs that are written in the wrong time zone"),
          "Manual changes made outside the code cause drift. Making every change through code, and checking "
          "with `plan`, keeps them in line."),
        q("Why keep infrastructure definitions in version control?",
          "Changes can be reviewed, tracked and repeated exactly",
          ("So the cloud provider can bill you correctly", "Because cloud consoles have been retired",
           "So that servers never need updates"),
          "Infrastructure as code brings review, history and repeatable environments to servers and networks."),
    ],
    "devops_config_management": [
        q("What does it mean that an Ansible task is idempotent?",
          "Running it again changes nothing once the system is in the right state",
          ("It can run only once on each server", "It runs on every server at exactly the same moment",
           "It undoes itself if it fails"),
          "Tasks describe the desired state, such as \"this package is installed\", so repeating a playbook is "
          "safe."),
        q("How does Ansible usually connect to the servers it manages?", "Over SSH, with no agent installed",
          ("Through an agent that must run on every server", "By emailing commands to each server",
           "Through the servers' web browsers"),
          "Being agentless means there's nothing extra to install or keep updated on the managed machines."),
        q("What is the idea of immutable infrastructure?",
          "Replace servers with new ones built from an image, not change them",
          ("Servers can never be turned off", "Configuration files are written in a read-only language",
           "Every server keeps the same IP address forever"),
          "Building fresh servers from a known image avoids drift; changes go into the image and the old "
          "servers are thrown away."),
    ],
    # --- The cloud --------------------------------------------------------------------------------
    "cloud_computing_basics": [
        q("Which service model has the provider run the servers and runtime while you supply just your "
          "application code?", "Platform as a Service (PaaS)",
          ("Infrastructure as a Service (IaaS)", "Software as a Service (SaaS)", "On-premises hosting"),
          "With IaaS you manage virtual machines yourself; with SaaS you use a finished application such as "
          "web email."),
        q("What is an availability zone?",
          "An isolated data centre location within a region",
          ("A country where cloud services are legal", "A time window when servers can be updated",
           "A discount for running servers all year"),
          "Spreading an application across zones keeps it running if one data centre fails."),
        q("What does elasticity mean in cloud computing?",
          "Resources can grow and shrink with demand",
          ("Prices change every hour", "Data is copied to every region automatically",
           "Servers are made of flexible hardware"),
          "You can add capacity for a busy period and release it afterwards, paying only for what you use."),
    ],
    "cloud_compute": [
        q("What does an autoscaling group do?",
          "Adds or removes instances to match load",
          ("Makes each instance's CPU faster as load grows", "Copies instances to another cloud provider",
           "Backs up instances every night"),
          "Scaling out adds more instances; a policy such as average CPU usage decides when."),
        q("What does a load balancer do for a group of web servers?",
          "Spreads incoming requests across the healthy servers",
          ("Stores the servers' files in one place", "Encrypts the servers' disks",
           "Merges the servers into one bigger machine"),
          "It also stops sending traffic to servers that fail health checks, which makes autoscaling and "
          "replacement invisible to users."),
        q("What is a machine image (such as an AMI) used for?",
          "Starting new instances with the same operating system and software",
          ("Recording a picture of the console for an audit", "Calculating the bill for the instance's usage",
           "Measuring how busy each running instance is"),
          "An image is a template for instances, so autoscaling can launch identical servers in minutes."),
    ],
    "cloud_storage": [
        q("Which kind of cloud storage stores files as objects in buckets, reached over HTTP?",
          "Object storage, such as Amazon S3",
          ("Block storage, such as a virtual disk", "File storage, such as a network share",
           "Instance memory"),
          "Object storage scales to vast amounts of data and suits images, backups and logs; block storage "
          "acts like a disk attached to one machine."),
        q("S3 Standard is designed for 99.999999999% durability. What does durability measure?",
          "How unlikely stored data is to be lost",
          ("How often the data can be reached", "How fast the data can be read",
           "How long the data must be kept by law"),
          "Durability is about not losing data; availability is about being able to reach it at a given "
          "moment, and is a separate figure."),
        q("Why choose a managed database service over running a database on your own VM?",
          "The provider handles patching, backups and failover",
          ("Managed databases don't need any schema", "Managed databases are always free",
           "Only managed databases can use SQL"),
          "You still design the schema and queries, but routine operations are automated, at a higher price."),
    ],
    "cloud_iam": [
        q("Why should a program running on a cloud server use a role rather than a stored access key?",
          "Roles give temporary credentials that rotate automatically",
          ("Roles make the program run faster", "Access keys don't work on cloud servers",
           "Roles give the program full administrator rights"),
          "Long-lived keys can leak from code or disks; temporary credentials from a role expire on their own."),
        q("An IAM policy allows `s3:*` on a bucket, and another policy attached to the same user explicitly "
          "denies `s3:DeleteObject` on it. Can the user delete objects?", "No: an explicit deny wins",
          ("Yes: the allow came first", "Yes: wildcards override specific actions",
           "Only if they use the console instead of the API"),
          "In AWS policy evaluation an explicit deny always overrides any allow."),
        q("What should you do with a cloud account's root user?",
          "Protect it with MFA and use it only for rare account tasks",
          ("Use it for everyday work so nothing is blocked", "Share its password with the whole team",
           "Create access keys for it and put them in scripts"),
          "The root user can do anything, including closing the account. Everyday work belongs to named users "
          "or roles with limited permissions."),
    ],
    "cloud_networking": [
        q("What makes a subnet public in a cloud network?",
          "Its route table sends internet traffic to an internet gateway",
          ("It has the word \"public\" in its name", "Its servers all use the same password",
           "It is in a different region from the private one"),
          "Only the routing decides it. Private subnets reach the internet, if at all, through a NAT gateway, "
          "which allows outbound connections only."),
        q("Where should a database usually go in a cloud network?",
          "In a private subnet that only the app servers can reach",
          ("In a public subnet so the app can find it", "Outside the network so it scales better",
           "On the same instance as the load balancer"),
          "Keeping the database unreachable from the internet removes a large attack surface; security groups "
          "then allow only the app servers in."),
        q("How does an AWS security group differ from a network ACL?",
          "A security group is stateful and protects instances; an ACL is stateless and covers a subnet",
          ("A security group is stateless; a network ACL is stateful", "A security group only blocks traffic; an ACL only allows it",
           "They are identical apart from their names"),
          "Stateful means return traffic is allowed automatically. A stateless ACL needs rules for both "
          "directions."),
    ],
    "cloud_serverless": [
        q("What is a cold start in serverless computing?",
          "Extra delay when a function runs in a newly created environment",
          ("A function restarted after it throws an error", "Restarting all functions after an outage",
           "A function running with its lowest memory setting"),
          "After a period of no traffic, or when scaling up, the platform must create and initialise a new "
          "environment, which adds latency to that request."),
        q("Why should serverless functions be stateless?",
          "Each call may run in a different environment, so local data may be gone",
          ("Because functions can't read any input", "Because state makes the code longer",
           "Because serverless platforms forbid variables"),
          "Keep state in a database, cache or object store, not in the function's memory or local disk."),
        q("Which workload suits serverless functions best?",
          "Short tasks triggered by events, with spiky traffic",
          ("A database server that must run all the time", "A job that runs for several days without stopping",
           "Software that needs a specific graphics card driver"),
          "Functions scale with events and cost nothing when idle; long-running or always-on work is usually "
          "cheaper on servers or containers."),
    ],
    "cloud_architecture": [
        q("How do you keep a web app running if one availability zone fails?",
          "Run instances in at least two zones behind a load balancer",
          ("Use a bigger instance in a single zone", "Take a backup of the instance every hour",
           "Turn on autoscaling in only one zone"),
          "Spreading across zones removes a single point of failure; backups help you recover, but not stay "
          "up."),
        q("What does the twelve-factor app say about configuration such as database URLs?",
          "Store it in the environment, separate from the code",
          ("Hard-code it so it can't be changed by mistake", "Put it in a comment in the main source file",
           "Keep a different code branch for each environment"),
          "The same build can then run in development, staging and production with different settings."),
        q("Which is a common way to cut a cloud bill without hurting the service?",
          "Turning off or right-sizing idle and oversized resources",
          ("Removing all backups", "Moving everything into a single zone",
           "Turning off monitoring and logging"),
          "Cost optimisation is a pillar of well-architected frameworks: measure usage, then remove waste "
          "without removing resilience."),
    ],
    # --- Running in production --------------------------------------------------------------------
    "devops_monitoring": [
        q("What are the three main kinds of telemetry in observability?", "Metrics, logs and traces",
          ("Users, servers and networks", "Errors, warnings and info", "CPU, memory and disk"),
          "Metrics are numbers over time, logs are records of events and traces follow one request through "
          "many services."),
        q("Which of these is one of Google SRE's four golden signals?", "Latency",
          ("Code coverage", "Number of deployments", "Build duration"),
          "The four golden signals are latency, traffic, errors and saturation."),
        q("Which alert is most useful to wake someone up at night?",
          "Users' requests failing above the agreed level",
          ("CPU on one server briefly reached 80%", "A log file grew by 10 MB",
           "A deployment finished successfully"),
          "Page on symptoms that users feel. Causes such as high CPU belong on dashboards unless they will "
          "soon cause user-visible harm."),
    ],
    "devops_sre": [
        q("A service's SLO is 99.9% of requests succeeding over 30 days. What is its error budget?",
          "0.1% of requests may fail in those 30 days",
          ("99.9% of requests may fail", "The money set aside for outages", "Exactly 30 failed requests"),
          "The error budget is 100% minus the SLO. While budget remains, the team can take risks such as "
          "releasing faster; when it runs out, it focuses on reliability."),
        q("What is the difference between an SLI and an SLO?",
          "An SLI is a measurement; an SLO is the target for it",
          ("An SLI is a contract with penalties; an SLO is not", "An SLO is measured; an SLI is a goal",
           "They are the same thing with different names"),
          "For example, the SLI is the share of requests faster than 300 ms and the SLO says it should be at "
          "least 99%. An SLA is the contract."),
        q("Why are postmortems written to be blameless?",
          "So people report honestly and the system gets fixed",
          ("So nobody has to write anything down", "So the incident can be forgotten quickly",
           "So that managers can decide who to blame later"),
          "Blaming individuals hides information. Blameless postmortems look for the conditions that let the "
          "mistake cause harm."),
    ],
    "devops_devsecops": [
        q("What does \"shifting security left\" mean?", "Checking for security problems early in development",
          ("Moving the security team to another office", "Doing security reviews only after release",
           "Giving security checks a lower priority than features"),
          "Finding issues in design, code review and CI is far cheaper than finding them in production."),
        q("A pipeline scan finds a dependency with a known critical vulnerability. What is a sensible pipeline "
          "policy?", "Fail the build until the dependency is upgraded or the risk is accepted",
          ("Ignore it, since the code still compiles", "Delete the scanner from the pipeline",
           "Deploy, then check the dependency next quarter"),
          "Software composition analysis catches known flaws before deployment; an exception should be a "
          "recorded decision, not silence."),
        q("Why sign build artefacts and record where they came from?",
          "So deployments can check they weren't tampered with",
          ("To make the artefacts smaller", "To make the build run faster",
           "So the artefacts can be deployed without testing"),
          "Supply-chain attacks target build systems and dependencies. Signatures and provenance (as in SLSA) "
          "let you trust what you deploy."),
    ],
}
