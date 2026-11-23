#!/usr/bin/env python3
"""
LinkedIn CS/Tech jobs scraper (Egypt) using LinkedIn's public *guest* job endpoints.
No login required. Collects:
  1. specialization        5. level (Intern / Junior / Mid / Senior)
  2. company name          6. years of experience (min / max)
  3. company country*      7. technical requirements
  4. work mode (Remote / Hybrid / On-site)

* LinkedIn's public pages expose the JOB location, not the company HQ. `company_country`
  is derived from the job location (default: Egypt). See README for details.

Usage:
  python linkedin_jobs_scraper.py                       # all default roles, last 30 days
  python linkedin_jobs_scraper.py -k "data engineer" "ai engineer" --pages 5
  python linkedin_jobs_scraper.py --split-work-mode     # exact Remote/Hybrid/On-site via LinkedIn filters
"""
import argparse
import random
import re
import sys
import time
from urllib.parse import quote_plus

import pandas as pd
import requests
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
DETAIL_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

DEFAULT_KEYWORDS = [
    "AI Engineer", "Machine Learning Engineer", "Data Engineer", "Data Analyst",
    "Data Scientist", "Software Engineer", "Software Developer", "Backend Developer",
    "Frontend Developer", "Full Stack Developer", ".NET Developer", "Cybersecurity",
    "Security Analyst", "Network Engineer", "QA Engineer", "Software Tester",
    "DevOps Engineer", "Cloud Engineer", "BI Developer", "NLP Engineer",
]

# Random pause (seconds) before EVERY request, picked uniformly from this (min, max) range.
# Larger values = slower but far less likely to be blocked (HTTP 429/999).
# Safe starting point: (3, 7). Raise to (6, 12) if you still get blocked.
REQUEST_DELAY_RANGE = (3.0, 7.0)
# Extra long "human" pause after every N requests (0 disables it)
LONG_PAUSE_EVERY = 25
LONG_PAUSE_RANGE = (20.0, 40.0)

TIME_FILTERS = {"day": "r86400", "week": "r604800", "month": "r2592000", "any": ""}
WORK_MODE_FILTER = {"On-site": "1", "Remote": "2", "Hybrid": "3"}

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
}

