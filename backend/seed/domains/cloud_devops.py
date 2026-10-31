"""Cloud & DevOps: running software reliably, from Linux servers and pipelines to containers and the cloud.

DevOps Principles is the starting topic. The rest builds on Foundations (the command line, the
operating system, Git, how the internet works and security basics).
"""

from seed.model import Domain, Topic, article, docs, video

TOPICS: tuple[Topic, ...] = (
    # --- Working practices and servers ------------------------------------------------------
    Topic(
        "devops_culture", "DevOps Principles",
        "Why development and operations work together: small, frequent changes, automating repetitive "
        "work, fast feedback, shared ownership of running software, and the DORA delivery metrics.",
        1,
        (
            article("AWS: What is DevOps?", "https://aws.amazon.com/devops/what-is-devops/"),
            article("Atlassian: What is DevOps?", "https://www.atlassian.com/devops"),
            docs("DORA: Software delivery performance metrics", "https://dora.dev/guides/dora-metrics/"),
        ),
    ),
    Topic(
        "devops_linux_admin", "Linux Administration",
        "Looking after a Linux server: users, groups and sudo, installing packages, running services "
        "with systemd, logging in with SSH keys, and reading system logs.",
        2,
        (
            video("Linux in 100 Seconds (Fireship)", "https://www.youtube.com/watch?v=rrB13utjYV4"),
            docs("Ubuntu Server documentation", "https://ubuntu.com/server/docs"),
            docs("ArchWiki: systemd", "https://wiki.archlinux.org/title/Systemd"),
        ),
    ),
    Topic(
        "devops_shell_scripting", "Shell Scripting",
        "Automating the terminal with Bash: variables and quoting, conditions and loops, exit codes, "
        "pipes and redirection, and making scripts stop safely when a command fails.",
        2,
        (
            video("Bash in 100 Seconds (Fireship)", "https://www.youtube.com/watch?v=I4EWvMFj37g"),
            article("MIT Missing Semester: Shell tools and scripting", "https://missing.csail.mit.edu/2020/shell-tools/"),
            docs("GNU Bash reference manual", "https://www.gnu.org/software/bash/manual/bash.html"),
        ),
    ),
    Topic(
        "devops_git_workflows", "Git Workflows & Code Review",
        "How teams change code together: feature branches and pull requests, reviewing code, GitHub "
        "flow and trunk-based development, and keeping branches short-lived.",
        2,
        (
            docs("GitHub docs: GitHub flow", "https://docs.github.com/en/get-started/using-github/github-flow"),
            article("Atlassian: Comparing Git workflows", "https://www.atlassian.com/git/tutorials/comparing-workflows"),
            article("Martin Fowler: Patterns for managing source code branches", "https://martinfowler.com/articles/branching-patterns.html"),
        ),
    ),
    # --- Delivery pipelines ---------------------------------------------------------------------
    Topic(
        "devops_ci", "Continuous Integration",
        "Merging everyone's work often and checking it automatically: builds and tests on every push, "
        "pipelines as code in tools such as GitHub Actions, and fixing a broken build first.",
        3,
        (
            article("Martin Fowler: Continuous integration", "https://martinfowler.com/articles/continuousIntegration.html"),
            docs("GitHub docs: Understanding GitHub Actions", "https://docs.github.com/en/actions/get-started/understand-github-actions"),
            video("DevOps CI/CD Explained in 100 Seconds (Fireship)", "https://www.youtube.com/watch?v=scEDHsr3APg"),
        ),
    ),
    Topic(
        "devops_cd", "Continuous Delivery & Deployment",
        "Getting changes to users safely: deployment pipelines and environments, delivery versus "
        "deployment, blue-green and canary releases, feature flags, and rolling back.",
        3,
        (
            article("Atlassian: Continuous integration vs delivery vs deployment", "https://www.atlassian.com/continuous-delivery/principles/continuous-integration-vs-delivery-vs-deployment"),
            article("Martin Fowler: Blue-green deployment", "https://martinfowler.com/bliki/BlueGreenDeployment.html"),
            article("Martin Fowler: Canary release", "https://martinfowler.com/bliki/CanaryRelease.html"),
        ),
    ),
    Topic(
        "devops_containers", "Containers & Docker",
        "Packaging an app with everything it needs: images and containers, Dockerfiles and layers, "
        "registries, ports and volumes, Docker Compose, and how containers differ from virtual machines.",
        3,
        (
            video("Docker in 100 Seconds (Fireship)", "https://www.youtube.com/watch?v=Gjnup-PuquQ"),
            docs("Docker docs: What is Docker?", "https://docs.docker.com/get-started/docker-overview/"),
            docs("Docker docs: Docker Compose", "https://docs.docker.com/compose/"),
        ),
    ),
    Topic(
        "devops_kubernetes", "Kubernetes",
        "Running containers across many machines: clusters and nodes, pods, deployments and services, "
        "describing the desired state in YAML, self-healing and scaling.",
        4,
        (
            video("Kubernetes Explained in 100 Seconds (Fireship)", "https://www.youtube.com/watch?v=PziYflu8cB8"),
            docs("Kubernetes docs: Overview", "https://kubernetes.io/docs/concepts/overview/"),
            docs("Kubernetes docs: Learn Kubernetes basics", "https://kubernetes.io/docs/tutorials/kubernetes-basics/"),
        ),
    ),
    Topic(
        "devops_iac", "Infrastructure as Code",
        "Describing servers, networks and databases in files: declarative tools such as Terraform, "
        "plan and apply, state, drift, and reviewing infrastructure changes like code.",
        3,
        (
            video("Terraform in 100 Seconds (Fireship)", "https://www.youtube.com/watch?v=tomUWcQ0P3k"),
            docs("HashiCorp: What is Terraform?", "https://developer.hashicorp.com/terraform/intro"),
            article("AWS: What is infrastructure as code?", "https://aws.amazon.com/what-is/iac/"),
        ),
    ),
    Topic(
        "devops_config_management", "Configuration Management",
        "Keeping many servers configured the same way: Ansible playbooks and inventories, idempotent "
        "tasks, and replacing servers instead of changing them by hand.",
        3,
        (
            docs("Ansible docs: Introduction to Ansible", "https://docs.ansible.com/projects/ansible/latest/getting_started/introduction.html"),
            article("Red Hat: What is configuration management?", "https://www.redhat.com/en/topics/automation/what-is-configuration-management"),
        ),
    ),
    # --- The cloud --------------------------------------------------------------------------------
    Topic(
        "cloud_computing_basics", "Cloud Computing Concepts",
        "Renting computing instead of owning it: on-demand resources and pay-as-you-go, IaaS, PaaS and "
        "SaaS, public, private and hybrid clouds, and regions and availability zones.",
        1,
        (
            article("AWS: What is cloud computing?", "https://aws.amazon.com/what-is-cloud-computing/"),
            article("AWS: Types of cloud computing (IaaS, PaaS, SaaS)", "https://aws.amazon.com/types-of-cloud-computing/"),
            article("Google Cloud: What is cloud computing?", "https://cloud.google.com/learn/what-is-cloud-computing"),
        ),
    ),
    Topic(
        "cloud_compute", "Virtual Machines & Autoscaling",
        "Running servers in the cloud: virtual machine instances and their sizes, machine images, "
        "load balancers spreading traffic, and autoscaling groups that add and remove instances.",
        2,
        (
            docs("AWS docs: What is Amazon EC2 Auto Scaling?", "https://docs.aws.amazon.com/autoscaling/ec2/userguide/what-is-amazon-ec2-auto-scaling.html"),
            article("Azure: What is cloud computing?", "https://azure.microsoft.com/en-us/resources/cloud-computing-dictionary/what-is-cloud-computing"),
        ),
    ),
    Topic(
        "cloud_storage", "Cloud Storage",
        "Where cloud data lives: object, block and file storage, buckets such as Amazon S3, durability "
        "versus availability, storage classes, and managed database services.",
        2,
        (
            article("AWS: What is cloud storage?", "https://aws.amazon.com/what-is/cloud-storage/"),
            docs("AWS docs: What is Amazon S3?", "https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html"),
        ),
    ),
    Topic(
        "cloud_iam", "Cloud Identity & Access",
        "Deciding who and what can use cloud resources: users, groups and roles, JSON policies that "
        "allow and deny, least privilege, temporary credentials, and protecting the root account.",
        3,
        (
            docs("AWS docs: What is IAM?", "https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html"),
            docs("AWS docs: Security best practices in IAM", "https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html"),
        ),
    ),
    Topic(
        "cloud_networking", "Cloud Networking",
        "Private networks in the cloud: virtual private clouds, public and private subnets, route "
        "tables, internet and NAT gateways, security groups and network ACLs.",
        3,
        (
            docs("AWS docs: What is Amazon VPC?", "https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html"),
            docs("AWS docs: How Amazon VPC works", "https://docs.aws.amazon.com/vpc/latest/userguide/how-it-works.html"),
        ),
    ),
    Topic(
        "cloud_serverless", "Serverless & Functions",
        "Running code without managing servers: functions triggered by events, scaling to zero, cold "
        "starts, keeping functions stateless, and paying per request.",
        3,
        (
            article("AWS: What is serverless computing?", "https://aws.amazon.com/what-is/serverless-computing/"),
            docs("AWS docs: What is AWS Lambda?", "https://docs.aws.amazon.com/lambda/latest/dg/welcome.html"),
            article("IBM: What is serverless computing?", "https://www.ibm.com/think/topics/serverless"),
        ),
    ),
    Topic(
        "cloud_architecture", "Cloud Architecture & Cost",
        "Designing systems for the cloud: the well-architected pillars, surviving the loss of a zone, "
        "scaling out, twelve-factor apps, and keeping the bill under control.",
        4,
        (
            docs("AWS Well-Architected Framework", "https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html"),
            docs("Google Cloud Well-Architected Framework", "https://docs.cloud.google.com/architecture/framework"),
            article("The Twelve-Factor App", "https://12factor.net/"),
        ),
    ),
    # --- Running in production --------------------------------------------------------------------
    Topic(
        "devops_monitoring", "Monitoring & Observability",
        "Knowing what a running system is doing: metrics, logs and traces, Prometheus and dashboards, "
        "the four golden signals, and alerting on what users actually feel.",
        3,
        (
            docs("OpenTelemetry: Observability primer", "https://opentelemetry.io/docs/concepts/observability-primer/"),
            docs("Prometheus: Overview", "https://prometheus.io/docs/introduction/overview/"),
            article("Google SRE book: Monitoring distributed systems", "https://sre.google/sre-book/monitoring-distributed-systems/"),
        ),
    ),
    Topic(
        "devops_sre", "Site Reliability Engineering",
        "Running services reliably at scale: service level indicators and objectives, error budgets, "
        "on-call, blameless postmortems, and reducing toil.",
        4,
        (
            article("Google SRE book: Service level objectives", "https://sre.google/sre-book/service-level-objectives/"),
            article("Google SRE book: Postmortem culture", "https://sre.google/sre-book/postmortem-culture/"),
            article("AWS: What is site reliability engineering?", "https://aws.amazon.com/what-is/sre/"),
        ),
    ),
    Topic(
        "devops_devsecops", "DevSecOps & Supply Chain",
        "Building security into delivery: security checks in the pipeline, managing secrets, scanning "
        "dependencies and container images, and trusting what you build and deploy.",
        4,
        (
            article("Red Hat: What is DevSecOps?", "https://www.redhat.com/en/topics/devops/what-is-devsecops"),
            article("IBM: What is DevSecOps?", "https://www.ibm.com/think/topics/devsecops"),
            docs("SLSA: Supply-chain levels for software artifacts", "https://slsa.dev/"),
        ),
    ),
)

