from typing import List, Dict, Any
from agent_builder import build_agent_from_metadata
from data_service_other import (
    fetch_task_chat_history, 
    insert_user_message, 
    insert_agent_response, 
    update_task_status,
    get_task_status,
    verify_task_exists,
    create_streaming_chat_record,
    update_streaming_content,
)
from fastapi import HTTPException
import asyncio
from concurrent.futures import ThreadPoolExecutor
import traceback

def execute_agent_task(agent_id: str, task_id: str, user_message: str) -> str:
    """Execute agent task synchronously"""
    try:
        # Build agent from metadata
        agent = build_agent_from_metadata(agent_id)
        
        # Get chat history and build messages
        chat_history = fetch_task_chat_history(task_id)
        
        # If no history, use the user message directly
        if not chat_history:
            messages = user_message
        else:
            # Append new user message to history
            chat_history.append({"role": "user", "content": user_message})
            messages = chat_history
        
        # Execute agent with kickoff
        result = agent.kickoff(messages)
        
        # Return raw output
        return result.raw
        
    except Exception as e:
        error_msg = f"Agent execution error: {str(e)}"
        print(f"Error in execute_agent_task: {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
        return error_msg

# async def process_task_message(task_id: str, agent_id: str, user_message: str) -> Dict[str, Any]:
#     """Process task message asynchronously"""
    
#     try:
#         # Verify task exists
#         if not verify_task_exists(task_id):
#             raise HTTPException(status_code=404, detail="Task not found")
        
#         # Check if task is already being processed
#         current_status = get_task_status(task_id)
#         if current_status == "agent_processing":
#             raise HTTPException(status_code=400, detail="Task is already being processed")
        
#         # Insert user message
#         # insert_user_message(task_id, user_message)

#         if not agent_response.lower().startswith("agent execution error"):
#             insert_agent_response(task_id, agent_response)
#             update_task_status(task_id, "agent_responded")
#         else:
#             # Don't insert anything in s_taskchats
#             update_task_status(task_id, "error")
        
#         # Update task status to processing
#         update_task_status(task_id, "agent_processing")
        
#         # Execute agent task in thread pool to avoid blocking
#         loop = asyncio.get_event_loop()
#         with ThreadPoolExecutor() as executor:
#             agent_response = await loop.run_in_executor(
#                 executor, 
#                 execute_agent_task, 
#                 agent_id, 
#                 task_id, 
#                 user_message
#             )
        
#         # Insert agent response
#         insert_agent_response(task_id, agent_response)
        
#         # Update task status to responded
#         update_task_status(task_id, "agent_responded")
        
#         return {
#             "success": True,
#             "message": "Task processed successfully",
#             "task_id": task_id,
#             "status": "agent_responded",
#             "agent_response": agent_response
#         }
        
#     except HTTPException:
#         # Re-raise HTTP exceptions
#         raise
#     except Exception as e:
#         # Handle any other errors
#         error_msg = f"Error processing task: {str(e)}"
        
#         try:
#             # Try to update task status to error
#             update_task_status(task_id, "error")
#             # Insert error message as agent response
#             insert_agent_response(task_id, f"Error: {error_msg}")
#         except:
#             pass  # If we can't update status, just continue
        
#         print(f"Error in process_task_message: {error_msg}")
#         print(f"Traceback: {traceback.format_exc()}")
        
#         raise HTTPException(status_code=500, detail=error_msg)


async def process_task_message(task_id: str, agent_id: str, user_message: str) -> Dict[str, Any]:
    """Process task message asynchronously with streaming support"""

    try:
        # 1. Verify task exists
        if not verify_task_exists(task_id):
            raise HTTPException(status_code=404, detail="Task not found")

        # 2. Check if task is already being processed
        current_status = get_task_status(task_id)
        if current_status == "agent_processing":
            raise HTTPException(status_code=400, detail="Task is already being processed")

        # 3. Insert user message
        insert_user_message(task_id, user_message)

        # 4. Create streaming record
        stream_id = create_streaming_chat_record(task_id)

        # 5. Update task status
        update_task_status(task_id, "agent_processing")

        # 6. Define stream callback
        def stream_callback(token: str):
            try:
                update_streaming_content(stream_id, token)
            except Exception as e:
                print(f"Stream callback error: {e}")

        # 7. Execute agent task with streaming
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            agent_response = await loop.run_in_executor(
                executor,
                execute_agent_task,
                agent_id,
                task_id,
                user_message,
                stream_callback  # <-- pass callback
            )

        # 8. Final response insert
        complete_streaming_response(stream_id, agent_response)
        insert_agent_response(task_id, agent_response)
        update_task_status(task_id, "agent_responded")

        return {
            "success": True,
            "message": "Task processed successfully",
            "task_id": task_id,
            "status": "agent_responded",
            "agent_response": agent_response
        }

    except HTTPException:
        raise

    except Exception as e:
        error_msg = f"Error processing task: {str(e)}"
        try:
            update_task_status(task_id, "error")
            insert_agent_response(task_id, f"Error: {error_msg}")
        except:
            pass
        print(f"Error in process_task_message: {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")

        raise HTTPException(status_code=500, detail=error_msg)