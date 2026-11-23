# SADAT – Student Career Intelligence & Skills Growth Portal
## 11. Authentication & Identity Specification

### 1. External IdP Integration (Graduates Affairs OIDC)
The SADAT Portal delegates user identity verification entirely to the University's Graduates Affairs OAuth 2.0 / OpenID Connect provider.

The platform never requests, collects, or stores student passwords.

---

### 2. OIDC Authorization Code Flow with PKCE

```text
[Student Browser]       [SADAT Node API]       [Graduates Affairs IdP]
       |                        |                         |
       | 1. Click "Login"       |                         |
       |----------------------->|                         |
       |                        | 2. Generate PKCE &      |
       |                        |    redirect to IdP      |
       | 3. 302 Redirect to IdP |                         |
       |<-----------------------|                         |
       |                                                  |
       | 4. User Authenticates with University Account    |
       |------------------------------------------------->|
       |                                                  |
       | 5. 302 Redirect to callback with code & state   |
       |<-------------------------------------------------|
       |                                                  |
       | 6. Forward code to /api/v1/auth/callback         |
       |----------------------->|                         |
       |                        | 7. POST code + verifier |
       |                        |------------------------>|
       |                        | 8. Return ID + Access   |
       |                        |<------------------------|
       |                        | 9. Retrieve user claims |
       |                        |    Map to StudentProfile|
       |                        |    Issue Session Cookie |
       | 10. 302 to Dashboard   |                         |
       |<-----------------------|                         |
```

---

### 3. Session Security
- **Cookie Name**: `sadat_session`
- **Options**:
  - `httpOnly: true` (Prevents JavaScript read access via `document.cookie`).
  - `secure: true` in production (Transmitted only over HTTPS).
  - `sameSite: 'strict'` (Guards against CSRF attacks).
  - `maxAge: 86400000` (24 hours).
- The session payload contains:
  - `sessionId`: Cryptographically random UUID v4.
  - `studentId`: The verified student identifier (`SAD2026xxxx`).
  - `role`: `'student'` or `'admin'`.
  - `issuedAt`: Unix timestamp.

---

### 4. Configuration Placeholders & Mocking for Offline Development
The system supports both live OIDC and a configured offline mock identity provider for local development without external internet dependencies.

Environment configuration variables:
```bash
OIDC_ISSUER=https://auth.sadat.edu.eg/oauth2
OIDC_CLIENT_ID=sadat_career_portal_client
OIDC_CLIENT_SECRET=sadat_secret_placeholder
OIDC_REDIRECT_URI=http://localhost:5000/api/v1/auth/callback
OIDC_AUTHORIZATION_URL=https://auth.sadat.edu.eg/oauth2/authorize
OIDC_TOKEN_URL=https://auth.sadat.edu.eg/oauth2/token
OIDC_USERINFO_URL=https://auth.sadat.edu.eg/oauth2/userinfo
OIDC_SCOPES=openid profile email academic_id

# Local Simulation Mode (bypasses remote IdP during testing)
AUTH_MOCK_ENABLED=true
AUTH_DEFAULT_STUDENT_ID=SAD20260001
```