# ----------------------------------------------------------------------------
# Skill dictionary: canonical name -> regex (case-insensitive unless noted)
# ----------------------------------------------------------------------------
SKILLS = {
    "SQL": r"\b(?:sql|t-sql|pl/sql|mysql|postgres(?:ql)?|sql server)\b",
    "Python": r"\bpython\b",
    "R": None,  # handled specially (case-sensitive)
    "C": None,  # handled specially (case-sensitive)
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
    # --- added for the SADAT course-to-skill map ---
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

SKILL_PATTERNS = {k: re.compile(v, re.I) for k, v in SKILLS.items() if v}

# ----------------------------------------------------------------------------
# Certificates: (display name, provider, regex, skills the certificate evidences)
# The skills column doubles as the certificate->skill table for student profiles.
# ----------------------------------------------------------------------------
CERTIFICATES = [
    # --- Microsoft ---
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
    # --- AWS ---
    ("AWS Certified Cloud Practitioner", "AWS", r"aws (?:certified )?cloud practitioner|\bclf[\s-]?c0\d\b", ["AWS"]),
    ("AWS Certified Solutions Architect", "AWS", r"aws (?:certified )?solutions? architect|\bsaa[\s-]?c0\d\b", ["AWS", "Cloud Architecture"]),
    ("AWS Certified Developer", "AWS", r"aws (?:certified )?developer|\bdva[\s-]?c0\d\b", ["AWS"]),
    ("AWS Certified SysOps/DevOps", "AWS", r"aws (?:certified )?(?:sysops|devops)", ["AWS", "CI/CD"]),
    ("AWS Certified Data Engineer", "AWS", r"aws (?:certified )?data engineer|\bdea[\s-]?c0\d\b", ["AWS", "ETL", "Data Warehouse"]),
    ("AWS Certified Machine Learning", "AWS", r"aws (?:certified )?machine learning|\bmla[\s-]?c0\d\b|\bmls[\s-]?c0\d\b", ["AWS", "Machine Learning"]),
    # --- Google ---
    ("Google Associate Cloud Engineer", "Google", r"associate cloud engineer", ["GCP"]),
    ("Google Professional Cloud Architect", "Google", r"professional cloud architect", ["GCP", "Cloud Architecture"]),
    ("Google Professional Data Engineer", "Google", r"professional data engineer", ["GCP", "ETL", "Data Warehouse"]),
    ("Google Professional Machine Learning Engineer", "Google", r"professional machine learning engineer", ["GCP", "Machine Learning"]),
    ("Google Data Analytics Certificate", "Google", r"google data analytics|google analytics certif\w*", ["SQL", "Excel", "Tableau", "R"]),
    # --- Security / networking ---
    ("CompTIA Security+", "CompTIA", r"comptia security\+?|\bsecurity\+", ["Security Fundamentals"]),
    ("CompTIA Network+", "CompTIA", r"comptia network\+?|\bnetwork\+", ["Networking"]),
    ("CompTIA CySA+", "CompTIA", r"\bcysa\+?", ["SIEM/SOC"]),
    ("CISSP", "ISC2", r"\bcissp\b", ["Security Fundamentals"]),
    ("CEH (Certified Ethical Hacker)", "EC-Council", r"\bceh\b|certified ethical hacker", ["Pen Testing"]),
    ("OSCP", "OffSec", r"\boscp\b", ["Pen Testing"]),
    ("CISM / CISA", "ISACA", r"\bcism\b|\bcisa\b", ["Security Fundamentals"]),
    ("Cisco CCNA", "Cisco", r"\bccna\b", ["Networking"]),
    ("Cisco CCNP", "Cisco", r"\bccnp\b", ["Networking"]),
    # --- DevOps / Linux / data platforms ---
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
    # --- Process / testing ---
    ("Scrum (CSM / PSM)", "Scrum", r"\bcsm\b|\bpsm\b|certified scrum master|professional scrum master", ["Agile/Scrum"]),
    ("ISTQB", "ISTQB", r"\bistqb\b", ["Test Automation"]),
    ("PMP", "PMI", r"\bpmp\b|project management professional", []),
]
CERT_PATTERNS = [(n, prov, re.compile(rx, re.I), sk) for n, prov, rx, sk in CERTIFICATES]


def extract_certs(text: str) -> list[str]:
    return [n for n, _prov, pat, _sk in CERT_PATTERNS if pat.search(text)]

R_PATTERN = re.compile(r"(?<![\w&/.\-])R(?=[\s,;/)]|$)(?:\s*(?:programming|language|studio|shiny))?(?![\w&#+])")
C_PATTERN = re.compile(r"(?<![\w+#.\-])C(?=[\s,;/)]|$)(?![\w+#])")


def extract_skills(text: str) -> list[str]:
    found = [name for name, pat in SKILL_PATTERNS.items() if pat.search(text)]
    if R_PATTERN.search(text) and re.search(r"\b(python|sql|statistic|data|analytics?)\b", text, re.I):
        found.append("R")
    if C_PATTERN.search(text) and re.search(r"\b(c\+\+|embedded|programming|language|developer|engineer)\b", text, re.I):
        found.append("C")
    return sorted(set(found), key=lambda s: list(SKILLS).index(s))


SPECIALIZATION_RULES = [
    ("AI / ML Engineer", r"\b(ai|ml|machine learning|deep learning|nlp|llm|generative|genai|computer vision|mlops)\b.*\b(engineer|developer|specialist|researcher|scientist)?|\b(engineer|developer)\b.*\b(ai|ml|machine learning)\b"),
    ("Data Scientist", r"data scien\w+|research scientist|applied scientist"),
    ("Data Engineer", r"data engineer\w*|etl|big data|data platform|analytics engineer|data architect"),
    ("Data Analyst / BI", r"data analy\w+|business intelligence|\bbi\b|reporting analyst|analytics|insights analyst|business analyst"),
    ("Cybersecurity", r"cyber|security|soc analyst|penetration|infosec|\bgrc\b|threat|vulnerab"),
    ("Network Engineer / Tester", r"network|noc\b|ccna|ccnp|telecom|wireless|\brf\b"),
    ("QA / Software Tester", r"\bqa\b|quality assurance|\btest(?:er|ing)?\b|sdet|automation engineer"),
    ("DevOps / Cloud", r"devops|\bsre\b|site reliability|cloud|infrastructure|platform engineer|sysadmin|system admin"),
    ("Mobile Developer", r"android|\bios\b|flutter|react native|mobile"),
    ("Embedded / Firmware", r"embedded|firmware|\bfpga\b|\biot\b"),
    ("Full Stack Developer", r"full[\s-]?stack"),
    ("Frontend Developer", r"front[\s-]?end|\breact\b|angular|\bvue\b|\bui developer"),
    ("Backend Developer", r"back[\s-]?end|\.net|java\b|python developer|php|node|golang|api developer"),
    ("Software Engineer / Developer", r"software|developer|programmer|engineer"),
]
SPECIALIZATION_RULES = [(n, re.compile(p, re.I)) for n, p in SPECIALIZATION_RULES]


def classify_specialization(title: str, description: str = "") -> str:
    for name, pat in SPECIALIZATION_RULES:
        if pat.search(title):
            return name
    head = description[:600]
    for name, pat in SPECIALIZATION_RULES[:-1]:
        if pat.search(head):
            return name
    return "Other / Unclassified"


WORK_MODE_PATTERNS = [
    ("Hybrid", re.compile(r"\bhybrid\b|(?:\d|two|three)\s*days?\s*(?:/|per|a|in the)\s*(?:week\s*)?(?:in[\s-]?office|onsite|on-site)", re.I)),
    ("Remote", re.compile(r"\bremote(?:ly)?\b|work from home|\bwfh\b|\bfully distributed\b", re.I)),
    ("On-site", re.compile(r"\bon[\s-]?site\b|\bonsite\b|in[\s-]?office|in[\s-]?person|office[\s-]based", re.I)),
]


def infer_work_mode(title: str, location: str, description: str) -> str:
    for text in (title, location, description):
        for mode, pat in WORK_MODE_PATTERNS:
            if pat.search(text):
                return mode
    return "Not specified"


def extract_years(text: str) -> tuple[int | None, int | None]:
    text = text.replace("–", "-").replace("—", "-")
    best = None
    for m in re.finditer(r"(\d{1,2})\s*(?:-|to)\s*(\d{1,2})\s*\+?\s*(?:years?|yrs?)", text, re.I):
        lo, hi = int(m.group(1)), int(m.group(2))
        if lo <= hi <= 25:
            best = (lo, hi)
            break
    if best:
        return best
    singles = []
    for m in re.finditer(r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)(?:\W+(?:of|in|with))?", text, re.I):
        n = int(m.group(1))
        ctx = text[max(0, m.start() - 60): m.end() + 60].lower()
        if n <= 25 and re.search(r"experience|exp\b|background|working|hands[\s-]on", ctx):
            singles.append(n)
    if singles:
        return (min(singles), None)
    if re.search(r"\bfresh\s*grad\w*|no experience required|entry[\s-]level", text, re.I):
        return (0, 0)
    return (None, None)


def classify_level(title: str, linkedin_seniority: str, years_min: int | None, description: str = "") -> str:
    t = title.lower()
    if re.search(r"\bintern(?:ship)?\b|\btrainee\b|\bco-?op\b|summer training|\bapprentice", t) \
            or "internship" in (linkedin_seniority or "").lower():
        return "Intern"
    if re.search(r"\b(senior|sr\.?|lead|principal|staff|head|manager|director|architect|expert)\b", t):
        return "Senior"
    if re.search(r"\b(junior|jr\.?|entry|graduate|fresh\w*|associate)\b", t):
        return "Junior"
    ls = (linkedin_seniority or "").lower()
    if "entry" in ls:
        return "Junior"
    if any(x in ls for x in ("senior", "director", "executive")):
        return "Senior"
    if years_min is not None:
        if years_min <= 1:
            return "Junior"
        if years_min >= 5:
            return "Senior"
        return "Mid"
    if "mid" in ls or "associate" in ls:
        return "Mid"
    return "Not specified"


def country_from_location(location: str) -> str:
    if not location:
        return ""
    last = location.split(",")[-1].strip()
    egypt_cities = {"cairo", "giza", "alexandria", "new cairo", "6th of october city", "maadi",
                    "nasr city", "heliopolis", "sheikh zayed", "smart village", "mansoura", "tanta"}
    if last.lower() in egypt_cities or "governorate" in last.lower():
        return "Egypt"
    return last


class Client:
    def __init__(self, delay=None, proxy=None):
        self.s = requests.Session()
        self.s.headers.update(HEADERS)
        if proxy:
            self.s.proxies = {"http": proxy, "https": proxy}
        self.delay = tuple(delay) if delay else REQUEST_DELAY_RANGE
        if self.delay[0] > self.delay[1]:
            self.delay = (self.delay[1], self.delay[0])
        self.count = 0
        self.stats = {}

    def get(self, url, params=None, retries=4):
        for attempt in range(retries):
            self.count += 1
            if LONG_PAUSE_EVERY and self.count % LONG_PAUSE_EVERY == 0:
                pause = random.uniform(*LONG_PAUSE_RANGE)
                print(f"  ... resting {pause:.0f}s to avoid being blocked", file=sys.stderr)
                time.sleep(pause)
            time.sleep(random.uniform(*self.delay))
            try:
                r = self.s.get(url, params=params, timeout=25)
            except requests.RequestException as e:
                self.stats['network error'] = self.stats.get('network error', 0) + 1
                print(f"  ! network error: {e}", file=sys.stderr)
                time.sleep(2 ** attempt * 3)
                continue
            self.stats[r.status_code] = self.stats.get(r.status_code, 0) + 1
            if r.status_code == 200:
                return r.text
            if r.status_code in (429, 999, 503):
                wait = 2 ** attempt * 15
                print(f"  ! rate limited ({r.status_code}); sleeping {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            if r.status_code == 404:
                return None
            print(f"  ! HTTP {r.status_code} for {url}", file=sys.stderr)
            time.sleep(2 ** attempt * 3)
        return None


def parse_search_cards(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    out = []
    for li in soup.select("li"):
        card = li.select_one("div.base-card, div.job-search-card")
        if not card:
            continue
        urn = card.get("data-entity-urn", "")
        m = re.search(r"(\d{6,})$", urn)
        link = card.select_one("a.base-card__full-link")
        href = link["href"].split("?")[0] if link and link.get("href") else ""
        if not m and href:
            m = re.search(r"-(\d{6,})$", href)
        if not m:
            continue
        title = card.select_one("h3.base-search-card__title")
        comp = card.select_one("h4.base-search-card__subtitle")
        loc = card.select_one("span.job-search-card__location")
        date = card.select_one("time")
        out.append({
            "job_id": m.group(1),
            "title": title.get_text(strip=True) if title else "",
            "company": comp.get_text(strip=True) if comp else "",
            "location": loc.get_text(strip=True) if loc else "",
            "posted": date.get("datetime", "") if date else "",
            "url": href or f"https://www.linkedin.com/jobs/view/{m.group(1)}",
        })
    return out


def parse_detail(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    desc_el = soup.select_one("div.show-more-less-html__markup, div.description__text")
    description = desc_el.get_text("\n", strip=True) if desc_el else ""
    criteria = {}
    for item in soup.select("li.description__job-criteria-item"):
        k = item.select_one("h3")
        v = item.select_one("span")
        if k and v:
            criteria[k.get_text(strip=True).lower()] = v.get_text(strip=True)
    return {
        "description": description,
        "linkedin_seniority": criteria.get("seniority level", ""),
        "employment_type": criteria.get("employment type", ""),
        "linkedin_function": criteria.get("job function", ""),
        "linkedin_industries": criteria.get("industries", ""),
    }


def build_record(card: dict, detail: dict, forced_mode: str | None) -> dict:
    desc = detail.get("description", "")
    full_text = f"{card['title']}\n{desc}"
    ymin, ymax = extract_years(desc)
    skills = extract_skills(full_text)
    mode = forced_mode or infer_work_mode(card["title"], card["location"], desc)
    return {
        "job_id": card["job_id"],
        "title": card["title"],
        "specialization": classify_specialization(card["title"], desc),
        "company": card["company"],
        "company_country": country_from_location(card["location"]),
        "job_location": card["location"],
        "work_mode": mode,
        "level": classify_level(card["title"], detail.get("linkedin_seniority", ""), ymin, desc),
        "years_exp_min": ymin,
        "years_exp_max": ymax,
        "technical_requirements": ", ".join(skills),
        "certifications_mentioned": ", ".join(extract_certs(full_text)),
        "employment_type": detail.get("employment_type", ""),
        "linkedin_seniority": detail.get("linkedin_seniority", ""),
        "posted": card["posted"],
        "url": card["url"],
    }


def scrape(keywords, location, pages, since, split_modes, fetch_details, client, checkpoint=None):
    seen, rows = set(), []
    modes = list(WORK_MODE_FILTER.items()) if split_modes else [(None, "")]
    for kw in keywords:
        for mode_name, mode_code in modes:
            label = f"{kw}" + (f" [{mode_name}]" if mode_name else "")
            print(f"\n== {label}")
            for page in range(pages):
                params = {"keywords": kw, "location": location, "start": page * 25}
                if TIME_FILTERS.get(since):
                    params["f_TPR"] = TIME_FILTERS[since]
                if mode_code:
                    params["f_WT"] = mode_code
                html = client.get(SEARCH_URL, params=params)
                cards = parse_search_cards(html) if html else []
                if not cards:
                    break
                new = [c for c in cards if c["job_id"] not in seen]
                print(f"  page {page + 1}: {len(cards)} cards, {len(new)} new")
                for c in new:
                    seen.add(c["job_id"])
                    detail = {}
                    if fetch_details:
                        dhtml = client.get(DETAIL_URL.format(job_id=c["job_id"]))
                        detail = parse_detail(dhtml) if dhtml else {}
                    rows.append(build_record(c, detail, mode_name))
                if checkpoint:
                    checkpoint(rows)
    return rows


def run(keywords=None, location="Egypt", pages=4, since="month", split_work_mode=False,
        details=True, proxy=None, output="linkedin_egypt_tech_jobs", download=False,
        delay=None):
    client = Client(delay=delay, proxy=proxy)

    def checkpoint(rows):
        pd.DataFrame(rows).drop_duplicates(subset=["job_id"]).to_csv(
            f"{output}_partial.csv", index=False, encoding="utf-8-sig")

    rows = scrape(keywords or DEFAULT_KEYWORDS, location, pages, since,
                  split_work_mode, details, client, checkpoint)
    if not rows:
        print("\nNo jobs collected.")
        return None
    df = pd.DataFrame(rows).drop_duplicates(subset=["job_id"])
    df.to_csv(f"{output}.csv", index=False, encoding="utf-8-sig")
    return df
