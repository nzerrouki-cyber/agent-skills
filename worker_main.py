# worker_main.py
from fastapi import FastAPI, Depends, HTTPException
from agents.worker_agent import WorkerAgent
from models.schemas import TaskPayload
from utils.security import verify_cloud_tasks_oidc_token
from utils.logger import logger

app = FastAPI(title="Enterprise Agentic Workflow - Worker Service", version="1.0.0")


@app.get("/health")
async def health_check():
    """Health check probe endpoint for worker pods."""
    return {"status": "healthy"}


@app.post("/worker/{target_datastore_id}")
async def execute_worker_task(
    target_datastore_id: str,
    payload: TaskPayload,
    auth_claims: dict = Depends(verify_cloud_tasks_oidc_token)
):
    """
    Stateless worker task endpoint invoked asynchronously by Cloud Tasks.
    Protected via OIDC token verification.
    """
    logger.info(f"Worker task received for datastore: '{target_datastore_id}'", extra={"skill_id": payload.skill_id})
    try:
        worker = WorkerAgent(category=target_datastore_id)
        result = await worker.execute_task(payload)
        return {"status": "SUCCESS", "skill_id": payload.skill_id, "result": result}
    except Exception as e:
        logger.error(f"Worker task execution failed: {str(e)}", extra={"skill_id": payload.skill_id})
        raise HTTPException(status_code=500, detail=f"Worker execution failed: {str(e)}")