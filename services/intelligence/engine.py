"""
Matching Engine and Recommendation Catalog for Sadat Academy Career Matching Platform
"""

import re
import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# Skill Definitions & Regex
# ----------------------------------------------------------------------------
SKILLS = {
    "SQL": r"\b(?:sql|t-sql|pl/sql|mysql|postgres(?:ql)?|sql server)\b",
    "Python": r"\bpython\b",
    "R": None,
    "C": None,
    "C++": r"c\+\+",
    "C#": r"c#|c-sharp|c sharp",
    ".NET": r"\.net\b|dotnet|asp\.net",
    "Java": r"\bjava\b(?!\s*script)",
    "JavaScript": r"\bjavascript\b|\bjs\b",
    "TypeScript": r"\btypescript\b",
    "Go": r"\bgolang\b|\bgo\s+(?:language|lang)\b",
    "Scala": r"\bscala\b",
    "Rust": r"\brust\b",
    "PHP": r"\bphp\b",
    "Machine Learning": r"machine[\s-]?learning|\bml\b",
    "Deep Learning": r"deep[\s-]?learning",
    "NLP": r"\bnlp\b|natural language processing",
    "Computer Vision": r"computer vision|\bopencv\b",
    "LLM": r"\bllms?\b|large language models?",
    "RAG": r"\brag\b|retrieval[\s-]augmented",
    "Prompt Engineering": r"prompt[\s-]?engineering",
    "Generative AI": r"gen(?:erative)?[\s-]?ai\b|\bgenai\b",
    "LangChain": r"\blang[\s-]?chain\b|\blanggraph\b|llama[\s-]?index",
    "Vector DB": r"vector (?:db|database|store)|\bpinecone\b|\bfaiss\b|\bchroma(?:db)?\b|\bweaviate\b|\bmilvus\b",
    "TensorFlow": r"\btensorflow\b|\bkeras\b",
    "PyTorch": r"\bpytorch\b",
    "Scikit-learn": r"scikit[\s-]?learn|\bsklearn\b",
    "Hugging Face": r"hugging[\s-]?face|\btransformers\b",
    "NumPy": r"\bnumpy\b",
    "Pandas": r"\bpandas\b",
    "Matplotlib": r"\bmatplotlib\b",
    "Seaborn": r"\bseaborn\b",
    "Spark": r"\bspark\b|\bpyspark\b|\bdatabricks\b",
    "Hadoop": r"\bhadoop\b|\bhive\b",
    "Kafka": r"\bkafka\b",
    "Airflow": r"\bairflow\b",
    "dbt": r"\bdbt\b",
    "ETL": r"\betl\b|\belt\b|data pipelines?",
    "Data Warehouse": r"data warehous\w*|\bsnowflake\b|\bredshift\b|\bbigquery\b|\bsynapse\b",
    "Power BI": r"power[\s-]?bi",
    "Tableau": r"\btableau\b",
    "Excel": r"\bexcel\b",
    "Azure": r"\bazure\b",
    "AWS": r"\baws\b|amazon web services",
    "GCP": r"\bgcp\b|google cloud",
    "Cloud Architecture": r"cloud architect\w*|cloud (?:design|infrastructure)",
    "Docker": r"\bdocker\b",
    "Kubernetes": r"\bkubernetes\b|\bk8s\b",
    "Terraform": r"\bterraform\b",
    "CI/CD": r"ci\s*/\s*cd|\bjenkins\b|github actions|gitlab ci|azure devops",
    "Git": r"\bgit\b|\bgithub\b|\bgitlab\b",
    "Linux": r"\blinux\b|\bunix\b",
    "REST APIs": r"\brest(?:ful)?\b|\bapis?\b",
    "Microservices": r"microservices?",
    "React": r"\breact(?:\.?js)?\b",
    "Angular": r"\bangular\b",
    "Vue": r"\bvue(?:\.?js)?\b",
    "Node.js": r"node\.?js",
    "Django/Flask/FastAPI": r"\bdjango\b|\bflask\b|\bfastapi\b",
    "Spring": r"\bspring(?:\s?boot)?\b",
    "MongoDB": r"\bmongo(?:db)?\b",
    "NoSQL": r"\bnosql\b|\bcassandra\b|\bredis\b|\bdynamodb\b",
    "Selenium": r"\bselenium\b",
    "Test Automation": r"test automation|automated testing|\bcypress\b|\bplaywright\b|\bappium\b|\bpostman\b|\bjmeter\b",
    "Statistics": r"statistic\w*|a/b test\w*|hypothesis testing",
    "Networking": r"\btcp/?ip\b|\bcisco\b|\bccna\b|\bccnp\b|\bbgp\b|\bospf\b|\bvlan\b|\bfirewalls?\b|\bnetworking\b|\bdns\b",
    "SIEM/SOC": r"\bsiem\b|\bsoc\b|\bsplunk\b|\bqradar\b|\bsentinel\b",
    "Pen Testing": r"penetration test\w*|pen[\s-]?test\w*|\bowasp\b|\bburp\b|vulnerabilit\w+|ethical hacking",
    "Security Certs": r"\bcissp\b|\bceh\b|\bcomptia security\+?|\bcism\b|\boscp\b",
    "Agile/Scrum": r"\bagile\b|\bscrum\b|\bjira\b",
    "Data Structures & Algorithms": r"data structures?|\balgorithms?\b|\bdsa\b",
    "Programming Fundamentals": r"\boop\b|object[\s-]oriented|programming fundamentals|programming skills",
    "Operating Systems": r"operating systems?",
    "Software Design (UML/SDLC)": r"\buml\b|\bsdlc\b|design patterns?|software design|software architecture|system design",
    "Business Analysis": r"business analy\w+|requirements? (?:gathering|analysis)|user stories|\bbrd\b",
    "Security Fundamentals": r"information security|cyber[\s-]?security|network security|\bnist\b|iso\s*27001|security (?:controls|best practices|policies)",
    "Communication": r"communication skills?|written and verbal|verbal and written|presentation skills?|teamwork|team player",
    "Embedded/Hardware": r"\bembedded\b|firmware|microcontrollers?|\barduino\b|raspberry pi|\bfpga\b|\brtos\b|\bplc\b",
    "IoT": r"\biot\b|internet of things|\bmqtt\b",
    "Robotics": r"\brobot\w*|robot operating system",
    "AR/VR": r"augmented reality|virtual reality|\bar/vr\b|\bxr\b|\bunity(?:3d)?\b|unreal engine",
    "HCI/UX": r"\bux\b|ui/ux|user experience|usability|\bfigma\b|wireframes?|human[\s-]computer interaction|\bhci\b",
    "Speech Processing": r"speech (?:recognition|processing|synthesis)|text[\s-]to[\s-]speech|speech[\s-]to[\s-]text|\basr\b|\btts\b|voice assistants?",
    "Digital Marketing": r"digital marketing|\bseo\b|\bsem\b|social media marketing|google ads|performance marketing",
}

