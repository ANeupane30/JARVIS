# test_mcp_client.py   (run with: uv run python test_mcp_client.py)
from jarvis.brain.mcp_client import mcp_client

print("1. Connecting...")
mcp_client.connect()

print("2. Tools discovered:")
for t in mcp_client.get_tools():
    print("   -", t["name"], "|", t["description"])
    print("     schema:", t["input_schema"])

print("3. First call:")
print("  ", mcp_client.call_tool("get_weather", {"city": "Delhi"}))

print("4. Second call (session persistence):")
print("  ", mcp_client.call_tool("get_weather", {"city": "Mumbai"}))

print("5. Bad call (error handling):")
print("  ", mcp_client.call_tool("get_weather", {"wrong_arg": 123}))

print("All good.")