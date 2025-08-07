from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn
from orchestrator import process_task_message
from data_service_other import get_task_status, verify_task_exists
import os

app = FastAPI(
    title="CrewAI Task Orchestration API",
    description="API for orchestrating CrewAI agents with task management",
    version="1.0.0"
)

class TaskMessage(BaseModel):
    task_id: str
    agent_id: str
    user_message: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    exists: bool

@app.get("/")
async def root():
    return {
        "message": "CrewAI Task Orchestration API",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/process-task")
async def process_task(task_data: TaskMessage):
    """
    Process a task message with CrewAI agent
    
    - **task_id**: ID of the task
    - **agent_id**: ID of the agent to use
    - **user_message**: Message from the user
    """
    try:
        result = await process_task_message(
            task_id=task_data.task_id,
            agent_id=task_data.agent_id,
            user_message=task_data.user_message
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/task-status/{task_id}")
async def get_task_status_endpoint(task_id: str) -> TaskStatusResponse:
    """
    Get the current status of a task
    
    - **task_id**: ID of the task to check
    """
    try:
        exists = verify_task_exists(task_id)
        if exists:
            status = get_task_status(task_id)
        else:
            status = "not_found"
        
        return TaskStatusResponse(
            task_id=task_id,
            status=status,
            exists=exists
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking task status: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "API is running"}

# from fastapi import APIRouter, BackgroundTasks, HTTPException
# from your_module import verify_task_exists, get_task_status, insert_user_message, update_task_status, run_streaming_agent_logic

# router = APIRouter()

# @router.post("/stream-task/")
# async def process_task_message_streaming(
#     task_id: str,
#     agent_id: str,
#     user_message: str,
#     background_tasks: BackgroundTasks
# ):
#     """
#     Starts background agent streaming for a task
#     """
#     try:
#         if not verify_task_exists(task_id):
#             raise HTTPException(status_code=404, detail="Task not found")

#         if get_task_status(task_id) == "agent_processing":
#             raise HTTPException(status_code=400, detail="Task already processing")

#         insert_user_message(task_id, user_message)
#         update_task_status(task_id, "agent_processing")

#         # Launch background stream
#         background_tasks.add_task(run_streaming_agent_logic, agent_id, task_id, user_message)

#         return {
#             "success": True,
#             "message": "Streaming started",
#             "task_id": task_id,
#             "status": "agent_processing"
#         }

#     except Exception as e:
#         update_task_status(task_id, "error")
#         raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

