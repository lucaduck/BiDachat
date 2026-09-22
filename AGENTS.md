# AGENTS.md — BIDACHAT

## 1. Purpose

This file defines the technical and operational rules that any coding agent must follow when working on BIDACHAT.

`AGENTS.md` explains **how to implement the system**. It does not replace the software requirements.

The main rule is:

> Implement the simplest solution that correctly satisfies the approved requirement. Do not add complexity without a concrete need.

---

## 2. Project context

BIDACHAT is a web application for managing and configuring chatbots that help users interpret BI-DATA analytical dashboards.

The application combines:

- chatbot management;
- document processing;
- multimodal RAG;
- LLM integration;
- an embeddable JavaScript widget;
- usage metrics.

BIDACHAT is a **web application**, not a Business Intelligence platform and not a replacement for the existing BI-DATA dashboards.

General flow:

```text
Researcher / Administrator
          |
          v
   BIDACHAT Web App
          |
          v
      REST API
          |
          v
       FastAPI
          |
    +-----+------+----------------+
    |            |                |
    v            v                v
Chatbots        RAG             Metrics
                 |
          +------+------+
          |             |
          v             v
 PostgreSQL          Gemini
 + pgvector
          ^
          |
   JavaScript Widget
          ^
          |
   BI-DATA Dashboard
```

---

## 3. Sources of truth

The project documentation has different responsibilities.

```text
SRS.md
  |
  | defines WHAT the system must do
  v
AGENTS.md
  |
  | defines HOW agents must implement it
  v
Source code
  |
  | contains the implementation
  v
README.md / docs/
  |
  | explain installation and technical usage
```

The Notion project page contains the broader thesis context, architecture decisions, technology definitions, visual design and project planning.

### Priority rule

When implementing a feature:

1. Read the related requirement in `SRS.md`.
2. Apply the implementation rules in `AGENTS.md`.
3. Review the existing code before creating new abstractions or dependencies.
4. Use Notion as supporting project context when necessary.

If an implementation idea conflicts with an approved requirement in `SRS.md`, the requirement has priority.

Do not invent missing requirements.

---

## 4. Version strategy

### 4.1 Version 1 — MVP

Version 1 is the current development target.

It must provide a complete end-to-end flow for the thesis:

```text
Login
  |
  v
Create chatbot
  |
  v
Configure chatbot
  |
  v
Upload documents
  |
  v
Process documents
  |
  v
Generate / store embeddings
  |
  v
Integrate chatbot widget
  |
  v
Ask question
  |
  +---------- optional image / screenshot
  |
  v
Retrieve RAG context
  |
  v
Send context to LLM
  |
  v
Return answer
  |
  v
Record metrics
```

Version 1 includes the functional, non-functional and security requirements defined for the MVP in `SRS.md`.

Functionality has priority over advanced customization.

### 4.2 Version 2 — Complete application

Version 2 represents the future evolution of BIDACHAT after the MVP is stable.

Do not implement Version 2 features unless they have been explicitly approved and incorporated into the requirements.

The agent must not assume that a feature belongs to Version 2 simply because it appears useful.

```text
Version 1
   |
   v
Stable MVP
   |
   v
Approved new requirements
   |
   v
Version 2
```

---

## 5. Architecture

BIDACHAT uses a **Service-Oriented Architecture (SOA)**.

SOA does not imply microservices.

For Version 1, logical services may live inside a single FastAPI backend.

Expected logical separation:

```text
FastAPI
  |
  +-- Authentication service
  |
  +-- Chatbot service
  |
  +-- Document service
  |
  +-- RAG service
  |
  +-- LLM service
  |
  +-- Metrics service
```

Do not split these services into independent deployments unless an approved requirement makes it necessary.

### Communication rule

Frontend and widget clients communicate with the backend through the API.

```text
Next.js --------                                   >---- REST API ---- FastAPI
                 /
Widget ----------/
```

Clients must not access PostgreSQL, pgvector, RAG internals or the LLM provider directly.

