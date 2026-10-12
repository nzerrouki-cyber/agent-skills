# Granular Functional Decomposition, Pseudocode, Function Naming & OOP Architecture Knowledge Base
> **Target AI Assistants:** OpenAI Codex, Cursor, Anthropic Claude Code, GitHub Copilot  
> **Core Focus:** Granular System Decomposition, Relegation of Tool Calls, Conversational Chat Flow Decomposition, `camelCase` Naming Conventions, Pseudocode Standards, Object-Oriented Principles, Abstraction  
> **Verification Status:** Chain-of-Verification (CoVE) Audited  

---

## 1. Executive Summary & Core Philosophy

This knowledge base provides a concrete, deterministic rule set governing **granular functional decomposition**, **tool-call delegation**, **conversational pipeline architecture**, **pseudocode generation**, **function naming conventions**, and **object-oriented design (OOP)**.

While high-level architectural frameworks (*Clean Architecture*, *Domain-Driven Design*) establish structural boundaries, human developers struggle when complex workflows—such as multi-agent orchestration or conversational chat state management—are collapsed into monolithic routines. 

To ensure codebases are immediately digestible, maintainable, and verifiable by human developers, **every service, feature, integration, and tool invocation MUST be relegated to its own distinct, single-responsibility function**.

---

## 2. System, Feature & Integration Decomposition via Granular Functions

### 2.1 The Core Law of Granular Functional Decomposition
Complex software systems must be broken down into hierarchical, single-purpose functions. No single function should attempt to execute end-to-end orchestration, state ingestion, tool invocation, and persistence simultaneously.

1. **Granular Problem Breakdown:** Divide macro-features into large sub-problems, medium workflows, and atomic low-level functions.
2. **Relegation of External Tool Calls:** Every external integration, API call, database query, or tool invocation MUST be housed in its own dedicated, named function.
3. **Traceable Context Hand-off:** Pass explicit inputs and return typed outputs or DTOs between functions rather than mutating hidden global state.
4. **Human Digestibility Standard:** A developer reading any function should be able to grasp its entire operation within 10 seconds without scrolling or context-switching.

---

### 2.2 Orchestrator Agent & Tool Call Relegation Architecture

In agentic and multi-agent architectures, an **Orchestrator Agent** evaluates user intent and delegates tasks to specialized sub-agents or tools. 

#### Structural Rule for Tool Calls:
* **NEVER** inline tool calls directly inside a massive `switch` or `if/else` orchestrator block.
* **ALWAYS** relegate each tool call to a specialized, camelCase function (e.g., `invokeSkillRetrievalTool`, `invokeDatabaseQueryTool`, `invokeNotificationTool`).

```
[User Request] 
      │
      ▼
ingestUserRequest(...) ────────► [Request DTO]
                                      │
                                      ▼
                           orchestrateAgentTask(...)
                                      │
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
   invokeSkillRetrievalTool() invokeDatabaseQueryTool() invokeNotificationTool()
              │                       │                       │
              ▼                       ▼                       ▼
   receiveAgentRequest(...)   receiveAgentRequest(...)   receiveAgentRequest(...)
```

---

### 2.3 Conversational Chat Session Pipeline Decomposition

Managing interactive, multi-turn conversational chat sessions requires strict decomposition across ingestion, orchestrator routing, agent reception, user input handling, and storage persistence.

#### Required Functional Pipeline Steps:
1. `ingestUserRequest(rawRequestPayload)`: Parses, validates, and normalizes the initial incoming request payload from the client/UI.
2. `invokeAgentToolCall(toolIdentifier, toolParameters)`: Encapsulates the execution of a specific tool call by the orchestrator agent.
3. `receiveAgentRequest(agentIdentifier, requestDto)`: Handles reception and execution setup within the targeted sub-agent or service.
4. `ingestUserInput(sessionId, inputMessagePayload)`: Ingests subsequent conversational user turns in an ongoing session.
5. `receiveAgentInput(agentContext, normalizedInput)`: Delivers the user's input turn to the active agent model or cognitive loop.
6. `persistChatSessionHistory(sessionId, chatTurnRecord)`: Routes and persists chat history records to a database, vector store, or persistent storage.

---

### 2.4 End-to-End Pseudocode Example: Orchestrator & Conversational Chat Flow

Below is the complete, modern pseudocode illustrating how multi-agent interaction and conversational chat history are fully decomposed into digestible, single-responsibility functions.

