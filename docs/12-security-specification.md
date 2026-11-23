# SADAT – Student Career Intelligence & Skills Growth Portal
## 12. Security Specification

### 1. Threat Model & Mitigation Matrix

| Threat Category | Potential Attack Vector | Applied Mitigation Strategy |
|:---|:---|:---|
| **Identity & Access** | Horizontal privilege escalation (student A requesting student B's transcript) | Student ownership verification on every endpoint using server-side session claims. URL parameters requesting cross-student data are ignored or forbidden (`403 Forbidden`). |
| **Session Hijacking** | XSS stealing session cookies | `HttpOnly`, `SameSite=Strict`, and `Secure` cookie flags. Strong Content Security Policy (CSP). |
| **Input Tampering** | Injection of negative numbers, arbitrary weights, or non-existent skills | Strict Zod validation schemas rejecting unknown attributes and out-of-range numerical values. |
| **Malicious File Uploads** | Uploading executable scripts disguised as certificate PDFs | Multer file filter validating MIME types (`application/pdf`, `image/jpeg`, `image/png`), magic byte inspection via `file-type`, sanitized UUID filenames, storage outside web root. |
| **Denial of Service** | Flooding calculation endpoints with heavy requests | `express-rate-limit` (100 requests per 15 minutes per IP; 20 requests per minute on calculation endpoints). |
| **Intelligence Exposure** | Direct public access to internal Python engine | Python service binds strictly to `127.0.0.1:8000` or an internal Docker network with firewall rules preventing external ingress. |
| **Graduates Affairs Compromise** | Compromised portal affecting university database | Zero direct connection to Graduates Affairs database. One-way OIDC assertion only. |

---

### 2. Audit Logging
Every security-sensitive operation is logged with structured JSON telemetry (Pino):
- Successful and failed authentication attempts.
- Document uploads and verification state changes.
- Questionnaire submissions and matching recalculations.
- Administrative overrides.

Log entry schema:
```json
{
  "timestamp": "2026-11-23T15:30:00.000Z",
  "level": "info",
  "event": "MATCH_RECALCULATED",
  "studentId": "SAD20260001",
  "ipAddress": "192.168.1.50",
  "userAgent": "Mozilla/5.0 ...",
  "executionDurationMs": 142
}
```
