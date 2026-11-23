# SADAT – Student Career Intelligence & Skills Growth Portal
## 02. Functional Requirements Specification

This document provides formal requirements for all modules of the modernized SADAT portal.

---

### REQ-AUTH-001: Student Authentication via External Identity Provider
- **Title**: University OIDC / OAuth 2.0 Single Sign-On
- **Description**: The system shall authenticate students using the University's Graduates Affairs identity provider via OAuth 2.0 / OpenID Connect authorization code flow with PKCE.
- **Input Requirements**: Authorization code from university identity provider callback.
- **Expected Behavior**: Exchange authorization code for tokens, retrieve verified user claims (student ID, email, full name), establish an isolated HttpOnly session cookie, and create/update local student profile.
- **Expected Output**: Authenticated session cookie; student profile overview payload.
- **Validation Rules**: Validate state parameter against CSRF; verify JWT signature and issuer against configured OIDC discovery document.
- **Error Handling**: On authorization failure or token rejection, redirect to login page with localized error notification (`AUTH_FAILED_OR_CANCELLED`).
- **Acceptance Criteria**: Student logs in without a separate portal password; session is completely isolated from the Graduates Affairs database.
- **Related API Endpoints**: `GET /api/v1/auth/login`, `GET /api/v1/auth/callback`, `POST /api/v1/auth/logout`, `GET /api/v1/auth/me`.
- **Related Database Entities**: `UserSession`, `StudentProfile`, `AuditLog`.
- **Related Test Cases**: `TEST-AUTH-001` (login flow), `TEST-AUTH-002` (CSRF mismatch).

---

### REQ-PROF-001: Student Profile and Academic Record Retrieval
- **Title**: View Authorized Academic Information
- **Description**: The system shall display the authenticated student's official 4-year transcript, GPA, degree classification, and completed coursework.
- **Input Requirements**: Authenticated student session.
- **Expected Behavior**: Fetch academic records linked strictly to the student's authenticated ID. All official marks are rendered read-only.
- **Expected Output**: JSON document with student metadata, cumulative GPA, grade label, and course marks array (C001-C049).
- **Validation Rules**: Frontend request must NOT be allowed to specify an arbitrary student ID; the identity is bound to session claims.
- **Error Handling**: If no academic records are found, return `404 Academic Record Not Found` with guidance to contact academy administration.
- **Acceptance Criteria**: Academic records cannot be tampered with by the student; other students' transcripts are strictly unreachable.
- **Related API Endpoints**: `GET /api/v1/students/me`, `GET /api/v1/students/me/academic-records`.
- **Related Database Entities**: `StudentProfile`, `StudentAcademicRecord`, `StudentGrade`.
- **Related Test Cases**: `TEST-PROF-001` (own transcript access), `TEST-PROF-002` (cross-student access prevention).

---

### REQ-QUEST-001: Student Career Questionnaire Submission
- **Title**: Dynamic Evidence & Experience Questionnaire
- **Description**: Students shall report professional work experience, internships, self-ratings, and international certifications.
- **Input Requirements**: Validated questionnaire payload: work experience (months, role, verified flag), claimed/verified certifications (names, dates, verification docs), self-ratings.
- **Expected Behavior**: Validate fields via Zod schema, persist responses, attach uploaded proof documents, and trigger asynchronous skill reevaluation.
- **Expected Output**: Questionnaire response object with saved timestamp and updated evaluation task ID.
- **Validation Rules**: Months must be a non-negative integer ($\le 240$); ratings must be $0-100$; certificate names must map to recognized providers or custom text.
- **Error Handling**: Return `422 Unprocessable Entity` with specific field validation errors on malformed payloads.
- **Acceptance Criteria**: Submission updates student evidence state and initiates matching recalculation without blocking the web UI.
- **Related API Endpoints**: `GET /api/v1/questionnaire`, `GET /api/v1/questionnaire/responses`, `POST /api/v1/questionnaire/responses`.
- **Related Database Entities**: `QuestionnaireResponse`, `StudentEvidence`, `DocumentUpload`.
- **Related Test Cases**: `TEST-QUEST-001` (valid submission), `TEST-QUEST-002` (negative months validation).

---

### REQ-SKILL-001: Evidence-Weighted Competency Evaluation
- **Title**: Calculate Multi-Source Skill Competency
- **Description**: The system shall execute the authoritative evidence aggregation formula combining transcripts, verified/claimed experience, certificates, and test scores.
- **Input Requirements**: Course marks array, evidence list (source, level, months).
- **Expected Behavior**: Compute $S_s = \frac{\sum W_e \cdot L_e}{\max(\sum W_e, 1.0)}$ for all 72 technical skills using the exact weights:
  - Transcript: 1.0 (scaled by credit-hour evidence)
  - Verified Certificate: 0.9 (Level = 1.0)
  - Verified Experience: 0.8 (Level = min(1.0, Months/12))
  - Online Tests: 0.7 (Level = Score/100)
  - Claimed Certificate: 0.5 (Level = 1.0)
  - Claimed Experience: 0.5 (Level = min(1.0, Months/12))
  - Self-Rating: 0.3 (Level = Rating/100)