```text
// ============================================================================
// SECTION A: USER REQUEST INGESTION & ORCHESTRATION PIPELINE
// ============================================================================

FUNCTION ingestUserRequest(rawRequestPayload)
    DISPLAY "ingest user request from client payload"
    
    // Step 1: Validate payload schema
    IF NOT validateRequestPayloadSchema(rawRequestPayload) THEN
        RETURN raiseErrorResponse("INVALID_PAYLOAD_FORMAT")
    END IF

    // Step 2: Extract normalized request DTO
    requestDto = extractRequestDataTransferObject(rawRequestPayload)
    
    // Step 3: Forward to orchestrator agent
    orchestrationResult = orchestrateAgentTask(requestDto)
    RETURN orchestrationResult
END FUNCTION


FUNCTION orchestrateAgentTask(requestDto)
    DISPLAY "evaluate user intent and route to appropriate tools or sub-agents"
    
    // Step 1: Retrieve session context
    sessionContext = fetchSessionContext(requestDto.sessionId)

    // Step 2: Determine execution path
    IF requestDto.targetCapability EQUALS "SKILL_RETRIEVAL" THEN
        toolResponse = invokeSkillRetrievalTool(requestDto.userId, requestDto.filterCriteria)
        agentResponse = receiveAgentRequest("SkillManagerAgent", toolResponse)
    ELSE IF requestDto.targetCapability EQUALS "DATABASE_QUERY" THEN
        toolResponse = invokeDatabaseQueryTool(requestDto.queryParameters)
        agentResponse = receiveAgentRequest("DataQueryAgent", toolResponse)
    ELSE
        agentResponse = executeDefaultConversationLoop(requestDto, sessionContext)
    END IF

    RETURN agentResponse
END FUNCTION


FUNCTION invokeSkillRetrievalTool(userId, filterCriteria)
    DISPLAY "retrieve all skills for user"
    
    // Relegated tool call function
    rawSkillsData = invokeExternalTool("skill_retriever_tool", userId, filterCriteria)
    normalizedSkills = formatSkillListResponse(rawSkillsData)
    
    RETURN normalizedSkills
END FUNCTION


FUNCTION invokeDatabaseQueryTool(queryParameters)
    DISPLAY "execute database query tool call"
    
    // Relegated tool call function
    queryResult = invokeExternalTool("database_query_tool", queryParameters)
    RETURN queryResult
END FUNCTION


FUNCTION receiveAgentRequest(agentIdentifier, requestDto)
    DISPLAY "receive and process request for specific sub-agent"
    
    // Step 1: Initialize sub-agent context
    subAgent = initializeSubAgentInstance(agentIdentifier)
    
    // Step 2: Execute sub-agent processing
    executionResult = subAgent.processTask(requestDto)
    
    RETURN executionResult
END FUNCTION


// ============================================================================
// SECTION B: CONVERSATIONAL CHAT SESSION & HISTORY PERSISTENCE PIPELINE
// ============================================================================

FUNCTION ingestUserInput(sessionId, inputMessagePayload)
    DISPLAY "ingest user input message in active conversational session"
    
    // Step 1: Validate session activity
    IF NOT isSessionActive(sessionId) THEN
        RETURN raiseErrorResponse("SESSION_EXPIRED_OR_NOT_FOUND")
    END IF

    // Step 2: Sanitize input content
    sanitizedMessage = sanitizeUserText(inputMessagePayload.text)
    userTurnRecord = buildChatTurnRecord(sessionId, "USER", sanitizedMessage)

    // Step 3: Route to agent receiver
    agentResponseTurn = receiveAgentInput(sessionId, userTurnRecord)

    // Step 4: Persist chat session history
    persistChatSessionHistory(sessionId, userTurnRecord)
    persistChatSessionHistory(sessionId, agentResponseTurn)

    RETURN formatChatResponsePayload(agentResponseTurn)
END FUNCTION


FUNCTION receiveAgentInput(sessionId, userTurnRecord)
    DISPLAY "agent receives user input turn and generates response"
    
    // Step 1: Load conversational context window
    conversationHistory = loadRecentSessionHistory(sessionId, 10)

    // Step 2: Prompt cognitive agent model
    agentOutputText = queryCognitiveModel(conversationHistory, userTurnRecord)

    // Step 3: Construct agent response record
    agentTurnRecord = buildChatTurnRecord(sessionId, "ASSISTANT", agentOutputText)
    
    RETURN agentTurnRecord
END FUNCTION


FUNCTION persistChatSessionHistory(sessionId, chatTurnRecord)
    DISPLAY "route and persist chat turn record to database storage"
    
    // Relegated storage persistence function
    storagePayload = formatStorageRecord(sessionId, chatTurnRecord)
    saveStatus = executeDatabaseInsert("chat_history_table", storagePayload)

    IF NOT saveStatus.isSuccess THEN
        logSystemWarning("Failed to persist chat history turn", sessionId)
    END IF

    RETURN saveStatus
END FUNCTION
```

