# Hands-On Lab: Build Your First MCP Server

**Time:** about 45 minutes
**Level:** Beginner to intermediate (comfortable running commands in a terminal; some Python helps)
**What you'll build:** A small MCP server that gives Claude a new tool, a certification lookup, and then you'll extend it with a second tool of your own.

---

## Why this lab exists

Claude is good at reasoning, but it only knows what it was trained on and what you put in front of it. The Model Context Protocol (MCP) is the standard way to give Claude access to your own data and actions. Once you've built one server end to end, every other MCP integration (a database, an internal API, a ticketing system) follows the same pattern.

This lab uses a deliberately small example so you can focus on the pattern instead of the data.

## Learning objectives

By the end of this lab, you will be able to:

1. Explain how an MCP client (Claude Desktop) and an MCP server talk to each other.
2. Define a tool in Python and describe how Claude decides when to call it.
3. Connect a local MCP server to Claude Desktop and verify that Claude uses it.
4. Return useful errors from a tool instead of letting it crash.
5. Extend a server with a new tool that you design yourself.

## Prerequisites

- Python 3.10 or newer (`python3 --version` to check)
- Claude Desktop, installed and signed in
- A terminal and a text editor
- Git (optional, only if you clone instead of building from scratch)

---

## Part 1: The mental model (5 minutes)

Before writing code, picture three pieces:

```
You  ──>  Claude Desktop (MCP client)  ──>  server.py (MCP server)  ──>  certifications.json
                    <── JSON-RPC over stdin/stdout ──>
```

- **Claude Desktop** starts your server as a background process when it launches.
- The two processes exchange **JSON-RPC** messages over standard input and output. You never write that plumbing; the MCP Python SDK handles it.
- Your server advertises **tools**. Each tool has a name, a description, and typed inputs.
- When you ask Claude a question, Claude reads the tool descriptions and decides whether calling a tool would help. If so, it sends a request, your function runs, and the result goes back into Claude's answer.

**Key idea:** Claude chooses tools based on their descriptions. A clear docstring matters as much as the code inside the function.

### Check your understanding

1. Which side starts the other: the client or the server?
2. What does Claude read to decide whether to call your tool?

<details>
<summary>Answers</summary>

1. The client. Claude Desktop launches the server as a subprocess.
2. The tool's name, its description (the docstring), and its input schema (built from the type hints).
</details>

---

## Part 2: Set up the project (5 minutes)

Create a folder and a virtual environment:

```bash
mkdir cert-mcp-server
cd cert-mcp-server
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install "mcp>=2.0.0"
```

Create `certifications.json` with your data:

```json
[
  { "id": "CCAO-F", "name": "Claude Certified Associate Foundations", "level": "Foundations", "cost": "$99" },
  { "id": "CCDV-F", "name": "Claude Certified Developer Foundations", "level": "Foundations", "cost": "$125" },
  { "id": "CCAR-F", "name": "Claude Certified Architect Foundations", "level": "Foundations", "cost": "$125" },
  { "id": "CCAR-P", "name": "Claude Certified Architect Professional", "level": "Professional", "cost": "$175" }
]
```

> **Why a JSON file?** Keeping data separate from code means anyone can update the catalog without touching Python. The server reads the file on every call, so edits show up without a restart.

---

## Part 3: Write the server (10 minutes)

Create `server.py`. Type it out rather than copying if you can; you'll remember the pattern better.

