# cert-mcp-server

An MCP (Model Context Protocol) server that lets Claude Desktop look up Claude certification details by ID.

## What it does

This server exposes a single tool — `get_certification` — that Claude can call during a conversation. When you ask Claude about a certification (e.g. "What does CCAR-P cover?"), Claude calls this tool, which reads `certifications.json` and returns the matching record.

Currently tracked certifications:

| ID | Name | Level | Cost |
|----|------|-------|------|
| CCAO-F | Claude Certified Associate Foundations | Foundations | $99 |
| CCDV-F | Claude Certified Developer Foundations | Foundations | $125 |
| CCAR-F | Claude Certified Architect Foundations | Foundations | $125 |
| CCAR-P | Claude Certified Architect Professional | Professional | $175 |

## How `get_certification` works

```python
get_certification(cert_id: str) -> dict
```

- Pass a specific ID (`"CCAO-F"`, `"CCDV-F"`, `"CCAR-F"`, `"CCAR-P"`) to get that certification's details.
- Pass `"all"` to get every certification at once.
- If the ID isn't found, the tool returns an error message and the list of valid IDs (rather than crashing).

The server reads `certifications.json` on every call, so you can update that file without restarting anything.

**Communication model:** Claude Desktop launches `server.py` as a subprocess and exchanges JSON-RPC messages with it over stdin/stdout. The MCP SDK handles all of that plumbing — `server.py` just defines the tool as a plain Python function.

## Installation

**Requirements:** Python 3.10+

1. Clone the repo:
   ```bash
   git clone https://github.com/YOUR_USERNAME/cert-mcp-server.git
   cd cert-mcp-server
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # macOS / Linux
   # .venv\Scripts\activate    # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Verify it starts up:
   ```bash
   python server.py
   ```
   You should see the server waiting for input (press Ctrl-C to stop).

## Connect to Claude Desktop

1. Open Claude Desktop → **Settings → Developer → Edit Config** (or open `claude_desktop_config.json` directly).

2. Add an entry under `mcpServers`:
   ```json
   {
     "mcpServers": {
       "cert-lookup": {
         "command": "/path/to/cert-mcp-server/.venv/bin/python",
         "args": ["/path/to/cert-mcp-server/server.py"]
       }
     }
   }
   ```
   Replace `/path/to/cert-mcp-server` with the absolute path to the cloned directory.

   > **Tip:** To find the absolute path, run `pwd` inside the repo directory.

3. Save the file and **restart Claude Desktop**.

4. In a new conversation, look for **"Cert Lookup"** in the connected-servers list (the plug icon). You can now ask Claude things like:
   - *"What are all the available Claude certifications?"*
   - *"Tell me about the CCAR-P certification."*

## Adding or updating certifications

Edit `certifications.json` directly — no code changes needed. Each entry follows this shape:

```json
{
  "id": "CERT-ID",
  "name": "Full Certification Name",
  "level": "Foundations | Professional",
  "cost": "$XX",
  "domains": []
}
```

The server picks up changes on the next tool call without a restart.

## Project structure

```
cert-mcp-server/
├── server.py            # MCP server + tool definition
├── certifications.json  # Certification data
├── requirements.txt     # Python dependencies
└── README.md
```
