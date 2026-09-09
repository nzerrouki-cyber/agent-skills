# worker_main.py
import logging
from fastapi import FastAPI, HTTPException, Status
from models.schemas import TaskPayload
from agents.worker_agent import WorkerAgent

logger = logging.getLogger("worker_main")

app = FastAPI(title="Enterprise Agentic Workflow - Worker Service", version="1.0.0")


@app.get("/health", status_code=Status.HTTP_200_OK)
async def health_check():
    """GKE / Cloud Run liveness probe endpoint."""
    return {"status": "healthy"}

# 1. Retrieves appropriate skill.
# 2. Executes RAG to retrieve the correct knowledge files to execute the worker task.
# 3. Streams the final output to the BigQuery Database.
@app.post("/worker/{datastore_id}")
async def execute_worker_task(datastore_id: str, payload: TaskPayload):
    """Pulls mapped skill, executes RAG against target_datastore_id, and streams output to BigQuery."""
    worker = WorkerAgent(category=datastore_id)
    
    try:
        result = await worker.execute_task(payload)
        return {"status": "Success", "audit_result": result}
    except Exception as e:
        logger.error(f"Worker task execution failed for datastore '{datastore_id}': {str(e)}", exc_info=True)
        # HTTP 500 status code triggers Cloud Tasks automatic retries
        raise HTTPException(
            status_code=Status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Worker execution failed. Task will be retried by Cloud Tasks."
        )