---

## 6. Authorized technology stack

Use the project stack already selected.

| Area | Technology |
|---|---|
| Frontend | Next.js + TypeScript |
| UI styles | Tailwind CSS |
| Backend / API | FastAPI + Python |
| RAG support | LangChain |
| Relational database | PostgreSQL |
| Vector storage | pgvector |
| Main LLM integration | Gemini |
| Dashboard integration | Embeddable JavaScript widget |
| Infrastructure | Docker + Docker Compose |
| API style | REST |
| Version control | Git + GitHub |
| Frontend linting | ESLint |
| Frontend formatting | Prettier |
| Python linting / formatting | Ruff |
| Python style | PEP 8 |

### Dependency rule

Do not introduce a new framework, database, vector database, message broker, cache, architectural pattern or infrastructure component if the requirement can reasonably be solved with the existing stack.

Examples of technologies that must **not** be added without a concrete approved need:

```text
Redis
MongoDB
Pinecone
Kafka
RabbitMQ
Kubernetes
another backend framework
another vector database
microservice infrastructure
```

This is not a permanent ban. It means that every additional technology must solve a real requirement.

---

## 7. Repository structure

Use a single repository for Version 1.

```text
BIDACHAT/
|
+-- frontend/
|   +-- app/
|   +-- components/
|   +-- services/
|   +-- types/
|   +-- lib/
|   +-- public/
|
+-- backend/
|   +-- app/
|   |   +-- api/
|   |   +-- services/
|   |   +-- models/
|   |   +-- schemas/
|   |   +-- rag/
|   |   +-- llm/
|   |   +-- database/
|   |   +-- core/
|   |
|   +-- tests/
|
+-- widget/
|   +-- src/
|   +-- dist/
|
+-- database/
|   +-- migrations/
|   +-- seeds/
|
+-- docs/
|
+-- docker/
|
+-- AGENTS.md
+-- SRS.md
+-- docker-compose.yml
+-- .env.example
+-- .gitignore
+-- README.md
```

### Folder responsibilities

| Folder | Responsibility |
|---|---|
| `frontend/` | BIDACHAT administrative web interface |
| `backend/` | API, business logic, RAG, LLM integration and metrics |
| `widget/` | Chatbot client embedded in dashboards |
| `database/` | Database migrations, seeds and initialization scripts |
| `docs/` | Technical documentation and diagrams |
| `docker/` | Docker build files |

### Backend responsibilities

```text
backend/app/
|
+-- api/        -> REST endpoints
+-- services/   -> application logic
+-- models/     -> persistence models
+-- schemas/    -> API input/output validation
+-- rag/        -> document processing and retrieval
+-- llm/        -> provider integration
+-- database/   -> database connection
+-- core/       -> configuration and shared infrastructure
```

Endpoints should remain thin. Business logic belongs in services.

---

## 8. Code naming and language conventions

All technical identifiers must be written in **English**.

This applies to:

- variables;
- functions;
- classes;
- components;
- file names;
- directories;
- database tables;
- database columns;
- API endpoints;
- route parameters;
- environment variables;
- Git branches;
- commit messages;
- code comments.

User-facing interface text may be written in Spanish.

Academic thesis documentation may be written in Spanish.

### 8.1 Naming table

Use the following conventions exactly:

| Element | Convention | Correct example |
|---|---|---|
| TypeScript variables | `camelCase` | `chatbotName` |
| TypeScript functions | `camelCase` | `getChatbots()` |
| React components | `PascalCase` | `ChatbotCard` |
| TypeScript classes | `PascalCase` | `ChatbotService` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_FILE_SIZE` |
| Next.js / TypeScript files | `kebab-case` | `chatbot-card.tsx` |
| Python variables | `snake_case` | `chatbot_name` |
| Python functions | `snake_case` | `process_document()` |
| Python classes | `PascalCase` | `ChatbotService` |
| Python modules | `snake_case` | `chatbot_service.py` |
| PostgreSQL tables | `snake_case` | `chatbot_documents` |
| PostgreSQL columns | `snake_case` | `created_at` |
| REST endpoints | lowercase, plural nouns | `/api/v1/chatbots` |
| Route parameters | `snake_case` | `{chatbot_id}` |
| Git branches | `type/kebab-case` | `feature/document-upload` |
| Environment variables | `UPPER_SNAKE_CASE` | `DATABASE_URL` |

### 8.2 Clear example

Do this:

```text
Frontend
--------
chatbotName
getChatbots()
ChatbotCard
chatbot-card.tsx

