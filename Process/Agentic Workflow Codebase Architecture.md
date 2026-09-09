## **Core Architecture & Resource Locations**

The system utilizes several Google Cloud resources to manage state, storage, and event queuing.

* **Intake GCS Bucket:** gs://intake-ideas-bucket/raw stores the initial user submissions.  
* **Draft Skills GCS Bucket:** gs://enterprise-skillbank/drafts/\<skill\_id\>.md stores newly authored skills before validation.  
* **Production Skills GCS Bucket:** gs://enterprise-skillbank/production/\<skill\_id\>.md stores immutable, validated skills.  
* **Skill Registry Index:** A GCP Firestore database tracking active skills, categories, and routing metadata i.e \<skill\_id, generation\_id, target\_datastore\_id, etc.\>  
* **Live Session Chat Store:** GCP Firestore or Cloud Memorystore (Redis) conversational turns during the intake process.This facilitates the user’s chat session with both the IntakeAgent and the GemCreatorAgent.  
  * Located at (projects/{project\_id}/databases/(default)/documents/skill\_registry)  
* **Worker Redis Cache:** Redis store (redis://\<host\>:\<port\>) using the key format \<skill\_id\>:\<generation\_id\> to cache the Markdown string of the skill at runtime.  
* **Audit Database:** BigQuery (accessed via Storage Write API) for persisting Pydantic-parsed JSON outputs.   
  * Located at (projects/{project\_id}/datasets/{dataset\_id}/tables/{table\_id})

---

## **Skill Lifecycle Pipeline**

This module handles the conception, validation, and promotion of agentic skills.

* **Skill Draft Creation:** The GemCreatorAgent interactively authors skills and saves them to the draft GCS bucket with standard YAML frontmatter.  
* **Automated Validation Trigger:** An Eventarc trigger detects the new draft and invokes the SkillValidationAgent.  
* **Skill Validation Process:** The agent conducts a structural audit, security gate audit, and cryptographic sign check.  
* **Promotion & Indexing:** Following human-in-the-loop (HITL) sign-off, a Cloud Build pipeline copies the skill to the production bucket and updates the Firestore Skill Registry Index.

---

## **Intake & Discovery Services**

These services manage the user interface and initial payload routing.

* **IntakeAgent Class:** Maintains a stateful WebSockets connection via GKE Ingress and logs chat history to the Live Session Chat Store.  
  * **Intake Webhook:** Converts the session to a Markdown file (intake.md) upon a COMPLETED status and pushes it to the Intake GCS Bucket.  
* **DiscoveryAgent Class:** Triggered via Eventarc and sanitized by Model Armor, it inspects intake metadata and fetches the mapped skill payload from Firestore.  
  * **Queue Dispatch:** The Discovery Agent enqueues a JSON payload (skill\_id, generation\_id, target\_datastore\_id, skill\_gcs\_uri, intake\_uri) to a throttled Cloud Tasks queue.

---

## **Worker Execution Service**

This service dynamically executes tasks based on the matched skill and user intake.

* **WorkerAgent Class:** Operates statelessly in a GKE pod, authenticating via Workload Identity to pull HTTP tasks from the Cloud Task Queue.  
  * **Skill Retrieval:** Checks the Redis cache for the skill; if missing, it downloads it from the production GCS bucket and updates the cache.  
  * **Dynamic Context (RAG):** Queries domain-specific Vertex AI Search Data Stores based on the target\_datastore\_id with strict boundary caps.  
  * **Execution & Output:** Injects the skill into system\_instruction, enforces a Pydantic response schema (e.g., SecurityAuditResult), and streams the validated output directly to BigQuery.

---

**Codebase Directory Structure** 

enterprise-agent-workflow/  
├── config/  
│   └── settings.py              \# Centralized environment & GCP resource configs  
├── models/  
│   └── schemas.py               \# Task payloads & worker Pydantic response schemas  
├── agents/  
│   ├── base\_agent.py            \# Abstract agent with genai.Client & prompt resolution  
│   ├── discovery\_agent.py       \# Intake parsing, Model Armor sanitization, & enqueueing  
│   ├── gem\_creator\_agent.py     \# Interactive skill authoring & frontmatter injection  
│   ├── intake\_agent.py          \# Stateful WebSocket intake & conversation tracking  
│   ├── validation\_agent.py      \# 3-stage structural, security, & promotion auditor  
│   └── worker\_agent.py          \# RAG retrieval, Gemini constrained decoding, & BQ write  
├── services/  
│   ├── base\_service.py          \# Shared GCP auth, Firestore singleton, & URI parser  
│   ├── bigquery\_writer.py       \# BigQuery Storage Write API audit logging  
│   ├── cloud\_tasks.py           \# Task queueing & authenticated dispatching  
│   ├── discovery\_engine.py      \# Vertex AI Search Data Store RAG querying  
│   ├── firestore\_client.py      \# Skill Registry Index lookups & upserts  
│   ├── gcs\_service.py           \# Asynchronous GCS object management & promotion  
│   ├── intake\_webhook.py        \# Intake markdown formatting & GCS ingestion  
│   ├── model\_armor.py           \# Model Armor REST API security sanitization  
│   ├── redis\_cache.py           \# In-memory worker skill caching (\<skill\_id\>:\<generation\_id\>)  
│   └── session\_store.py         \# Live session state & chat history tracking  
├── utils/  
│   ├── logger.py                \# Telemetry and GCP Cloud Logging structured JSON formatter  
│   └── security.py              \# Workload Identity & Cloud Tasks OIDC token verification  
├── skills/                       \# Seed/Bootstrap system skills for pipeline seeding  
│   ├── SKILL\_GEM\_CREATOR.md     \# Gem Creator Meta-Skill seed prompt  
│   ├── SKILL\_INTAKE.md          \# Conversational Intake System seed prompt  
│   └── SKILL\_VALIDATION.md      \# Skill Validation & Security Auditor seed prompt  
├── k8s/                          \# Kubernetes deployment manifests and ingress rules  
│   └── ingress.yaml             \# GKE Ingress & BackendConfig configuration with 3600s   
├── requirements.txt             \# Project dependencies (google-genai, fastapi, pydantic)  
└── router\_main.py               \# FastAPI entry points, WebSocket routes, & Eventarc handlers  
└── worker\_main.py		\# FastAPI entrypoints for worker agents

---

**Definitions (Not DEFINED)**

1. WORKER\_SERVICE\_URL (config/settings.py)  
2. PROJECT\_ID (config/settings.py)  
3. INTAKE\_QUESTIONS (agents/intake\_agent.py)  
4. CATEGORY\_DATASTORE\_MAP (agents/intake\_agent.py)  
5. Google Cloud OAuth2 token (services/model\_armor.py)  
6. target\_datastore\_id for each agent skill must be defined.  
7. Kubernetes Service Accounts for each agent using GCP Workload Identity.   
8. Validation Agent Skill has not been defined properly in its seed file i.e SKILL\_VALIDATION.md  
9. Intake Agent Skill has not been defined properly in its seed file i.e SKILL\_INTAKE.md  
10. InnovationIntakeResult is a placeholder, and needs refinement. (models/schemas.py)

---

