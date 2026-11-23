# SADAT – Student Career Intelligence & Skills Growth Portal
## 13. Testing and Validation Specification

### 1. Test Levels & Strategy

```text
+-------------------------------------------------------+
|                END-TO-END WORKFLOW TESTS              |
|        (Playwright: Login -> Questionnaire -> Match)  |
+-------------------------------------------------------+
                           |
+-------------------------------------------------------+
|              DIFFERENTIAL REGRESSION TESTS            |
|       (Experimental Python Output == New API Output)  |
+-------------------------------------------------------+
                           |
+-------------------------------------------------------+
|                INTEGRATION CONTRACT TESTS             |
|          (Node API -> Internal Python Service)        |
+-------------------------------------------------------+
                           |
+-------------------------------------------------------+
|                   UNIT TESTS & SCHEMAS                |
|      (Zod validators, Evidence formulas, i18n keys)   |
+-------------------------------------------------------+
```

---

### 2. Differential Testing Requirements
For identical inputs (Student ID `SAD20260001` with baseline transcript and simulated questionnaire), the modernized platform must yield exact numerical equivalence with `backend/test_platform.py`:
1. **Top Roles Match %**:
   - Cybersecurity: $55.0\%$
   - Network Engineer / Tester: $50.6\%$
   - Data Analyst / BI: $50.5\%$
2. **Top 3 Job Fit %**:
   - #1 SOC Analyst (L1) at Si-Ware Systems: $63.8\%$
   - #2 Junior Cybersecurity Analyst at Valu: $63.8\%$
   - #3 Junior Cybersecurity Analyst at Bosta: $63.8\%$
3. **Weak Grade Gap Diagnosis**:
   - Skill: Linux $\rightarrow$ Cause: *"Weak grades in related courses"* $\rightarrow$ Action: *"Revisit Computer Operating Systems (your mark 62)"* $\rightarrow$ Est Fit Gain: $+11.1$ pts.
4. **Questionnaire Updated Fit**:
   - 14 mo experience, Python 95, SQL 90, ML 88, Docker 80, AWS ML Cert.
   - Top Job #1: Junior Machine Learning Engineer at ITWorx: $76.6\%$ fit.

Any deviation $> 0.1\%$ is treated as a regression bug and blocks deployment.
