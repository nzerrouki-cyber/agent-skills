## **Core Architecture & Resource Locations**

The system utilizes several Google Cloud resources to manage state, storage, and event queuing.

* **Apigee LLM Gateway:** `APIGEE_GATEWAY_URL` routes all Vertex AI Gemini API calls through enterprise API proxies using custom HTTP options and authentication headers (`APIGEE_API_KEY`).   
* **Intake GCS Bucket:** gs://intake-ideas-bucket/raw stores the initial user submissions.  
* **Draft Skills GCS Bucket:** gs://enterprise-skillbank/drafts/\<skill\_id\>.md stores newly authored skills before validation.  
* **Production Skills GCS Bucket:** gs://enterprise-skillbank/production/\<skill\_id\>.md stores immutable, validated skills.  
* **Skill Registry Index:** A GCP Firestore database tracking active skills, categories, and routing metadata i.e \<skill\_id, generation\_id, target\_datastore\_id, etc.\>  
* **Vertex AI Data Store(s):** As a default, the knowledge base for the GemCreatorAgent is stored in system-core-ds / gem-creator-ds.  
* **Live Session Chat Store:** GCP Firestore or Cloud Memorystore (Redis) conversational turns during the intake process.This facilitates the user’s chat session with both the IntakeAgent and the GemCreatorAgent.  
  * Located at (projects/{project\_id}/databases/(default)/documents/skill\_registry)  