```python
import json
from pathlib import Path

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("Cert Lookup")
DATA_FILE = Path(__file__).parent / "certifications.json"


@mcp.tool()
def get_certification(cert_id: str) -> dict:
    """
    Look up a Claude certification by its ID.

    Args:
        cert_id: The certification identifier, such as "CCAO-F" or "CCAR-P".
                 Pass "all" to list every certification.
    """
    certs = json.loads(DATA_FILE.read_text())

    if cert_id == "all":
        return {"certifications": certs}

    for cert in certs:
        if cert["id"] == cert_id:
            return cert

    return {
        "error": f"Certification '{cert_id}' not found.",
        "valid_ids": [c["id"] for c in certs],
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### What each piece does

| Line | Purpose |
|------|---------|
| `MCPServer("Cert Lookup")` | Creates the server. The name appears in Claude Desktop. |
| `@mcp.tool()` | Registers the function as a tool Claude can call. |
| `cert_id: str` | The type hint becomes the tool's input schema. |
| The docstring | Becomes the description Claude reads. Write it for Claude. |
| The `error` return | Gives Claude something useful to say instead of a crash. |
| `mcp.run(transport="stdio")` | Starts listening on stdin/stdout for the client. |

Run it once to confirm there are no errors:

```bash
python server.py
```

The terminal will sit there quietly. That's correct: it's waiting for a client. Press **Ctrl+C** to stop.

---

## Part 4: Connect it to Claude Desktop (10 minutes)

1. Get the absolute path to your project by running `pwd` inside the folder.
2. In Claude Desktop, open **Settings > Developer > Edit Config**.
3. Add your server under `mcpServers`, replacing the paths with your own:

```json
{
  "mcpServers": {
    "cert-lookup": {
      "command": "/absolute/path/to/cert-mcp-server/.venv/bin/python",
      "args": ["/absolute/path/to/cert-mcp-server/server.py"]
    }
  }
}
```

4. Save the file and fully quit and reopen Claude Desktop.
5. Start a new conversation and confirm **Cert Lookup** appears in the connected tools list.

### Try it

Ask Claude each of these and watch for the tool call:

- "What Claude certifications are available?"
- "How much does CCAR-P cost?"
- "Tell me about the XYZ-9 certification."

The last one should come back with a friendly "not found" answer that lists the valid IDs. That's your error handling at work.

### Check your understanding

3. Why does the config point to the Python inside `.venv` instead of just `python`?
4. You edit `certifications.json` to change a price. Do you need to restart Claude Desktop?

<details>
<summary>Answers</summary>

3. Claude Desktop doesn't activate your virtual environment. Pointing at `.venv/bin/python` guarantees it uses the interpreter where `mcp` is installed.
4. No. The server reads the file on every call. You only restart Claude Desktop when you change `server.py` or the config.
</details>

---

## Part 5: Extend it yourself (15 minutes)

Now design a tool on your own. The goal: let a learner ask, "Which certifications are at the Foundations level?"

**Your task:** Add a second tool, `list_by_level(level: str)`, that returns every certification matching the level passed in.

Requirements:

- Matching should ignore capitalization ("foundations" and "Foundations" both work).
- If nothing matches, return an error along with the valid levels.
- Write a docstring that tells Claude exactly when to use this tool instead of `get_certification`.

Restart Claude Desktop after saving, then test with:

- "Which certifications are Foundations level?"
- "Show me the professional ones."

<details>
<summary>One possible solution</summary>

```python
@mcp.tool()
def list_by_level(level: str) -> dict:
    """
    List all Claude certifications at a given level.
    Use this when the user asks about a level or tier (for example,
    "Foundations" or "Professional") rather than a specific certification ID.

    Args:
        level: The certification level, such as "Foundations" or "Professional".
    """
    certs = json.loads(DATA_FILE.read_text())
    matches = [c for c in certs if c["level"].lower() == level.lower()]

    if not matches:
        return {
            "error": f"No certifications found at level '{level}'.",
            "valid_levels": sorted({c["level"] for c in certs}),
        }

    return {"level": level, "certifications": matches}
```
</details>

### Stretch challenges

Pick one if you have time:

- **Richer data:** Add a `domains` list to each certification and update the tool output so Claude can answer "What topics does CCAR-F cover?"
- **Better descriptions:** Rewrite the `get_certification` docstring so it's vague, ask Claude a question, and see whether it still calls the tool. Then restore it. What did you learn about descriptions?
- **Your own data:** Swap the certification catalog for something from your own work, such as a product glossary, a course list, or an FAQ.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Cert Lookup doesn't appear in Claude Desktop | Config path is wrong or JSON is invalid | Check the absolute paths and validate the JSON (a missing comma is common). |
| `ModuleNotFoundError: mcp` | Config points to the system Python | Use the full path to `.venv/bin/python`. |
| Tool appears but Claude never calls it | Description is unclear | Make the docstring say plainly what the tool does and when to use it. |
| Changes to `server.py` don't show up | Claude Desktop is still running the old process | Fully quit and reopen Claude Desktop. |

---

## Wrap-up

You built an MCP server, connected it to Claude, handled errors gracefully, and designed a tool of your own. The same three steps apply to any integration:

1. **Define the data or action** you want Claude to reach.
2. **Wrap it in a tool** with a clear name, typed inputs, and a description written for Claude.
3. **Connect and test** with real questions, including ones that should fail.

### Reflect

- Where in your own work would giving Claude one well-scoped tool save the most time?
- What would you need to change before sharing a server like this with a team (for example, authentication, logging, or input validation)?

---

*Built by [Elizabeth Shin](https://github.com/elizabeth-shin). The finished reference version of this server is in [`server.py`](server.py).*
