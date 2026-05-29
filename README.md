# SED Energy — Autonomous AI Marketing System
**South Africa's Tier 1 Solar Distributor | Fully Autonomous AI Marketing Operations**

---

## What This Is

A complete, production-ready AI marketing operating system purpose-built for **SED Energy** (Solar Energy Distributor Pty Ltd). The system operates as a full AI marketing department — generating content, managing social media across all platforms, monitoring stock arrivals, educating followers, and publishing autonomously with minimal human intervention.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    NEXT.JS DASHBOARD                        │
│  Overview · Content Queue · Social Calendar · WhatsApp      │
│  Analytics · Knowledge Base · Media Studio · Stock Monitor  │
└───────────────────────┬─────────────────────────────────────┘
                        │ REST API
┌───────────────────────▼─────────────────────────────────────┐
│                  FASTAPI BACKEND                             │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            LANGGRAPH MULTI-AGENT SYSTEM              │   │
│  │                                                      │   │
│  │  Strategy → Content → Design → Brand Check          │   │
│  │  Stock → Content → Design → Brand Check             │   │
│  │  News → Content → Brand Check                       │   │
│  │  WhatsApp → Brand Check                             │   │
│  │  Analytics → Insights                               │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  Services: VectorStore · SocialPublisher · WhatsApp         │
│            ImageGen · VideoGen · NASIngestion · Scheduler   │
└──────────┬─────────────────┬───────────────────────────────┘
           │                 │
    ┌──────▼──────┐  ┌───────▼──────────────────────┐
    │  POSTGRESQL │  │        PINECONE               │
    │  Content DB │  │  RAG Knowledge Vectors        │
    └─────────────┘  └──────────────────────────────┘
           │
    ┌──────▼──────┐
    │    REDIS    │
    │ Cache/Queue │
    └─────────────┘
           │
    ┌──────▼──────────────────────────────────────┐
    │              CELERY WORKERS                  │
    │  Content Gen · Image Gen · Video Gen         │
    │  Publishing · Ingestion · Analytics          │
    └──────────────────────────────────────────────┘
```

---

## The 10 AI Agents

| Agent | Role |
|-------|------|
| **Strategy Agent** | Plans content calendars, identifies opportunities, directs other agents |
| **Content Agent** | Generates platform-specific copy using Claude API + RAG context |
| **Design Agent** | Creates image generation prompts for Flux/DALL-E/Ideogram |
| **Video Agent** | Builds video prompts + voiceover scripts for Runway/Pika/Kling |
| **WhatsApp Agent** | Tailored messaging per group type (installer, VIP, EPC, internal) |
| **News Agent** | Monitors SA solar industry news, triggers content on events |
| **Analytics Agent** | Tracks performance, identifies top content, generates weekly reports |
| **Stock Agent** | Detects inventory changes, triggers stock arrival content |
| **Brand Compliance Agent** | Validates all content — catches hallucinations, off-brand messaging |
| **Engagement Agent** | Generates reply suggestions for comments and DMs |

---

## Tech Stack

**Backend**
- Python 3.12 + FastAPI (async)
- LangGraph for multi-agent orchestration
- Anthropic Claude API (primary AI)
- OpenAI API (embeddings + DALL-E 3)
- PostgreSQL 16 + SQLAlchemy (async)
- Redis 7 + Celery 5 (task queue)
- APScheduler (cron jobs)
- Pinecone (vector database for RAG)

**Frontend**
- Next.js 14 (App Router)
- TypeScript + Tailwind CSS
- TanStack Query (data fetching)
- Recharts (analytics)
- React Hot Toast + Radix UI

**AI/Generation**
- Flux SDXL via Replicate (images)
- DALL-E 3 via OpenAI (images)
- Runway ML Gen-3 (video)
- Claude Opus/Sonnet/Haiku (content)

**Infrastructure**
- Docker + Docker Compose
- Nginx reverse proxy + SSL
- AWS S3 / MinIO (asset storage)
- Celery Flower (task monitoring)

---

## Quick Start

### Prerequisites
- Docker + Docker Compose
- Node.js 20+ (for frontend dev)
- Python 3.12+ (for backend dev)

### 1. Clone and Configure

```bash
git clone https://github.com/sed-energy/ai-marketing-system
cd sed-ai-marketing
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start All Services

