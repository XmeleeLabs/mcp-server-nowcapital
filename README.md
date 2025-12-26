# NowCapital.ca Retirement MCP Server

This is a **Model Context Protocol (MCP)** server for the **NowCapital.ca Retirement Planning API**.
It allows AI Agents (like Claude, Gemini, etc.) to perform complex Canadian retirement simulations with high-precision tax logic, government benefit modeling (CPP/OAS), and longevity planning.

## Features
*   **Precision Math**: Calculates sustainable monthly spending with backend tax details.
*   **Smart Defaults**: Translates simple prompts ("I have $500k") into tax-optimized account splits.
*   **Couple Support**: Automatic optimizations for spousal income splitting.
*   **Advanced Mode**: Supports specific Acet allocations (RRSP/TFSA/Non-Reg), Actuarial Death Age, and Adjusted Cost Base (ACB).

## Requirements
*   Python 3.10+
*   A valid **NowCapital.ca API Key**

## Quick Start (Using `uv`)
The easiest way to run this server is with `uv`, a fast Python tool.

### 1. Configure Claude Desktop
Edit your `claude_desktop_config.json` file:
*   **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
*   **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add this entry (replace the **path** and **API Key**):

```json
{
  "mcpServers": {
    "nowcapital-retirement": {
      "command": "uv",
      "args": [
        "run",
        "--with", "fastmcp",
        "--with", "requests",
        "python",
        "/absolute/path/to/mcp-server-nowcapital/server.py"
      ],
      "env": {
        "NOWCAPITAL_API_KEY": "sk_your_key_here",
        "NOWCAPITAL_API_BASE_URL": "https://api.nowcapital.ca"
      }
    }
  }
}
```

### 2. Verify
Restart Claude Desktop. You should see the 🔌 icon indicating the tool is connected.
Try asking: *"Calculate my max retirement spend if I have $600k in savings and I am 55 years old."*

## Standard Installation (No `uv`)
If you prefer standard pip:

1.  **Clone and Install**:
    ```bash
    git clone https://github.com/XmeleeLabs/mcp-server-nowcapital.git
    cd mcp-server-nowcapital
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Run Development Inspector**:
    ```bash
    export NOWCAPITAL_API_KEY="sk_test_key"
    export NOWCAPITAL_API_BASE_URL="http://your-backend-url" # or https://api.nowcapital.ca
    fastmcp dev mcp_server.py
    ```