Backend
-------
chatbot_name
get_chatbots()
ChatbotService
chatbot_service.py

Database
--------
chatbots
chatbot_documents
created_at
response_time_ms

API
---
/api/v1/chatbots
/api/v1/chatbots/{chatbot_id}/documents

Git
---
feature/chatbot-management
fix/authentication-error

Environment
-----------
DATABASE_URL
GEMINI_API_KEY
SECRET_KEY
```

Do not mix Spanish and English identifiers:

```text
Avoid
-----
nombre_chatbot
obtener_chatbots()
procesar_documento()
fecha_creacion
feature/carga-documentos
/api/v1/crear-chatbot
```

Use:

```text
Correct
-------
chatbot_name
get_chatbots()
process_document()
created_at
feature/document-upload
/api/v1/chatbots
```

### 8.3 User-facing text

Technical code remains in English, but visible text may be Spanish.

Example:

```text
Code:
createChatbot()

UI:
"Crear chatbot"
```

This rule keeps the source code consistent while preserving a Spanish interface for BIDACHAT users.

---

## 9. REST API conventions

The API uses:

```text
/api/v1
```

Use lowercase resource names and plural nouns.

Actions are represented by HTTP methods, not by verbs inside URLs.

### Example table

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/chatbots` | List chatbots |
| `POST` | `/api/v1/chatbots` | Create a chatbot |
| `GET` | `/api/v1/chatbots/{chatbot_id}` | Get one chatbot |
| `PUT` | `/api/v1/chatbots/{chatbot_id}` | Update a chatbot |
| `DELETE` | `/api/v1/chatbots/{chatbot_id}` | Delete a chatbot |
| `GET` | `/api/v1/chatbots/{chatbot_id}/documents` | List chatbot documents |
| `POST` | `/api/v1/chatbots/{chatbot_id}/documents` | Upload a chatbot document |
| `POST` | `/api/v1/chatbots/{chatbot_id}/queries` | Submit a chatbot query |
| `GET` | `/api/v1/chatbots/{chatbot_id}/metrics` | Get chatbot metrics |

Preferred structure:

```text
/api/v1/resource
/api/v1/resource/{resource_id}
/api/v1/resource/{resource_id}/subresource
```

Avoid:

```text
/api/v1/createChatbot
/api/v1/getChatbots
/api/v1/uploadDocument
/api/v1/deleteChatbot
```

Authentication actions such as `/api/v1/auth/login` and `/api/v1/auth/logout` are accepted because they represent authentication operations rather than CRUD resources.

Use the HTTP methods as follows:

| Method | Main use |
|---|---|
| `GET` | Read data |
| `POST` | Create a resource or execute an operation |
| `PUT` | Replace/update a resource |
| `DELETE` | Delete a resource |

Do not create extra endpoints unless they correspond to a requirement or a necessary implementation of an approved use case.

---

## 10. Implementation rules by module

Version 1 is organized around the approved functional areas.

### Authentication

Implement only what is needed for:

- authorized researcher login;
- protection of administrative functions;
- logout.

Do not add complex role hierarchies unless requirements change.

### Chatbot management

Support:

- create;
- list/read;
- update;
- delete;
- LLM configuration;
- knowledge-source association;
- behavior instructions;
- integration mechanism.

### Documents and RAG

Support:

