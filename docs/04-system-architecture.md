# SADAT – Student Career Intelligence & Skills Growth Portal
## 04. System Architecture Specification

### 1. High-Level Topology
The modernized SADAT Portal is designed as a standalone, decoupled, distributed system partitioned into four distinct tiers:
1. **Client Tier**: Single-Page Application (React 18 + TypeScript + TailwindCSS + Vite).
2. **Application Tier**: Node.js / Express TypeScript API gateway handling authentication, request validation, business workflows, and file storage.
3. **Intelligence Tier**: Private Python 3 service wrapping the verified matching engine, recommendation catalog, and LinkedIn scraper.
4. **Data & Queue Tier**: MongoDB database for persistence and Redis / BullMQ for asynchronous job scheduling.

```text
                        EXTERNAL IDENTITY
                        [Graduates Affairs]
                                |
                         OAuth 2.0 / OIDC
                                |
                                v
+---------------------------------------------------------------+
|                      CLIENT APPLICATION                       |
|               React 18 + TypeScript + TailwindCSS             |
|                                                               |
|  [Student Dashboard]       [Profile & Transcript]             |
|  [Skills Competency]       [Top 10 Job Matches]               |
|  [Improvement Roadmap]     [14 Missing Skills & Tests]        |
|  [Market Intelligence]     [Bilingual Switcher (RTL / LTR)]   |
+-------------------------------+-------------------------------+
                                | HTTPS (REST + Cookies)
                                v
+---------------------------------------------------------------+
|                   NODE.JS / EXPRESS API TIER                  |
|                   (TypeScript, Port 5000)                     |
|                                                               |
|  - OIDC Authentication / Session Management                   |
|  - Role-Based Access Control (Student vs Admin)               |
|  - Request Validation via Zod Schemas                         |
|  - File Upload Handler (Multer + Storage Manager)             |
|  - REST Controllers & Data Mappers                            |
|  - Background Queue Dispatcher (BullMQ)                       |
+---------------+-------------------------------+---------------+
                |                               |
                v                               v
    +-----------------------+       +-----------------------+
    |   MongoDB Database    |       |   Redis & BullMQ      |
    |   (Port 27017)        |       |   (Port 6379)         |
    |                       |       |                       |
    | - Students & Grades   |       | - Scraper Jobs        |
    | - Jobs & Matches      |       | - Async Evaluations   |
    | - Market Analytics    |       | - Ingestion Tasks     |
    +-----------+-----------+       +-----------+-----------+
                |                               |
                +---------------+---------------+
                                |
                                v
+---------------------------------------------------------------+
|                  PRIVATE PYTHON INTELLIGENCE                  |
|                    (Internal, Port 8000)                      |
|                                                               |
|  - Matching Engine (Evidence Aggregation & Top 10 Scoring)    |
|  - Recommendation Logic (Gap Cause Diagnosis & Fit Gain)     |
|  - LinkedIn Egyptian Jobs Harvester                           |
|  - Exact Baseline Logic & Formulas Preserved                  |
+---------------------------------------------------------------+
```

---

### 2. Tier Details & Responsibilities

#### 2.1 Web Client Tier
- Built with React 18, TypeScript, and Vite for optimal build performance and developer experience.
- UI styling powered by TailwindCSS with a custom theme honoring the **Minimalistic Retro Grid + Calm Sea Palette**.
- Data fetching, optimistic caching, and server state synchronization managed by TanStack Query (React Query).
- Client-side application state (active preview overrides, locale, UI toggles) managed with Zustand.
- Bilingual localization managed via `react-i18next`, dynamically toggling document direction (`dir="rtl"` vs `dir="ltr"`).

#### 2.2 Application Backend Tier (Node.js / Express)
- Handles all public HTTP traffic, CORS, rate limiting, and security headers (Helmet).
- Serves as the sole entry point for the client; the client never communicates directly with the Python service or database.
- Implements session management with cryptographically signed cookies.
- Orchestrates asynchronous background tasks (scrapes, heavy batch recalculations) via Redis and BullMQ.
- Mediates synchronous dynamic evaluation requests to the Python intelligence layer.

#### 2.3 Intelligence Layer (Python 3)
- Encapsulates `matching_engine.py`, `recommendation_catalog.py`, and `linkedin_jobs_scraper.py`.
- Exposes high-performance internal REST endpoints over localhost/internal Docker network.
- Completely isolated from public access; only authenticated internal requests from the Node.js backend are serviced.
- Guarantees 100% numerical and algorithmic fidelity with zero deviations from verified formulas.

#### 2.4 Data Tier
- **MongoDB**: Primary document store housing students, course mappings, transcript marks, jobs, student recommendations, and market analytics.
- **Redis**: High-speed in-memory store for session caching, rate-limiting tokens, and BullMQ task queues.
