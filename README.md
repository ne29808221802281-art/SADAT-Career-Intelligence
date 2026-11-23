# SADAT – Student Career Intelligence & Skills Growth Portal
### Faculty of Computers and Information — Class of 2026
**Full-Stack Modernization of the Experimental Platform (Specification-Driven Development)**

---

## 🌟 Executive Summary
**SADAT – Student Career Intelligence & Skills Growth Portal** is a production-grade, standalone, bilingual (English LTR & Arabic RTL) academic career guidance platform for students and graduates of Sadat Academy.

The system evaluates:
1. **Official 4-Year Academic Transcripts**: 49 courses ($C001 - C049$), credit hours, marks, and faculty relevance mappings.
2. **Professional Work Experience**: Verified and claimed experience with eligibility filters.
3. **Online Assessment Scores**: 14 high-demand missing skills with interactive real-time score preview sliders.
4. **International Certifications**: 31 industry credentials mapped directly to market competencies.

These evidence sources are evaluated against **169 real Egyptian tech market job postings** to produce:
- **Top 10 Matching Jobs** with dynamic fit percentages:
  $$\text{Fit}(j) = \frac{\sum_{s \in \text{Skills}(j)} S_s}{\max(|\text{Skills}(j)|, 4)}$$
- **Experience Eligibility Constraint**:
  $$\text{Years Required} \le 2 + 1.0 \times \lfloor\text{Experience Years}\rfloor$$
- **Actionable Fit Improvement Roadmaps** with exact **Estimated Fit Gain points** ($+X.X\text{ pts}$).
- **14 Missing Skills & Free Tests Center** with direct official assessment links.
- **Job Market & Cohort Intelligence Dashboards** grounded strictly in empirical market data.

---

## 🎨 Visual Identity: Minimalistic Retro Grid + Calm Sea Palette
The platform adheres strictly to an editorial academic aesthetic, avoiding generic AI tropes (neon purples, glowing orbs, robots):
- **Deep Navy** (`#15354B`): Headers, primary actions, and active states.
- **Ocean Blue** (`#286581`): Brand highlights, fit scores, and key links.
- **Sea Blue** (`#4E8298`): Subheadings, badges, and progress tracks.
- **Muted Teal** (`#76A9A6`): Cohort readiness indicators and secondary series.
- **Seafoam** (`#C5DFD9`): Soft highlights and pill backgrounds.
- **Ice Blue** (`#EAF3F5`): Card backgrounds and subtle panels.
- **Off-White** (`#F8FAF9`): Canvas background with low-contrast technical grid.
- **Bilingual RTL Support**: Full bi-directional mirroring for Arabic (`dir="rtl"`) with `IBM Plex Sans Arabic` typography.

---

## 🚀 How to Run the Platform

### Option A: 1-Click Launch (Recommended)
Double-click `run_portal.bat` or run:
```cmd
.\run_portal.bat
```
This starts both the private Python intelligence microservice (port 8000) and the Node.js REST API server (port 5000), opening your browser automatically to:
**`http://127.0.0.1:5000`**

### Option B: Standalone Zero-Setup Direct Browser Launch
Open `apps/web/public/index.html` directly in any modern browser (Chrome, Edge, Firefox). The platform hydrates with preloaded offline data and works 100% locally with zero latency!

---

## 🧪 Automated Differential Testing
The platform includes an automated regression test suite verifying 100% mathematical and ranking parity with the experimental baseline:
```cmd
"C:\Users\elmasria\AppData\Local\Programs\Orange\python.exe" tests\regression\test_differential_validation.py
```
**Output:**
```text
......
----------------------------------------------------------------------
Ran 6 tests in 0.137s

OK
```

---

## 📁 Repository Structure
```text
sadat-career-portal/
├── run_portal.bat               # 1-Click Launcher
├── docker-compose.yml           # Multi-container production deployment
├── .env.example                 # Environment variables specification
├── package.json                 # Monorepo metadata & scripts
├── README.md                    # Project documentation
│
├── apps/
│   ├── web/
│   │   └── public/
│   │       ├── index.html       # Bilingual portal interface
│   │       ├── css/style.css    # Calm Sea design system & retro grid
│   │       └── js/
│   │           ├── i18n.js      # English & Arabic translation engine
│   │           ├── app.js       # Reactive UI controller & slider previews
│   │           └── embedded_data.js # Preloaded offline dataset
│   └── api/
│       └── src/
│           ├── config.js        # Environment and file path configuration
│           ├── db.js            # SQLite database & CSV automatic seeder
│           ├── pythonBridge.js  # Private RPC connector to Python engine
│           ├── server.js        # Node.js REST API server
│           └── routes/          # REST endpoint controllers
│
├── services/
│   └── intelligence/
│       ├── matching_engine.py   # Reference matching engine
│       ├── recommendation_catalog.py # Reference recommendation catalog
│       ├── linkedin_jobs_scraper.py  # Reference LinkedIn Egyptian jobs scraper
│       ├── matcher.py           # Dynamic evaluation logic
│       ├── engine.py            # Parameters and 14 missing skills catalog
│       ├── server.py            # Internal REST microservice (Port 8000)
│       └── test_platform.py     # Intelligence layer test runner
│
├── data/                        # 7 Original CSV datasets
│   ├── course_catalog.csv
│   ├── course_skill_map.csv
│   ├── students_info.csv
│   ├── student_grades.csv
│   ├── jobs.csv
│   ├── market_vs_cohort_skills.csv
│   └── role_summary.csv
│
├── docs/                        # Complete SDD Specification Documents (16 docs)
│   ├── 00-project-overview.md
│   ├── 01-existing-system-analysis.md
│   ├── 02-functional-requirements.md
│   ├── 03-non-functional-requirements.md
│   ├── 04-system-architecture.md
│   ├── 05-data-dictionary.md
│   ├── 06-database-schema.md
│   ├── 07-engine-integration-contracts.md
│   ├── 08-api-specification.md
│   ├── 09-scoring-and-recommendation-spec.md
│   ├── 10-ui-ux-design-system.md
│   ├── 11-authentication-spec.md
│   ├── 12-security-specification.md
│   ├── 13-testing-and-validation.md
│   ├── 14-deployment-specification.md
│   └── 15-implementation-roadmap.md
│
└── tests/
    └── regression/
        └── test_differential_validation.py # Differential regression test runner
```

---

## 🔒 Non-Negotiable Preservation Guarantees
1. **Mathematical Scoring Integrity**: Every evidence weight (Transcript: 1.0, Verified Cert: 0.9, Verified Exp: 0.8, Test: 0.7, Claimed Cert: 0.5, Claimed Exp: 0.5, Self-Rating: 0.3) is preserved exactly.
2. **Top 10 Matching Algorithm**: $Fit(j)$ calculation uses exact divisor $\max(|\text{Skills}(j)|, 4)$.
3. **Experience Eligibility**: $\text{YearsRequired} \le 2 + 1.0 \times \lfloor\text{ExperienceYears}\rfloor$.
4. **Estimated Fit Gain**: Accurately calculates predicted percentage point gains without synthetic numbers.
5. **Data Grounding**: Grounded strictly in empirical data from the 7 authoritative CSV files.
