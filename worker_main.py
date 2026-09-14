# worker_main.py
from fastapi import FastAPI, Depends, HTTPException
from models.schemas import TaskPayload
from agents.base_agent import BaseAgent
from services.core_service import CoreWorkflowService
from utils.security import verify_cloud_tasks_oidc_token
from utils.logger import logger

app = FastAPI(title="Enterprise Agentic Workflow - Worker HTTP Service", version="1.0.0")


@app.get("/health")
async def health_check():
    """Health check probe endpoint for worker service instances."""
    return {"status": "healthy"}


@app.post("/worker/{target_datastore_id}")
async def execute_worker_task(
    target_datastore_id: str,
    payload: TaskPayload,
    auth_claims: dict = Depends(verify_cloud_tasks_oidc_token)
):
    """
    HTTP worker endpoint invoked asynchronously by Cloud Tasks.
    Protected via OIDC token verification. Executes tasks via CoreWorkflowService.
    """
    logger.info(
        f"Worker HTTP task received for datastore: '{target_datastore_id}'", 
        extra={"skill_id": payload.skill_id}
    )
    try:
        # 1. Initialize BaseAgent (handles Apigee LLM Gateway setup)
        base_agent = BaseAgent()
        core_service = CoreWorkflowService(genai_client=base_agent.genai_client)

        # 2. Resolve skill prompt (Redis MemoryStore -> Production GCS)
        skill_prompt, generation_id = await core_service.load_skill_prompt(
            skill_id=payload.skill_id,
            generation_id=payload.generation_id
        )

        # 3. Strip YAML frontmatter headers
        clean_system_prompt = base_agent.strip_yaml_frontmatter(skill_prompt)

        # 4. Execute workflow (RAG Context + Gemini LLM + BigQuery Write)
        result = await core_service.execute_skill_workflow(
            payload=payload,
            clean_system_prompt=clean_system_prompt
        )

        return {"status": "SUCCESS", "skill_id": payload.skill_id, "result": result}

    except Exception as e:
        logger.error(
            f"Worker HTTP task execution failed: {str(e)}", 
            extra={"skill_id": payload.skill_id}
        )
        raise HTTPException(status_code=500, detail=f"Worker execution failed: {str(e)}")