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

from fastapi import HTTPException
from pydantic import BaseModel
from groq import AsyncGroq
import os
import asyncio
from supabase import create_client

# Supabase client
supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

# Groq client
client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])

# class TaskMessage(BaseModel):
#     task_id: str
#     agent_id: str
#     user_message: str

@app.post("/process-task")
async def process_task(task_data: TaskMessage):
    try:
        # 1️⃣ Verify task exists
        task = supabase.table("s_tasks").select("*").eq("id", task_data.task_id).execute()
        if not task.data:
            raise HTTPException(status_code=404, detail="Task not found")

        # 2️⃣ Insert the user message
        supabase.table("s_taskchats").insert({
            "task_id": task_data.task_id,
            "task_prompt": task_data.user_message,
            "is_streaming": False,
            "stream_completed": True
        }).execute()

        # 3️⃣ Insert empty row for agent response
        agent_msg = supabase.table("s_taskchats").insert({
            "task_id": task_data.task_id,
            "task_prompt": None,
            "response": None,
            "partial_content": "",
            "is_streaming": True,
            "stream_completed": False
        }).execute()

        agent_msg_id = agent_msg.data[0]["id"]

        # 4️⃣ Stream tokens from Groq and update DB
        final_text = ""
        stream = await client.chat.completions.create(
            messages=[{"role": "user", "content": task_data.user_message}],
            model="llama3-8b-8192",
            stream=True
        )

        async for chunk in stream:
            token = chunk.choices[0].delta.content or ""
            if token:
                final_text += token
                supabase.table("s_taskchats").update({
                    "partial_content": final_text
                }).eq("id", agent_msg_id).execute()

        # 5️⃣ Mark stream as completed and save final response
        supabase.table("s_taskchats").update({
            "response": final_text,
            "is_streaming": False,
            "stream_completed": True
        }).eq("id", agent_msg_id).execute()

        # 6️⃣ Update task status
        supabase.table("s_tasks").update({"task_status": "agent_responded"}).eq("id", task_data.task_id).execute()

        return {
            "success": True,
            "message": "Task processed successfully",
            "task_id": task_data.task_id,
            "status": "agent_responded",
            "agent_response": final_text
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# @app.post("/process-task")
# async def process_task(task_data: TaskMessage):
#     """
#     Process a task message with CrewAI agent
    
#     - **task_id**: ID of the task
#     - **agent_id**: ID of the agent to use
#     - **user_message**: Message from the user
#     """
#     try:
#         result = await process_task_message(
#             task_id=task_data.task_id,
#             agent_id=task_data.agent_id,
#             user_message=task_data.user_message
#         )
#         return result
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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

