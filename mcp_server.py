import os
import sys

import anyio
from dotenv import load_dotenv
from mcp.server.lowlevel.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import ServerCapabilities, Tool, ToolsCapability

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from agent.tool_definitions import TOOL_DEFINITIONS

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
    