# **SKILL Lifecycle (AgentOps)**

## **1\. Lifecycle Overview & Control Plane Pattern**

The **SKILL Lifecycle** defines the end-to-end process of conceiving, authoring, validating, deploying, and executing operational skills within the multi-agent ecosystem.

All lifecycle actions are governed by the **Orchestrator Agent (Supervisor)**, which acts as the centralized control plane routing requests via tool calls to specialized micro-agents (`GemCreatorAgent`, `ValidationAgent`, `DiscoveryAgent`). System prompts and skill payloads are transferred asynchronously using lightweight Google Cloud Storage (GCS) URIs to maintain minimal latency and keep Orchestrator context lean.

---

## **2\. Skill Authoring & Modifications**

```
[User] ---> (Orchestrator Agent)
                  |
                  |--- (Tool Call: GemCreatorService)
                  v
         [GemCreatorAgent] <===> (GCS Staging: gs://skill-bank/staging/)
                  |
                  |--- (Returns Staging GCS URI)
                  v
         (Orchestrator Agent)
                  |
                  |--- (Tool Call: ValidationService with GCS URI)
                  v
         [ValidationAgent] <===> (GCS Production: gs://skill-bank/production/)
```

### **Pathway A: Initial Skill Creation Flow (New Gem)**

1. **User Request & Intent Classification:** The user submits a prompt or draft attachment to create a new skill. The Orchestrator Agent classifies the intent and invokes the `GemCreatorService` tool call.  
2. **Draft Synthesis:** The `GemCreatorAgent` processes the request, synthesizes the system prompt, taxonomy, and output rules according to target archetype templates.  
3. **Staging Persistence:** The `GemCreatorAgent` writes the complete candidate Markdown file to a staging path (`gs://skill-bank/staging/new_skill_candidate.md`) and returns the staging GCS URI to the Orchestrator.  
4. **Validation Routing:** The Orchestrator Agent receives the GCS URI pointer and immediately routes it to the `ValidationService` (`ValidationAgent`) via a secondary tool call.

```

[User] ---> (Orchestrator Agent)
                  |
                  |--- 1. Tool Call: GemCreatorService(baseline_gcs_uri)
                  v
         [GemCreatorAgent] <=== Fetches Baseline === (GCS Production: gs://skill-bank/production/)
                  |
                  |--- 2. Writes Candidate Draft
                  v
         (GCS Staging: gs://skill-bank/staging/)
                  |
                  |--- 3. Returns Candidate & Baseline GCS URIs
                  v
         (Orchestrator Agent)
                  |
                  |--- 4. Tool Call: ValidationService(candidate_uri, baseline_uri)
                  v
         [ValidationAgent] --- (Archives Active Prompt) ---> (GCS Archive: gs://skill-bank/archive/)
                  |
                  |--- 5. Promotes Candidate & Invalidates Discovery Cache
                  v
         (GCS Production: gs://skill-bank/production/)

```

### **Pathway B: Skill Refinement & Modification Flow (Existing Gem)**

1. **User Request & Target Resolution:** The user requests an update or bug fix for an existing skill (e.g., *"Update the Intake Validation skill rules"*).  
2. **Context-Lean Handoff:** The Orchestrator Agent resolves the skill identifier against the Skill Registry to locate its production GCS path (`gs://skill-bank/production/skills/{skill_id}.md`). The Orchestrator passes this URI string directly in the tool call to `GemCreatorService` without loading the raw prompt text into its own context window.  
3. **Direct Prompt Retrieval:** `GemCreatorAgent` fetches the active system prompt directly from the production GCS URI using standard cloud SDKs, loads it into its internal working memory, and applies the requested modifications.  
4. **Delta Staging:** `GemCreatorAgent` writes the updated candidate prompt to the staging bucket (`gs://skill-bank/staging/{skill_id}_candidate.md`) and returns the new candidate GCS URI (along with the baseline URI reference) to the Orchestrator.  
5. **Validation Routing:** The Orchestrator Agent receives the staging and baseline GCS URIs and triggers a tool call to the `ValidationService` (`ValidationAgent`).

---

## **3\. Automated Validation & Quality Gate**

The `ValidationAgent` acts as an isolated staging gate before any prompt can be published to the active repository.

### **Evaluation Suite Mechanics**

Upon receiving a staging GCS URI from the Orchestrator, the `ValidationAgent` reads the file directly from storage and executes a multi-tiered audit:

* **Structural & Taxonomy Format Check:** Validates Markdown completeness, token boundaries, and mandatory section headers (Persona, Directives, Archetype Rules).  
* **Prompt Defense & Anti-Hijack Audit:** Verifies that mandatory system isolation rules, negative prohibitions, and injection defenses are present and unaltered.  
* **Synthetic Execution Sandbox:** Generates synthetic edge-case inputs relevant to the skill's domain and executes the prompt in a sandboxed Vertex AI environment to confirm strict JSON/Pydantic or structured output adherence.  
* **Historical Regression Testing (Refinement Pathway Only):** Runs the candidate prompt against a benchmark suite of historical inputs from the baseline prompt to guarantee zero functional regressions.

---

## **4\. Production Promotion, Cache Invalidation & Deployment**

### **Pass / Fail Branching**

* **On Validation Failure (`REJECTED`):**  
  1. The `ValidationAgent` generates a structured diagnostic error log detailing the specific failure (e.g., schema mismatch, missing defense directive, regression failure).  
  2. The failure payload is returned to the Orchestrator Agent.  
  3. The Orchestrator automatically routes the error log back to `GemCreatorAgent` to initiate an automated remediation retry loop. Production prompts remain active and untouched.  
* **On Validation Success (`APPROVED`):**  
  1. **Archival:** For refined gems, the `ValidationAgent` copies the existing production file to an immutable archive directory (`gs://skill-bank/archive/{skill_id}_v{timestamp}.md`).  
  2. **Production Promotion:** The candidate file is promoted from staging to the canonical production path (`gs://skill-bank/production/skills/{skill_id}.md`).  
  3. **Data Store Re-indexing:** The `ValidationAgent` triggers an incremental index update on the Vertex AI Search Data Stores so the new version is immediately indexable.  
  4. **Cache Invalidation:** The `ValidationAgent` broadcasts an invalidation event for any active `DiscoveryAgent` semantic cache or short-term memory keys tied to `{skill_id}`.  
  5. **Orchestrator Notification:** A success status with the canonical production GCS URI is returned to the Orchestrator Agent to finalize the conversation with the user.

---

## **5\. Runtime Discovery & Execution Phase**

Once deployed, production skills follow the low-latency execution pathway:

1. **Intake-to-Discovery State Passing:** The `IntakeAgent` extracts innovation ideas, saves the structured output to GCS, and returns a payload GCS URI to the Orchestrator.  
2. **Skill Lookup:** The Orchestrator invokes `DiscoveryService` with the payload URI. The `DiscoveryAgent` fetches the payload from GCS, queries Vertex AI Search Data Stores, and locates the target production skill (`gs://skill-bank/production/skills/{skill_id}.md`).  
3. **Semantic Caching & Memory Commit:** The `DiscoveryAgent` fetches the skill prompt, executes it directly (bypassing legacy worker containers), and commits the skill parameters to its short-term session memory. Subsequent interactions in the same session bypass vector lookups for near-instantaneous Time to Last Syllable (TLS) performance.