- document upload;
- validation;
- processing;
- semantic representation generation;
- vector storage;
- retrieval;
- isolation by chatbot.

### Conversation and multimodal processing

Support:

- natural-language queries;
- optional image/screenshot input;
- document retrieval;
- context construction;
- LLM request;
- response delivery.

### Metrics

Support the metrics required by the SRS:

- queries per chatbot;
- response time;
- association of metrics with the chatbot;
- administrative metric consultation.

Do not automatically expand this into a full analytics product.

---

## 11. RAG and LLM rules

LangChain is a support library for the RAG pipeline. It is not the system architecture.

Expected document flow:

```text
Document
   |
   v
Load
   |
   v
Split
   |
   v
Generate embeddings
   |
   v
PostgreSQL + pgvector
   |
   v
Retrieve relevant context
```

Expected query flow:

```text
User question
     |
     +------ optional dashboard image
     |
     v
Identify chatbot
     |
     v
Load chatbot configuration
     |
     v
Retrieve chatbot documents
     |
     v
Build context
     |
     v
Send context to Gemini
     |
     v
Return answer
```

### RAG rules

- Retrieval must use only sources associated with the current chatbot.
- Do not create a separate vector database while PostgreSQL + pgvector satisfies the requirement.
- Keep retrieval logic separated from API endpoint code.
- Do not add an agent framework or multi-agent system unless explicitly required.
- Do not add automatic dashboard capture unless it becomes an approved requirement.

### LLM rules

- LLM integration must be isolated behind backend code.
- Frontend and widget must not call the LLM provider directly.
- Model/provider-specific code should remain separated from general application logic.
- Do not train a custom LLM as part of Version 1.

---

## 12. Widget rules

The widget is a client that allows a BIDACHAT chatbot to be embedded in a dashboard.

Expected relationship:

```text
BI-DATA Dashboard
        |
        v
JavaScript Widget
        |
        v
BIDACHAT REST API
        |
        v
FastAPI
```

The widget must not communicate directly with:

```text
PostgreSQL
pgvector
Gemini API
RAG internals
```

The widget should contain only the logic needed to:

- identify the chatbot;
- render the conversational interface;
- send user input;
- optionally send supported visual input;
- display processing feedback;
- display the response.

Keep the widget independent from the host dashboard framework when possible.

---

## 13. Database rules

Use:

```text
PostgreSQL + pgvector
```

Do not add a second database solely for vector search unless a future approved requirement justifies it.

Technical database identifiers use `snake_case`.

Examples:

```text
users
chatbots
documents
document_chunks
queries
metrics

chatbot_id
document_id
created_at
updated_at
response_time_ms
```

Database access belongs in the backend.

Frontend and widget clients must never access the database directly.

Schema changes should be tracked through migrations rather than undocumented manual changes.

---

## 14. Security rules

All security requirements in `SRS.md` must be respected.

Core rules:

- protect the administrative interface with authentication;
- verify authorization for administrative API operations;
- use HTTPS/TLS in deployment;
- keep secrets in backend configuration;
- validate API input;
- validate document uploads;
- isolate data by chatbot;
- protect public chatbot endpoints from abusive use;
- do not expose sensitive internal information in client errors.

Chatbot isolation example:

```text
Chatbot A
  |
  +-- Document A1
  +-- Document A2

Chatbot B
  |
  +-- Document B1

Allowed:
Chatbot A --> A1, A2

Not allowed:
Chatbot A -X-> B1
```

Never hardcode private API keys or database credentials in source code.

---

## 15. Testing and acceptance criteria

Implementation must be traceable to the requirements in `SRS.md`.

Expected relationship:

```text
Requirement
    |
    v
Use Case
    |
    v
Acceptance Criterion
    |
    v
Implementation
    |
    v
Test
```

Example:

```text
RF-04
Create chatbot
    |
    v
UC-02
Manage chatbots
    |
    v
CA-UC02-01
Valid chatbot data is stored
    |
    v
Implementation
    |
    v
Automated / integration test
```

