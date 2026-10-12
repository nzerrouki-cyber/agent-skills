# Claude Code Skills & Non-Functional Requirements (NFR) Knowledge Base
> **Complementary Guide To:** `agent-rules-knowledge-base.md` (`ciembor/agent-rules-books`)  
> **Ecosystem:** Anthropic Claude Code, Model Context Protocol (MCP), Agent Skills Open Standard  
> **Focus:** Software Architecture Workflows, Non-Functional Requirements (Security, Scalability, Latency, Observability, Reliability), & Skill Authoring Best Practices  
> **Verification Status:** Fact-Checked via Chain-of-Verification (CoVE) for Zero Conflicts with Classic Book Rules

---

## 1. Executive Summary & Architecture Overview

While `agent-rules-knowledge-base.md` encapsulates timeless programming principles from foundational books (*Clean Code*, *DDD*, *DDIA*, *Release It!*), this knowledge base curates the top **Claude Code skills** and **Non-Functional Requirement (NFR) engineering practices** from the official Anthropic ecosystem and leading community skill marketplaces.

### The Two-Pillar Synergy
1. **Book Rules Baseline (`agent-rules-knowledge-base.md`):** Defines *what clean code, deep abstractions, and solid architecture look like* (declarative standards).
2. **Claude Skills & NFR Harness (`claude-skills-nfr-knowledge-base.md`):** Provides *procedural execution workflows, automated verification gates, performance optimizations, and security scanning tools* (actionable execution).

Together, they form a complete, production-grade engineering operating model for AI coding agents.

---

## 2. Top Architectural & Development Process Skills

These top-tier community skills govern *how* AI agents approach software development tasks, moving them from naive "vibe coding" to disciplined, senior-engineer-level execution.

### 2.1 Superpowers (Software Development Methodology)
* **GitHub Community Rank:** #1 Most Adopted Skill Framework (243,000+ stars)
* **Core Directives for AI Agents:**
  * **Plan-First Architecture:** Never jump straight to writing implementation code. Always generate a structured design spec and component breakdown before editing files.
  * **Strict Test-Driven Development (TDD):** Execute the RED-GREEN-REFACTOR cycle. Write failing tests first, verify the failure mode, implement minimal code to pass, and refactor.
  * **Systematic Root-Cause Debugging:** When encountering errors, perform hypothesis-driven debugging. Never guess or apply random patches without isolating root causes.
  * **Subagent Delegation:** Delegate sub-tasks (e.g., test writing, linting, documentation) to dedicated sub-agents to preserve primary context window depth.
  * **Verification Before Completion:** Execute automated test suites, type checkers, and linter pipelines before marking any task as complete.

### 2.2 Handoff & Session Compression (`HANDOFF.md`)
* **Core Directives for AI Agents:**
  * **Context Window Stewardship:** When a session reaches high context consumption, generate a structured `HANDOFF.md` document capturing current task state, completed steps, uncommitted changes, open architectural decisions, and next actions.
  * **Fresh Session Continuation:** Allow a newly initialized agent to instantly resume work by reading `HANDOFF.md` without re-parsing hundreds of thousands of historical conversation tokens.

### 2.3 Grill Me (Architectural Alignment & Requirement Discovery)
* **Core Directives for AI Agents:**
  * **Interactive Requirement Extraction:** When given a broad or ambiguous task, pause code execution and interview the user with targeted questions.
  * **NFR & Edge-Case Probing:** Explicitly clarify performance budgets, security boundaries, failure recovery strategies, and domain constraints prior to drafting technical specifications.

### 2.4 Fullstack Reverse Engineer & C4 Mapping (Phoenix Skills)
* **Core Directives for AI Agents:**
  * **Systematic Codebase Exploration:** When entering an unfamiliar codebase, construct a multi-level C4 architectural model (Context, Container, Component, Code).
  * **Contract & Data Flow Mapping:** Document runtime execution paths, database interaction patterns, external API dependencies, and module boundaries into a reference knowledge layer.

---

## 3. Non-Functional Requirements (NFR) Skills Library

Non-functional requirements dictate how software behaves under real-world operational strain. The following skills inject specialized domain expertise directly into the agentic workflow.

