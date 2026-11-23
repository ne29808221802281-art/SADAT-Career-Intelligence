# SADAT – Student Career Intelligence & Skills Growth Portal
## 05. Data Dictionary Specification

This document provides exact definitions, types, constraints, and valid ranges for all data attributes in the SADAT platform.

---

### 1. Student Domain Entities

#### 1.1 `Student`
| Field | Type | Required | Description | Example / Constraints |
|:---|:---|:---|:---|:---|
| `studentId` | String | Yes | Unique institutional identifier | `"SAD20260001"`, format `^SAD\d{8}$` |
| `fullName` | String | Yes | Official student full name | `"Adam Gamal Samir"` |
| `email` | String | Yes | Academic institutional email | `"adam.samir@sadat.edu.eg"` |
| `gpa` | Number | Yes | Cumulative Grade Point Average | Range: `0.00 - 4.00`, 2 decimal places |
| `gradeLabel` | String | Yes | Academic standing class | `"Excellent"`, `"Very Good"`, `"Good"`, `"Pass"` |
| `cohortYear` | Number | Yes | Expected graduation year | `2026` |
| `createdAt` | Date | Yes | Record creation timestamp | ISO 8601 |
| `updatedAt` | Date | Yes | Last modification timestamp | ISO 8601 |

#### 1.2 `Course`
| Field | Type | Required | Description | Constraints |
|:---|:---|:---|:---|:---|
| `courseId` | String | Yes | Official course code | `"C001"` - `"C049"` |
| `courseName` | String | Yes | Title of the academic course | `"Machine&Deep Learning"` |
| `year` | Number | Yes | Academic year taught | `1`, `2`, `3`, or `4` |
| `creditHours` | Number | Yes | Credit hours allocated | `2` or `3` |

#### 1.3 `CourseSkillMapping`
| Field | Type | Required | Description | Constraints |
|:---|:---|:---|:---|:---|
| `courseId` | String | Yes | Reference to `Course.courseId` | Valid foreign reference |
| `skill` | String | Yes | Canonical skill name | Must match canonical skill vocab |
| `relevance` | Number | Yes | Faculty relevance weight | Range: `0.1 - 1.0` |
| `evidenceWeight`| Number | Yes | Precomputed $\text{relevance} \times \text{creditHours}$ | Range: `0.2 - 3.0` |
| `confidence` | String | No | Mapping confidence flag | `"H"`, `"M"`, `"L"` |

#### 1.4 `StudentGrade`
| Field | Type | Required | Description | Constraints |
|:---|:---|:---|:---|:---|
| `studentId` | String | Yes | Reference to `Student.studentId` | Indexed foreign reference |
| `courseId` | String | Yes | Reference to `Course.courseId` | Indexed foreign reference |
| `mark` | Number | Yes | Official grade score out of 100 | Range: `0 - 100` |
| `creditHours` | Number | Yes | Credit hours for weighting | `2` or `3` |

---

### 2. Evidence Domain Entities

#### 2.1 `StudentEvidence`
| Field | Type | Required | Description | Constraints |
|:---|:---|:---|:---|:---|
| `id` | String | Yes | Unique evidence entry ID | UUID v4 |
| `studentId` | String | Yes | Reference to `Student.studentId` | Indexed foreign reference |
| `source` | String | Yes | Categorical source type | `"transcript"`, `"certificate_verified"`, `"experience_verified"`, `"online_test"`, `"certificate_claimed"`, `"experience_claimed"`, `"self_rating"` |
| `skill` | String | Yes | Target canonical skill name | Must match canonical vocab |
| `level` | Number | Yes | Competency level | Range: `0.0 - 1.0` |
| `months` | Number | No | Duration of work experience | Integer $\ge 0$ |
| `certificateName`| String | No | Official certificate title | Recognized in cert catalog |
| `testScore` | Number | No | Raw score if online test | Range: `0 - 100` |
| `verificationDoc`| String | No | File storage ID of uploaded proof | Valid storage reference |
| `isVerified` | Boolean | Yes | Administrative verification status | `true` or `false` |

