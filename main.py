from fastapi import FastAPI, WebSocket, Request, BackgroundTasks, HTTPException
from pydantic import BaseModel

# Import Agent Classes
from agents.intake_agent import IntakeAgent
from agents.discovery_agent import DiscoveryAgent
from agents.worker_agent import WorkerAgent
from agents.validation_agent import SkillValidationAgent
from agents.gem_creator_agent import GemCreatorAgent

app = FastAPI(title="Enterprise Agentic Workflow", version="1.0.0")

# Initialize Agents
intake_agent = IntakeAgent()
discovery_agent = DiscoveryAgent()
validation_agent = SkillValidationAgent()
gem_creator_agent = GemCreatorAgent()

# SKILL Creation
# 1. GemCreatorAgent dynamically asks the user to answer intake questions for intake.md and category.
@app.websocket("/ws/gem-creator/{session_id}")
async def gem_creator_endpoint(websocket: WebSocket, session_id: str):
    """Interactive guided loop (Steps 0-7) for authoring new skills."""
    await websocket.accept()
    while True:
        user_payload = await websocket.receive_text()
        response = await gem_creator_agent.process_intake_pathway(session_id, user_payload)
        await websocket.send_text(response)

# 2. Awaits new skills that are being added to the pipeline.
@app.post("/events/skill-draft-uploaded")
async def validate_draft_skill(request: Request):
    """Eventarc trigger for new skills in gs://enterprise-skillbank/drafts/."""
    event_payload = await request.json()
    await validation_agent.run_audit_pipeline(event_payload)
    return {"status": "Skill validation initiated"}

# Conversational Intake
# 1. Establish websocket connection between the user and the application (IntakeAgent).
@app.websocket("/ws/intake/{session_id}")
async def intake_chat_endpoint(websocket: WebSocket, session_id: str):
    """Maintains persistent WebSocket connection for the Intake Agent."""
    await websocket.accept()
    while True:
        user_payload = await websocket.receive_text()
        response = await intake_agent.process_active_turn(session_id, user_payload)
        await websocket.send_text(response)

# 2. IntakeAgent uploads the complete markdown file once the user is finished answering all intake questions.
@app.post("/webhook/intake/complete")
async def finalize_intake(session_id: str, background_tasks: BackgroundTasks):
    """Converts a COMPLETED session into a Markdown file and uploads to Intake GCS bucket."""
    # Complete intake.md is sent to gs://intake-ideas-bucket/raw.
    background_tasks.add_task(intake_agent.generate_handoff_webhook, session_id)
    return {"status": "Intake finalization queued"}

# 3. Once the intake idea is sent to gs://intake-ideas-bucket/raw, an eventarc trigger is sent.
@app.post("/events/intake-uploaded")
async def route_intake_payload(request: Request):
    """Eventarc trigger for gs://intake-ideas-bucket/raw/ objects."""
    event_payload = await request.json()
    # Sent to Model Armor for input santization, categorizes, and enqueues Cloud Task
    await discovery_agent.process_and_enqueue(event_payload)
    return {"status": "Intake routed to Cloud Tasks"}

# Worker Agent Execution Routes
# TaskPayload represents the payload that is sent to the worker via DiscoveryAgent.
class TaskPayload(BaseModel):
    skill_id: str
    generation_id: str
    target_datastore_id: str
    skill_gcs_uri: str
    intake_uri: str

# Worker is selected and retrieves the correct TaskPayload from DiscoveryAgent.
@app.post("/worker/{category}")
async def execute_worker_task(category: str, payload: TaskPayload):
    """Pulls mapped skill, executes RAG, and streams output to BigQuery."""
    worker = WorkerAgent(category=category)
    try:
        result = await worker.execute_task(payload)
        return {"status": "Success", "audit_result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))