### 3.1 Security & Vulnerability Defense (Security NFR)
* **Representative Skills:** *Trail of Bits Security Audit*, *Phoenix SAST Rules & CTI*, *Snyk Security Assistant*
* **Core Directives for AI Agents:**
  * **Automated SAST Integration:** Run static analysis scanners (Semgrep, CodeQL, Opengrep) against code changes before committing.
  * **OWASP Top 10 Mitigation:** Explicitly screen for SQL injection, cross-site scripting (XSS), broken access control, insecure deserialization, and hardcoded secrets.
  * **STRIDE Threat Modeling:** During architecture design, systematically analyze threats across **S**poofing, **T**ampering, **R**epudiation, **I**nformation Disclosure, **D**enial of Service, and **E**levation of Privilege.
  * **Input Sanitization Boundaries:** Treat all data crossing external boundaries (HTTP requests, CLI args, file uploads) as untrusted; enforce strong schema validation.

### 3.2 Scalability & Distributed Database Optimization (Scalability NFR)
* **Representative Skills:** *PlanetScale Schema Optimizer*, *DDIA Data Pipeline Rules*
* **Core Directives for AI Agents:**
  * **Non-Blocking Schema Evolution:** Design database migrations using online DDL patterns to prevent lock escalation and zero-downtime deployments.
  * **Index & Query Optimization:** Analyze query execution plans (`EXPLAIN`) to eliminate full table scans, optimize composite indexes, and prevent N+1 query patterns.
  * **Partitioning & Connection Pooling:** Implement horizontal sharding keys, connection pool limits, and read-replica routing for high-throughput database layers.

### 3.3 Latency & Performance Optimization (Performance NFR)
* **Representative Skills:** *Vercel React & Next.js Performance Rules (57 Rules)*, *AWS SageMaker AI Inference Optimization (`aws-ai-ml`)*
* **Core Directives for AI Agents:**
  * **UI & Rendering Efficiency:** Eliminate unnecessary re-renders, enforce component memoization, leverage dynamic imports/lazy loading, and optimize bundle sizes.
  * **Async Non-Blocking Execution:** Offload compute-intensive or IO-bound operations to asynchronous background queues and non-blocking event loops.
  * **Inference & Profiling:** Micro-benchmark service endpoints, measure p95/p99 latency distributions, optimize payload compression, and implement response caching.

### 3.4 Reliability, High Availability & Readiness Gates (Reliability NFR)
* **Representative Skills:** *Phoenix Readiness Review Gates*, *Release It! Stability Patterns*
* **Core Directives for AI Agents:**
  * **Plan Readiness Review:** Adversarially audit design specs prior to coding. Answer: *"Could another senior engineer build this without inventing requirements or API contracts?"*
  * **Production Readiness Review:** Adversarially audit pull requests before deployment. Answer: *"Is this feature wired, fully tested, and safe to deploy?"*
  * **Deterministic 3-State Verdicts:** Enforce strict verification verdicts (`VERIFIED`, `GAP`, `UNVERIFIABLE`). Refuse to emit fake percentage scores; require proof of execution for every assertion.
  * **Cascading Failure Protection:** Wrap external HTTP/gRPC calls with circuit breakers, configurable timeouts, bulkheads, and exponential backoff retry policies.

### 3.5 Maintainability, Observability & Testability (Maintainability NFR)
* **Representative Skills:** *PICT Pairwise Testing (`pypict`)*, *Playwright Automation*, *OpenTelemetry Observability*
* **Core Directives for AI Agents:**
  * **Combinatorial Test Optimization:** Utilize Pairwise Independent Combinatorial Testing (PICT) to generate high-coverage test suites with minimal test cases.
  * **Automated End-to-End Verification:** Run headless browser automation scripts (Playwright) to validate end-to-end user flows against live local builds.
  * **Structured Observability:** Inject OpenTelemetry tracing spans, structured JSON logging with correlation IDs, and operational metrics (latency counters, error rates) into core business handlers.

---

## 4. Anthropic Official Skill Authoring Architecture & Best Practices

To ensure agent skills run reliably without polluting context windows or failing silently, skills must adhere to Anthropic's official skill design principles.