- **Expected Output**: Competency profile with numerical scores ($0-100\%$), evidence breakdown, and status classifications (Strong/Developing/Missing).
- **Validation Rules**: Calculated skill levels must strictly lie within $[0.0, 1.0]$.
- **Error Handling**: If a calculation error occurs, log structured diagnostic telemetry and return cached previous evaluation if available.
- **Acceptance Criteria**: Identical numeric output to the experimental Python engine for any given test student.
- **Related API Endpoints**: `GET /api/v1/students/me/skills`, `POST /api/v1/matching/evaluate`.
- **Related Database Entities**: `StudentSkill`, `StudentEvidence`, `EngineExecution`.
- **Related Test Cases**: `TEST-ENG-001` (evidence weight validation), `TEST-ENG-002` (credit hour scaling).

---

### REQ-MATCH-001: Generate Top 10 Job Matches
- **Title**: Top 10 Compatible Job Rankings
- **Description**: Rank candidate jobs based on the student's evaluated competency profile and filter by experience eligibility.
- **Input Requirements**: Evaluated skill profile $S$, student experience years, candidate job collection.
- **Expected Behavior**: Evaluate fit using $\text{Fit}(j) = \frac{\sum_{s \in \text{Skills}(j)} S_s}{\max(|\text{Skills}(j)|, 4)}$. Enforce eligibility $\text{YearsMin}(j) \le 2 + \lfloor\text{ExpYears}\rfloor$. Sort eligible jobs descending by fit score and return top 10.
- **Expected Output**: Array of top 10 job match objects containing rank, job title, company, work mode, eligibility status, fit percentage, and skill classification lists (Strong $\ge 50\%$, Developing $1-49\%$, Missing $0\%$).
- **Validation Rules**: Returned ranking must not contain ineligible jobs before eligible ones; fit percentages must match original engine calculations.
- **Error Handling**: If candidate jobs cannot be loaded, fail gracefully with `503 Service Unavailable` without crashing the service.
- **Acceptance Criteria**: Baseline evaluation of student `SAD20260001` must return the exact 3 top jobs from the reference engine (SOC Analyst @ Si-Ware, Jr Cyber Analyst @ Valu, Jr Cyber Analyst @ Bosta at 63.8% fit).
- **Related API Endpoints**: `GET /api/v1/matching/me`, `GET /api/v1/matching/me/:jobId`.
- **Related Database Entities**: `JobPosting`, `JobMatch`, `EngineExecution`.
- **Related Test Cases**: `TEST-MATCH-001` (Top 10 ranking parity), `TEST-MATCH-002` (experience eligibility cutoff).

---

### REQ-RECOM-001: Fit Improvement Roadmap and Estimated Fit Gain
- **Title**: Personalized Actionable Recommendations
- **Description**: For each missing or developing skill in top jobs and target roles, diagnose the root cause and generate prioritized learning actions with calculated fit gain points.
- **Input Requirements**: Evaluated student skills, course marks, course-skill mapping, recommendation catalog.
- **Expected Behavior**:
  - If skill covered by curriculum and mark $< 65$: Recommend revisiting specific university course (e.g. "Revisit C015 Computer Operating Systems (your mark 62)").
  - If skill not covered: Recommend external certification (AWS, Azure, etc.) or free assessments (HackerRank, Kaggle).
  - Calculate estimated fit gain $\Delta \text{Fit} = \text{round}\left(100.0 \times \frac{S_{\text{new}} - S_{\text{old}}}{N_{\text{eff}}}, 1\right)$ using assumed credential weights ($0.9$ for certs, $0.7$ for tests at 80% score).
- **Expected Output**: Roadmap items with target skill, cause description, recommended actions list (provider, cost, link), and estimated gain in percentage points.
- **Validation Rules**: Gain points must reflect actual formula, not arbitrary additions.
- **Error Handling**: Fallback to self-directed GitHub project recommendation when a skill lacks a specific catalog entry.
- **Acceptance Criteria**: Estimated fit gain matches Python engine outputs within $0.1$ percentage points.
- **Related API Endpoints**: `GET /api/v1/recommendations/me`, `PATCH /api/v1/recommendations/me/:id/progress`.
- **Related Database Entities**: `StudentRoadmap`, `RecommendationCatalog`.
- **Related Test Cases**: `TEST-RECOM-001` (weak grade course recommendation), `TEST-RECOM-002` (fit gain math).

---

