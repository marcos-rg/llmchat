# LLMChat Hackathon Project Specifications

This document describes the specifications for a hackathon project. The idea is to have a platform where a LLM developer can send the same prompt multiple times and compare the responses from the same model to evaluate consistency and quality.

## Stack

- Frontend: React
- Backend: Python (Django)
- Database: PostgreSQL
- Hosting: Docker (local development using Docker Compose)
- Queue and worker: Django-Q2
- Message Broker: Redis
- LLM orchestration: LangChain / Langgraph

## Scope Assumptions

- Data is ephemeral: prompt runs and responses are not persisted beyond the active browser session (no history page, nothing survives logout/refresh).
- Deployment target is local only, via Docker Compose. There is no cloud/production hosting requirement.
- LLM API keys (OpenAI, Anthropic) are configured once by an admin via environment variables and shared by all users; users never supply or see raw API keys.

## Functional Requirements

- As a user, I want to log in with an email/password so that I can access the platform.
- As a user, I want to select an LLM provider and model (from OpenAI and Anthropic) so that I can compare responses across models.
- As a user, I want to send the same prompt multiple times to the LLM so that I can evaluate the consistency of its responses.
- As a user, I want to configure the number of times (2 to 5) a prompt is sent so that I can control how many responses I get for comparison.
- As a user, I want to change the system prompt so that I can influence the behavior of the LLM.
- As a user, I want to be warned when my prompt exceeds a configured maximum length so that I can shorten it before submitting.
- As a user, I want responses to be generated asynchronously (queued as background jobs) so that I can continue using the app while I wait.
- As a user, I want to see the status of each response (queued, running, complete, failed) via periodic polling so that I can track progress without manual refresh.
- As a user, I want to see all responses to a prompt run displayed side by side so that I can compare them.
- As a user, I want differences between responses to be automatically highlighted (diffed) so that I can spot variations quickly.
- As a user, I want to toggle the diff highlighting on/off so that I can view raw responses when I prefer.

## Non-Functional Requirements

- Performance & Scalability
  - No optimization for high performance or horizontal scalability is required at this stage.
  - The system should support at least 10 concurrent users without noticeable degradation.
- Reliability & Fault Tolerance
  - The system should track errors per response and retry failed LLM calls when possible, without requiring complex disaster-recovery mechanisms.
  - Failed background jobs should be recoverable by restarting the affected component (worker/broker).
- Security & Privacy
  - Authentication is required for all prompt/response functionality (Django email/password auth).
  - LLM provider API keys are stored server-side only (environment variables) and are never exposed to the frontend or logged.
  - Each user can only access their own active session's prompt runs.
- Usability & Accessibility
  - Core actions (submit prompt, view status, compare responses) should be usable without a manual, following standard web accessibility practices (e.g., keyboard navigation, sufficient color contrast for diff highlighting).
- Maintainability & Testability
  - Core business logic (prompt fan-out, LLM orchestration, diffing) should have basic unit test coverage.
  - The codebase should be modular and documented enough for another developer to extend it.
- Portability
  - The system should run via `docker compose up` with minimal manual configuration (environment variables documented in a `.env.example`).