### 4.1 Progressive Disclosure Discipline (3-Level Architecture)
Skills use a 3-tiered loading pattern to conserve the context window budget:
* **Level 1 (Metadata Preload):** Only the skill's `name` and `description` are loaded at session startup (~20–50 tokens). Descriptions must act as sharp discovery triggers.
* **Level 2 (`SKILL.md` File):** The primary instruction file is loaded *only* when Claude determines the skill is relevant to the user's active task (<500 tokens recommended).
* **Level 3 (Sub-files & Scripts):** Supplementary reference docs or executable scripts in the skill folder are read on-demand during execution.

### 4.2 The 100-Line Contents List Rule
Large language models frequently run partial reads (skimming the first ~100 lines) when opening context files.
* **Rule:** Any reference document or rule set exceeding **100 lines** MUST include a **Table of Contents (ToC)** at the top. This ensures the model maps the full structure even during initial partial reads.

### 4.3 Calibrated Degrees of Freedom
Skill authors must tailor the precision of instructions based on task risk:
* **High Freedom:** Exploratory architecture, UI design concepts, and creative brainstorming. Give high-level goals and allow agent judgment.
* **Medium Freedom:** Standard feature engineering, REST API creation, and component building. Provide structured templates and guidelines.
* **Low Freedom (Scripted):** High-risk operations (database migrations, payments, infrastructure destruction, deployment commands). Provide explicit step-by-step CLI commands or shell scripts.

### 4.4 Dependency Self-Containment Rule
Skills must never assume external tools or runtime packages are pre-installed.
* **Rule:** Every skill executing CLI tools (e.g., `semgrep`, `playwright`, `pypict`) must include an explicit verification step that checks binary availability and installs dependencies automatically if missing.

### 4.5 Self-Verification Checklists & Error Recovery
Multi-step skills must include explicit self-verification loops.
* **Rule:** Pair checklists with validation steps that send the agent back to earlier phases if verification fails (e.g., re-running tests after refactoring or validating API schema types prior to commit).

---

## 5. Chain-of-Verification (CoVE) Audit Matrix

To guarantee that the skills and NFR rules in this document do not contradict the 14 classic programming books in `agent-rules-knowledge-base.md`, a rigorous Chain-of-Verification audit was conducted.

| Skill / NFR Module | Primary Focus | Related Book in `agent-rules-books` | CoVE Verification Verdict & Synergy Analysis |
| :--- | :--- | :--- | :--- |
| **Superpowers (TDD & Planning)** | Plan-first spec, RED-GREEN-REFACTOR, debugging | *Clean Code*, *Refactoring*, *Pragmatic Programmer* | **VERIFIED: Zero Conflict.** Reinforces Clean Code's AAA test requirement and Fowler's step-by-step refactoring loop. |
| **Grill Me (Requirements)** | Pre-code developer interviewing | *Code Complete*, *DDD Distilled* | **VERIFIED: Zero Conflict.** Directly supports McConnell's requirement clarification and Evans' Ubiquitous Language discovery. |
| **Fullstack Reverse Engineer** | Codebase mapping & C4 diagrams | *Working Effectively with Legacy Code* | **VERIFIED: Zero Conflict.** Systematically locates seams and dependencies required for Feathers' characterization testing. |
| **Trail of Bits & Phoenix SAST** | OWASP Top 10, CodeQL, threat modeling | *Code Complete* (Defensive Programming) | **VERIFIED: Zero Conflict.** Extends McConnell's defensive input checks into automated CI/CD pipeline scanning. |
| **PlanetScale Schema Optimizer** | Online DDL, indexing, non-blocking migrations | *Designing Data-Intensive Applications*, *PPoEAA* | **VERIFIED: Zero Conflict.** Implements Kleppmann's schema evolution and Fowler's Repository isolation without touching domain logic. |
| **Vercel React Performance** | 57 frontend performance & SSR rules | *A Philosophy of Software Design* | **VERIFIED: Zero Conflict.** Keeps performance optimizations contained within presentation layers, preserving deep module abstractions. |
| **Readiness Review Gates** | Plan and Production readiness 3-state reviews | *Release It!*, *Refactoring* | **VERIFIED: Zero Conflict.** Enforces Nygard's production stability requirements through pre-deploy verification checks. |
| **Pairwise Testing (`pypict`)** | Combinatorial branch testing | *Clean Code*, *Code Complete* | **VERIFIED: Zero Conflict.** Maximizes test coverage efficiency while upholding Martin's unit testing discipline. |
| **OpenTelemetry Observability** | Tracing context, structured logging, metrics | *Release It!* | **VERIFIED: Zero Conflict.** Directly fulfills Nygard's operational readiness and system health instrumentation rules. |

