"""
MCP server that exposes one tool: get_certification

How MCP works at a high level:
  Claude Desktop (or any MCP client) launches this script as a subprocess.
  The two processes talk to each other over stdin/stdout using JSON-RPC.
  When Claude wants to call get_certification, it sends a JSON message here;
  this server reads the data file and sends back a JSON response.
  You never see any of that plumbing — the SDK handles it.
"""

import json
from pathlib import Path

# mcp.server.mcpserver is the high-level SDK interface (called FastMCP in v1).
# MCPServer lets you define tools with plain Python functions + decorators.
# Under the hood it handles the JSON-RPC protocol, schema generation, and
# error formatting — you just write normal Python.
from mcp.server.mcpserver import MCPServer

# Create the server instance. The string is the server's display name —
# it appears in Claude Desktop's connected-servers list.
mcp = MCPServer("Cert Lookup")

# The data file sits next to this script.
DATA_FILE = Path(__file__).parent / "certifications.json"


@mcp.tool()
def get_certification(cert_id: str) -> dict:
    """
    Look up a Claude certification by its ID.

    This docstring becomes the tool's description that Claude reads to decide
    when and how to call the tool. Write it for Claude, not for humans.

    Args:
        cert_id: The certification identifier. Valid values are:
                 "CCAO-F", "CCDV-F", "CCAR-F", "CCAR-P".
                 Pass "all" to list every certification.
    """
    # Load the JSON data fresh on every call (fine for a small file).
    certs = json.loads(DATA_FILE.read_text())

    if cert_id == "all":
        return {"certifications": certs}

    # Search for an exact ID match.
    for cert in certs:
        if cert["id"] == cert_id:
            return cert

    # Returning a dict with an "error" key is a clean way to signal "not found"
    # without raising an exception that would crash the tool call.
    valid_ids = [c["id"] for c in certs]
    return {
        "error": f"Certification '{cert_id}' not found.",
        "valid_ids": valid_ids,
    }


# mcp.run() starts the event loop and listens on stdin/stdout.
# transport="stdio" is the standard transport for Claude Desktop.
# This line only executes when you run the script directly, not on import.
if __name__ == "__main__":
    mcp.run(transport="stdio")
