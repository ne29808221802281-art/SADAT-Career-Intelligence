# SADAT – Student Career Intelligence & Skills Growth Portal
## 03. Non-Functional Requirements Specification

### 1. Performance and Latency
- **NFR-PERF-001**: API response time for precalculated student matching results (`GET /api/v1/matching/me`) shall be under 200ms at the 95th percentile under normal load.
- **NFR-PERF-002**: On-the-fly dynamic student reevaluation (including questionnaire updates and slider preview recalculations) shall return within 500ms.
- **NFR-PERF-003**: Frontend client bundle shall load with a First Contentful Paint (FCP) of under 1.2s on standard broadband connections.
- **NFR-PERF-004**: Large analytical datasets (e.g. 77 market skills, 169 jobs) shall be cached in memory or Redis to eliminate redundant disk/database hits during student browsing sessions.

### 2. Availability and Reliability
- **NFR-REL-001**: The portal shall operate independently with an availability target of 99.5% uptime.
- **NFR-REL-002**: External identity provider downtime (Graduates Affairs OIDC) must not crash the application server; active authenticated sessions shall continue functioning normally until token expiration.
- **NFR-REL-003**: Background scraper job failures (e.g., LinkedIn HTTP 429/999 rate limits) shall fail silently in the queue with exponential backoff and never degrade student-facing portal availability.

### 3. Scalability
- **NFR-SCAL-001**: System architecture shall support horizontal scaling of the stateless Node.js application server behind a reverse proxy (Nginx).
- **NFR-SCAL-002**: The MongoDB database shall comfortably support the entire 1,000-student cohort, transcript marks (49,000 records), and thousands of job postings with indexed queries.

### 4. Security and Data Protection
- **NFR-SEC-001**: Sessions shall be secured with `HttpOnly`, `SameSite=Strict`, and `Secure` cookies to prevent XSS session theft.
- **NFR-SEC-002**: All cross-student data access is strictly forbidden. The system must verify student ownership on every data request using session claims rather than client-supplied URL IDs.
- **NFR-SEC-003**: All incoming payloads shall be strictly validated using Zod schemas with sanitized text inputs to prevent injection attacks.
- **NFR-SEC-004**: File uploads (CVs, certificate proof documents) shall be restricted to PDF, PNG, and JPEG formats, maximum 5MB, stored with randomized server filenames in a private storage directory outside web root.
- **NFR-SEC-005**: The internal Python intelligence execution layer must run on a private internal network interface (e.g. `127.0.0.1` or internal Docker network) and never be exposed publicly.

### 5. Maintainability and Modularity
- **NFR-MAINT-001**: Clean separation of concerns following a feature-based monorepo structure.
- **NFR-MAINT-002**: TypeScript strict mode enabled across all frontend and backend codebases.
- **NFR-MAINT-003**: Python intelligence code adheres to the canonical baseline scripts, maintaining exact formula parity.

### 6. Usability, Accessibility and Internationalization
- **NFR-UX-001**: Full support for WCAG 2.1 AA accessibility guidelines, including proper contrast ratios on the calm sea palette and keyboard navigable interactive cards.
- **NFR-UX-002**: Bi-directional support with native Right-to-Left (RTL) mirroring when Arabic locale is selected, including mirrored layouts, margin/padding adjustments, and typography.
- **NFR-UX-003**: Respects user's `prefers-reduced-motion` settings for all transition and animation effects.