---

## 3. Modern Senior Software Developer Architectural Principles

To ensure AI coding agents operate at the level of experienced senior staff engineers, the following principles MUST be reflected across all function signatures, pseudocode, and class designs.

### 3.1 Single Level of Abstraction (SLA)
Every function must contain statements operating at the same conceptual depth. 
* **High-Level Orchestrator:** Contains only strategic workflow calls (`ingestUserRequest`, `orchestrateAgentTask`).
* **Mid-Level Business Routine:** Handles domain rules and transformation (`buildChatTurnRecord`, `sanitizeUserText`).
* **Low-Level I/O Operation:** Manages raw data, SQL, or HTTP tool calls (`executeDatabaseInsert`, `invokeExternalTool`).

### 3.2 Command-Query Responsibility Segregation (CQRS) at Function Boundaries
* **Command Functions:** Modify state, perform side-effects, return status/confirmation (`persistChatSessionHistory`, `executeOrderCheckout`).
* **Query Functions:** Pure functions that calculate or retrieve data without mutating system state (`loadRecentSessionHistory`, `getSkillsForUser`).

### 3.3 Explicit DTOs & Contract-First Hand-offs
Never pass untyped primitive blobs or huge implicit dictionaries between decomposed functions. Always wrap cross-function messages into explicit Data Transfer Objects (DTOs) or typed interfaces.

### 3.4 Idempotency & Fault Isolation in Tool Calls
External tool calls are prone to network timeouts or rate limits. Every relegated tool call function must be idempotent or wrapped in defensive retry/circuit-breaker handlers.

### 3.5 Traceable Context & Correlation Tracking
In multi-agent systems, function signatures must explicitly accept correlation IDs or session tokens (e.g., `sessionId`, `traceId`) to ensure end-to-end observability across decomposed calls.

---

## 4. Modern Pseudocode Standards & Integration Expressiveness

### 4.1 Core Rules for Pseudocode Generation
1. **High-Level Intent Over Implementation:** Focus on *what* is being accomplished.
2. **Explicit Natural-Language Action Phrasing:** Use clear, declarative plain-English statements for actions and integrations.
   * **Good:** `"retrieve all skills for user"`
   * **Bad:** `SELECT * FROM skills WHERE user_id = u_id`
3. **Consistent Structural Keywords:** Standardize control flow constructs using UPPERCASE block markers:
   * `IF / ELSE IF / ELSE`
   * `FOR EACH ... IN ...`
   * `WHILE ... DO`
   * `TRY / CATCH`
   * `RETURN`
4. **Tool and Integration Transparency:** State external tool calls explicitly via `DISPLAY` or `invokeExternalTool`.

---

## 5. Function Naming Conventions & camelCase Discipline

Every function or method signature generated by an AI coding agent must convey its exact responsibility directly through its name.

### 5.1 Strict Naming Rules
1. **camelCase Format:** Every function and method name MUST strictly follow `camelCase` formatting (e.g., `getSkill`, `ingestUserRequest`, `persistChatSessionHistory`).
2. **Verb-Noun Structure:** Function names must begin with an explicit action verb followed by the target entity (e.g., `invokeAgentToolCall`, `receiveAgentRequest`).
3. **Self-Explanatory Clarity:** A developer should understand the function's purpose purely from its signature.
4. **Standardized Verb Prefixes:**
   * `get` / `fetch` / `retrieve`: Queries returning data without state modification.
   * `ingest` / `receive` / `parse`: Data intake and validation routines.
   * `invoke` / `execute` / `dispatch`: Triggering external tools, sub-agents, or commands.
   * `persist` / `save` / `store`: Database or state persistence functions.
   * `is` / `has` / `can`: Predicate checks returning booleans.

### 5.2 Functional Reference Matrix

| Architectural Stage | Functional Action | Standard camelCase Function Name |
| :--- | :--- | :--- |
| **Request Intake** | Parse raw payload from user client | `ingestUserRequest(rawRequestPayload)` |
| **Orchestration** | Route request to tools / agents | `orchestrateAgentTask(requestDto)` |
| **Tool Execution** | Retrieve all user skills via tool call | `invokeSkillRetrievalTool(userId, filter)` |
| **Tool Execution** | Execute raw database query tool call | `invokeDatabaseQueryTool(queryParams)` |
| **Agent Reception** | Receive request in sub-agent | `receiveAgentRequest(agentId, requestDto)` |
| **Session Ingestion**| Ingest user message turn in chat | `ingestUserInput(sessionId, inputPayload)` |
| **Agent Reaction** | Agent processes turn and replies | `receiveAgentInput(sessionId, userRecord)` |
| **Persistence** | Persist chat history turn to storage | `persistChatSessionHistory(sessionId, turnRecord)` |

