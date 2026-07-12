import asyncio
import threading
from contextlib import AsyncExitStack
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys

SERVER_COMMAND = sys.executable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
# --- Point at your local MCP server -----------------------------------
# SERVER_COMMAND = "python"
SERVER_ARGS = [str(PROJECT_ROOT / "mcp_server" / "server.py")]
assert Path(SERVER_ARGS[0]).exists(), f"MCP server not found: {SERVER_ARGS[0]}"
# -----------------------------------------------------------------------


class MCPClient:
    def __init__(self):
        self._loop = None
        self._thread = None
        self._session = None
        self._stack = None
        self._tools = []          # Anthropic tool format
        self._ready = threading.Event()

    # ---------- public sync API (call these from JARVIS) ----------

    def connect(self, timeout=15):
        """Start background loop + connect to the MCP server. Call once."""
        if self._thread and self._thread.is_alive():
            return
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever, daemon=True, name="mcp-client-loop"
        )
        self._thread.start()
        fut = asyncio.run_coroutine_threadsafe(self._connect(), self._loop)
        fut.result(timeout=timeout)  # raise here if the server fails to start
        self._ready.set()
        print(f"[MCP] connected, tools: {[t['name'] for t in self._tools]}")

    def get_tools(self):
        """Tool definitions in Anthropic API format (name/description/input_schema)."""
        return self._tools

    def call_tool(self, name: str, arguments: dict, timeout=30) -> str:
        """Synchronously execute a tool on the MCP server, return text result."""
        if not self._ready.is_set():
            return "Error: MCP client not connected."
        fut = asyncio.run_coroutine_threadsafe(
            self._call_tool(name, arguments), self._loop
        )
        try:
            return fut.result(timeout=timeout)
        except Exception as e:
            # Return errors as text so the LLM can react gracefully
            return f"Tool '{name}' failed: {e}"

    # ---------- async internals (run on the background loop) ----------

    async def _connect(self):
        self._stack = AsyncExitStack()
        params = StdioServerParameters(command=SERVER_COMMAND, args=SERVER_ARGS)
        read, write = await self._stack.enter_async_context(stdio_client(params))
        self._session = await self._stack.enter_async_context(
            ClientSession(read, write)
        )
        await self._session.initialize()
        result = await self._session.list_tools()
        self._tools = [
            {
                "name": t.name,
                "description": t.description or "",
                "input_schema": t.inputSchema,
            }
            for t in result.tools
        ]

    async def _call_tool(self, name, arguments):
        result = await self._session.call_tool(name, arguments)
        parts = [c.text for c in result.content if getattr(c, "type", "") == "text"]
        return "\n".join(parts) if parts else "(tool returned no text)"


# Module-level singleton, same style as your speaker.py
mcp_client = MCPClient()