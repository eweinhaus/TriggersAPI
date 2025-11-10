# Project Brief: Zapier Triggers API

**Organization:** Zapier  
**Project ID:** K1oUUDeoZrvJkVZafqHL_1761943818847  
**Version:** 2.0  
**Project Type:** Take-home project for AI Software Engineer interview

---

## Core Purpose

The Zapier Triggers API is a unified, real-time event ingestion system that enables external systems to send events into Zapier via a standardized RESTful interface. This API empowers developers to build event-driven automations and agentic workflows, moving beyond traditional scheduled polling to true real-time reactivity.

## Project Scope

This project is split into **6 phases**, each independently testable and deployable:

1. **Phase 1: Core API Backend (P0)** - Working API with all P0 endpoints, testable locally
2. **Phase 2: AWS Infrastructure & Deployment** - API deployed and accessible on AWS
3. **Phase 3: Testing & Error Handling** - Production-ready API with comprehensive testing
4. **Phase 4: Developer Experience (P1)** - Enhanced API with P1 features
5. **Phase 5: Documentation & Example Clients** - Complete developer documentation
6. **Phase 6: Frontend Dashboard (P2)** - Web-based UI for testing and managing events

## Key Requirements

### Functional Requirements (P0 - Must Have)
- Event ingestion endpoint (POST /v1/events)
- Event persistence and retrieval (GET /v1/inbox)
- Event acknowledgment (POST /v1/events/{id}/ack)
- Event deletion (DELETE /v1/events/{id})
- Health check endpoint (GET /v1/health)
- API key authentication
- Request ID tracking

### Non-Functional Requirements
- **Performance:** < 100ms p95 for event ingestion
- **Reliability:** 99.9% event ingestion success rate
- **Availability:** > 99.9% uptime
- **Security:** API key-based authentication, TLS encryption
- **Scalability:** AWS Lambda auto-scaling, DynamoDB on-demand

## Success Metrics

- Event ingestion latency: < 100ms (p95)
- API availability: > 99.9% uptime
- Event delivery success rate: > 99%
- Error rate: < 0.1%
- Developer satisfaction: > 4.5/5 on ease of use surveys
- Time to integrate: < 2 hours for basic integration

## Out of Scope (MVP)

- Rate limiting (deferred to post-MVP)
- Advanced filtering beyond source/event_type
- Event transformation or enrichment
- Webhooks (polling only)
- Event replay
- Analytics dashboard
- Multi-tenancy
- Event batching
- Long-term retention beyond 7-day TTL
- Event versioning

## Project Constraints

- Must be testable locally (Phase 1)
- Must be deployable to AWS (Phase 2)
- Must be fully automated (no manual testing required)
- Must be developer-friendly (simple integration)
- Must use publicly available tools and resources

## Implementation Philosophy

1. **Working Prototype First:** Get a working system quickly
2. **Developer-Friendly:** Minimal integration effort
3. **Minimal Effort:** Don't over-engineer for MVP
4. **Technical Impressiveness:** Show good engineering practices
5. **Automation:** Zero manual testing required

---

**Document Status:** Active  
**Last Updated:** 2025-11-10 (Phase 3 completion)

