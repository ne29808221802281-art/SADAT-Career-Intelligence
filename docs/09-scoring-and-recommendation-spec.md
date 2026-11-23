# SADAT – Student Career Intelligence & Skills Growth Portal
## 09. Scoring and Recommendation Specification

This document provides complete documentation of the authoritative scoring, matching, eligibility, and recommendation logic to guarantee 100% adherence to the baseline algorithms.

---

### 1. Skill Proficiency Formulation

#### 1.1 Transcript Contribution
For student $i$ and skill $s$:
- Let $C(s)$ be the set of courses mapped to skill $s$ in `course_skill_map.csv`.
- For each course $c \in C(s)$, let:
  - $R_{c,s} \in [0.1, 1.0]$: Faculty relevance score.
  - $H_c \in \{2, 3\}$: Course credit hours.
  - $M_{i,c} \in [0, 100]$: Student's mark in course $c$.
- Weighted Credit Hours: $w_{c,s} = R_{c,s} \times H_c$.
- Weighted Mark: $wm_{i,c,s} = w_{c,s} \times M_{i,c}$.
- Raw Transcript Proficiency:
  $$P_{i,s} = \frac{\sum_{c \in C(s)} wm_{i,c,s}}{\sum_{c \in C(s)} w_{c,s}}$$
- Curriculum Evidence Sum:
  $$E_{i,s} = \sum_{c \in C(s)} w_{c,s}$$
- Transcript Evidence Multiplier:
  $$M_{\text{transcript}} = 1.0 \times \min\left(1.0, \frac{E_{i,s}}{\text{FULL\_EVIDENCE}}\right) \quad (\text{where } \text{FULL\_EVIDENCE} = 3.0)$$
- Transcript Numerator Contribution:
  $$\text{Num}_{\text{transcript}} = M_{\text{transcript}} \times \left(\frac{P_{i,s}}{100.0}\right)$$
- Transcript Denominator Contribution:
  $$\text{Den}_{\text{transcript}} = M_{\text{transcript}}$$

#### 1.2 External Evidence Contributions
For external sources $k \in \{\text{cert\_ver}, \text{exp\_ver}, \text{test}, \text{cert\_clm}, \text{exp\_clm}, \text{self}\}$:
- **Verified Certificate**: Weight $W = 0.9$, Level $L = 1.0$.
- **Verified Experience**: Weight $W = 0.8$, Level $L = \min(1.0, \text{Months}/12)$.
- **Online Test**: Weight $W = 0.7$, Level $L = \text{Score}/100.0$.
- **Claimed Certificate**: Weight $W = 0.5$, Level $L = 1.0$.
- **Claimed Experience**: Weight $W = 0.5$, Level $L = \min(1.0, \text{Months}/12)$.
- **Self-Rating**: Weight $W = 0.3$, Level $L = \text{Rating}/100.0$.

For each active source $k$:
$$\text{Num}_k = W_k \times L_k, \quad \text{Den}_k = W_k$$

#### 1.3 Total Aggregated Skill Level
$$S_{i,s} = \frac{\text{Num}_{\text{transcript}} + \sum_k \text{Num}_k}{\max\left(\text{Den}_{\text{transcript}} + \sum_k \text{Den}_k, 1.0\right)}$$

---

### 2. Job Fit and Role Matching

#### 2.1 Job Compatibility Score $\text{Fit}(j)$
Given candidate job $j$ with required skills $\text{Skills}(j)$:
$$\text{Fit}(j) = \frac{\sum_{s \in \text{Skills}(j)} S_{i,s}}{\max(|\text{Skills}(j)|, 4)}$$

#### 2.2 Role Compatibility Score $\text{Match}(r)$
For technical track role $r$ with empirical skill frequency weights $w_{r,s} \ge 0.10$ from `role_summary.csv`:
$$\text{Match}(r) = \frac{\sum_{s} w_{r,s} \cdot S_{i,s}}{\sum_s w_{r,s}}$$

#### 2.3 Experience Eligibility Threshold
Student experience in years:
$$\text{ExpYears} = \frac{\max(\text{Months}_{\text{experience}})}{12.0}$$
Allowed maximum required years for the student:
$$\text{AllowedExp} = 2.0 + 1.0 \times \lfloor\text{ExpYears}\rfloor$$
A job is **Eligible** if:
$$\text{YearsRequired}(j) \text{ is NULL or } \text{YearsRequired}(j) \le \text{AllowedExp}$$
Ineligible jobs are penalized during sorting so they never displace an eligible job in the Top 10.

---

### 3. Gap Root-Cause Diagnosis Rules

| Condition | Diagnosed Cause | Prescribed Action Strategy |
|:---|:---|:---|
| $S_{i,s} \ge 0.50$ | **Covered** | No gap action needed; skill is Strong. |
| $E_{i,s} < 1.5$ and external evidence present | **Not proven strongly yet** | Provide online test or verified certificate to demonstrate mastery. |
| $E_{i,s} < 1.5$ and no external evidence | **Not covered by the curriculum** | Free online assessment first, followed by micro-courses or professional certifications. |
| $E_{i,s} \ge 1.5$ and $P_{i,s} < 65$ | **Weak grades in related courses** | Revisit the specific university course with the lowest mark. |
| $E_{i,s} \ge 1.5$ and $P_{i,s} \ge 65$ | **Only partly covered** | Build a hands-on GitHub portfolio project or achieve an advanced credential. |

---

### 4. Estimated Fit Gain Formulation

For a missing or developing skill $s \in \text{Skills}(j)$ where an actionable credential is recommended:
- Let $N_{\text{eff}} = \max(|\text{Skills}(j)|, 4)$.
- If action is a **Certificate**: $W_{\text{assumed}} = 0.9$, $L_{\text{assumed}} = 1.0$.
- If action is an **Online Test**: $W_{\text{assumed}} = 0.7$, $L_{\text{assumed}} = 0.8$.
- Calculate new skill level:
  $$S_{i,s, \text{new}} = \frac{\text{Num}_{i,s} + W_{\text{assumed}} \cdot L_{\text{assumed}}}{\max(\text{Den}_{i,s} + W_{\text{assumed}}, 1.0)}$$
- Estimated Fit Gain in percentage points:
  $$\Delta \text{Fit} = \text{round}\left(100.0 \times \frac{S_{i,s, \text{new}} - S_{i,s}}{N_{\text{eff}}}, 1\right)$$
- If the calculated gain is negative or zero, it is omitted.
