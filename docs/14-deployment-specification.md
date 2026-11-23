# SADAT – Student Career Intelligence & Skills Growth Portal
## 14. Deployment Specification

### 1. Multi-Container Docker Architecture
The platform is deployed using Docker Compose with four isolated containers:
1. `sadat-web`: Nginx reverse proxy serving optimized React static assets and proxying `/api` requests.
2. `sadat-api`: Node.js 20 LTS runtime executing the Express REST API.
3. `sadat-intelligence`: Python 3.12 slim runtime executing the private FastAPI intelligence service.
4. `sadat-mongo`: MongoDB 7.0 database with persistent volume storage.
5. `sadat-redis`: Redis 7 Alpine cache and BullMQ job broker.

```yaml
version: '3.8'

services:
  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - api
    restart: always

  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    environment:
      - NODE_ENV=production
      - PORT=5000
      - MONGO_URI=mongodb://mongo:27017/sadat_career_db
      - REDIS_URL=redis://redis:6379
      - PYTHON_SERVICE_URL=http://intelligence:8000
    depends_on:
      - mongo
      - redis
      - intelligence
    restart: always

  intelligence:
    build:
      context: ./services/intelligence
      dockerfile: Dockerfile
    environment:
      - PYTHONUNBUFFERED=1
      - PORT=8000
    restart: always

  mongo:
    image: mongo:7.0
    volumes:
      - mongo_data:/data/db
    restart: always

  redis:
    image: redis:7-alpine
    restart: always

volumes:
  mongo_data:
```

---

### 2. Standalone Environment Variables (`.env.example`)
```bash
# Server & Ports
PORT=5000
WEB_PORT=3000
PYTHON_SERVICE_PORT=8000

# Security Secrets
SESSION_SECRET=sadat_session_super_secret_key_change_in_production_2026
INTERNAL_API_SECRET=sadat_internal_python_secret_2026

# Database & Cache
MONGO_URI=mongodb://127.0.0.1:27017/sadat_career_db
REDIS_URL=redis://127.0.0.1:6379

# Identity Provider (OIDC)
OIDC_ISSUER=https://auth.sadat.edu.eg/oauth2
OIDC_CLIENT_ID=sadat_portal_client
OIDC_CLIENT_SECRET=sadat_portal_secret
OIDC_REDIRECT_URI=http://localhost:5000/api/v1/auth/callback
AUTH_MOCK_ENABLED=true
AUTH_DEFAULT_STUDENT_ID=SAD20260001
```
