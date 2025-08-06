# agent_builder.py

from crewai import Agent, LLM
from crewai.tools import BaseTool
from typing import Dict, List, Any
import requests
import json
import os
from dotenv import load_dotenv
from pprint import pprint
from data_service import fetch_agent_metadata, fetch_tools_metadata, safe_json_load, fetch_agent_configs
load_dotenv()



class APICallTool(BaseTool):
    name: str
    description: str
    endpoint_url: str
    http_method: str
    headers: Dict[str, Any] = None
    query_params: Dict[str, Any] = None
    body: Dict[str, Any] = None

    def _run(self, **kwargs) -> str:
        try:
            headers = self.headers or {}
            params = self.query_params or {}
            data = self.body or {}

            method = self.http_method.upper()

            response = requests.request(
                method=method,
                url=self.endpoint_url,
                headers=headers,
                params=params,
                json=data if method in ["POST", "PUT", "PATCH"] else None,
                data=data if method not in ["POST", "PUT", "PATCH"] else None
            )

            response.raise_for_status()
            return response.text
        except Exception as e:
            return f"API call failed: {str(e)}"


def build_tools_from_metadata(tool_data_list: List[Dict[str, Any]]) -> List[BaseTool]:
    tools = []
    for tool_data in tool_data_list:
        headers = safe_json_load(tool_data.get("headers"))
        params = safe_json_load(tool_data.get("query_params"))
        body = safe_json_load(tool_data.get("body"))

        tool = APICallTool(
            name=tool_data["name"],
            description=tool_data.get("tool_description", "No description"),
            endpoint_url=tool_data["endpoint_url"],
            http_method=tool_data["http_method"],
            headers=headers,
            query_params=params,
            body=body
        )
        tools.append(tool)
    return tools

def build_agent_from_metadata(agent_id: str) -> Agent:
    agent_data = fetch_agent_metadata(agent_id)
    tool_data_list = fetch_tools_metadata(agent_data["tools"])
    tools = build_tools_from_metadata(tool_data_list)
    agent_config = fetch_agent_configs()

    llm = LLM(model=agent_config["llm"])  if agent_config.get("llm") else None
    function_calling_llm_config = LLM(model=agent_config["function_calling_llm"]) if agent_config.get("function_calling_llm") else None
    agent = Agent(
        config={
        "role": agent_data["role"],
        "goal": agent_data["goal"],
        "backstory": agent_data["backstory"],
        "tools": tools,
        "llm": llm,
        "function_calling_llm": function_calling_llm_config,
        "verbose": agent_config.get("verbose", False),
        "allow_delegation": agent_config.get("allow_delegation", False),
        "max_iter": agent_config.get("max_iter", 20),
        "max_rpm": agent_config.get("max_rpm"),
        "max_execution_time": agent_config.get("max_execution_time"),
        "max_retry_limit": agent_config.get("max_retry_limit", 2),
        "allow_code_execution": agent_config.get("allow_code_execution", False),
        "code_execution_mode": agent_config.get("code_execution_mode", "safe"),
        "respect_context_window": agent_config.get("respect_context_window", True),
        "multimodal": agent_config.get("multimodal", False),
        "inject_date": agent_config.get("inject_date", False),
        "date_format": agent_config.get("date_format", "%Y-%m-%d"),
        "reasoning": agent_config.get("reasoning", False),
        "max_reasoning_attempts": agent_config.get("max_reasoning_attempts"),
        "embedder": agent_config.get("embedder"),
        "knowledge_sources": agent_config.get("knowledge_sources"),
        "system_template": agent_config.get("system_template"),
        "prompt_template": agent_config.get("prompt_template"),
        "response_template": agent_config.get("response_template"),
        "step_callback": agent_config.get("step_callback"),
        "cache": agent_config.get("cache", True),
        "use_system_prompt": agent_config.get("use_system_prompt", True),

        }
    )
    return agent

# agents = build_agent_from_metadata('4a95e784-0079-4adb-a579-d50e883076b5')
# print(agents)
