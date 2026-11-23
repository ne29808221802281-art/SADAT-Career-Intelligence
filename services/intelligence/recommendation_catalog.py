"""
What to suggest when a student is weak in, or missing, a skill.

Edit this file freely: the academy owns it. Every option is a dict:
  kind  : "certificate" | "test" | "course" | "practice" | "project"
  cost  : "free" | "paid exam" | "unknown"
  Only "certificate" and "test" options count as evidence in the engine (see WEIGHTS in matching_engine.py).
  "practice" = a readiness check that is NOT a credential.  "course" = learning only.
Entries marked (verified) were checked against the provider's own page; the rest are from general knowledge:
check names, prices and availability before publishing them to students.
"""


def _o(kind, name, provider, cost, note=""):
    return {"kind": kind, "name": name, "provider": provider, "cost": cost, "note": note}


# ---- reusable options -------------------------------------------------------------------------------------
HR = lambda skill, level="Basic": _o("test", f"HackerRank {skill} ({level}) skills certification", "HackerRank", "free",
                                     "(verified: listed as free)")
KAGGLE = lambda c: _o("course", f"Kaggle Learn: {c}", "Kaggle", "free", "(verified: free micro-course)")
LEARNSQL = _o("test", "LearnSQL SQL Skill Assessment (certificate at 70%+)", "LearnSQL", "free", "(verified: free, 18 hands-on tasks)")
MS_PRACTICE = _o("practice", "Microsoft Learn practice assessment for the matching exam", "Microsoft", "free",
                 "(verified: free score report, not a credential)")
AWS_PRACTICE = _o("practice", "AWS Skill Builder official practice question set", "AWS", "free",
                  "(verified: free with a Skill Builder login)")