# ----------------------------------------------------------------------------
# Certificates Catalog
# ----------------------------------------------------------------------------
CERTIFICATES = [
    ("Microsoft AZ-900 Azure Fundamentals", "Microsoft", r"\baz[\s-]?900\b|azure fundamentals", ["Azure"]),
    ("Microsoft AZ-104 Azure Administrator", "Microsoft", r"\baz[\s-]?104\b|azure administrator", ["Azure"]),
    ("Microsoft AZ-204 Azure Developer", "Microsoft", r"\baz[\s-]?204\b|azure developer associate", ["Azure"]),
    ("Microsoft AZ-305 Azure Solutions Architect", "Microsoft", r"\baz[\s-]?305\b|azure solutions architect", ["Azure", "Cloud Architecture"]),
    ("Microsoft AZ-400 DevOps Engineer", "Microsoft", r"\baz[\s-]?400\b|azure devops engineer expert", ["Azure", "CI/CD"]),
    ("Microsoft AZ-500 Azure Security Engineer", "Microsoft", r"\baz[\s-]?500\b", ["Azure", "Security Fundamentals"]),
    ("Microsoft AI-900 Azure AI Fundamentals", "Microsoft", r"\bai[\s-]?900\b|azure ai fundamentals", ["Azure", "Machine Learning"]),
    ("Microsoft AI-102 Azure AI Engineer", "Microsoft", r"\bai[\s-]?102\b|azure ai engineer", ["Azure", "Machine Learning", "NLP", "Computer Vision"]),
    ("Microsoft DP-100 Azure Data Scientist", "Microsoft", r"\bdp[\s-]?100\b|azure data scientist", ["Azure", "Machine Learning"]),
    ("Microsoft DP-900 Azure Data Fundamentals", "Microsoft", r"\bdp[\s-]?900\b|azure data fundamentals", ["Azure", "SQL"]),
    ("Microsoft DP-203 Azure Data Engineer", "Microsoft", r"\bdp[\s-]?203\b|azure data engineer", ["Azure", "ETL", "Data Warehouse"]),
    ("Microsoft DP-300 Azure Database Administrator", "Microsoft", r"\bdp[\s-]?300\b", ["Azure", "SQL"]),
    ("Microsoft DP-600/DP-700 Fabric", "Microsoft", r"\bdp[\s-]?(?:600|700)\b|fabric (?:analytics|data) engineer", ["Azure", "Data Warehouse"]),
    ("Microsoft PL-300 Power BI Data Analyst", "Microsoft", r"\bpl[\s-]?300\b|power bi data analyst", ["Power BI"]),
    ("Microsoft SC-900 Security Fundamentals", "Microsoft", r"\bsc[\s-]?900\b", ["Security Fundamentals"]),
    ("Microsoft SC-200 Security Operations Analyst", "Microsoft", r"\bsc[\s-]?200\b", ["SIEM/SOC", "Azure"]),
    ("AWS Certified Cloud Practitioner", "AWS", r"aws (?:certified )?cloud practitioner|\bclf[\s-]?c0\d\b", ["AWS"]),
    ("AWS Certified Solutions Architect - Associate", "AWS", r"aws (?:certified )?solutions? architect|\bsaa[\s-]?c0\d\b", ["AWS", "Cloud Architecture"]),
    ("AWS Certified Developer - Associate", "AWS", r"aws (?:certified )?developer|\bdva[\s-]?c0\d\b", ["AWS"]),
    ("AWS Certified SysOps/DevOps", "AWS", r"aws (?:certified )?(?:sysops|devops)", ["AWS", "CI/CD"]),
    ("AWS Certified Data Engineer - Associate", "AWS", r"aws (?:certified )?data engineer|\bdea[\s-]?c0\d\b", ["AWS", "ETL", "Data Warehouse"]),
    ("AWS Certified Machine Learning - Associate", "AWS", r"aws (?:certified )?machine learning|\bmla[\s-]?c0\d\b|\bmls[\s-]?c0\d\b", ["AWS", "Machine Learning"]),
    ("AWS Certified AI Practitioner", "AWS", r"aws (?:certified )?ai practitioner", ["AWS", "LLM", "Generative AI"]),
    ("Google Associate Cloud Engineer", "Google", r"associate cloud engineer", ["GCP"]),
    ("Google Professional Cloud Architect", "Google", r"professional cloud architect", ["GCP", "Cloud Architecture"]),
    ("Google Professional Data Engineer", "Google", r"professional data engineer", ["GCP", "ETL", "Data Warehouse"]),
    ("Google Professional Machine Learning Engineer", "Google", r"professional machine learning engineer", ["GCP", "Machine Learning"]),
    ("Google Data Analytics Certificate", "Google", r"google data analytics|google analytics certif\w*", ["SQL", "Excel", "Tableau", "R"]),
    ("CompTIA Security+", "CompTIA", r"comptia security\+?|\bsecurity\+", ["Security Fundamentals"]),
    ("CompTIA Network+", "CompTIA", r"comptia network\+?|\bnetwork\+", ["Networking"]),
    ("CompTIA CySA+", "CompTIA", r"\bcysa\+?", ["SIEM/SOC"]),
    ("CISSP", "ISC2", r"\bcissp\b", ["Security Fundamentals"]),
    ("CEH (Certified Ethical Hacker)", "EC-Council", r"\bceh\b|certified ethical hacker", ["Pen Testing"]),
    ("OSCP", "OffSec", r"\boscp\b", ["Pen Testing"]),
    ("CISM / CISA", "ISACA", r"\bcism\b|\bcisa\b", ["Security Fundamentals"]),
    ("Cisco CCNA", "Cisco", r"\bccna\b", ["Networking"]),
    ("Cisco CCNP", "Cisco", r"\bccnp\b", ["Networking"]),
    ("Kubernetes CKA/CKAD", "CNCF", r"\bckad?\b|certified kubernetes (?:administrator|application developer)", ["Kubernetes", "Docker"]),
    ("HashiCorp Terraform Associate", "HashiCorp", r"terraform associate", ["Terraform"]),
    ("Red Hat RHCSA/RHCE", "Red Hat", r"\brhcsa\b|\brhce\b", ["Linux"]),
    ("Linux LPIC / CompTIA Linux+", "Linux", r"\blpic\b|comptia linux\+?|linux\+", ["Linux"]),
    ("Oracle Certified Java Programmer", "Oracle", r"oracle certified (?:associate|professional)|\bocpjp\b|\bocajp\b", ["Java"]),
    ("Databricks Certification", "Databricks", r"databricks certified|databricks (?:data engineer|associate)", ["Spark"]),
    ("Snowflake SnowPro", "Snowflake", r"\bsnowpro\b", ["Data Warehouse"]),
    ("Tableau Desktop Specialist", "Tableau", r"tableau (?:desktop )?(?:specialist|certified)", ["Tableau"]),
    ("IBM Data Science Certificate", "IBM", r"ibm data science", ["Python", "SQL", "Machine Learning"]),
    ("DeepLearning.AI Specialization", "DeepLearning.AI", r"deeplearning\.ai", ["Deep Learning", "Machine Learning"]),
    ("Scrum (CSM / PSM)", "Scrum", r"\bcsm\b|\bpsm\b|certified scrum master|professional scrum master", ["Agile/Scrum"]),
    ("ISTQB Certified Tester", "ISTQB", r"\bistqb\b", ["Test Automation"]),
]

