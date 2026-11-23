# SADAT – Student Career Intelligence & Skills Growth Portal
## 01. Existing System Analysis & Source Inspection (Gate 1 Deliverable)

### 1. Overview of Inspected Artifacts
The existing experimental system was audited across its source repository (`career-matching-platform`) and the three authoritative reference scripts:
1. `backend/test_platform.py`: Executed on Python 3.12 (`C:\Users\elmasria\AppData\Local\Programs\Orange\python.exe`). Result: **100% Passed**.
2. `backend/engine.py` & `recommendation_catalog.py`: Defines 72 technical skills, 31 international certificates, 14 missing skills with free tests, and recommendation action mappings.
3. `backend/matcher.py` & `matching_engine.py`: Implements evidence aggregation, role matching, top 10 job ranking, experience eligibility, gap explanation, and fit gain calculation.
4. `backend/server.py`: Multi-threaded Python HTTP server exposing REST endpoints (`/api/students`, `/api/student/<id>`, `/api/match`, `/api/missing-skills`, `/api/certificates`, `/api/market-dashboard`, `/api/jobs`).
5. `linkedin_jobs_scraper.py`: Public LinkedIn guest job scraper harvesting Egypt tech postings.
6. `data/`: Seven CSV datasets:
   - `course_catalog.csv` (49 courses: C001 - C049)
   - `course_skill_map.csv` (106 mappings with relevance `rel` $\in [0.1, 1.0]$)
   - `students_info.csv` (1,000 students with GPA, Degree Grade)
   - `student_grades.csv` (49,000 marks across 4 years)
   - `jobs.csv` (169 real Egyptian tech postings)
   - `market_vs_cohort_skills.csv` (77 skill gap metrics)
   - `role_summary.csv` (13 technical roles with cohort fit & core skill weights)

---

### 2. Algorithmic Formulations

#### 2.1 Evidence-Weighted Skill Proficiency Engine
A student's competency level for skill $s$, denoted $S_s \in [0.0, 1.0]$, is aggregated from all evidence sources $e \in E(s)$:

$$S_s = \frac{\sum_{e \in E(s)} W(e) \cdot L(e)}{\max\left(\sum_{e \in E(s)} W(e), 1.0\right)}$$

Where:
- **University Transcript Evidence**:
  - Credit hours $C_c$, Relevance $R_{c,s}$, Course mark $M_c \in [0, 100]$.
  - Transcript Level: $L_{\text{transcript}} = \frac{\sum_{c} R_{c,s} \cdot C_c \cdot M_c}{\sum_{c} R_{c,s} \cdot C_c \cdot 100}$
  - Transcript Evidence Sum: $E_{\text{sum}} = \sum_{c} R_{c,s} \cdot C_c$
  - Transcript Weight: $W_{\text{transcript}} = 1.0 \times \min\left(1.0, \frac{E_{\text{sum}}}{\text{FULL\_EVIDENCE}}\right)$, where $\text{FULL\_EVIDENCE} = 3.0$.
- **Verified Certificate**: Weight $0.9$, Level $= 1.0$.
- **Verified Work Experience**: Weight $0.8$, Level $= \min\left(1.0, \frac{\text{Months}}{12}\right)$.
- **Online Test Scores**: Weight $0.7$, Level $= \frac{\text{Score}}{100.0}$.
- **Claimed Certificate**: Weight $0.5$, Level $= 1.0$.
- **Claimed Experience**: Weight $0.5$, Level $= \min\left(1.0, \frac{\text{Months}}{12}\right)$.
- **Self-Rating**: Weight $0.3$, Level $= \frac{\text{Rating}}{100.0}$.

#### 2.2 Top 10 Job Matching Formula
For each candidate job $j$ with required skills $\text{Skills}(j)$:

$$\text{Fit}(j) = \frac{\sum_{s \in \text{Skills}(j)} S_s}{\max(|\text{Skills}(j)|, 4)}$$

