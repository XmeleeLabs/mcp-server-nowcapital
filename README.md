# NowCapital.ca Retirement Planner MCP Server

This is a **Model Context Protocol (MCP)** server for the **NowCapital.ca Retirement Planning API**.
It allows AI Agents (like Claude, Gemini, etc.) to perform complex Canadian retirement simulations with high-precision tax logic, government benefit modeling (CPP/OAS), and longevity planning.
Obtain API keys at https://NowCapital.ca or in Android https://play.google.com/store/apps/details?id=ca.nowcapital.app

## **CONTACT US**

Need help or have questions?

* Email: support@nowcapital.ca  
* YouTube: [@NowCapital-ca](https://www.youtube.com/@NowCapital-ca)  
* Facebook: [NowCapital](https://www.facebook.com/profile.php?id=61584898631313)  
* Instagram: [@nowcapital.ca](https://www.instagram.com/nowcapital.ca?utm_source=qr&igsh=dmZmbGlvMnlxb3Fq)


## Features
*   **Precision Math**: Calculates sustainable monthly spending with backend tax details.
*   **Smart Defaults**: Translates simple prompts ("I have $500k") into tax-optimized account splits.
*   **Couple Support**: Automatic optimizations for spousal income splitting.
*   **Advanced Mode**: Supports couple expense phases (Go-Go, Slow-Go, No-Go), DB Pension, LIRA, and Split allocation strategies (RRSP/TFSA/Non-Reg).

## Requirements
*   Python 3.10+
*   A valid **NowCapital.ca API Key**

## Quick Start (Using `uv`)
The easiest way to run this server is with `uv`, a fast Python tool.

> **Don't have `uv`?**
> *   **Windows**: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
> *   **Mac/Linux**: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 1. Configure Claude Desktop
Edit `claude_desktop_config.json`:
*   **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
*   **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add this entry (replace the **path** and **API Key**):

### Windows Configuration
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
        "C:\\Users\\YourName\\path\\to\\mcp-server-nowcapital\\server.py"
      ],
      "env": {
        "NOWCAPITAL_API_KEY": "your_key_here",
        "NOWCAPITAL_API_BASE_URL": "https://api.nowcapital.ca"
      }
    }
  }
}
```

### Mac/Linux Configuration
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
        "NOWCAPITAL_API_KEY": "your_nowcapital_api_key_here",
        "NOWCAPITAL_API_BASE_URL": "https://api.nowcapital.ca"
      }
    }
  }
}
```

### 2. Verify
Restart Claude Desktop. You should see the 🔌 icon indicating the tool is connected.
Try asking:
*   **Simple Summary:** "Calculate my max retirement spend if I have $600k in savings and I am 55 years old."
*   **Detailed Cash Flow:** "Provide a detailed year-by-year retirement spend plan for someone aged 60 with $800k in savings."
*   **Risk Analysis:** "Run a Monte Carlo simulation for my retirement plan if I spend $5,000 per month. I have $700k in savings and I am 60 years old." (Note: This process typically takes 5-15 seconds).
*   **Capabilities:** "What are the full retirement calculation defaults for single or a couple that I can modify?"

## Standard Installation (No `uv`)
If you prefer standard pip:

### Windows (PowerShell)
```powershell
git clone https://github.com/XmeleeLabs/mcp-server-nowcapital.git
cd mcp-server-nowcapital
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Mac/Linux (Bash)
```bash
git clone https://github.com/XmeleeLabs/mcp-server-nowcapital.git
cd mcp-server-nowcapital
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run Development Inspector
```bash
# Windows (PowerShell)
$env:NOWCAPITAL_API_KEY="your_key_here"
$env:NOWCAPITAL_API_BASE_URL="https://api.nowcapital.ca"
fastmcp dev server.py

# Mac/Linux
export NOWCAPITAL_API_KEY="your_key_here"
export NOWCAPITAL_API_BASE_URL="https://api.nowcapital.ca"
fastmcp dev server.py
```
## Streamable HTTP support
python server.py --transport http --port 8000 --host 0.0.0.0

### Configure gemini cli client
You need to tell the Gemini CLI where to find this HTTP endpoint. You do this by editing the settings.json file.
Gemini may find the API KEY in it's settings.json file, if not, you can specify the API KEY in the actual chatbot request.

Mac/Linux: ~/.gemini/settings.json

Windows: %USERPROFILE%\.gemini\settings.json

Add (or update) the mcpServers block to use httpUrl instead of command.

JSON
{
  "mcpServers": {
    "nowcapital-retirement": {
      "httpUrl": "https://mcp.nowcapital.ca/mcp"
      "headers": {
        "X-API-Key": "NOWCAPITAL_API_KEY_HERE"
    }
  }
}

### Configure anything llm
Specify the API KEY in the chatbot request.

JSON
{
  "mcpServers": {
    "nowcapital-retirement": {
      "type": "streamable",
      "url": "https://mcp.nowcapital.ca/mcp"
    }
  }
}