CERT_MAP = {c[0]: c[3] for c in CERTIFICATES}

# ----------------------------------------------------------------------------
# The 14 In-Demand Missing Skills with Free Tests & Resources
# ----------------------------------------------------------------------------
MISSING_SKILLS_14 = [
    {
        "id": "Python",
        "name": "Python",
        "category": "Programming",
        "test_name": "HackerRank Python Skills Certification",
        "test_provider": "HackerRank",
        "test_cost": "Free",
        "test_url": "https://www.hackerrank.com/skills-verification/python_basic",
        "test_desc": "Covers Python basics, control flow, functions, OOP, and data structures.",
        "icon": "fab fa-python",
        "prep_course": "Kaggle Learn: Python (Free Micro-Course)"
    },
    {
        "id": "SQL",
        "name": "SQL & Relational Databases",
        "category": "Data & Databases",
        "test_name": "LearnSQL Skill Assessment (Certificate at 70%+)",
        "test_provider": "LearnSQL / HackerRank",
        "test_cost": "Free",
        "test_url": "https://learnsql.com/assessment-test/",
        "test_desc": "Hands-on assessment: complex queries, JOINs, aggregations, and subqueries.",
        "icon": "fas fa-database",
        "prep_course": "Kaggle Learn: Intro to SQL & HackerRank SQL (Basic/Intermediate)"
    },
    {
        "id": "REST APIs",
        "name": "REST APIs & Web Services",
        "category": "Backend Engineering",
        "test_name": "HackerRank REST API (Intermediate) Skills Assessment",
        "test_provider": "HackerRank",
        "test_cost": "Free",
        "test_url": "https://www.hackerrank.com/skills-verification/rest_api_intermediate",
        "test_desc": "HTTP methods, payload parsing, endpoint integration, and JSON APIs.",
        "icon": "fas fa-network-wired",
        "prep_course": "Postman API Fundamentals Student Expert (Free Certification)"
    },
    {
        "id": "Docker",
        "name": "Docker & Containerization",
        "category": "DevOps & Cloud",
        "test_name": "KodeKloud Docker Essentials Free Challenge",
        "test_provider": "KodeKloud / Docker",
        "test_cost": "Free",
        "test_url": "https://kodekloud.com/courses/docker-for-the-absolute-beginner/",
        "test_desc": "Hands-on containerization, Dockerfile creation, multi-stage builds, and volumes.",
        "icon": "fab fa-docker",
        "prep_course": "Docker Official Getting Started Tutorial & Hands-on labs"
    },
    {
        "id": "Kubernetes",
        "name": "Kubernetes & Orchestration",
        "category": "DevOps & Cloud",
        "test_name": "Killercoda Interactive Kubernetes Scenario Labs",
        "test_provider": "Killercoda / CNCF",
        "test_cost": "Free",
        "test_url": "https://killercoda.com/playgrounds/scenario/kubernetes",
        "test_desc": "Pod management, Deployments, Services, ConfigMaps, and ingress in real cluster.",
        "icon": "fas fa-dharmachakra",
        "prep_course": "CNCF Kubernetes Fundamentals & CKAD Free Practice Labs"
    },
    {
        "id": "AWS",
        "name": "AWS Cloud Services",
        "category": "Cloud Computing",
        "test_name": "AWS Skill Builder Official Practice Question Set (Cloud Practitioner & ML)",
        "test_provider": "AWS",
        "test_cost": "Free",
        "test_url": "https://explore.skillbuilder.aws/learn/course/external/view/elearning/14050/aws-certified-cloud-practitioner-official-practice-question-set",
        "test_desc": "Official 20-question practice test with diagnostic score report and answers.",
        "icon": "fab fa-aws",
        "prep_course": "AWS Educate & Skill Builder Free Learning Pathways"
    },
    {
        "id": "Azure",
        "name": "Microsoft Azure Cloud",
        "category": "Cloud Computing",
        "test_name": "Microsoft Learn Free Practice Assessment (AZ-900 / DP-100 / AI-900)",
        "test_provider": "Microsoft",
        "test_cost": "Free",
        "test_url": "https://learn.microsoft.com/en-us/credentials/certifications/azure-fundamentals/practice/assessment?assessment-type=practice&assessmentId=23",
        "test_desc": "50-question official practice test providing detailed competency report.",
        "icon": "fab fa-microsoft",
        "prep_course": "Microsoft Learn Cloud Skills Challenges"
    },
    {
        "id": "React",
        "name": "React.js & Frontend",
        "category": "Frontend Engineering",
        "test_name": "HackerRank React (Basic) Skills Certification",
        "test_provider": "HackerRank",
        "test_cost": "Free",
        "test_url": "https://www.hackerrank.com/skills-verification/react_basic",
        "test_desc": "React hooks, component lifecycle, state management, props, and JSX rendering.",
        "icon": "fab fa-react",
        "prep_course": "Scrimba Learn React Free Interactive Course"
    },
    {
        "id": "Node.js",
        "name": "Node.js & Express",
        "category": "Backend Engineering",
        "test_name": "HackerRank Node.js (Basic/Intermediate) Certification",
        "test_provider": "HackerRank",
        "test_cost": "Free",
        "test_url": "https://www.hackerrank.com/skills-verification/node_basic",
        "test_desc": "Asynchronous event loop, Express routing, middleware, and streams.",
        "icon": "fab fa-node-js",
        "prep_course": "The Odin Project: NodeJS Course (Free Open Source)"
    },
    {
        "id": "JavaScript",
        "name": "JavaScript (ES6+)",
        "category": "Web Development",
        "test_name": "HackerRank JavaScript (Basic & Intermediate)",
        "test_provider": "HackerRank",
        "test_cost": "Free",
        "test_url": "https://www.hackerrank.com/skills-verification/javascript_basic",
        "test_desc": "Promises, closures, prototypes, async/await, and array manipulation.",
        "icon": "fab fa-js",
        "prep_course": "freeCodeCamp JavaScript Algorithms & Data Structures"
    },
    {
        "id": "Test Automation",
        "name": "Test Automation & QA (Selenium/Cypress)",
        "category": "Quality Assurance",
        "test_name": "TestAutomationU Free Certification Exams",
        "test_provider": "Test Automation University (Applitools)",
        "test_cost": "Free",
        "test_url": "https://testautomationu.applitools.com/",
        "test_desc": "Test suites, locator strategies, Selenium WebDriver, Cypress, and CI integration.",
        "icon": "fas fa-vial",
        "prep_course": "TAU Web UI Automation with Selenium in Python / Java"
    },
    {
        "id": "Power BI",
        "name": "Power BI & Business Intelligence",
        "category": "Data & Analytics",
        "test_name": "Microsoft Learn PL-300 Official Practice Assessment",
        "test_provider": "Microsoft",
        "test_cost": "Free",
        "test_url": "https://learn.microsoft.com/en-us/credentials/certifications/data-analyst-associate/practice/assessment?assessment-type=practice&assessmentId=48",
        "test_desc": "Data modeling, DAX measures, Power Query transformations, and executive dashboards.",
        "icon": "fas fa-chart-pie",
        "prep_course": "Microsoft Learn: Get started with Power BI Desktop (Free)"
    },
    {
        "id": "CI/CD",
        "name": "CI/CD & DevOps Automation",
        "category": "DevOps",
        "test_name": "GitHub Actions Official Skills Course & Assessment",
        "test_provider": "GitHub Skills",
        "test_cost": "Free",
        "test_url": "https://skills.github.com/",
        "test_desc": "Automated build, test, and deploy pipelines with GitHub Actions workflows.",
        "icon": "fas fa-sync-alt",
        "prep_course": "GitLab CI/CD Fundamentals & GitHub Actions Documentation"
    },
    {
        "id": "Git",
        "name": "Git & Version Control",
        "category": "Software Engineering",
        "test_name": "Learn Git Branching Interactive Challenge",
        "test_provider": "LearnGitBranching",
        "test_cost": "Free",
        "test_url": "https://learngitbranching.js.org/",
        "test_desc": "Branching, rebasing, merge conflict resolution, cherry-pick, and pull request flows.",
        "icon": "fab fa-git-alt",
        "prep_course": "Atlassian Git Tutorials & GitHub Skills: Introduction to GitHub"
    }
]