PREREQUISITES: tuple[tuple[str, str], ...] = (
    ("operating_system_basics", "devops_linux_admin"),
    ("command_line_basics", "devops_shell_scripting"),
    ("devops_culture", "devops_git_workflows"),
    ("git_basics", "devops_git_workflows"),

    ("devops_git_workflows", "devops_ci"),
    ("devops_shell_scripting", "devops_ci"),
    ("devops_ci", "devops_cd"),
    ("devops_linux_admin", "devops_containers"),
    ("devops_containers", "devops_kubernetes"),
    ("cloud_networking", "devops_kubernetes"),
    ("cloud_computing_basics", "devops_iac"),
    ("devops_git_workflows", "devops_iac"),
    ("devops_linux_admin", "devops_config_management"),
    ("devops_shell_scripting", "devops_config_management"),

    ("how_the_internet_works", "cloud_computing_basics"),
    ("cloud_computing_basics", "cloud_compute"),
    ("cloud_computing_basics", "cloud_storage"),
    ("cloud_computing_basics", "cloud_iam"),
    ("security_basics", "cloud_iam"),
    ("cloud_compute", "cloud_networking"),
    ("cloud_compute", "cloud_serverless"),
    ("cloud_networking", "cloud_architecture"),
    ("cloud_storage", "cloud_architecture"),
    ("cloud_iam", "cloud_architecture"),

    ("devops_linux_admin", "devops_monitoring"),
    ("cloud_compute", "devops_monitoring"),
    ("devops_monitoring", "devops_sre"),
    ("devops_cd", "devops_sre"),
    ("devops_cd", "devops_devsecops"),
    ("devops_containers", "devops_devsecops"),
    ("cloud_iam", "devops_devsecops"),
)

CLOUD_DEVOPS = Domain(
    id="cloud-devops",
    name="Cloud & DevOps",
    description=(
        "Running software reliably: Linux and shell scripting, Git workflows and CI/CD pipelines, "
        "containers and Kubernetes, infrastructure as code, cloud compute, storage and networking, "
        "and monitoring what runs in production."
    ),
    topics=TOPICS,
    prerequisites=PREREQUISITES,
)
