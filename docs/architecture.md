# SED Energy AI Marketing System — Architecture Guide

## Overview

The system is a fully autonomous AI marketing operating system built on a microservices architecture. It combines multiple AI models, a multi-agent orchestration layer, and social media APIs to run SED Energy's marketing operations with minimal human intervention.

## Request Flow

```
User Action / Cron Trigger
        │
        ▼
FastAPI Backend (async)
        │
        ├─── Validate request + JWT auth
        ├─── Query Pinecone RAG for context
        │
        ▼
LangGraph Orchestrator
        │
        ├─── Strategy Agent    (Claude Opus)
        ├─── Content Agent     (Claude Sonnet)
        ├─── Design Agent      (Claude Haiku → Flux/DALL-E)
        ├─── Video Agent       (Claude Haiku → Runway)
        ├─── WhatsApp Agent    (Claude Haiku)
        └─── Brand Compliance  (Claude Haiku + rules)
                │
                ▼
        Confidence ≥ 85% + no pricing/specs?
                │
        ┌───────┴────────┐
        ▼                ▼
  Auto-approve      Human review
        │                │
        └───────┬─────────┘
                ▼
        PostgreSQL (persist)
        Celery (background: image gen, publishing)
        Social APIs (publish)
```

## Agent Communication

Agents communicate via `AgentState` — a TypedDict passed through the LangGraph `StateGraph`. Each node reads from and writes to this shared state. The orchestrator uses conditional edges to route based on `task_type`, `content_type`, and `platform`.

## RAG Architecture

- Documents uploaded → chunked (512 tokens, 64 overlap) → embedded (text-embedding-3-small) → stored in Pinecone
- At content generation time: semantic search across 3 query variations → top 5 chunks per query → deduplicated → injected into agent context
- Score threshold: 0.70

## Brand Compliance

The Brand Compliance Agent runs as the final gate before any content is approved or auto-published. It checks:
1. No unapproved competitor brands mentioned
2. No fabricated specifications or pricing
3. South African English spelling
4. SED tone and voice guidelines
5. Platform-appropriate length and format
6. Factual accuracy against RAG knowledge base

Items that fail critical checks are rejected. Minor issues are auto-corrected.

## Scaling Notes

- Celery workers can be scaled horizontally: `docker-compose up --scale celery_worker=4`
- Pinecone serverless scales automatically
- Backend is stateless; add more replicas behind Nginx upstream
- PostgreSQL: add read replicas for analytics queries at scale
- Redis: use Redis Cluster for high availability

## Adding a New Platform

1. Add platform to `Platform` enum in `models/content.py`
2. Add posting guidelines to `PLATFORM_POSTING_GUIDELINES` in `core/brand.py`
3. Add platform instructions to `PLATFORM_INSTRUCTIONS` in `agents/content_agent.py`
4. Implement publisher method in `services/social_publisher.py`
5. Add route handler in `api/routes/social.py`
6. Add frontend option to content generator dropdowns
