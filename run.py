# run_agent.py

from agent_builder import build_agent_from_metadata

if __name__ == "__main__":
    agent_id = "4a95e784-0079-4adb-a579-d50e883076b5"
    agent = build_agent_from_metadata(agent_id)

    # print("\n--- Agent Details ---")
    # print(f"Role      : {agent.role}")
    # print(f"Goal      : {agent.goal}")
    # print(f"Backstory : {agent.backstory}")
    # print(f"LLM       : {agent.llm.model}")
    # print(f"Tools     : {[tool.name for tool in agent.tools]}")
    

    # print("\n--- Running Agent ---")
    # user_message = "Can you fetch something interesting about cats or dogs for me?"
    result = agent.kickoff("Can you fetch something interesting about cats and dogs for me? and summarize both of them and then tell me which one is more interesting according to you.")

    # print("\n--- Agent Response ---\n")
    print(result)
