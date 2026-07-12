import asyncio
import mcp.types as types

from mcp.server.lowlevel import Server
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel.server import NotificationOptions
from mcp.server.stdio import stdio_server

# Initializing the server
server = Server('jarvis-server')


# Defining Handler Function
@server.list_tools()
async def tools_lists() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_weather",
            description="Get current weather for a city",
            inputSchema={
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        )
    ]

@server.call_tool()
async def call_tools(name: str, arguments: dict) -> list[types.TextContent]:
    if name != "get_weather":
        raise ValueError(f"Unknown tool: {name}")
 
    city = arguments["city"]
    text = f"{city}: 24°C, clear skies"  # fake data for now
    return [types.TextContent(type="text", text=text)]



# Starting the server communication loop
async def app():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="jarvis-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(app())