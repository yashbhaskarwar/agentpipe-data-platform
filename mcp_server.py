import json
import os
import sys
from typing import Any

import anyio
from dotenv import load_dotenv
from mcp.server.lowlevel.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    ServerCapabilities,
    TextContent,
    Tool,
    ToolsCapability,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from agent.tool_definitions import TOOL_DEFINITIONS
from agent.tools import TOOL_DISPATCH

server = Server("agentpipe")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name=defn["name"],
            description=defn["description"],
            inputSchema=defn["input_schema"],
        )
        for defn in TOOL_DEFINITIONS
    ]

@server.call_tool()
async def handle_call_tool(
    name: str,
    arguments: dict[str, Any],
) -> list[TextContent]:
    fn = TOOL_DISPATCH.get(name)

    if fn is None:
        result = {"error": f"Unknown tool '{name}'."}
    else:
        result = fn(**arguments)

    return [
        TextContent(
            type="text",
            text=json.dumps(result, default=str, indent=2),
        )
    ]

async def main() -> None:
    init_options = InitializationOptions(
        server_name="agentpipe",
        server_version="1.0.0",
        capabilities=ServerCapabilities(
            tools=ToolsCapability(listChanged=False),
        ),
    )

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream=read_stream,
            write_stream=write_stream,
            initialization_options=init_options,
        )

if __name__ == "__main__":
    anyio.run(main)