---

## 6. Object-Oriented Programming (OOP) Principles

### 6.1 Encapsulation & State Protection
* **Private State, Public Behavior:** Keep internal object state private. Expose controlled `camelCase` public methods.
* **Invariant Enforcement:** Validate business invariants inside class constructors and setters.
* **Avoid Anemic Models:** Encapsulate state and business operations within domain objects.

### 6.2 Inheritance & Composition
* **Liskov Substitution Principle (LSP):** Subclasses must be completely substitutable for superclasses.
* **Favor Composition Over Inheritance:** Inject dependencies rather than building deep inheritance trees (max 2-3 levels).

### 6.3 Polymorphism & Strategy Pattern
* **Dynamic Dispatch:** Replace complex conditional branches (`switch` statements) with polymorphic interface implementations.

---

## 7. Abstraction: Abstract Classes vs. Interfaces

| Dimension | Interface | Abstract Class |
| :--- | :--- | :--- |
| **Primary Purpose** | Defines a strict behavioral contract | Provides base implementation & shared state |
| **Multiple Inheritance** | Classes can implement multiple interfaces | Classes can inherit from only one abstract class |
| **State Storage** | Cannot store instance state | Can declare instance fields and constructors |
| **Use Case** | Unrelated classes share common capabilities | Closely related classes share code and state |

---

## 8. Chain-of-Verification (CoVE) Audit & Non-Conflict Matrix

A Chain-of-Verification (CoVE) audit was conducted to ensure zero conflicts exist between this Functional Decomposition & OOP Knowledge Base and the existing rule sets (`agent-rules-knowledge-base-v2.md` and `claude-skills-nfr-knowledge-base.md`).

### 8.1 CoVE Audit Findings

1. **Does relegating every tool call to a function conflict with Clean Code or Clean Architecture?**
   * *Verification:* No. Relegating tool calls enforces the Single Responsibility Principle (SRP) and Dependency Inversion Principle (DIP). It keeps orchestrators clean and decouples infrastructure tool code from core business logic.
2. **Does explicit chat history function decomposition (`ingestUserRequest`, `persistChatSessionHistory`) align with DDD and DDIA?**
   * *Verification:* Yes. *Implementing DDD* advocates for explicit Application Services to manage transaction boundaries and event persistence. *Designing Data-Intensive Applications* emphasizes explicit data pipelines and audit history persistence.
3. **Is camelCase naming universally consistent across all rule sets?**
   * *Verification:* Yes. All 3 knowledge base files mandate explicit `camelCase` function signatures with verb-noun clarity.

### 8.2 Cross-Knowledge Base Alignment Matrix

| Rule Domain | Guideline Mandate | Cross-KB Alignment Status |
| :--- | :--- | :---: |
| **Decomposition** | Every service/tool/feature relegated to distinct function | Aligned with *Clean Code* & *Clean Architecture* |
| **Chat Pipeline** | `ingestUserRequest`, `receiveAgentInput`, `persistChatSessionHistory` | Aligned with *Implementing DDD* & *DDIA* |
| **Tool Delegation**| Orchestrator delegates tool calls to dedicated `camelCase` functions | Aligned with *Superpowers / Plan Readiness* |
| **Pseudocode** | Plain-English statements (`"retrieve all skills for user"`) | Aligned with *A Philosophy of Software Design* |
| **OOP & Interfaces**| Lean interfaces, encapsulation, composition over inheritance | Aligned with *Refactoring* & *Design Patterns* |

---

## 9. Agent Execution & Verification Checklist

When generating code, pseudocode, or system architecture, the AI coding agent MUST verify:

- [ ] Every service, feature, or integration is decomposed into dedicated, single-responsibility functions.
- [ ] Every tool call made by an orchestrator agent is relegated to its own specific function (e.g., `invokeSkillRetrievalTool`).
- [ ] Conversational chat sessions use explicit functional steps (`ingestUserRequest`, `invokeAgentToolCall`, `receiveAgentRequest`, `ingestUserInput`, `receiveAgentInput`, `persistChatSessionHistory`).
- [ ] All function and method signatures strictly use **`camelCase`** with action verbs.
- [ ] Pseudocode uses readable plain-English action statements (e.g., `"retrieve all skills for user"`).
- [ ] Statements inside each function maintain a Single Level of Abstraction (SLA).
- [ ] Data across function boundaries is passed via explicit DTOs rather than mutating hidden global state.
- [ ] Class attributes remain private/protected with invariant validation in constructors.
