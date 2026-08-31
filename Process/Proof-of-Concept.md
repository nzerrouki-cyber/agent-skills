# Proof-of-Concept: Enterprise Innovation Intake Pipeline via Vertex AI

This document describes the end-to-end architecture for integrating custom Google Gems into an automated, production-grade agentic workflow hosted on Google Cloud Platform (GCP).

---

## 1\. Intake Ingestion & Payload Formatting

* **Trigger:** Users submit an intake idea via Google Forms.  
* **Ingestion Webhook:** A lightweight Cloud Function or Google Apps Script is triggered via HTTP/webhook upon form completion.  
* **Markdown Formatting:** The service formats the form submission data into a standardized Markdown file (`.md`) or text payload.  
* **GCS Storage:** The resulting Markdown file is uploaded to a dedicated Google Cloud Storage (GCS) intake bucket (e.g., `gs://intake-ideas-bucket/raw/`).

---

## 2\. Event Dispatch & Router Cloud Run Container (Service 1\)

* **Eventarc Trigger:** An Eventarc trigger listens for `storage.objects.v1.finalized` events on the GCS bucket and immediately invokes the **Router Cloud Run Container**.  
* **Router Cloud Run Service (Container 1):**  
  * Hosts a lightweight microservice (FastAPI/Flask) responsible for initial request parsing and categorization.  
  * **Input Sanitization:** Uses **Model Armor** to validate and sanitize incoming Markdown text before passing it to downstream agents, mitigating indirect prompt injection attempts.  
  * **Intake Categorization:** Invokes **Gemini 2.5 Flash** to analyze the submission metadata and categorize the intake request (e.g., Security & Compliance, CSA Architecture, Supply Chain SOP, Technical Audit).  
  * **Idempotency Gate:** Checks a fast cache (e.g., Firestore) using the GCS file hash to prevent duplicate processing from Eventarc retries.

---

## 3\. Traffic Smoothing via Cloud Tasks Throttled Queue

* **Queue Placement:** Instead of invoking workers directly, the Router Service enqueues an HTTP task into a **Google Cloud Tasks Queue**.  
* **Traffic Control & Rate Limiting:**  
  * Configured with strict dispatch rates (`max_dispatches_per_second`) and concurrency limits (`max_concurrent_tasks`).  
  * Smooths out traffic spikes from bulk form submissions, preventing `429 Resource Exhausted` quota errors on Vertex AI API calls.  
* **Targeted Dispatch:** Routes the HTTP payload directly to the appropriate endpoint on the downstream Worker Cloud Run service based on the assigned category.

---

## 4\. Worker Cloud Run Container (Service 2\)

* **Worker Cloud Run Service (Container 2):**  
  * Hosts the execution logic for all specialized Gem worker agents within a single container using dedicated HTTP routes (e.g., `/worker/category1`, `/worker/category2`, `/worker/category3`).  
  * Operates statelessly, scaling horizontally from 0 to *N* instances based on queue volume.  
  * Configured with an extended request timeout (10–15 minutes) to accommodate deep reasoning and RAG lookups without HTTP disconnects.

---

## 5\. Worker Execution & Gem System Instructions

* **System Prompt Injection:** The worker code injects the specific Gem system prompt directly into the `system_instruction` parameter of the Vertex AI Gemini API call (`google-genai` SDK).  
* **Gem Framework Lock:** System instructions enforce core personas, anti-hijack gatekeeper rules, 6-system-plane mappings, and deterministic scoring algorithms (e.g., severity-weighted 0.0–10.0 scoring math or metric checkpoint averages).  
* **Model Selection:** Uses **Gemini 2.5 Flash** as the default engine for evaluation and recommendations to minimize latency and token costs.

---

## 6\. Dynamic RAG Retrieval via Vertex AI Search Data Stores

* **Decoupled Knowledge Bases:** Static reference documents (CISO Policies, SCM Mapping SOPs, Architectural Guidelines) are removed from system prompts and hosted inside **Vertex AI Search Data Stores**.  
* **On-Demand Context Querying:** Once a worker agent receives an intake task, it dynamically queries its corresponding Data Store via internal RAG.  
* **Retrieval Guardrails:** Strict boundary caps (`top_k=3` or `top_k=5`) and chunk limits are enforced during search retrieval to minimize execution latency and context overhead.

---

## 7\. Structured JSON Output via Pydantic API

* **Schema Contract:** Each worker defines a Pydantic model (`SecurityAuditResult(BaseModel)`) specifying required fields, data types, and field descriptions.  
* **Constrained Generation:**  
  * The worker passes the Pydantic class to Vertex AI via `response_mime_type="application/json"` and `response_schema=SecurityAuditResult`.  
  * Gemini uses token-level constrained decoding at runtime to guarantee 100% schema-compliant JSON generation.  
* **SDK Deserialization:** The `google-genai` SDK natively parses and validates the response, making the strongly typed Python object accessible via `response.parsed`.

---

## 8\. Database Ingestion & Audit Persistence

* **BigQuery Storage Write API:** The worker calls `.model_dump()` on the validated Pydantic object and streams the clean dictionary directly into BigQuery using the high-throughput BigQuery Storage Write API.  
* **Analytics & Human-in-the-Loop:**  
  * Structured numerical metrics (scores, compliance flags, risk categories) populate relational BigQuery tables for executive dashboards.  
  * Human-readable markdown reports (generated as string fields within the JSON schema) are written to GCS or database tables for frontend UI display and automated submitter notification emails.

