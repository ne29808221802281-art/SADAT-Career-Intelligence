# SADAT – Student Career Intelligence & Skills Growth Portal
## 00. Project Overview

### 1. Executive Summary
**SADAT – Student Career Intelligence & Skills Growth Portal** is a production-grade, standalone, bilingual (Arabic RTL & English LTR) university career intelligence platform designed specifically for students and graduates of the Faculty of Computers and Information at Sadat Academy.

The platform provides intelligent, evidence-weighted academic career guidance by evaluating:
1. Four-year official university transcripts (course-to-skill mappings, credit hours, marks).
2. Professional work experience (verified and self-reported/claimed).
3. Online skill assessment scores (14 high-demand missing skills).
4. International industry certifications (Microsoft, AWS, Google Cloud, Cisco, CompTIA, CNCF, etc.).

These inputs are evaluated against 169 real Egyptian tech market job postings (and newly scraped live opportunities) to generate the student's **Top 10 Matching Jobs**, diagnose precise skill gaps (Strong $\ge 50\%$, Developing $1-49\%$, Missing $0\%$), provide actionable **Fit Improvement Roadmaps**, and compute mathematical **Estimated Fit Gain** points.

---

### 2. Core Objectives
1. **Accurate Skill Profiling**: Translate raw university course marks and external credentials into evidence-weighted skill competency scores without modifying or inventing scoring heuristics.
2. **Top 10 Job Matching**: Rank real job openings using the authoritative algorithm:
   $$\text{Fit}(j) = \frac{\sum_{s \in \text{Skills}(j)} S_s}{\max(|\text{Skills}(j)|, 4)}$$
3. **Experience Eligibility Filtering**: Enforce the non-negotiable eligibility constraint:
   $$\text{Years Required} \le 2 + 1.0 \times \lfloor\text{Experience Years}\rfloor$$
4. **Actionable Growth Roadmap**: Categorize gap root causes (*Weak grades in related courses*, *Not covered by curriculum*, *Only partly covered*) and deliver concrete learning actions (revisiting courses, taking certifications, micro-courses, or hands-on projects).
5. **Estimated Fit Gain**: Compute the exact increase in job compatibility ($+X.X\%$) when a student completes a recommended test or certification.
6. **14 Missing Skills & Free Tests Center**: Provide structured access and interactive sliders to 14 high-demand Egyptian market skills absent from the academic curriculum, with real-time recalculation of job matches.
7. **Market & Cohort Intelligence**: Deliver real dashboards grounded in empirical data from `market_vs_cohort_skills.csv` and `role_summary.csv`.
8. **Bilingual Academic UX**: Deliver an editorial, minimalistic retro-grid interface themed with a calm sea palette (`#15354B`, `#286581`, `#4E8298`, `#76A9A6`, `#EAF3F5`, `#F8FAF9`), fully localized in Arabic (RTL) and English (LTR).

---

### 3. Source of Truth & Preservation Mandate
The experimental implementation in `career-matching-platform` and the three reference scripts:
- `linkedin_jobs_scraper.py`
- `recommendation_catalog.py`
- `matching_engine.py`

constitute the non-negotiable functional baseline. All weights, formulas, thresholds, catalogs, regex patterns, and CSV schemas must be preserved with exact parity.

---

### 4. Implementation Gates Overview
| Gate | Phase | Scope |
|:---|:---|:---|
| **Gate 1** | Discovery | Deep source code audit, baseline testing, existing-to-new mapping (`01-existing-system-analysis.md`). |
| **Gate 2** | Architecture | Specification of all 16 docs, API contracts, data models, and system topology. |
| **Gate 3** | Foundation | Scaffolding web and API layers, database models, design tokens, and RTL i18n system. |
| **Gate 4** | Intelligence Integration | Packaging scraper, recommendation catalog, and matching engine into private service interfaces. |
| **Gate 5** | Student Portal | Student dashboard, profile, transcript review, questionnaire, job cards, and roadmap tracker. |
| **Gate 6** | Analytics | Grounded market intelligence dashboard with interactive charts and role summaries. |
| **Gate 7** | Validation | Differential verification comparing new platform outputs with original Python baseline. |
| **Gate 8** | Production Readiness | Security hardening, audit logging, Docker containerization, and final verification. |