OPTIONS = {
    # --- AI / data ---
    "Machine Learning": [
        _o("certificate", "AWS Certified Machine Learning Engineer - Associate", "AWS", "paid exam", "check the current exam name"),
        _o("certificate", "Microsoft Azure Data Scientist Associate (DP-100)", "Microsoft", "paid exam"),
        _o("certificate", "Google Professional Machine Learning Engineer", "Google", "paid exam"),
        KAGGLE("Intro to Machine Learning"), KAGGLE("Intermediate Machine Learning")],
    "Deep Learning": [
        _o("certificate", "AWS Certified Machine Learning Engineer - Associate", "AWS", "paid exam", "check the current exam name"),
        _o("course", "DeepLearning.AI Deep Learning Specialization", "DeepLearning.AI", "unknown")],
    "NLP": [_o("certificate", "Microsoft Azure AI Engineer Associate (AI-102)", "Microsoft", "paid exam"),
            _o("course", "DeepLearning.AI Natural Language Processing Specialization", "DeepLearning.AI", "unknown")],
    "Computer Vision": [_o("certificate", "Microsoft Azure AI Engineer Associate (AI-102)", "Microsoft", "paid exam")],
    "LLM": [_o("certificate", "AWS Certified AI Practitioner", "AWS", "paid exam"),
            _o("certificate", "Microsoft Azure AI Engineer Associate (AI-102)", "Microsoft", "paid exam")],
    "Generative AI": [_o("certificate", "AWS Certified AI Practitioner", "AWS", "paid exam"),
                      _o("certificate", "Microsoft Azure AI Fundamentals (AI-900)", "Microsoft", "paid exam")],
    "Python": [HR("Python"), KAGGLE("Python")],
    "SQL": [LEARNSQL, HR("SQL", "Basic"), HR("SQL", "Intermediate"), KAGGLE("Intro to SQL"),
            _o("certificate", "Microsoft Azure Data Fundamentals (DP-900)", "Microsoft", "paid exam")],
    "Pandas": [KAGGLE("Pandas")],
    "Matplotlib": [KAGGLE("Data Visualization")],
    "Statistics": [_o("course", "Google Data Analytics Professional Certificate", "Google", "unknown")],
    "Excel": [_o("course", "Google Data Analytics Professional Certificate (spreadsheets module)", "Google", "unknown")],
    "Power BI": [_o("certificate", "Microsoft Power BI Data Analyst (PL-300)", "Microsoft", "paid exam"), MS_PRACTICE],
    "Tableau": [_o("certificate", "Tableau Desktop Specialist", "Tableau", "paid exam")],
    "ETL": [_o("certificate", "AWS Certified Data Engineer - Associate", "AWS", "paid exam"),
            _o("certificate", "Google Professional Data Engineer", "Google", "paid exam")],
    "Data Warehouse": [_o("certificate", "Snowflake SnowPro Core", "Snowflake", "paid exam")],
    "Spark": [_o("certificate", "Databricks Certified Data Engineer Associate", "Databricks", "paid exam")],
    # --- cloud / devops ---
    "Azure": [_o("certificate", "Microsoft Azure Fundamentals (AZ-900)", "Microsoft", "paid exam"), MS_PRACTICE],
    "AWS": [_o("certificate", "AWS Certified Cloud Practitioner", "AWS", "paid exam"), AWS_PRACTICE],
    "GCP": [_o("certificate", "Google Associate Cloud Engineer", "Google", "paid exam")],
    "Cloud Architecture": [_o("certificate", "AWS Certified Solutions Architect - Associate", "AWS", "paid exam"),
                           _o("certificate", "Microsoft Azure Solutions Architect Expert (AZ-305)", "Microsoft", "paid exam")],
    "Docker": [_o("certificate", "Kubernetes CKAD (also covers containers)", "CNCF", "paid exam"),
               _o("project", "Containerise one of your own projects with Docker and publish it on GitHub", "-", "free")],
    "Kubernetes": [_o("certificate", "Kubernetes CKA or CKAD", "CNCF", "paid exam")],
    "CI/CD": [_o("certificate", "Microsoft DevOps Engineer Expert (AZ-400)", "Microsoft", "paid exam", "needs an Azure associate first"),
              _o("project", "Add a CI/CD pipeline (e.g. GitHub Actions) to one of your projects", "-", "free")],
    "Terraform": [_o("certificate", "HashiCorp Terraform Associate", "HashiCorp", "paid exam")],
    "Linux": [_o("certificate", "Red Hat RHCSA", "Red Hat", "paid exam"), _o("certificate", "CompTIA Linux+ or LPIC-1", "CompTIA / LPI", "paid exam")],
    "Git": [_o("project", "Keep your projects in a public GitHub repository with a clear README and commit history", "-", "free")],
    # --- software ---
    "REST APIs": [HR("REST API", "Intermediate")],
    "Microservices": [_o("certificate", "AWS Certified Developer - Associate", "AWS", "paid exam"),
                      _o("project", "Build a small two-service application with its own API for each service", "-", "free")],
    "JavaScript": [HR("JavaScript"), HR("JavaScript", "Intermediate")],
    "Java": [HR("Java"), _o("certificate", "Oracle Java certification", "Oracle", "paid exam")],
    "React": [HR("React")], "Angular": [HR("Angular")], "Node.js": [HR("Node.js")],
    "C#": [HR("C#")], "R": [HR("R")], "Go": [HR("Go")],
    "Test Automation": [_o("certificate", "ISTQB Certified Tester Foundation Level", "ISTQB", "paid exam")],
    "Agile/Scrum": [_o("certificate", "Professional Scrum Master (PSM) or Certified ScrumMaster (CSM)", "Scrum.org / Scrum Alliance", "paid exam")],
    # --- security / network ---
    "Networking": [_o("certificate", "Cisco CCNA", "Cisco", "paid exam"), _o("certificate", "CompTIA Network+", "CompTIA", "paid exam")],
    "Security Fundamentals": [_o("certificate", "CompTIA Security+", "CompTIA", "paid exam"),
                              _o("certificate", "Microsoft Security Fundamentals (SC-900)", "Microsoft", "paid exam")],
    "Pen Testing": [_o("certificate", "Certified Ethical Hacker (CEH)", "EC-Council", "paid exam")],
    "SIEM/SOC": [_o("certificate", "Microsoft Security Operations Analyst (SC-200)", "Microsoft", "paid exam"),
                 _o("certificate", "CompTIA CySA+", "CompTIA", "paid exam")],
}


def actions_for(skill, cause, weakest_course="", max_actions=3):
    """Ordered list of suggested actions (dicts with kind/name/provider/cost/note/text)."""
    opts = OPTIONS.get(skill, [])
    certs = [o for o in opts if o["kind"] == "certificate"]
    tests = [o for o in opts if o["kind"] == "test"]
    courses = [o for o in opts if o["kind"] == "course"]
    practice = [o for o in opts if o["kind"] == "practice"]
    projects = [o for o in opts if o["kind"] == "project"]
    out = []
    if cause.startswith("Weak grades") and weakest_course:
        out.append(_o("revisit", f"Revisit {weakest_course}", "-", "free"))
        order = certs[:1] + tests[:1] + courses[:1] + practice[:1]       # credential first for weak grades
    elif cause.startswith("Only partly"):
        order = projects[:1] + certs[:1] + tests[:1] + courses[:1]
    else:                                                                # not covered / not proven yet
        order = tests[:1] + courses[:1] + certs[:1] + practice[:1] + projects[:1]
    for o in order:
        if o not in out:
            out.append(o)
    if not out:
        out.append(_o("project", f"Build a small project that uses {skill} and publish it on GitHub", "-", "free"))
    res = []
    for o in out[:max_actions]:
        t = o["name"] + (f" [{o['provider']}, {o['cost']}]" if o["kind"] not in ("revisit",) and o["provider"] != "-" else "")
        res.append({**o, "text": t})
    return res
