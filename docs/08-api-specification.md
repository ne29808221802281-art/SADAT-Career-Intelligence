# SADAT – Student Career Intelligence & Skills Growth Portal
## 08. Public REST API Specification

All endpoints are prefixed with `/api/v1`. Authentication is verified via HttpOnly session cookies unless otherwise documented.

---

### 1. Authentication Endpoints (`/api/v1/auth`)

#### `GET /api/v1/auth/login`
- **Description**: Initiates OIDC authorization flow with university identity provider.
- **Parameters**: `redirect_uri` (optional).
- **Response**: `302 Found` redirecting to University IdP authorization URL.

#### `GET /api/v1/auth/callback`
- **Description**: Handles callback from IdP, validates authorization code, creates session.
- **Query**: `code`, `state`.
- **Response**: `302 Found` redirecting to student dashboard; sets `Set-Cookie: sadat_session=...; HttpOnly; Secure; SameSite=Strict`.

#### `POST /api/v1/auth/logout`
- **Description**: Terminates active session and clears session cookie.
- **Response**: `200 OK` `{ "success": true, "message": "Logged out" }`.

#### `GET /api/v1/auth/me`
- **Description**: Retrieves current authenticated identity.
- **Response**:
```json
{
  "studentId": "SAD20260001",
  "fullName": "Adam Gamal Samir",
  "email": "adam.samir@sadat.edu.eg",
  "role": "student"
}
```

---

### 2. Student & Academic Endpoints (`/api/v1/students`)

#### `GET /api/v1/students/me`
- **Description**: Returns student profile, cumulative GPA, and graduation status.
- **Response**:
```json
{
  "studentId": "SAD20260001",
  "fullName": "Adam Gamal Samir",
  "gpa": 3.29,
  "gradeLabel": "Very Good",
  "cohortYear": 2026
}
```

#### `GET /api/v1/students/me/academic-records`
- **Description**: Returns official 4-year transcript marks (Read-Only).
- **Response**:
```json
{
  "totalCourses": 49,
  "courses": [
    {
      "courseId": "C015",
      "courseName": "Computer Operating Systems",
      "year": 2,
      "creditHours": 3,
      "mark": 62
    },
    {
      "courseId": "C026",
      "courseName": "Machine&Deep Learning",
      "year": 3,
      "creditHours": 3,
      "mark": 78
    }
  ]
}
```

#### `GET /api/v1/students/me/skills`
- **Description**: Returns evaluated competencies across all 72 market skills with evidence breakdowns.
- **Response**:
```json
{
  "skills": [
    {
      "skill": "Python",
      "levelPct": 98.5,
      "transcriptEvidence": 1.2,
      "status": "ready"
    }
  ]
}
```

---

### 3. Questionnaire & Evidence Endpoints (`/api/v1/questionnaire`)

#### `GET /api/v1/questionnaire`
- **Description**: Returns questionnaire definitions, recognized certificate choices, and role options.
- **Response**:
```json
{
  "recognizedCertificates": ["AWS Certified Machine Learning - Associate", "Microsoft AZ-900 Azure Fundamentals"],
  "technicalTracks": ["AI / ML Engineer", "Cybersecurity", "Data Scientist"]
}
```

#### `GET /api/v1/questionnaire/responses`
- **Description**: Returns student's currently saved questionnaire responses.

#### `POST /api/v1/questionnaire/responses`
- **Description**: Saves or updates questionnaire responses and triggers matching reevaluation.
- **Payload**:
```json
{
  "hasExperience": true,
  "months": 14,
  "role": "AI / ML Engineer",
  "verified": true,
  "certificates": [
    { "name": "AWS Certified Machine Learning - Associate", "verified": true }
  ],
  "testScores": {
    "Python": 95,
    "SQL": 90
  }
}
```
- **Response**: `200 OK` with updated evaluation results.

---

### 4. Job Matching Endpoints (`/api/v1/matching`)

#### `GET /api/v1/matching/me`
- **Description**: Returns Top 10 Job Matches for the student with fit percentages and skill breakdowns.
- **Response**:
```json
{
  "eligibleExperienceYears": 1.17,
  "topJobs": [
    {
      "rank": 1,
      "jobId": "4100105",
      "title": "Junior Machine Learning Engineer",
      "company": "ITWorx",
      "specialization": "AI / ML Engineer",
      "level": "Junior",
      "workMode": "Remote",
      "fitPct": 76.6,
      "isEligible": true,
      "url": "https://www.linkedin.com/jobs/view/4100105",
      "strongSkills": ["Python", "Machine Learning", "Deep Learning", "Docker"],
      "developingSkills": ["TensorFlow", "PyTorch", "Scikit-learn", "Git"],
      "missingSkills": []
    }
  ]
}
```

#### `GET /api/v1/matching/me/:jobId`
- **Description**: Detailed diagnostic compatibility view for an individual job posting.

---

### 5. Recommendations Endpoints (`/api/v1/recommendations`)

#### `GET /api/v1/recommendations/me`
- **Description**: Returns the Fit Improvement Roadmap with estimated fit gain points.
- **Response**:
```json
{
  "recommendations": [
    {
      "id": "rec-001",
      "skill": "Linux",
      "cause": "Weak grades in related courses",
      "currentLevelPct": 37.7,
      "estFitGainPts": 11.1,
      "actions": [
        {
          "kind": "revisit",
          "name": "Revisit Computer Operating Systems (your mark 62)",
          "provider": "Sadat Academy",
          "cost": "free"
        }
      ],
      "status": "suggested"
    }
  ]
}
```

#### `PATCH /api/v1/recommendations/me/:id/progress`
- **Description**: Updates student's roadmap item status (`"planned"`, `"in_progress"`, `"completed"`).

---

### 6. Free Tests Center (`/api/v1/free-tests`)

#### `GET /api/v1/free-tests`
- **Description**: Returns the 14 in-demand missing skills with verified free test resources.
- **Response**: Array of 14 skill cards with provider, free test URL, and prep course.

#### `POST /api/v1/free-tests/preview`
- **Description**: Dynamic "What-If" preview recalculation without persisting data.
- **Payload**: `{ "testScores": { "Python": 90, "Kubernetes": 70 } }`
- **Response**: Instant recalculated Top 10 jobs and fit percentages.

---

### 7. Market Intelligence (`/api/v1/market`)

#### `GET /api/v1/market/overview`
- **Description**: Overview statistics of market demand vs cohort readiness.

#### `GET /api/v1/market/skills`
- **Description**: Returns all 77 market skills from `market_vs_cohort_skills.csv`.

#### `GET /api/v1/market/roles`
- **Description**: Returns all 13 role profiles and cohort match statistics from `role_summary.csv`.

---

### 8. Documents & File Uploads (`/api/v1/documents`)

#### `POST /api/v1/documents/upload`
- **Description**: Uploads CV, certificate PDF, or proof document via multipart/form-data.
- **Constraints**: PDF/PNG/JPEG, max 5MB.
- **Response**: `{ "documentId": "doc-uuid", "filename": "cert.pdf", "status": "uploaded" }`.
