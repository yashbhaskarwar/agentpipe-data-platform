import os
import sys
from typing import Any

import anthropic
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.tool_definitions import TOOL_DEFINITIONS

load_dotenv()

MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = """You are AgentPipe, an AI assistant that helps data engineers monitor and manage data pipelines.

You have access to tools that let you query a live PostgreSQL database tracking pipeline execution history.

Guidelines:
- Always use the available tools to get real data before answering questions about pipeline status, failures or quality issues.
"""


def run_agent(
    user_message: str,
    conversation_history: list[dict[str, Any]] | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    history: list[dict[str, Any]] = list(conversation_history or [])
    history.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=TOOL_DEFINITIONS,
        messages=history,
    )

    assistant_content = [block.model_dump() for block in response.content]
    history.append({"role": "assistant", "content": assistant_content})

    text_blocks = [
        block.text
        for block in response.content
        if hasattr(block, "text")
    ]

    final_text = "\n".join(text_blocks).strip()
    return final_text, history