---

### 3. Jobs Domain Entities

#### 3.1 `JobPosting`
| Field | Type | Required | Description | Constraints |
|:---|:---|:---|:---|:---|
| `jobId` | String | Yes | Unique job identifier | e.g. `"4100101"` |
| `title` | String | Yes | Job posting title | `"Junior Machine Learning Engineer"` |
| `company` | String | Yes | Hiring employer organization | `"ITWorx"` |
| `specialization`| String | Yes | Classified technical track | `"AI / ML Engineer"`, `"Cybersecurity"`, etc. |
| `workMode` | String | Yes | Workplace arrangement | `"Remote"`, `"Hybrid"`, `"On-site"`, `"Not specified"` |
| `level` | String | Yes | Seniority classification | `"Intern"`, `"Junior"`, `"Mid"`, `"Senior"` |
| `yearsExpMin` | Number | No | Minimum years of experience | Nullable, Integer $\ge 0$ |
| `yearsExpMax` | Number | No | Maximum years of experience | Nullable, Integer $\ge 0$ |
| `technicalRequirements`| Array<String> | Yes | Required skills list | Extracted canonical skills |
| `url` | String | Yes | LinkedIn posting URL | Valid HTTP/HTTPS URL |
| `source` | String | Yes | Ingestion source origin | Default: `"linkedin_egypt_scraper"` |
| `isLive` | Boolean | Yes | Active posting indicator | Default: `true` |

---

### 4. Matching & Recommendation Domain Entities

#### 4.1 `JobMatch`
| Field | Type | Required | Description | Constraints |
|:---|:---|:---|:---|:---|
| `studentId` | String | Yes | Reference to `Student.studentId` | Indexed foreign reference |
| `jobId` | String | Yes | Reference to `JobPosting.jobId` | Indexed foreign reference |
| `rank` | Number | Yes | Ranking in Top 10 | `1` to `10` |
| `fitPct` | Number | Yes | Engine compatibility score | Range: `0.0 - 100.0` (1 decimal place) |
| `isEligible` | Boolean | Yes | Experience eligibility filter flag | `true` or `false` |
| `strongSkills` | Array<String>| Yes | Skills where $S_s \ge 0.50$ | String array |
| `developingSkills`| Array<String>| Yes | Skills where $0.0 < S_s < 0.50$| String array |
| `missingSkills`| Array<String>| Yes | Skills where $S_s = 0.0$ | String array |

#### 4.2 `RoadmapItem`
| Field | Type | Required | Description | Constraints |
|:---|:---|:---|:---|:---|
| `id` | String | Yes | Unique recommendation ID | UUID v4 |
| `studentId` | String | Yes | Reference to student | Indexed foreign reference |
| `jobId` | String | No | Target job context | Nullable reference |
| `skill` | String | Yes | Target skill name | Canonical skill name |
| `currentLevelPct`| Number | Yes | Pre-improvement level | Range: `0.0 - 100.0` |
| `cause` | String | Yes | Diagnosed root cause | `"Weak grades in related courses"`, `"Not covered by the curriculum"`, `"Only partly covered"` |
| `actionKind` | String | Yes | Recommendation kind | `"revisit"`, `"certificate"`, `"test"`, `"course"`, `"practice"`, `"project"` |
| `actionName` | String | Yes | Action title | e.g. `"Revisit C015 Computer Operating Systems"` |
| `actionProvider`| String | Yes | Offering entity | `"Sadat Academy"`, `"AWS"`, `"Microsoft"`, `"HackerRank"` |
| `actionCost` | String | Yes | Cost indicator | `"free"`, `"paid exam"`, `"unknown"` |
| `estFitGainPts`| Number | No | Calculated fit improvement | Nullable float, e.g. `11.1` |
| `status` | String | Yes | Student progress tracking | `"suggested"`, `"planned"`, `"in_progress"`, `"completed"` |
