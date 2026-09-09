# router_main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from agents.intake_agent import IntakeAgent
from agents.discovery_agent import DiscoveryAgent
from agents.validation_agent import SkillValidationAgent
from agents.gem_creator_agent import GemCreatorAgent
from agents.worker_agent import WorkerAgent
from models.schemas import TaskPayload
from services.session_store import SessionStoreService
from config.settings import settings

# Runs a FastAPI application that ois hoted in GKE pods. 
# This routes the appropriate WebSocket connections through the correct agents and eventarc triggers.
app = FastAPI(title="Enterprise Agentic Workflow - Router Service", version="1.0.0")

# Instantiate agents. 
intake_agent = IntakeAgent()
discovery_agent = DiscoveryAgent()
validation_agent = SkillValidationAgent()
gem_creator_agent = GemCreatorAgent()

# Checks router microserve is healthy.
@app.get("/health")
async def health_check():
    """Health check probe endpoint."""
    return {"status": "healthy"}

    # ---------------------------------------------------------
    # SKILL LifeCycle
    # ---------------------------------------------------------

# 1. Create session for Gem Creater Agent to add new skills.
@app.websocket("/ws/gem-creator/{session_id}")
async def gem_creator_endpoint(websocket: WebSocket, session_id: str):
    """Interactive guided loop (Steps 0-7) for authoring new skills."""
    await websocket.accept()
    try:
        while True:
            user_payload = await websocket.receive_text()
            response = await gem_creator_agent.process_intake_pathway(session_id, user_payload)
            await websocket.send_text(response)
    except WebSocketDisconnect:
        pass

# 2. Triggers eventarc trigger once a new skill has been created by the gem creator agent or directly added by user.
# This trigger is then sent to the validation agent before it is added to the production bucket.
@app.post("/events/skill-draft-uploaded")
async def validate_draft_skill(request: Request):
    """Eventarc trigger for new skills in gs://enterprise-skillbank/drafts/."""
    event_payload = await request.json()
    await validation_agent.run_audit_pipeline(event_payload)
    return {"status": "Skill validation initiated"}

# Enables manual uploads of skills via Aisleskill contract rather than relying on the gem creator agent.
@app.post("/skills/draft")
async def create_skill_draft(skill: AisleSkill):
    """Direct REST ingestion endpoint for registering new AisleSkill drafts."""
    formatted_markdown = skill.to_yaml_markdown()
    
    bucket_parts = settings.SKILL_DRAFTS_BUCKET.strip("/").split("/", 1)
    bucket_name = bucket_parts[0]
    prefix = bucket_parts[1] if len(bucket_parts) > 1 else ""
    blob_path = f"{prefix}/{skill.skill_id}.md" if prefix else f"{skill.skill_id}.md"

    await gcs_service.upload_string(
        bucket_setting=bucket_name,
        blob_name=blob_path,
        content=formatted_markdown,
        content_type="text/markdown"
    )
    return {
        "status": "SUCCESS", 
        "skill_id": skill.skill_id, 
        "gcs_path": f"gs://{bucket_name}/{blob_path}"
    }

    # ---------------------------------------------------------
    # Intake Form Agentic Process
    # ---------------------------------------------------------

# 1. Create session for intake agent to fill intake form.
@app.websocket("/ws/intake/{session_id}")
async def intake_chat_endpoint(websocket: WebSocket, session_id: str):
    """Maintains persistent WebSocket connection for the Intake Agent."""
    await websocket.accept()
    try:
        while True:
            user_payload = await websocket.receive_text()
            response = await intake_agent.handle_user_message(session_id, user_payload)
            await websocket.send_json(response)
    except WebSocketDisconnect:
        pass

# 2. Submit "COMPLETED" status after the intake has been finalized.
@app.post("/webhook/intake/complete/{session_id}")
async def finalize_intake(session_id: str):
    """Checks completion status without re-triggering duplicate GCS uploads."""
    session_store = SessionStoreService(collection_name=settings.FIRESTORE_INTAKE_SESSION_STORE)
    session = await session_store.get_session(session_id)
    return {
        "session_id": session_id, 
        "status": session.status,
        "collected_fields": session.collected_fields
    }

# 3. Route eventarc trigger to the discovery agent once intake has been added to its GCS bucket to be queued later.
@app.post("/events/intake-uploaded")
async def route_intake_payload(request: Request):
    """Eventarc trigger for gs://intake-ideas-bucket/raw/ objects."""
    event_payload = await request.json()
    await discovery_agent.process_and_enqueue(event_payload)
    return {"status": "Intake routed to Cloud Tasks"}

#4. Execute the worker's system prompt by retrieving the skill payload.
@app.post("/worker/{target_datastore_id}")
async def execute_worker_task(target_datastore_id: str, payload: TaskPayload):
    """Worker endpoint invoked asynchronously by Cloud Tasks."""
    worker = WorkerAgent(category=target_datastore_id)
    result = await worker.execute_task(payload)
    return {"status": "SUCCESS", "result": result}
