# SADAT – Student Career Intelligence & Skills Growth Portal
## 06. Database Schema Specification (MongoDB / Mongoose)

This document specifies the MongoDB collections, schema layouts, indexes, and document relationships.

---

### 1. Collections Overview

```text
sadat_career_db
├── students
├── courses
├── course_skill_mappings
├── student_grades
├── student_evidence
├── questionnaire_responses
├── jobs
├── job_matches
├── student_roadmaps
├── market_insights
├── role_summaries
├── free_test_resources
├── document_uploads
├── engine_executions
└── dataset_versions
```

---

### 2. Collection Schemas & Index Definitions

#### 2.1 `students`
```typescript
interface IStudent {
  _id: ObjectId;
  studentId: string;       // Unique institutional ID (e.g., "SAD20260001")
  fullName: string;
  email: string;
  gpa: number;             // e.g. 3.29
  gradeLabel: string;      // e.g. "Very Good"
  cohortYear: number;      // e.g. 2026
  role: 'student' | 'admin';
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

// Indexes:
// { studentId: 1 } (Unique)
// { email: 1 } (Unique)
```

#### 2.2 `courses` & `course_skill_mappings`
```typescript
interface ICourse {
  _id: ObjectId;
  courseId: string;        // "C001" - "C049"
  year: number;            // 1 - 4
  courseName: string;
  creditHours: number;     // 2 or 3
}

interface ICourseSkillMapping {
  _id: ObjectId;
  courseId: string;
  skill: string;           // Canonical skill
  relevance: number;       // 0.1 - 1.0
  evidenceWeight: number;  // relevance * creditHours
  confidence: 'H' | 'M' | 'L';
  facultyReview?: string;
  notes?: string;
}

// Indexes:
// courses: { courseId: 1 } (Unique)
// course_skill_mappings: { courseId: 1, skill: 1 } (Unique), { skill: 1 }
```

#### 2.3 `student_grades`
```typescript
interface IStudentGrade {
  _id: ObjectId;
  studentId: string;
  courseId: string;
  courseName: string;
  mark: number;            // 0 - 100
  creditHours: number;
}

// Indexes:
// { studentId: 1, courseId: 1 } (Unique)
// { studentId: 1 }
```

#### 2.4 `student_evidence` & `questionnaire_responses`
```typescript
interface IStudentEvidence {
  _id: ObjectId;
  studentId: string;
  source: 'transcript' | 'certificate_verified' | 'experience_verified' |
          'online_test' | 'certificate_claimed' | 'experience_claimed' | 'self_rating';
  skill: string;
  level: number;           // 0.0 - 1.0
  months?: number;
  certificateName?: string;
  testScore?: number;      // 0 - 100
  verificationDocId?: ObjectId;
  isVerified: boolean;
  createdAt: Date;
}

interface IQuestionnaireResponse {
  _id: ObjectId;
  studentId: string;
  hasExperience: boolean;
  experienceMonths: number;
  experienceRole?: string;
  experienceVerified: boolean;
  certificates: Array<{
    name: string;
    verified: boolean;
    issueDate?: string;
    docId?: ObjectId;
  }>;
  testScores: Record<string, number>; // { Python: 95, SQL: 90, ... }
  selfRatings: Record<string, number>;
  submittedAt: Date;
}

// Indexes:
// student_evidence: { studentId: 1, skill: 1, source: 1 }, { studentId: 1 }
// questionnaire_responses: { studentId: 1 } (Unique)
```

#### 2.5 `jobs` & `job_matches`
```typescript
interface IJobPosting {
  _id: ObjectId;
  jobId: string;           // "4100101"
  title: string;
  company: string;
  companyCountry: string;
  jobLocation: string;
  workMode: 'Remote' | 'Hybrid' | 'On-site' | 'Not specified';
  level: 'Intern' | 'Junior' | 'Mid' | 'Senior';
  yearsExpMin?: number;
  yearsExpMax?: number;
  technicalRequirements: string[];
  certificationsMentioned: string[];
  employmentType: string;
  linkedinSeniority?: string;
  postedDate?: string;
  url: string;
  isLive: boolean;
  scrapedAt: Date;
}

interface IJobMatch {
  _id: ObjectId;
  studentId: string;
  jobId: string;
  rank: number;            // 1 - 10
  fitPct: number;          // 0.0 - 100.0
  isEligible: boolean;
  skillsDetail: Array<{
    skill: string;
    levelPct: number;
    status: 'strong' | 'partial' | 'missing';
  }>;
  calculatedAt: Date;
}

// Indexes:
// jobs: { jobId: 1 } (Unique), { specialization: 1 }, { level: 1 }, { workMode: 1 }
// job_matches: { studentId: 1, rank: 1 }, { studentId: 1, jobId: 1 } (Unique)
```

#### 2.6 `student_roadmaps`
```typescript
interface IStudentRoadmapItem {
  _id: ObjectId;
  studentId: string;
  jobId?: string;
  skill: string;
  currentLevelPct: number;
  cause: string;
  actionKind: 'revisit' | 'certificate' | 'test' | 'course' | 'practice' | 'project';
  actionName: string;
  actionProvider: string;
  actionCost: string;
  actionUrl?: string;
  estFitGainPts?: number;
  status: 'suggested' | 'planned' | 'in_progress' | 'completed';
  evidenceDocId?: ObjectId;
  updatedAt: Date;
}

// Indexes:
// { studentId: 1, skill: 1 }
```

#### 2.7 `market_insights` & `role_summaries`
```typescript
interface IMarketInsight {
  _id: ObjectId;
  skill: string;
  demandEntryLevelAdsPct: number;
  demandAllLevelsPct: number;
  cohortMeanLevelPct: number;
  cohortReadyPct: number;
  curriculumEvidence: number;
  gapScore: number;
  datasetVersion: string;
}

interface IRoleSummary {
  _id: ObjectId;
  role: string;
  cohortMeanMatchPct: number;
  cohortMedianMatchPct: number;
  bestStudentMatchPct: number;
  adsUsed: number;
  entryLevelAds: number;
  basis: string;
  coreSkills: string;
  datasetVersion: string;
}

// Indexes:
// market_insights: { skill: 1, datasetVersion: 1 } (Unique)
// role_summaries: { role: 1, datasetVersion: 1 } (Unique)
```
