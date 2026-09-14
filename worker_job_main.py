# worker_job_main.py
import os
import sys
import json
import asyncio
from models.schemas import TaskPayload
from services.core_service import CoreWorkflowService
from agents.base_agent import BaseAgent
from utils.logger import logger


async def run_worker_job():
    """Main execution function for Cloud Run Job container instances."""
    raw_payload = os.environ.get("TASK_PAYLOAD")
    if not raw_payload:
        logger.error("Cloud Run Job failed: 'TASK_PAYLOAD' environment variable is missing.")
        sys.exit(1)

    try:
        payload_dict = json.loads(raw_payload)
        task_payload = TaskPayload(**payload_dict)
    except Exception as parse_err:
        logger.error(f"Failed to parse TASK_PAYLOAD JSON: {str(parse_err)}")
        sys.exit(1)

    logger.info(
        f"Starting worker job for skill '{task_payload.skill_id}'", 
        extra={"generation_id": task_payload.generation_id}
    )

    try:
        # 1. Initialize BaseAgent (for GenAI Client & Apigee routing)
        base_agent = BaseAgent()
        core_service = CoreWorkflowService(genai_client=base_agent.genai_client)

        # 2. Resolve & Load Skill Prompt (Redis MemoryStore -> Production GCS)
        skill_prompt, generation_id = await core_service.load_skill_prompt(
            skill_id=task_payload.skill_id,
            generation_id=task_payload.generation_id
        )

        # 3. Strip YAML frontmatter headers
        clean_system_prompt = base_agent.strip_yaml_frontmatter(skill_prompt)

        # 4. Execute Workflow (Vertex AI Search RAG + Gemini + BigQuery write)
        result = await core_service.execute_skill_workflow(
            payload=task_payload,
            clean_system_prompt=clean_system_prompt
        )

        logger.info(
            f"Worker job completed successfully for skill '{task_payload.skill_id}'", 
            extra={"status": "SUCCESS"}
        )
        sys.exit(0)

    except Exception as exec_err:
        logger.error(f"Worker job execution failed: {str(exec_err)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_worker_job())