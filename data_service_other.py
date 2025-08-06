from supabase_client import supabase
from typing import List, Dict, Any

def fetch_task_chat_history(task_id: str) -> List[Dict[str, str]]:
    """Fetch chat history for a task"""
    try:
        result = (
            supabase.table("s_taskchats")
            .select("role, content")
            .eq("task_id", task_id)
            .order("created_at", desc=False)
            .execute()
        )
        
        messages = []
        for chat in result.data:
            messages.append({
                "role": chat["role"],
                "content": chat["content"]
            })
        
        return messages
    except Exception as e:
        print(f"Warning: Could not fetch chat history: {str(e)}")
        return []

# print("started")
# try:
#     messages = fetch_task_chat_history('c412dcc3-82bd-4969-8d47-c92bfd5b9f64')
#     print("Returned messages:", messages)
# except Exception as e:
#     print("Exception when fetching task chat history:", str(e))
# print('hello')


def insert_user_message(task_id: str, content: str) -> None:
    """Insert user message into s_taskchats"""
    try:
        supabase.table("s_taskchats").insert({
            "task_id": task_id,
            "role": "user",
            "content": content
        }).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inserting user message: {str(e)}")
    
def insert_agent_response(task_id: str, content: str) -> None:
    """Insert agent response into s_taskchats"""
    try:
        supabase.table("s_taskchats").insert({
            "task_id": task_id,
            "role": "assistant",
            "content": content
        }).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inserting agent response: {str(e)}")
    
def update_task_status(task_id: str, status: str) -> None:
    """Update task status in s_tasks table"""
    try:
        supabase.table("s_tasks").update({"task_status": status}).eq("id", task_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating task status: {str(e)}")
    

def get_task_status(task_id: str) -> str:
    """Get current task status"""
    try:
        result = supabase.table("s_tasks").select("task_status").eq("id", task_id).single().execute()
        if result.data:
            return result.data.get("task_status", "idle")
        return "idle"
    except Exception:
        return "idle"

def verify_task_exists(task_id: str) -> bool:
    """Verify if task exists"""
    try:
        result = supabase.table("s_tasks").select("id").eq("id", task_id).single().execute()
        return bool(result.data)
    except Exception:
        return False    
    