# ----------------------------------------------------------------------------
# Recommendation Catalog Options
# ----------------------------------------------------------------------------
def _o(kind, name, provider, cost, note="", url=""):
    return {"kind": kind, "name": name, "provider": provider, "cost": cost, "note": note, "url": url}

HR = lambda skill, lvl="Basic", url="https://www.hackerrank.com/skills-verification": _o(
    "test", f"HackerRank {skill} ({lvl}) skills certification", "HackerRank", "free", "Official free certification badge", url
)
KAGGLE = lambda c, url="https://www.kaggle.com/learn": _o(
    "course", f"Kaggle Learn: {c}", "Kaggle", "free", "Hands-on micro-course with certificate", url
)

RECOMMENDATIONS = {
    "Machine Learning": [
        _o("certificate", "AWS Certified Machine Learning Engineer - Associate", "AWS", "paid exam", "Validates ML engineering, pipelines & model deployment on AWS", "https://aws.amazon.com/certification/certified-machine-learning-engineer-associate/"),
        _o("certificate", "Microsoft Azure Data Scientist Associate (DP-100)", "Microsoft", "paid exam", "Design and prepare ML solutions on Azure Machine Learning", "https://learn.microsoft.com/en-us/credentials/certifications/azure-data-scientist/"),
        _o("certificate", "Google Professional Machine Learning Engineer", "Google Cloud", "paid exam", "Build and scale production ML models on Google Cloud Vertex AI", "https://cloud.google.com/learn/certification/machine-learning-engineer"),
        KAGGLE("Intro to Machine Learning", "https://www.kaggle.com/learn/intro-to-machine-learning"),
        KAGGLE("Intermediate Machine Learning", "https://www.kaggle.com/learn/intermediate-machine-learning")
    ],
    "Deep Learning": [
        _o("certificate", "AWS Certified Machine Learning Engineer - Associate", "AWS", "paid exam", "Covers deep learning architectures, CNNs, transformers & deployment", "https://aws.amazon.com/certification/certified-machine-learning-engineer-associate/"),
        _o("course", "DeepLearning.AI Deep Learning Specialization", "Coursera / DeepLearning.AI", "unknown", "Five-course series by Andrew Ng on neural networks & DL architectures", "https://www.deeplearning.ai/courses/deep-learning-specialization/"),
        KAGGLE("Computer Vision with Deep Learning", "https://www.kaggle.com/learn/computer-vision")
    ],
    "NLP": [
        _o("certificate", "Microsoft Azure AI Engineer Associate (AI-102)", "Microsoft", "paid exam", "Build NLP, Speech and Cognitive Search solutions", "https://learn.microsoft.com/en-us/credentials/certifications/azure-ai-engineer/"),
        _o("course", "DeepLearning.AI Natural Language Processing Specialization", "DeepLearning.AI", "unknown", "Sentiment analysis, translation, transformers and attention", "https://www.deeplearning.ai/courses/natural-language-processing-specialization/"),
        HR("Python", "Intermediate", "https://www.hackerrank.com/skills-verification/python_basic")
    ],
    "Computer Vision": [
        _o("certificate", "Microsoft Azure AI Engineer Associate (AI-102)", "Microsoft", "paid exam", "Covers Vision APIs, custom vision and video indexing", "https://learn.microsoft.com/en-us/credentials/certifications/azure-ai-engineer/"),
        _o("project", "Build an end-to-end YOLOv8 object detection or segmentation project on GitHub", "Self-Directed", "free", "Deploy on Streamlit or Hugging Face Spaces", "https://github.com/")
    ],
    "LLM": [
        _o("certificate", "AWS Certified AI Practitioner", "AWS", "paid exam", "Covers LLM foundations, Bedrock, and generative AI security", "https://aws.amazon.com/certification/certified-ai-practitioner/"),
        _o("certificate", "Microsoft Azure AI Engineer Associate (AI-102)", "Microsoft", "paid exam", "Deploy Azure OpenAI models, completions and fine-tuning", "https://learn.microsoft.com/en-us/credentials/certifications/azure-ai-engineer/"),
        _o("course", "DeepLearning.AI Generative AI with Large Language Models", "DeepLearning.AI", "free", "In-depth training on transformer fine-tuning, RLHF and evaluation", "https://www.deeplearning.ai/courses/generative-ai-with-llms/")
    ],
    "Generative AI": [
        _o("certificate", "AWS Certified AI Practitioner", "AWS", "paid exam", "Official generative AI credential", "https://aws.amazon.com/certification/certified-ai-practitioner/"),
        _o("certificate", "Microsoft Azure AI Fundamentals (AI-900)", "Microsoft", "paid exam", "Fundamental GenAI concepts and responsible AI", "https://learn.microsoft.com/en-us/credentials/certifications/azure-ai-fundamentals/"),
        _o("practice", "Microsoft Learn AI-900 Practice Assessment", "Microsoft", "free", "Official practice assessment", "https://learn.microsoft.com/en-us/credentials/certifications/azure-ai-fundamentals/practice/assessment?assessment-type=practice&assessmentId=24")
    ],
    "Python": [
        HR("Python", "Basic", "https://www.hackerrank.com/skills-verification/python_basic"),
        KAGGLE("Python", "https://www.kaggle.com/learn/python"),
        _o("project", "Publish a modular Python package with unit tests and type hints on GitHub", "Self-Directed", "free", "Build portfolio evidence", "https://github.com/")
    ],
    "SQL": [
        _o("test", "LearnSQL SQL Skill Assessment (Certificate at 70%+)", "LearnSQL", "free", "Hands-on 18 real queries assessment", "https://learnsql.com/assessment-test/"),
        HR("SQL", "Basic", "https://www.hackerrank.com/skills-verification/sql_basic"),
        HR("SQL", "Intermediate", "https://www.hackerrank.com/skills-verification/sql_intermediate"),
        _o("certificate", "Microsoft Azure Data Fundamentals (DP-900)", "Microsoft", "paid exam", "Validates core relational and non-relational database concepts", "https://learn.microsoft.com/en-us/credentials/certifications/azure-data-fundamentals/")
    ],
    "Pandas": [
        KAGGLE("Pandas", "https://www.kaggle.com/learn/pandas"),
        _o("project", "Perform exploratory data analysis on a real Egyptian market dataset and share the notebook", "Self-Directed", "free", "Share on Kaggle / GitHub", "https://www.kaggle.com/")
    ],
    "Matplotlib": [
        KAGGLE("Data Visualization", "https://www.kaggle.com/learn/data-visualization"),
        _o("project", "Create an interactive data dashboard with Seaborn or Plotly", "Self-Directed", "free", "Demonstrates visual communication", "https://github.com/")
    ],
    "Statistics": [
        _o("course", "Google Data Analytics Professional Certificate", "Google", "unknown", "Comprehensive statistical analysis and hypothesis testing", "https://www.coursera.org/professional-certificates/google-data-analytics"),
        KAGGLE("Intro to Statistical Learning", "https://www.kaggle.com/learn")
    ],
    "Excel": [
        _o("course", "Google Data Analytics Professional Certificate (Spreadsheets)", "Google", "unknown", "Data analysis using advanced Excel/Sheets", "https://www.coursera.org/professional-certificates/google-data-analytics")
    ],
    "Power BI": [
        _o("certificate", "Microsoft Power BI Data Analyst (PL-300)", "Microsoft", "paid exam", "The premier business intelligence certification", "https://learn.microsoft.com/en-us/credentials/certifications/data-analyst-associate/"),
        _o("practice", "Microsoft Learn PL-300 Official Practice Assessment", "Microsoft", "free", "50 official questions", "https://learn.microsoft.com/en-us/credentials/certifications/data-analyst-associate/practice/assessment?assessment-type=practice&assessmentId=48")
    ],
    "Tableau": [
        _o("certificate", "Tableau Desktop Specialist", "Tableau", "paid exam", "Official Tableau visual analytics certification", "https://www.tableau.com/learn/certification/desktop-specialist")
    ],
    "ETL": [
        _o("certificate", "AWS Certified Data Engineer - Associate", "AWS", "paid exam", "ETL pipelines, Glue, Athena, Redshift", "https://aws.amazon.com/certification/certified-data-engineer-associate/"),
        _o("certificate", "Microsoft Azure Data Engineer Associate (DP-203)", "Microsoft", "paid exam", "Azure Data Factory, Synapse, Databricks ETL", "https://learn.microsoft.com/en-us/credentials/certifications/azure-data-engineer/"),
        _o("project", "Build an automated data pipeline using Python, SQL and Airflow or dbt", "Self-Directed", "free", "Demonstrates pipeline architecture", "https://github.com/")
    ],
    "Data Warehouse": [
        _o("certificate", "Snowflake SnowPro Core", "Snowflake", "paid exam", "Leading cloud data warehousing certification", "https://www.snowflake.com/en/resources/learn/certifications/"),
        _o("certificate", "Microsoft DP-600 Fabric Analytics Engineer", "Microsoft", "paid exam", "Lakehouse, warehouse, and semantic modeling", "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/")
    ],
    "Spark": [
        _o("certificate", "Databricks Certified Data Engineer Associate", "Databricks", "paid exam", "PySpark, Lakehouse, and Delta Lake engineering", "https://www.databricks.com/learn/certification/data-engineer-associate")
    ],
    "Azure": [
        _o("certificate", "Microsoft Azure Fundamentals (AZ-900)", "Microsoft", "paid exam", "Essential cloud credential recognized everywhere", "https://learn.microsoft.com/en-us/credentials/certifications/azure-fundamentals/"),
        _o("practice", "Microsoft Learn AZ-900 Practice Assessment", "Microsoft", "free", "Score report and detailed question explanations", "https://learn.microsoft.com/en-us/credentials/certifications/azure-fundamentals/practice/assessment?assessment-type=practice&assessmentId=23")
    ],
    "AWS": [
        _o("certificate", "AWS Certified Cloud Practitioner", "AWS", "paid exam", "Industry-standard cloud certification", "https://aws.amazon.com/certification/certified-cloud-practitioner/"),
        _o("practice", "AWS Skill Builder Official Practice Question Set", "AWS", "free", "Official practice questions", "https://explore.skillbuilder.aws/")
    ],
    "GCP": [
        _o("certificate", "Google Associate Cloud Engineer", "Google Cloud", "paid exam", "Deploy apps, monitor operations, and manage enterprise solutions", "https://cloud.google.com/learn/certification/cloud-engineer")
    ],
    "Cloud Architecture": [
        _o("certificate", "AWS Certified Solutions Architect - Associate", "AWS", "paid exam", "Top-demanded architecture certification globally", "https://aws.amazon.com/certification/certified-solutions-architect-associate/"),
        _o("certificate", "Microsoft Azure Solutions Architect Expert (AZ-305)", "Microsoft", "paid exam", "Advanced infrastructure and design expert credential", "https://learn.microsoft.com/en-us/credentials/certifications/azure-solutions-architect/")
    ],
    "Docker": [
        _o("certificate", "Kubernetes CKAD (includes containers)", "CNCF", "paid exam", "Hands-on containerization and orchestration", "https://www.cncf.io/certification/ckad/"),
        _o("project", "Containerize your graduation project with a multi-stage Dockerfile and Docker Compose", "Self-Directed", "free", "Deploy on GitHub", "https://github.com/")
    ],
    "Kubernetes": [
        _o("certificate", "Kubernetes CKA (Administrator) or CKAD (Developer)", "CNCF", "paid exam", "Hands-on lab exam recognized globally", "https://www.cncf.io/certification/cka/"),
        _o("test", "Killercoda Kubernetes Free Hands-on Sandbox", "Killercoda", "free", "Free interactive browser cluster", "https://killercoda.com/")
    ],
    "CI/CD": [
        _o("certificate", "Microsoft DevOps Engineer Expert (AZ-400)", "Microsoft", "paid exam", "Continuous integration, delivery and agile pipelines", "https://learn.microsoft.com/en-us/credentials/certifications/devops-engineer/"),
        _o("project", "Add an automated GitHub Actions CI/CD workflow with linting and unit testing to your project", "Self-Directed", "free", "High employer demand", "https://github.com/")
    ],
    "Terraform": [
        _o("certificate", "HashiCorp Terraform Associate", "HashiCorp", "paid exam", "Infrastructure as Code across multi-cloud environments", "https://www.hashicorp.com/certification/terraform-associate")
    ],
    "Linux": [
        _o("certificate", "Red Hat RHCSA (Certified System Administrator)", "Red Hat", "paid exam", "Hands-on enterprise Linux credential", "https://www.redhat.com/en/services/certification/rhcsa"),
        _o("certificate", "CompTIA Linux+ / LPIC-1", "CompTIA", "paid exam", "Covers Linux system administration and shell scripting", "https://www.comptia.org/certifications/linux")
    ],
    "Git": [
        _o("project", "Keep all your coursework and graduation projects in public GitHub repositories with clean READMEs", "Self-Directed", "free", "Portfolio requirement for tech interviews", "https://github.com/"),
        _o("test", "LearnGitBranching Interactive Mastery", "LearnGitBranching", "free", "Hands-on branching and conflict practice", "https://learngitbranching.js.org/")
    ],
    "REST APIs": [
        HR("REST API", "Intermediate", "https://www.hackerrank.com/skills-verification/rest_api_intermediate"),
        _o("project", "Build and document a RESTful CRUD API with FastAPI or Express and Swagger/OpenAPI docs", "Self-Directed", "free", "Live deployed endpoint", "https://github.com/")
    ],
    "Microservices": [
        _o("certificate", "AWS Certified Developer - Associate", "AWS", "paid exam", "Distributed systems, serverless and APIs", "https://aws.amazon.com/certification/certified-developer-associate/"),
        _o("project", "Decompose a monolithic application into two microservices communicating via HTTP/REST or RabbitMQ", "Self-Directed", "free", "Include Docker Compose", "https://github.com/")
    ],
    "JavaScript": [
        HR("JavaScript", "Basic", "https://www.hackerrank.com/skills-verification/javascript_basic"),
        HR("JavaScript", "Intermediate", "https://www.hackerrank.com/skills-verification/javascript_intermediate")
    ],
    "Java": [
        HR("Java", "Basic", "https://www.hackerrank.com/skills-verification/java_basic"),
        _o("certificate", "Oracle Certified Java Professional", "Oracle", "paid exam", "Java standard edition developer certification", "https://education.oracle.com/")
    ],
    "React": [
        HR("React", "Basic", "https://www.hackerrank.com/skills-verification/react_basic"),
        _o("project", "Build an interactive single-page web app with React and Tailwind CSS connecting to an API", "Self-Directed", "free", "Portfolio centerpiece", "https://github.com/")
    ],
    "Angular": [
        HR("Angular", "Basic", "https://www.hackerrank.com/skills-verification/angular_basic")
    ],
    "Node.js": [
        HR("Node.js", "Basic", "https://www.hackerrank.com/skills-verification/node_basic"),
        HR("Node.js", "Intermediate", "https://www.hackerrank.com/skills-verification/node_intermediate")
    ],
    "C#": [
        HR("C#", "Basic", "https://www.hackerrank.com/skills-verification/csharp_basic"),
        _o("project", "Build an ASP.NET Core Web API with Entity Framework and SQL Server", "Self-Directed", "free", "Standard enterprise stack", "https://github.com/")
    ],
    "R": [
        HR("R", "Basic", "https://www.hackerrank.com/skills-verification")
    ],
    "Go": [
        HR("Go", "Basic", "https://www.hackerrank.com/skills-verification")
    ],
    "Test Automation": [
        _o("certificate", "ISTQB Certified Tester Foundation Level", "ISTQB", "paid exam", "Internationally standardized QA methodology credential", "https://www.istqb.org/"),
        _o("test", "Test Automation University Free Course Tracks", "TAU Applitools", "free", "Selenium, Cypress, and Playwright certifications", "https://testautomationu.applitools.com/")
    ],
    "Agile/Scrum": [
        _o("certificate", "Professional Scrum Master I (PSM I)", "Scrum.org", "paid exam", "Lifetime credential recognized globally without renewal fees", "https://www.scrum.org/assessments/professional-scrum-master-i-certification")
    ],
    "Networking": [
        _o("certificate", "Cisco CCNA (200-301)", "Cisco", "paid exam", "Industry benchmark for routing, switching, IP services, and security", "https://www.cisco.com/c/en/us/training-events/training-certifications/certifications/associate/ccna.html"),
        _o("certificate", "CompTIA Network+", "CompTIA", "paid exam", "Vendor-neutral networking fundamentals", "https://www.comptia.org/certifications/network")
    ],
    "Security Fundamentals": [
        _o("certificate", "CompTIA Security+", "CompTIA", "paid exam", "Top globally required cybersecurity foundation certification", "https://www.comptia.org/certifications/security"),
        _o("certificate", "Microsoft Security Fundamentals (SC-900)", "Microsoft", "paid exam", "Identity, access, compliance and cloud security", "https://learn.microsoft.com/en-us/credentials/certifications/security-compliance-and-identity-fundamentals/")
    ],
    "Pen Testing": [
        _o("certificate", "CEH (Certified Ethical Hacker)", "EC-Council", "paid exam", "Widely requested in enterprise job postings in Egypt and Gulf", "https://www.eccouncil.org/programs/certified-ethical-hacker-ceh/"),
        _o("certificate", "OffSec OSCP", "OffSec", "paid exam", "Gold-standard practical hands-on penetration testing certification", "https://www.offsec.com/courses/pen-200/")
    ],
    "SIEM/SOC": [
        _o("certificate", "Microsoft Security Operations Analyst (SC-200)", "Microsoft", "paid exam", "Azure Sentinel, Defender, and threat mitigation", "https://learn.microsoft.com/en-us/credentials/certifications/security-operations-analyst/"),
        _o("certificate", "CompTIA CySA+ (Cybersecurity Analyst)", "CompTIA", "paid exam", "Behavioral analytics and threat intelligence for SOC analysts", "https://www.comptia.org/certifications/cybersecurity-analyst")
    ]
}