```bash
make up
# Dashboard: http://localhost:3000
# API Docs:  http://localhost:8000/api/docs
# Flower:    http://localhost:5555
```

### 3. Run Database Migrations

```bash
make migrate
```

### 4. Upload Initial Knowledge Base

Navigate to the Knowledge Base page in the dashboard and upload:
- Company info deck (uploaded PDF)
- Product catalogues
- Price lists
- Brand guidelines
- Technical datasheets

### 5. Configure WhatsApp Groups

Go to WhatsApp Manager and add your group configurations with group type, audience, and posting rules.

---

## Key Workflows

### Stock Arrival → Auto Content (Fully Automated)
```
Sage ERP stock change detected
    → Stock Agent analyzes opportunity
    → Strategy Agent selects platforms
    → Content Agent generates per-platform copy
    → Design Agent creates image prompts
    → Brand Compliance Agent validates
    → Images generated via Flux
    → Posts queued for approval or auto-published
    → WhatsApp messages generated per group
```

### Content Generation
```
User selects: platform + content_type + topic + audience
    → RAG search retrieves relevant knowledge
    → Strategy Agent enriches context
    → Content Agent generates with Claude
    → Design Agent creates image prompt
    → Brand Compliance validates
    → Confidence ≥ 85% → auto-approve
    → Confidence < 85% → human review queue
```

### Daily Autonomous Operations (Cron)
```
07:00 SAST  — News monitoring + analytics fetch
07:30 SAST  — Check stock updates (Sage poll)
08:00 SAST  — Publish scheduled posts
Every 5min  — Process publishing queue
Sunday 18:00 — Generate weekly content calendar
Monday 07:00 — Weekly analytics report
```

---

## API Reference

Full Swagger docs available at `http://localhost:8000/api/docs` (development mode).

Key endpoints:
- `POST /api/v1/content/generate` — Trigger AI content generation
- `PATCH /api/v1/content/{id}/approve` — Approve/reject content
- `POST /api/v1/social/publish-now` — Publish immediately
- `POST /api/v1/knowledge/upload` — Upload document to knowledge base
- `POST /api/v1/stock/{id}/quantity` — Update stock level
- `POST /api/v1/whatsapp/generate-message` — Generate group message
- `GET /api/v1/analytics/overview` — Dashboard analytics

---

## Estimated Monthly Infrastructure Costs (USD)

| Service | Tier | Est. Cost/month |
|---------|------|----------------|
| Anthropic Claude API | ~500K tokens/day | $150-300 |
| OpenAI (embeddings + DALL-E) | Standard | $50-100 |
| Pinecone | Serverless | $0-70 |
| Replicate (Flux images) | ~500 images | $50-100 |
| Runway ML (video) | ~20 videos | $50-150 |
| AWS / VPS hosting | t3.medium | $50-100 |
| AWS S3 storage | ~50GB | $5-10 |
| **Total estimate** | | **$355-830/month** |

Costs scale with usage. Starting costs for low-volume (~20 posts/week) are closer to $200/month.

---

## Security

- JWT authentication with role-based access (super_admin, admin, marketing_manager, content_editor, viewer)
- All API keys stored in environment variables, never in code
- Brand compliance agent prevents hallucinated or inaccurate content
- Human approval workflow for high-risk content (pricing, specs)
- Audit logging for all published content
- Rate limiting on all API endpoints via Nginx
- Non-root Docker containers

---

## Folder Structure

```
sed-ai-marketing/
├── backend/
│   ├── app/
│   │   ├── agents/          ← 10 AI agents + orchestrator
│   │   ├── api/routes/      ← FastAPI route handlers
│   │   ├── core/            ← Brand config, prompts, security
│   │   ├── models/          ← SQLAlchemy database models
│   │   ├── services/        ← Vector store, publishers, ingestion
│   │   └── workers/         ← Celery tasks and beat scheduler
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── app/(dashboard)/ ← All dashboard pages
│       ├── components/      ← Reusable UI components
│       └── lib/             ← API client, types, utils
├── nginx/                   ← Reverse proxy config
├── docs/                    ← Architecture and setup docs
├── docker-compose.yml
├── .env.example
└── Makefile
```

---

## Support

- Email: info@sed.energy
- Phone: 010 006 8246
- Website: sed.energy
