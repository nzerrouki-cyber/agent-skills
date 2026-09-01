# Skill Lifecycle: Conception \-\> Production

This document describes the skill lifecycle of each skill that will be stored in the Skill bank. This way, the Discovery Agent will be able to retrieve the appropriate skill file and route it to the worker pod.

---

1\. Skill Specification

Every skill will need to start with a specific engineering specification. These include:

* **Archetype Alignment:** Classify the target skill into one of three primary archetypes during intake:  
  * **Archetype A (Evaluator/Gatekeeper):** Audits artifacts against policy baselines and calculates deterministic scores (e.g., CISO Risk Audits, SCM Map Reviews).  
  * **Archetype B (Transformer/Utility):** Converts or restructures complex data streams into rigid schema outputs (e.g., Markdown-to-JSON formatting, dataset normalization).  
  * **Archetype C (Creator/Synthesizer):** Interactively guides users or generates publication-ready operational documents.  
* **Standard CDS Prompt Framework:** Each skill must adhere to the prompt framework that will be standardized across each skill.

---

2\. Automated Skill Creation (Draft Stage)

* **Creation:** Users can leverage the **Gem Creator Agent** to interactively author and refine the prompt instructions or submit their new skills. These skills will first be added to `gs://enterprise-skillbank/drafts/<skill_id>.md.`  
* **YAML Frontmatter Injection:** A standard YAML template with necessary metadata needs to be appended at the top of the skill’s markdown file, as an example:

  {

    "skill\_id": "SKILL\_SCM\_REVIEW",

    "active\_version": "1.2.0",

    "gcs\_uri": "gs://enterprise-skill-bank/production/SKILL\_SCM\_REVIEW.md",

    "generation\_id": "1700000000000000",

    "target\_datastore\_id": "scm-sop-ds",

    "status": "ACTIVE"

  }

* **Draft Storage:** The Gem Creator service account writes the finalized Markdown file directly to the staging bucket:  `gs://enterprise-skillbank/drafts/<skill_id><version>.md`


---

3\. Automated Skill Validation 

When a skill is first added to `gs://enterprise-skillbank/drafts/<skill_id>.md`, an event must be triggered via an **eventarc trigger**. This will trigger the Skill Validation Agent to validate that markdown file.

---

4\. Promoting Skills & Version Control

* **Human-in-the-Loop (HITL) Sign-Off:** The system can send a notification so the user validates the result of the validation conducted by the Skill Validation Agent.   
* **Immutable Promotion:** Upon human approval, a GCP Cloud Build pipeline executes the promotion script:  
  * Copies the skill file from gs://enterprise-skill-bank/drafts/ to gs://enterprise-skill-bank/production/.  
  * Captures the unique **GCS Generation ID** (e.g., gs://enterprise-skill-bank/production/SKILL\_SCM\_REVIEW.md\#1700000000000000).  
* **Registry Index Update:** When added to the production skill bank, the pipeline writes an entry to a Skill Registry Index hosted on a **Firestore database**. This way, the Discovery Agent can retrieve the skill\_id at runtime very quickly.

---

5\. Runtime Execution, Caching & Observability 

* **Read-Only IAM Isolation:** Worker Pods on GKE authenticate via Workload Identity using a dedicated Kubernetes Service Account (KSA) bound to an IAM account with read-only permissions (roles/storage.objectViewer) restricted exclusively to the /production/ GCS path.  
* **In-Memory Worker Caching (Redis):**  
  * To avoid GCS read latency on every worker invocation, GKE Worker Pods cache validated Markdown skill files in an internal Redis store keyed by skill\_id:generation\_id.  
  * When a new version is promoted, a Pub/Sub cache invalidation event clears the stale Redis key across all worker pods instantly.  
* **Telemetry & Audit Persistence:** Every worker execution logs the exact skill\_id and generation\_id alongside the Pydantic-parsed JSON output to BigQuery via the Storage Write API, guaranteeing 100% auditability for regulatory compliance.