def actions_for(skill, cause, weakest_course="", max_actions=3):
    opts = RECOMMENDATIONS.get(skill, [])
    certs = [o for o in opts if o["kind"] == "certificate"]
    tests = [o for o in opts if o["kind"] == "test"]
    courses = [o for o in opts if o["kind"] == "course"]
    practice = [o for o in opts if o["kind"] == "practice"]
    projects = [o for o in opts if o["kind"] == "project"]
    out = []
    if cause.startswith("Weak grades") and weakest_course:
        out.append(_o("revisit", f"Revisit {weakest_course}", "Sadat Academy", "free", "Review core syllabus and laboratory coursework"))
        order = certs[:1] + tests[:1] + courses[:1] + practice[:1]
    elif cause.startswith("Only partly"):
        order = projects[:1] + certs[:1] + tests[:1] + courses[:1]
    else:
        order = tests[:1] + courses[:1] + certs[:1] + practice[:1] + projects[:1]
    for o in order:
        if o not in out:
            out.append(o)
    if not out:
        out.append(_o("project", f"Build a hands-on project demonstrating {skill} on GitHub", "Self-Directed", "free", "Include architecture diagrams and documentation", "https://github.com/"))
    res = []
    for o in out[:max_actions]:
        provider_tag = f" [{o['provider']}, {o['cost']}]" if o["kind"] != "revisit" and o["provider"] != "-" else ""
        t = o["name"] + provider_tag
        res.append({**o, "text": t})
    return res

# ----------------------------------------------------------------------------
# Matching Parameters
# ----------------------------------------------------------------------------
MAX_YEARS = 2
EXTRA_YEARS_PER_EXP_YEAR = 1.0
MIN_ROLE_JOBS = 10
MIN_ROLE_ADS = 5
MIN_DEMAND = 0.10
FULL_EVIDENCE = 3.0
MIN_EVIDENCE = 1.5
WEAK_GRADE = 65
READY = 0.5
MIN_JOB_SKILLS = 4
TOP_ROLES = 3
TOP_GAPS = 5
TOP_JOBS = 10
TOP_IMPROVE = 3

WEIGHTS = {
    "transcript": 1.0,
    "certificate_verified": 0.9,
    "experience_verified": 0.8,
    "online_test": 0.7,
    "certificate_claimed": 0.5,
    "experience_claimed": 0.5,
    "self_rating": 0.3
}

ASSUMED = {
    "certificate": (WEIGHTS["certificate_verified"], 1.0),
    "test": (WEIGHTS["online_test"], 0.8)
}
