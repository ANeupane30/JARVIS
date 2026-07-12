# 08 — Brain: LLM, MCP, and Response Formatting

**Files:**
- `jarvis/brain/llm.py` — OpenRouter LLM API integration
- `jarvis/brain/mcp_client.py` — MCP client (tool-calling infrastructure)
- `jarvis/component/response_formatter.py` — parses LLM JSON responses to plain text
- `mcp_server/server.py` — MCP server exposing tools to the LLM

**Status:**
- `llm.py` ✅ Working — connected and called from `audio_orchestrator.py`
- `mcp_client.py` ✅ Implemented — not yet wired into the main loop
- `response_formatter.py` ✅ Working — called from `audio_orchestrator.py`
- `mcp_server/server.py` ✅ Implemented — stub tool, not yet wired

---

## `llm.py` — Language Model Integration

### What it does

Sends the user's transcribed speech to an LLM via the OpenRouter API and returns the raw
response JSON. OpenRouter is a unified API that routes requests to many model providers.

### How it works

```python
from decouple import config
import requests

OPENROUTER_API_KEY = config('OPENROUTER_API_KEY')

def llm_response(text):
    response = requests.post(
        'https://openrouter.ai/api/v1/responses',
        headers={
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json',
        },
        json={
            'model': 'openai/o4-mini',
            'input': text,
            'max_output_tokens': 9000,
        }
    )
    return response.json()
```

### Key details

| Detail | Value / Explanation |
|---|---|
| **API endpoint** | `https://openrouter.ai/api/v1/responses` — OpenRouter's responses API |
| **Model** | `openai/o4-mini` — a fast, capable OpenAI reasoning model |
| **Max output tokens** | 9,000 — allows long, detailed responses |
| **Auth** | Bearer token from `OPENROUTER_API_KEY` in `.env` |
| **HTTP library** | `requests` (synchronous) — the call blocks until the LLM responds |
| **Returns** | Raw `dict` (parsed JSON from `response.json()`) |

### The `OPENROUTER_API_KEY`

Loaded via `python-decouple`'s `config()` function, which reads from `.env` automatically.
The `.env` file must contain:
```
OPENROUTER_API_KEY=sk-or-your-key-here
```

### Why OpenRouter?

OpenRouter provides a single unified API key for accessing many LLM providers (OpenAI,
Anthropic, Google, Mistral, etc.). This means JARVIS can switch models by changing a single
string (`'openai/o4-mini'`) without changing authentication logic.

---

## `response_formatter.py` — JSON Response Parser

### What it does

The OpenRouter API returns a structured JSON response, not a plain string. `response_formatter.py`
extracts the actual text content from the nested structure.

### How it works

```python
def complete_json_response(data):
    while True:
        try:
            for output in data['output']:
                if output['type'] == 'message':
                    for item in output['content']:
                        return item['text']
        except:
            break
```

### OpenRouter response structure

The raw JSON from `llm_response()` looks like this:
```json
{
  "output": [
    {
      "type": "message",
      "content": [
        {
          "type": "output_text",
          "text": "The actual response text goes here."
        }
      ]
    }
  ]
}
```

`complete_json_response()` walks `data['output']`, finds the first item with `type == 'message'`,
then returns the first content item's `text` value.

> **Limitation:** Returns only the first message output. Future improvement: handle multiple
> outputs, handle `type == 'reasoning'` (for o4-mini's chain-of-thought), and strip markdown
> before passing to TTS.

---

## `mcp_client.py` — Model Context Protocol Client

### What it does

`MCPClient` provides JARVIS with a synchronous interface for:
1. Connecting to an MCP server (the `mcp_server/server.py` subprocess)
2. Listing available tools (e.g., `get_weather`)
3. Calling tools and receiving text results

This is the **client side** of the tool-use infrastructure. The LLM will eventually use these
tools to answer questions that require real data (e.g., weather, time, calendar).

### The async bridge problem

MCP is built on `asyncio`. JARVIS's main loop is synchronous. The solution:

```
Main thread (sync)
    │
    ├── MCPClient.connect()      ← Creates a new asyncio event loop
    │                               Starts it on a daemon background thread
    │                               Awaits _connect() on that loop
    │
    └── MCPClient.call_tool()    ← Submits coroutine to the background loop via
                                    asyncio.run_coroutine_threadsafe()
                                    .result(timeout=30) blocks main thread until done
```

This pattern lets JARVIS call MCP tools synchronously while the async protocol runs safely
on its own thread.

### Class: `MCPClient`

```python
class MCPClient:
    def connect(self, timeout=15):
        """Start background loop + connect to the MCP server. Call once."""

    def get_tools(self):
        """Tool definitions in Anthropic API format (name/description/input_schema)."""

    def call_tool(self, name: str, arguments: dict, timeout=30) -> str:
        """Synchronously execute a tool on the MCP server, return text result."""
```

#### `connect()`
- Creates a new `asyncio` event loop
- Starts it on a `daemon=True` thread so it doesn't block shutdown
- Launches the MCP server subprocess (`mcp_server/server.py`) via stdio
- Initialises the MCP session and discovers available tools

#### `get_tools()`
- Returns a list of tool definitions in Anthropic format:
  ```python
  [
      {
          "name": "get_weather",
          "description": "Get current weather for a city",
          "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}
      }
  ]
  ```
- This format can be passed directly to Anthropic's or OpenRouter's tool-use API

#### `call_tool(name, arguments)`
- Submits the tool call to the background loop
- Waits up to 30 seconds for the result
- Returns the tool's text output as a string
- On error, returns a descriptive error string (so the LLM can react gracefully)

### Module-level singleton

```python
mcp_client = MCPClient()
```

Follows the same pattern as `speaker.py` — one instance shared across the whole app.
Call `mcp_client.connect()` once at startup before using `get_tools()` or `call_tool()`.

---

## `mcp_server/server.py` — MCP Tool Server

### What it does

Implements the **server side** of MCP — the process that actually executes tools.
It runs as a subprocess and communicates with `mcp_client.py` over stdin/stdout.

### How it works

```python
server = Server('jarvis-server')

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
    text = f"{city}: 24°C, clear skies"  # stub — real weather API call goes here
    return [types.TextContent(type="text", text=text)]
```

### Current tools

| Tool | Status | Description |
|---|---|---|
| `get_weather` | 🔧 Stub | Returns hardcoded `"24°C, clear skies"`. Replace with a real API call (e.g., Open-Meteo) |

### Adding new tools

To add a new tool:
1. Add a `types.Tool(...)` entry to the `tools_lists()` handler
2. Add a `if name == "your_tool":` branch to `call_tools()`
3. The MCP client will automatically discover it on the next `connect()`

---

## Planned: Wiring MCP into the LLM Loop

Currently, `mcp_client` is implemented but not used in `audio_orchestrator.py`.
The next step is to pass `mcp_client.get_tools()` to the LLM call and handle tool-use
responses in a loop:

```
transcript → llm_response(with tools) → if tool_use: call_tool() → feed result back → final text → speak()
```

See `docs/user_guide/07_audio_orchestrator.md` for the planned loop structure.

---

## Planned: Memory (`memory.py`) and Response Cleanup (`response.py`)

**`memory.py`** (empty) — will hold conversation history so JARVIS remembers context across
multiple exchanges within a session. Will add a rolling list of `{"role": ..., "content": ...}`
messages passed into each `llm_response()` call.

**`response.py`** (empty) — will post-process LLM text before it reaches `speak()`:
- Strip markdown (e.g., `**bold**` → `bold`)
- Remove code blocks (read them differently or skip)
- Chunk long responses for better TTS pacing
