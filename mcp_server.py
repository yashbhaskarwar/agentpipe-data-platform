import anyio
from mcp.server.lowlevel.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import ServerCapabilities, ToolsCapability

server = Server("agentpipe")

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