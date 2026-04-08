import json
import os
import sys
from typing import Any

import anthropic
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.tool_definitions import TOOL_DEFINITIONS
from agent.tools import TOOL_DISPATCH

load_dotenv()

MODEL = "claude-sonnet-4-20250514"
MAX_TOOL_ROUNDS = 10  

SYSTEM_PROMPT = """You are AgentPipe, an AI assistant that helps data engineers monitor and manage data pipelines.

You have access to tools that let you query a live PostgreSQL database tracking pipeline execution history.

Guidelines:
- Always use the available tools to get real data before answering questions about pipeline status, failures, or quality issues.
- When the user mentions "last night", interpret it as yesterday's date and pass it to the date parameter.
- When the user mentions "this week", use days=7. "Today" means the current date.
- If a tool returns no results, say so clearly and suggest alternatives (e.g., check a wider time window).
- For trigger requests, confirm the action was taken and provide the run ID.
- Be concise. Data engineers want facts, not prose.
- If a tool returns an error field, report it transparently to the user."""


def _execute_tool(tool_name: str, tool_input: dict[str, Any]) -> str:
    fn = TOOL_DISPATCH.get(tool_name)
    if fn is None:
        result = {"error": f"Unknown tool '{tool_name}'."}
    else:
        result = fn(**tool_input)

    return json.dumps(result, default=str)

def _process_tool_use_block(block: anthropic.types.ToolUseBlock) -> dict[str, Any]:
    tool_result_content = _execute_tool(block.name, block.input)
    return {
        "type": "tool_result",
        "tool_use_id": block.id,
        "content": tool_result_content,
    }

def run_agent(
    user_message: str,
    conversation_history: list[dict[str, Any]] | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    history: list[dict[str, Any]] = list(conversation_history or [])
    history.append({"role": "user", "content": user_message})

    for round_num in range(MAX_TOOL_ROUNDS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=history,
        )

        # Append assistant's response to history 
        assistant_content = [block.model_dump() for block in response.content]
        history.append({"role": "assistant", "content": assistant_content})

        if response.stop_reason == "end_turn":
            # Extract the text from the final response
            text_blocks = [
                block.text
                for block in response.content
                if hasattr(block, "text")
            ]
            final_text = "\n".join(text_blocks).strip()
            return final_text, history

        if response.stop_reason == "tool_use":
            # Execute all tool calls in this turn
            tool_use_blocks = [
                block for block in response.content if block.type == "tool_use"
            ]

            tool_results = [
                _process_tool_use_block(block) for block in tool_use_blocks
            ]

            history.append({"role": "user", "content": tool_results})
            continue

        return (
            f"Agent stopped unexpectedly with reason: {response.stop_reason}",
            history,
        )

    return (
        "Agent reached the maximum number of tool-calling rounds without a final answer. "
        "Please try rephrasing your question.",
        history,
    )