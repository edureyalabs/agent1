from supabase_client import supabase
from fastapi import HTTPException
import json
from datetime import datetime
from typing import List, Dict, Any

def safe_json_load(value):
    """Safely parse JSON string"""
    try:
        if not value or value.lower() in ["none", "null", ""]:
            return {}
        if isinstance(value, dict):
            return value
        return json.loads(value)
    except Exception:
        return {}

def fetch_agent_metadata(agent_id: str) -> Dict[str, Any]:
    """Fetch agent basic metadata"""
    try:
        result = supabase.table("s_agent_basic_metadata").select("*").eq("id", agent_id).single().execute()
        if not result.data:
            raise HTTPException(status_code=404, detail=f"Agent with id {agent_id} not found")
        
        agent_data = result.data
        tools = agent_data.get("tools", [])
        if isinstance(tools, str):
            tools = safe_json_load(tools)
        
        return {
            "id": agent_data["id"],
            "created_at": agent_data["created_at"],
            "agent_name": agent_data.get("name"),
            "role": agent_data["role"],
            "goal": agent_data["goal"],
            "backstory": agent_data["backstory"],
            "tools": tools,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching agent metadata: {str(e)}")

def fetch_agent_configs() -> Dict[str, Any]:
    """Fetch agent configuration from s_agent_configs"""
    try:
        config_id = "dffeb172-175b-4ffb-bae1-17d0750167c1"
        result = supabase.table("s_agent_configs").select("*").eq("id", config_id).single().execute()
        
        if not result.data:
            # Return default config if not found
            return {
                "llm": "gpt-4",
                "function_calling_llm": None,
                "max_iter": 20,
                "max_rpm": None,
                "max_execution_time": None,
                "verbose": False,
                "allow_delegation": False,
                "step_callback": None,
                "cache": True,
                "system_template": None,
                "prompt_template": None,
                "response_template": None,
                "allow_code_execution": False,
                "max_retry_limit": 2,
                "respect_context_window": True,
                "code_execution_mode": "safe",
                "multimodal": False,
                "inject_date": False,
                "date_format": "%Y-%m-%d",
                "reasoning": False,
                "max_reasoning_attempts": None,
                "embedder": None,
                "knowledge_sources": None,
                "user_system_prompt": None
            }
        
        return result.data
    except Exception as e:
        print(f"Warning: Could not fetch agent configs: {str(e)}")
        # Return default config
        return {
            "llm": "gpt-4",
            "function_calling_llm": None,
            "max_iter": 20,
            "max_rpm": None,
            "max_execution_time": None,
            "verbose": False,
            "allow_delegation": False,
            "step_callback": None,
            "cache": True,
            "system_template": None,
            "prompt_template": None,
            "response_template": None,
            "allow_code_execution": False,
            "max_retry_limit": 2,
            "respect_context_window": True,
            "code_execution_mode": "safe",
            "multimodal": False,
            "inject_date": False,
            "date_format": "%Y-%m-%d",
            "reasoning": False,
            "max_reasoning_attempts": None,
            "embedder": None,
            "knowledge_sources": None,
            "user_system_prompt": None
        }

def fetch_tools_metadata(tool_ids: List[str]) -> List[Dict[str, Any]]:
    """Fetch tools metadata from api_metadata table"""
    if not tool_ids:
        return []
    
    try:
        result = supabase.table("api_metadata").select("*").in_("id", tool_ids).execute()
        return result.data or []
    except Exception as e:
        print(f"Warning: Could not fetch tools metadata: {str(e)}")
        return []

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