### Testing rule

Before considering a feature complete:

1. identify the related `RF`, `RNF` or `RS`;
2. identify the related use case and acceptance criteria where applicable;
3. implement the feature;
4. add or update the relevant tests;
5. run the affected tests;
6. verify that existing behavior remains functional.

At minimum, Version 1 should test critical flows for:

- authentication;
- chatbot CRUD;
- document processing;
- chatbot data isolation;
- RAG retrieval;
- conversational query;
- multimodal query;
- metrics registration.

Do not invent arbitrary performance thresholds. Use only approved thresholds or measurable values defined by the project.

---

## 16. Git workflow

Use a simple Git workflow.

```text
main
 ^
 |
 Pull Request
 |
 +-- feature/chatbot-management
 +-- feature/document-upload
 +-- feature/rag-processing
 +-- fix/authentication-error
 +-- docs/api-documentation
```

`main` should contain functional integrated code.

Use short-lived branches.

### Branch naming

```text
feature/short-description
fix/short-description
docs/short-description
test/short-description
refactor/short-description
```

### Commits

Use Conventional Commits in English.

Examples:

```text
feat(chatbot): add chatbot creation
feat(rag): add document processing
fix(auth): validate authentication
docs(api): document chatbot endpoints
test(rag): add retrieval tests
refactor(metrics): simplify query metrics service
```

Main commit types:

```text
feat
fix
docs
test
refactor
chore
```

Avoid introducing a full GitFlow model unless the project explicitly requires it.

---

## 17. Definition of Done

A change is considered complete only when all applicable conditions are met:

```text
Approved requirement identified
          |
          v
Implementation completed
          |
          v
Acceptance criteria satisfied
          |
          v
Relevant tests pass
          |
          v
Lint / formatting pass
          |
          v
No unrelated behavior is broken
          |
          v
Documentation updated when necessary
          |
          v
DONE
```

Checklist:

- [ ] The change satisfies an approved requirement.
- [ ] The implementation follows the existing architecture.
- [ ] Technical identifiers are in English.
- [ ] API conventions are respected.
- [ ] Relevant security requirements are respected.
- [ ] Tests were added or updated when required.
- [ ] Affected tests pass.
- [ ] Formatting and linting pass.
- [ ] Documentation was updated if behavior or setup changed.
- [ ] No unnecessary dependency or architectural component was introduced.

---

## 18. Agent restrictions

Every coding agent working on BIDACHAT must follow these rules.

1. Read the related requirement in `SRS.md` before implementing a feature.
2. Do not invent functional requirements.
3. Do not implement Version 2 features while working on Version 1 unless explicitly requested and approved.
4. Do not redesign the architecture without a concrete requirement.
5. Do not interpret SOA as a requirement for microservices.
6. Do not add dependencies only because they are common or fashionable.
7. Reuse existing services, utilities and components when appropriate.
8. Keep all technical identifiers in English.
9. Keep user-facing interface text in Spanish unless a requirement states otherwise.
10. Follow the REST conventions defined in this file.
11. Keep endpoint code thin and business logic in services.
12. Keep database and LLM access inside the backend.
13. Preserve chatbot data isolation.
14. Never expose private credentials in frontend or widget code.
15. Relate implementation and tests to the corresponding requirement or acceptance criterion.
16. Do not remove or change an approved requirement through implementation decisions.
17. Do not add a new technology when the existing stack already satisfies the need.
18. Prefer clear and direct code over unnecessary abstraction.

Final rule:

```text
+------------------------------------------------------------+
|                   BIDACHAT DEVELOPMENT RULE                 |
+------------------------------------------------------------+
|                                                            |
| Build the simplest implementation that correctly satisfies |
| the approved requirement.                                  |
|                                                            |
| Complete Version 1 end-to-end before adding unnecessary    |
| product expansion.                                         |
|                                                            |
| Do not add complexity without a concrete requirement.      |
|                                                            |
+------------------------------------------------------------+
```