---

## 6. Summary Matrix of Claude Code Skills

| Skill Category | Skill Name | Primary Objective | Key Tool / Technology |
| :--- | :--- | :--- | :--- |
| **Architecture & Workflow** | `superpowers` | TDD, plan-first design, subagent development | Git worktrees, test runners |
| **Architecture & Workflow** | `handoff` | Session compression into `HANDOFF.md` | Markdown state tracking |
| **Architecture & Workflow** | `grill-me` | Deep requirement & NFR discovery interview | Interactive Q&A loop |
| **Architecture & Workflow** | `fullstack-reverse-engineer` | C4 architectural mapping of legacy repos | Dependency analysis, C4 |
| **Security NFR** | `phoenix-security-review` | OWASP auditing, threat modeling (STRIDE) | CodeQL, Semgrep, SAST |
| **Security NFR** | `trail-of-bits-security` | Vulnerability detection & dependency auditing | Static analysis engines |
| **Scalability NFR** | `planetscale-schema-opt` | Non-blocking schema migrations & indexing | SQL execution plans |
| **Performance NFR** | `vercel-react-best-practices` | 57 React/Next.js rendering & bundle rules | AST linting, SSR |
| **Performance NFR** | `aws-ai-ml` | SageMaker inference & latency optimization | Micro-benchmarking |
| **Reliability NFR** | `plan-readiness-review` | Adversarial design spec audit (READY / NOT READY) | Verification gates |
| **Reliability NFR** | `production-readiness-review` | Pre-deploy code audit (SHIP / NO-SHIP) | Verification gates |
| **Maintainability NFR** | `pypict-testing` | Pairwise combinatorial test suite generation | PICT engine |
| **Maintainability NFR** | `webapp-playwright-testing` | End-to-end browser automation testing | Playwright headless browser |

---

## 7. Skill Installation & Management Guide

### Installing Skills via Claude Code CLI (`/plugin`)
Claude Code supports direct plugin and marketplace management:

```bash
# Add an official or community marketplace repository
/plugin marketplace add Security-Phoenix-demo/security-skills-claude-code

# Install specific standalone skills
/plugin install phoenix-security-review@phoenix-security
/plugin install phoenix-readiness-reviews@phoenix-security

# Install community skills via Agent Skills CLI
npx skills add coleam00/skills --skill superpowers
```

### Local Project Skill Registration (`.claude/skills/`)
To register custom project-level skills:
1. Create a directory `.claude/skills/<skill-name>/` in your repository root.
2. Add a `SKILL.md` file following Anthropic's progressive disclosure guidelines.
3. Include helper scripts or resource files in the same folder.
4. Claude Code will automatically detect and register the skill upon startup.


---

## 6. Granular Decomposition Standards for NFR Execution & Agent Tools

Non-functional requirement (NFR) implementations—such as security auditing, latency optimization, and telemetry logging—must follow strict functional decomposition rules to prevent bloated, unmaintainable agent code.

### 6.1 Relegation of NFR Sub-Systems
* **Security & Auth:** Relegate payload sanitization to `sanitizeUserText(...)` and token validation to `validateAuthorizationToken(...)`.
* **Telemetry & Observability:** Relegate chat session history persistence to `persistChatSessionHistory(...)` and metric collection to `recordLatencyMetric(...)`.
* **Latency & Resilience:** Relegate external tool invocations to `invokeAgentToolCall(...)` with embedded timeouts, retry strategies, and circuit breakers.

### 6.2 Updated CoVE NFR Alignment Matrix

| NFR Domain | Target Skill / Practice | Decomposition Standard | CoVE Status |
| :--- | :--- | :--- | :---: |
| **Security** | SAST & STRIDE Threat Auditing | Relegate input parsing to `ingestUserRequest(...)` | **Verified** |
| **Latency** | Vercel Rendering & Database Pooling | Relegate DB queries to `invokeDatabaseQueryTool(...)` | **Verified** |
| **Observability** | OpenTelemetry & Structured Logging | Relegate storage to `persistChatSessionHistory(...)` | **Verified** |
| **Reliability** | Plan Readiness & Production Gates | Relegate sub-agent routing to `receiveAgentRequest(...)` | **Verified** |