#### 2.3 Experience Eligibility Filter
A student with reported work experience $\text{ExpMonths}$ (converted to $\text{ExpYears} = \frac{\text{ExpMonths}}{12}$) is eligible for job $j$ with minimum required experience $\text{YearsMin}(j)$ if:

$$\text{YearsMin}(j) \le 2 + 1.0 \times \lfloor\text{ExpYears}\rfloor$$
*(Jobs with unstated experience are treated as eligible entry-level).*

#### 2.4 Skill Status Classification
- **Strong**: $S_s \ge 0.50$ (50%)
- **Developing / Partial**: $0.0 < S_s < 0.50$ (1% - 49%)
- **Missing / Untrained**: $S_s = 0.0$ (0%)

#### 2.5 Gap Cause Diagnosis
- If $S_s \ge 0.50$: **Covered**
- Else if $E_{\text{sum}} < 1.5$ ($\text{MIN\_EVIDENCE}$):
  - If external evidence was provided: **Not proven strongly yet**
  - Else: **Not covered by the curriculum**
- Else (Curriculum covers skill with $E_{\text{sum}} \ge 1.5$):
  - If transcript proficiency $P_s < 65$ ($\text{WEAK\_GRADE}$): **Weak grades in related courses**
  - Else: **Only partly covered**

#### 2.6 Estimated Fit Gain Calculation
When recommending a test or certification for missing/weak skill $s$ in job $j$ ($N_{\text{eff}} = \max(|\text{Skills}(j)|, 4)$):
- If the action is a certification: Assumed weight $W_{\text{new}} = 0.9$, Assumed level $L_{\text{new}} = 1.0$.
- If the action is an online test: Assumed weight $W_{\text{new}} = 0.7$, Assumed level $L_{\text{new}} = 0.8$.
- New skill level:
  $$S_{s, \text{new}} = \frac{\text{Num}_s + W_{\text{new}} \cdot L_{\text{new}}}{\max(\text{Den}_s + W_{\text{new}}, 1.0)}$$
- Estimated Fit Gain in percentage points:
  $$\Delta \text{Fit} = \text{round}\left(100.0 \times \frac{S_{s, \text{new}} - S_s}{N_{\text{eff}}}, 1\right)$$

---

### 3. Detailed Data Schemas

#### 3.1 Course Catalog (`course_catalog.csv`)
- `Course_ID`: String (e.g. "C001" - "C049")
- `Year`: Integer (1 - 4)
- `Course_Name`: String (e.g. "Database Systems", "Machine&Deep Learning")
- `Credit_Hours`: Integer (typically 2 or 3)

#### 3.2 Course Skill Map (`course_skill_map.csv`)
- `Course_ID`: String
- `Course_Name`: String
- `Year`: Integer
- `Credit_Hours`: Integer
- `Skill`: String (Canonical skill name from dictionary)
- `In_Scraper_Vocab`: String ("Y" or "N")
- `rel`: Float (Relevance weight, $0.1 \le \text{rel} \le 1.0$)
- `Confidence`: String ("H", "M", "L")
- `Evidence_Weight`: Float ($\text{rel} \times \text{Credit\_Hours}$)
- `Faculty_Review`: String (Optional review status)
- `Notes`: String

#### 3.3 Student Information (`students_info.csv`)
- `Student_ID`: String (e.g. "SAD20260001")
- `Student_Name`: String
- `GPA`: Float (e.g. 3.29)
- `Grade_Label`: String ("Excellent", "Very Good", "Good", "Pass")

#### 3.4 Student Grades (`student_grades.csv`)
- `Student_ID`: String
- `Course_ID`: String
- `Course_Name`: String
- `M_Mark`: Float (0 - 100)
- `C_H_Credit_Hours`: Integer