### REQ-TEST-001: Missing Skills & Free Tests Center
- **Title**: Interactive 14 Missing Skills Assessment Center
- **Description**: Provide a dedicated module displaying the 14 high-demand skills not covered by the curriculum, with verified free testing links and interactive score preview sliders.
- **Input Requirements**: Student test scores ($0-100\%$) per missing skill.
- **Expected Behavior**: Render responsive skill cards with direct assessment links. Sliders allow students to simulate what-if scenarios with real-time recalculation of job matches and fit gains.
- **Expected Output**: Preview evaluation results clearly distinguished from persisted official records.
- **Validation Rules**: Score slider inputs constrained between 0 and 100; slider changes do not alter official verified student records until officially saved/submitted with proof.
- **Error Handling**: On network failure during preview recalculation, retain client-side calculation fallback.
- **Acceptance Criteria**: All 14 skills match the catalog; external links lead to valid test providers (HackerRank, LearnSQL, KodeKloud, AWS, etc.).
- **Related API Endpoints**: `GET /api/v1/free-tests`, `POST /api/v1/students/me/assessments`.
- **Related Database Entities**: `FreeTestResource`, `StudentAssessment`.
- **Related Test Cases**: `TEST-TEST-001` (14 skill definitions), `TEST-TEST-002` (real-time recalculation preview).

---

### REQ-MKT-001: Job Market & Cohort Intelligence Dashboard
- **Title**: Empirical Market vs. Cohort Analytics
- **Description**: Render interactive analytics visualizations grounded strictly in `market_vs_cohort_skills.csv` and `role_summary.csv`.
- **Input Requirements**: Query parameters for filtering by role or specialization.
- **Expected Behavior**: Provide comparative bar charts of market demand vs cohort readiness, curriculum evidence, gap scores, and role summary benchmarks (mean, median, best student match).
- **Expected Output**: High-performance JSON analytics payloads rendered via responsive Recharts components.
- **Validation Rules**: Data must strictly reflect the imported dataset versions; no synthetic statistics.
- **Error Handling**: Return HTTP 500 if dataset is uninitialized, with administrative alert.
- **Acceptance Criteria**: Dashboard displays all 77 market skills and 13 roles with identical metric values to the CSV datasets.
- **Related API Endpoints**: `GET /api/v1/market/overview`, `GET /api/v1/market/skills`, `GET /api/v1/market/roles`.
- **Related Database Entities**: `MarketInsight`, `RoleSummary`, `DatasetVersion`.
- **Related Test Cases**: `TEST-MKT-001` (skills gap data integrity), `TEST-MKT-002` (role summaries).

---

### REQ-SCRP-001: Asynchronous Job Scraper Execution
- **Title**: LinkedIn Tech Jobs Background Harvester
- **Description**: Execute the LinkedIn scraper logic via BullMQ worker queues to harvest current Egyptian tech jobs without blocking the main application server.
- **Input Requirements**: Job search keywords list, location ("Egypt"), pages count, time filter.
- **Expected Behavior**: Fetch guest job cards and detail pages, extract skills using canonical regex dictionary, classify specialization and seniority, deduplicate by `(title, company)`, and store in MongoDB.
- **Expected Output**: Ingestion audit record with count of new, updated, and skipped postings.
- **Validation Rules**: Apply random delays ($3-7$s) and exponential backoff to handle rate limits (HTTP 429/999).
- **Error Handling**: Log network errors; save checkpoint batches to partial storage on failure.
- **Acceptance Criteria**: Scraper pipeline accurately extracts skills and work modes into the database schema matching `jobs.csv`.
- **Related API Endpoints**: `POST /api/v1/admin/scraper/run`, `GET /api/v1/admin/scraper/status`.
- **Related Database Entities**: `JobPosting`, `ScraperJobRun`.
- **Related Test Cases**: `TEST-SCRP-001` (skill extraction regex), `TEST-SCRP-002` (deduplication logic).

---

### REQ-I18N-001: Full Bilingual English and Arabic RTL Experience
- **Title**: Bi-directional Bilingual Interface
- **Description**: Support seamless runtime switching between English (LTR) and Arabic (RTL) with complete layout mirroring.
- **Input Requirements**: User language selection stored in cookies/localStorage.
- **Expected Behavior**: Dynamically toggle document `dir="rtl"` / `dir="ltr"` and `lang="ar"` / `lang="en"`, swap font families (Inter for English, IBM Plex Sans Arabic for Arabic), mirror navigation, cards, and charts. Keep technical names in original English where appropriate.
- **Expected Output**: Fully rendered localized UI.
- **Validation Rules**: Text strings must be loaded from translation dictionaries; zero untranslated UI strings.
- **Error Handling**: Fallback gracefully to English string if an Arabic key is missing.
- **Acceptance Criteria**: Layout visibly mirrors in Arabic; numbers and percentages format correctly according to locale.
- **Related API Endpoints**: Client-side locale state.
- **Related Test Cases**: `TEST-I18N-001` (RTL DOM attribute toggle), `TEST-I18N-002` (translation fallback).