* **Worker Redis Cache:** Redis store (redis://\<host\>:\<port\>) using the key format \<skill\_id\>:\<generation\_id\> to cache the Markdown string of the skill at runtime.  
* **Audit Database:** BigQuery (accessed via Storage Write API) for persisting Pydantic-parsed JSON outputs.   
  * Located at (projects/{project\_id}/datasets/{dataset\_id}/tables/{table\_id})  
* **Traffic Throttling Queue**: Google Cloud Tasks (`worker-dispatch-queue`) for rate-limited task smoothing to prevent Vertex AI / Apigee rate limit exhaustion 

---

## **Execution Plane Architecture (Cloud Run Services)**

### **Control Plane: Cloud Run Service (orchestrator-service)**

* **Service Entrypoint**: Runs orchestrator\_main.py as a continuous web service via FastAPI and Uvicorn.  
* **Interactive Control Plane**: Hosts OrchestratorAgent as the central supervisor for intent classification, conversational state management, and tool delegation.  
* **Interactive Agents & WebSockets**: Manages GemCreatorAgent, DiscoveryAgent and IntakeAgent over persistent WebSockets (/ws/gem-creator/{session\_id} and /ws/intake/{session\_id}) for real-time, low-latency chat turns.  
* **Event Ingestion**: Receives HTTP Eventarc notifications for draft skill audits (/events/skill-draft-uploaded) and raw intake uploads (/events/intake-uploaded).  
* **Discovery & HTTPS Tool Routes**: Exposes internal HTTPS tool endpoints (/services/discovery, /services/validation, /services/gem-creator) authenticated via IAM OIDC Bearer tokens, along with the Skill Discovery API (GET /skills).

### **Execution Plane: Asynchronous Task Dispatch & Tool Execution**

* **Task Entrypoint**: Cloud Tasks dispatches HTTP payloads to the execution endpoint (/tasks/execute-skill) hosted on the Cloud Run service.  
* **Traffic Control & Throttling**: Google Cloud Tasks (worker-dispatch-queue) rate-limits execution via strict concurrency limits (max\_dispatches\_per\_second and max\_concurrent\_tasks) to shield Vertex AI and Apigee endpoints from 429 Resource Exhausted errors.  
* **Stateless Tool Adapter**: Invokes skill\_bank\_tool.py to execute skills dynamically without maintaining dedicated worker container infrastructure.  
* **Dual-Lookup Prompt Resolution**: Resolves system prompts from Cloud Memorystore Redis (\<skill\_id\>:\<generation\_id\>), falling back to Production GCS (gs://enterprise-skillbank/production/\<skill\_id\>.md) on cache misses.  
* **Constrained LLM Inference**: Invokes Gemini 2.5 Flash through the Apigee LLM Gateway using token-level constrained decoding enforced by Pydantic response schemas (response\_schema, response\_mime\_type="application/json").  
* **Decoupled Audit Persistence**: Asynchronously streams validated Pydantic JSON outputs (response.parsed) to BigQuery via bigquery\_writer.py using the BigQuery Storage Write API.

## **Core Component & Service Modules**

### **A. Skill Lifecycle Module**

Manages the conception, validation, promotion, and discovery of agentic skills:

* **GemCreatorAgent**:  
  * Interactively asks questions to the user over WebSockets (/ws/gem-creator/{session\_id}), utilizing discovery\_engine.py to search system-core-ds for grounding knowledge.  
  * Synthesizes prompt structures and uploads candidate Markdown files to GCS staging (gs://enterprise-skillbank/staging/).  
* **SkillValidationAgent**:  
  * Triggered via Eventarc (/events/skill-draft-uploaded) or direct tool calls from ValidationService.  
  * Executes a 3-stage audit: Structural/Taxonomy Format Check, Prompt Defense & Anti-Hijack Audit via Gemini 2.5 Flash, and Synthetic Execution Sandbox validation.  
* **Promotion & Indexing**: Promotes validated skills to gs://enterprise-skillbank/production/\<skill\_id\>.md, updates the Firestore skill\_registry, invalidates stale cache keys, and warms the active prompt string in Redis Cloud Memorystore.  
* **Skill Discovery API**: GET /skills in orchestrator\_main.py invokes firestore\_client.list\_available\_skills() to return active registered skills from the registry.

### **B. Intake & Discovery Services**

Manages stateful user ingestion, safety scanning, domain context retrieval, and task queueing:

* **IntakeAgent**:  
  * Manages low-latency WebSocket chat turns (/ws/intake/{session\_id}), persisting active conversation state and field extractions in Firestore (intake\_chat\_sessions).  
  * Upon receiving a completion signal, formats the structured session data into intake.md and uploads it to raw GCS storage (gs://intake-ideas-bucket/raw/).  
* **DiscoveryAgent**:  
  * Invoked by OrchestratorAgent via tool calls to discovery\_service.py.  
  * Sanitizes input text using model\_armor.py to prevent prompt injection attempts.  
  * Performs dynamic RAG context retrieval via discovery\_engine.py against targeted Vertex AI Search Data Stores, strictly enforcing top\_k=3 or top\_k=5 boundary caps.  
  * Packages the retrieved context, intake payload, and resolved skill parameters, then enqueues the execution task into Cloud Tasks via cloud\_tasks.py.

### **C. Execution Adapter & Tool Execution Plane**

Executes domain evaluation tasks statelessly and handles schema decoding:

* **Cloud Tasks Execution Dispatcher**:  
  1. Receives routed HTTP POST requests from the worker-dispatch-queue at /tasks/execute-skill.  
  2. Extracts the task payload and delegates execution directly to skill\_bank\_tool.py.  
* **skill\_bank\_tool.py**:  
  1. Fetches the active system prompt string from Redis (\<skill\_id\>:\<generation\_id\>), falling back to Production GCS if un-cached, and strips YAML frontmatter headers.  
  2. Binds the corresponding Pydantic schema (e.g., InnovationIntakeResult, SecurityAuditResult) from models/schemas.py.  
  3. Executes model inference against Gemini 2.5 Flash via the Apigee LLM Gateway with constrained JSON generation.  
  4. Dispatches response.parsed asynchronously to bigquery\_writer.py for BigQuery Storage Write API persistence.  
  5. Returns the structured evaluation object back to DiscoveryAgent to push to OrchestratorAgent and display on the user's active WebSocket connection.

---

**Codebase Directory Structure** 

```
enterprise-agent-workflow/
├── config/
│   └── settings.py              # Centralized environment & GCP resource configs
├── models/
│   └── schemas.py               # Task payloads & worker Pydantic response schemas
├── agents/
│   ├── base_agent.py            # Abstract agent with genai.Client & prompt resolution
│   ├── orchestrator_agent.py    # Supervisor agent managing conversation flow & tool routing
│   ├── discovery_agent.py       # Intake resolution, Model Armor scan, Data Store RAG, & task queuing
│   ├── gem_creator_agent.py     # Interactive skill authoring with system-core-ds RAG
│   ├── intake_agent.py          # Stateful WebSocket intake & conversation tracking
│   └── validation_agent.py      # 3-stage structural, security, & promotion prompt auditor
├── services/
│   ├── base_service.py          # Shared GCP auth, Firestore singleton, & GCS URI parser
│   ├── discovery_service.py     # HTTPS tool endpoint for intake discovery & RAG dispatch
│   ├── gem_creator_service.py   # HTTPS tool endpoint for prompt authoring & tuning
│   ├── intake_service.py        # HTTPS tool endpoint for chat session management
│   ├── validation_service.py    # HTTPS tool endpoint for automated testing & GCS promotion
│   ├── skill_bank_tool.py       # Execution adapter for prompt loading & Apigee Gemini inference
│   ├── bigquery_writer.py       # Asynchronous BigQuery Storage Write API audit logging
│   ├── cloud_tasks.py           # Task queueing & rate-limited dispatching (worker-dispatch-queue)
│   ├── discovery_engine.py      # Vertex AI Search Data Store RAG querying (top_k=3/5)
│   ├── firestore_client.py      # Skill Registry Index lookups & status updates
│   ├── gcs_service.py           # Async GCS object management across staging, production, & archive
│   ├── intake_webhook.py        # Form data formatting & raw GCS payload ingestion
│   ├── model_armor.py           # Model Armor REST API security sanitization client
│   ├── redis_cache.py           # In-memory worker skill caching (<skill_id>:<generation_id>)
│   └── session_store.py         # Live session state & chat history tracking in Firestore
├── utils/
│   ├── logger.py                # Telemetry and GCP Cloud Logging structured JSON formatter
│   └── security.py              # Workload Identity & Cloud Tasks OIDC token verification
├── seeds/                       # Seed/Bootstrap system & domain skills
│   ├── SKILL_GEM_CREATOR.md
│   ├── SKILL_INTAKE.md
│   ├── SKILL_VALIDATION.md
│   ├── SKILL_CSA_REVIEW.md
│   ├── SKILL_ARCH_RISK_REVIEW.md
│   ├── SKILL_TECHNICAL_REVIEW.md
│   └── SKILL_CDS_DATA_EVALUATOR.md
├── scripts/
│   └── seed_skills.py           # Step 0 pipeline bootstrapping script
├── k8/
│   └── ingress.yaml             # Network ingress & security control policies
├── .env.example                 # Deployment environment template
├── Dockerfile                   # Container build file
├── requirements.txt             # Dependency definitions
└── orchestrator_main.py         # Control Plane FastAPI entrypoint hosting WebSockets & tool routes

```

## **Key Directory & File Scoping Details**

### **Core Control Plane Entrypoint**

* **`orchestrator_main.py`**: Replaces the deprecated `router_main.py` and `worker_main.py` files. Hosts the FastAPI service providing persistent WebSocket endpoints (`/ws/intake/{session_id}`) for user interaction and internal HTTPS endpoints for tool delegation.

### **Agent Layer (`agents/`)**

* **`base_agent.py`**: Base class providing shared `google-genai` SDK initialization, default parameters, and token management for specialized sub-agents.  
    
* **`orchestrator_agent.py`**: Implements the supervisor agent logic, parsing user intent and issuing tool calls to backend microservices.  
    
* **`discovery_agent.py`**: Executes the intake processing pipeline—running Model Armor checks, fetching domain context via `discovery_engine.py`, and enqueuing tasks into Cloud Tasks.  
    
* \*\*`gem_creator_agent.py` & `validation_agent.py**`: Manage the authoring, synthetic testing, anti-hijack auditing, and promotion of system skills.

### **Service & Tool Layer (`services/`)**

* **`skill_bank_tool.py`**: Acts as the execution driver triggered by Cloud Tasks. Resolves cached prompts from `redis_cache.py` or GCS, enforces Pydantic structured output constraints via Apigee, and delegates async persistence to `bigquery_writer.py`.  
    
* **`cloud_tasks.py`**: Manages the `worker-dispatch-queue` to enforce dispatch rates (`max_dispatches_per_second`) and prevent `429 Resource Exhausted` API errors.  
    
* **`discovery_engine.py`**: Connects directly to Vertex AI Search Data Stores, applying `top_k=3` or `top_k=5` caps to enforce token budget efficiency.

---

## **Resolved Definitions & System Configurations (Undefined)**

The following definitions and system configuration parameters represent architectural concepts, service credentials, and domain mappings that must be explicitly configured during deployment and infrastructure provisioning:

* **PROJECT\_ID**  
  * **File Location**: config/settings.py  
  * **Description**: The active Google Cloud Platform Project ID configured via environment variables (.env).  
* **REGION**  
  * **File Location**: config/settings.py  
  * **Description**: The targeted GCP deployment region (Default: us-central1) for Vertex AI, Cloud Run Services, Cloud Run Jobs, and Cloud Tasks.  
* **APIGEE\_GATEWAY\_URL**  
  * **File Location**: config/settings.py  
  * **Description**: The enterprise proxy endpoint URL routing Vertex AI Gemini 2.5 Flash traffic through Apigee.  
* **APIGEE\_API\_KEY**  
  * **File Location**: config/settings.py  
  * **Description**: The API key credential used in custom HTTP headers to authenticate requests with the Apigee LLM Gateway.  
* **REDIS\_CACHE\_URL**  
  * **File Location**: config/settings.py  
  * **Description**: The internal VPC Private IP address or URI binding to the GCP Cloud Memorystore Redis instance (redis://10.0.0.3:6379).  
* **target\_datastore\_id Mapping (CATEGORY\_DATASTORE\_MAP)**  
  * **File Locations**: agents/intake\_agent.py and config/settings.py  
  * **Description**: Explicit binding of intake operational categories to Vertex AI Search Data Store IDs (system-core-ds, ciso-policies-ds, csa-sop-ds, cds-schema-ds, ai-governance-ds).  
* **list\_available\_skills()**  
  * **File Locations**: services/firestore\_client.py and router\_main.py  
  * **Description**: The discovery method implemented in services/firestore\_client.py and exposed via the GET /skills route in router\_main.py to query active registered skills.  
* **InnovationIntakeResult**  
  * **File Location**: models/schemas.py  
  * **Description**: The standardized Pydantic schema that formats output evaluations, score classifications, recommendations, and compliance flags.  
* **GCP IAM & Service Account Roles**  
  * **File Locations**: scripts/seed\_skills.py and GCP Deployment/IAM Configurations  
  * **Description**: IAM permissions assigned to execution service accounts (e.g., roles/storage.objectViewer, roles/bigquery.dataEditor, roles/datastore.user, roles/run.developer) to enforce least-privilege security across Cloud Run execution planes.

---