#### 3.5 Jobs Dataset (`jobs.csv`)
- `job_id`: Integer / String
- `title`: String
- `specialization`: String (e.g. "AI / ML Engineer", "Cybersecurity")
- `company`: String
- `company_country`: String
- `job_location`: String
- `work_mode`: String ("Remote", "Hybrid", "On-site", "Not specified")
- `level`: String ("Junior", "Mid", "Senior", "Intern")
- `years_exp_min`: Float / Integer
- `years_exp_max`: Float / Integer
- `technical_requirements`: Comma-separated list of skills
- `certifications_mentioned`: Comma-separated list of certificates
- `employment_type`: String ("Full-time", "Part-time", etc.)
- `linkedin_seniority`: String
- `posted`: Date string ("YYYY-MM-DD")
- `url`: String (LinkedIn URL)

#### 3.6 Market vs. Cohort Skills (`market_vs_cohort_skills.csv`)
- `Skill`: String
- `Demand%_entry_level_ads`: Float
- `Demand%_all_levels`: Float
- `Cohort_mean_level%`: Float
- `Cohort_ready%`: Float
- `Curriculum_evidence`: Float
- `Gap_score`: Float

#### 3.7 Role Summary (`role_summary.csv`)
- `Role`: String
- `Cohort_mean_match%`: Float
- `Cohort_median_match%`: Float
- `Best_student_match%`: Float
- `Ads_used`: Integer
- `Entry_level_ads`: Integer
- `Basis`: String
- `Core_skills`: Formatted string of top skills and their market frequencies

---

### 4. Existing vs. Modernized Feature Mapping

| Experimental Feature | Modernized SADAT Portal Module | Modernization Strategy |
|:---|:---|:---|
| In-memory student picker & dropdown | OAuth 2.0 / OIDC Authenticated Student Portal | Student logs in securely; view is scoped exclusively to authenticated identity. |
| In-browser JavaScript engine / python `server.py` | Standalone Node.js API + Private Python Intelligence Service | Strict server separation; Node handles auth & data, Python executes engine logic. |
| Hardcoded sample student grades | MongoDB persistent student academic records | Authorized academic records loaded per authenticated student; immutable read-only view. |
| Interactive score sliders for 14 skills | Free Tests Center with Real-Time Preview | Sliders provide immediate "What-If" preview, distinctly marked from persisted records. |
| Dynamic questionnaire in `app.js` | Structured Multi-Step Student Questionnaire | Validated with Zod schemas; persists claims, verified flags, months, and cert attachments. |
| Static `style.css` layout | TailwindCSS Retro Grid + Calm Sea Palette | Modern editorial layout with subtle technical grid accents, responsive card grid. |
| Single language (English only) | Full Bilingual Engine (Arabic RTL & English LTR) | React-i18next with bi-directional CSS mirroring and localized terminology. |
| Static CSV dashboard | Interactive Market Intelligence Dashboard | Recharts visualization consuming verified datasets with version freshness indicators. |
| Python script scraper | BullMQ Background Job Scraper Service | Async queue-driven execution with deduplication and metadata auditing. |

---

### 5. Verification Baseline Outputs
Execution of `backend/test_platform.py` on 2026-11-23 produced the exact reference numbers for student `SAD20260001`:
- **Sample Student**: Adam Gamal Samir (GPA: 3.29, Grade: Very Good).
- **Baseline Top Roles**:
  - Cybersecurity: 55.0%
  - Network Engineer / Tester: 50.6%
  - Data Analyst / BI: 50.5%
- **Baseline Top Jobs**:
  - #1 SOC Analyst (L1) at Si-Ware Systems: 63.8% fit
  - #2 Junior Cybersecurity Analyst at Valu: 63.8% fit
  - #3 Junior Cybersecurity Analyst at Bosta: 63.8% fit
- **Post-Questionnaire Simulation** (14 mo experience, Python 95, SQL 90, ML 88, Docker 80, AWS ML Cert):
  - AI / ML Engineer: 67.4% match
  - Data Scientist: 57.8% match
  - Cybersecurity: 56.2% match
  - Top Job #1: Junior Machine Learning Engineer at ITWorx: 76.6% fit

These values serve as Gate 7 regression validation targets.
