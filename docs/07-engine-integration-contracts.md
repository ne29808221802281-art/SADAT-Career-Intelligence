# SADAT – Student Career Intelligence & Skills Growth Portal
## 07. Engine Integration Contracts Specification

This document defines the interface contracts between the Node.js API backend and the internal Python Intelligence Service (`services/intelligence`).

---

### 1. Architectural Boundary
- The Python Intelligence Service is a private service listening exclusively on internal localhost (e.g. `127.0.0.1:8000`).
- Communication is executed via HTTP JSON RPC contracts over private endpoints.
- All requests are authenticated via an internal preshared secret (`X-Internal-Token`).
- Under no circumstance is the Python intelligence layer reachable directly by the frontend browser.

---

### 2. Contract 1: Student Evaluation & Job Matching

#### Endpoint: `POST /internal/evaluate`
Executes `matcher.evaluate_student(...)` with full support for official transcripts, questionnaire overrides, and certificate mapping.

##### Request Payload (`EvaluateRequest`):
```json
{
  "student_id": "SAD20260001",
  "custom_grades": null,
  "experience": {
    "has_experience": true,
    "months": 14,
    "verified": true,
    "role": "AI / ML Engineer",
    "skills": ["Machine Learning", "Python", "Deep Learning"]
  },
  "test_scores": {
    "Python": 95,
    "SQL": 90,
    "Machine Learning": 88,
    "Docker": 80
  },
  "certificates": [
    {
      "name": "AWS Certified Machine Learning - Associate",
      "verified": true
    }
  ]
}
```

##### Response Payload (`EvaluateResponse`):
```json
{
  "student": {
    "Student_ID": "SAD20260001",
    "Student_Name": "Adam Gamal Samir",
    "GPA": 3.29,
    "Grade_Label": "Very Good"
  },
  "experience": {
    "months": 14.0,
    "years": 1.17
  },
  "top_roles": [
    {
      "role": "AI / ML Engineer",
      "match_pct": 67.4,
      "based_on": "entry-level ads",
      "core_skills": ["Python (100%)", "Git (85%)", "Machine Learning (77%)"],
      "gaps": [
        {
          "skill": "TensorFlow",
          "demand_pct": 46.2,
          "level_pct": 27.0,
          "cause": "Only partly covered",
          "actions": [
            {
              "kind": "project",
              "name": "Build a hands-on project demonstrating TensorFlow on GitHub",
              "provider": "Self-Directed",
              "cost": "free",
              "text": "Build a hands-on project demonstrating TensorFlow on GitHub [Self-Directed, free]"
            }
          ]
        }
      ]
    }
  ],
  "top_jobs": [
    {
      "rank": 1,
      "job_id": 4100105,
      "title": "Junior Machine Learning Engineer",
      "company": "ITWorx",
      "specialization": "AI / ML Engineer",
      "level": "Junior",
      "work_mode": "Remote",
      "years_required": 0,
      "fit_pct": 76.6,
      "is_eligible": true,
      "url": "https://www.linkedin.com/jobs/view/4100105",
      "skills_detail": [
        { "skill": "Python", "level_pct": 98.5, "status": "strong" },
        { "skill": "Machine Learning", "level_pct": 94.2, "status": "strong" },
        { "skill": "Deep Learning", "level_pct": 89.1, "status": "strong" },
        { "skill": "TensorFlow", "level_pct": 27.0, "status": "partial" },
        { "skill": "PyTorch", "level_pct": 27.0, "status": "partial" },
        { "skill": "Scikit-learn", "level_pct": 36.0, "status": "partial" },
        { "skill": "Docker", "level_pct": 80.0, "status": "strong" },
        { "skill": "Git", "level_pct": 27.0, "status": "partial" }
      ],
      "improve_plan": [
        {
          "skill": "TensorFlow",
          "level_pct": 27.0,
          "cause": "Only partly covered",
          "est_fit_gain_pts": null,
          "actions": [
            {
              "kind": "project",
              "name": "Build a hands-on project demonstrating TensorFlow on GitHub",
              "provider": "Self-Directed",
              "cost": "free",
              "text": "Build a hands-on project demonstrating TensorFlow on GitHub [Self-Directed, free]"
            }
          ]
        }
      ]
    }
  ],
  "skills_summary": [
    {
      "skill": "Python",
      "level_pct": 98.5,
      "transcript_evidence": 1.2,
      "status": "ready"
    }
  ]
}
```

---

### 3. Contract 2: Job Scraper Background Execution

#### Endpoint: `POST /internal/scraper/execute`
Executes `linkedin_jobs_scraper.scrape(...)` through an async job runner.

##### Request Payload:
```json
{
  "keywords": ["AI Engineer", "Cybersecurity", "Data Analyst"],
  "location": "Egypt",
  "pages": 2,
  "since": "month",
  "fetch_details": true
}
```

##### Response Payload:
```json
{
  "status": "success",
  "jobs_harvested": 48,
  "jobs_unique": 45,
  "execution_duration_sec": 84.2,
  "partial_file": "linkedin_egypt_tech_jobs_partial.csv"
}
```

---

### 4. Contract 3: Health & Readiness Probe

#### Endpoint: `GET /internal/health`
Returns runtime diagnostic health of the intelligence engine.

##### Response Payload:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "python_version": "3.12.12",
  "loaded_datasets": {
    "students": 1000,
    "courses": 49,
    "jobs": 169,
    "market_skills": 77,
    "roles": 13
  }
}
```
