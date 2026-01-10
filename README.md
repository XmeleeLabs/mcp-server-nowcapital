# NowCapital.ca Retirement Planner MCP Server

A **Model Context Protocol (MCP)** server that connects AI assistants like Claude to the **NowCapital.ca Retirement Planning API**. This integration enables sophisticated Canadian retirement simulations with precise tax calculations, government benefit modeling (CPP/OAS), and comprehensive longevity planning.

## What is This?

This MCP server acts as a bridge between AI assistants and NowCapital.ca's retirement planning engine. Once installed, you can have natural conversations with Claude about retirement planning, and Claude will automatically use these tools to provide accurate Canadian retirement projections.

**What you can do:**
- Calculate sustainable retirement spending based on your savings
- Generate detailed year-by-year cashflow projections
- Run Monte Carlo simulations to assess retirement plan risks
- Optimize tax strategies across RRSP, TFSA, and non-registered accounts
- Model couple scenarios with income splitting and spousal benefits

## Features

- **Precision Math**: Calculates sustainable monthly spending with detailed tax modeling
- **Smart Defaults**: Translates simple inputs ("I have $500k") into tax-optimized account allocations
- **Couple Support**: Automatic optimizations for spousal income splitting and survivor planning
- **Advanced Scenarios**: Supports expense phases (Go-Go, Slow-Go, No-Go), defined benefit pensions, LIRAs, and custom allocation strategies

## Prerequisites

**Required:**
- Claude Desktop application (or another MCP-compatible AI client)
- A NowCapital.ca API key ([see below](#getting-your-api-key))

**NOT Required (if using Quick Start method):**
- Python installation (uv manages this automatically)

## Getting Your API Key

1. **Web**: Visit [NowCapital.ca](https://NowCapital.ca)
2. **Mobile**: Install from [Google Play Store](https://play.google.com/store/apps/details?id=ca.nowcapital.app)
3. Navigate to **API Access** to generate an API key
4. Copy the key - you'll need it for configuration

**API Key Types:**
- **Demo/Free Keys**: Includes basic retirement calculations (sustainable spending, detailed projections)
- **Premium Keys**: Unlocks advanced features:
  - Monte Carlo simulations (risk analysis)
  - Additional income events (one-time windfalls, part-time work, etc.)
  - Custom expense phases (Go-Go, Slow-Go, No-Go spending patterns)

**Need help?** Contact support@nowcapital.ca

## Installation

Choose **one** of the two methods below:

### Method 1: Quick Start with uv (Recommended)

**Why uv?** uv is a fast Python package manager that automatically handles Python installation and dependencies. You don't need Python installed beforehand - uv takes care of everything.

#### Step 1: Install uv

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Mac/Linux (Terminal):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Step 2: Download the Server Code

**Option A - Using git:**
```bash
git clone https://github.com/XmeleeLabs/mcp-server-nowcapital.git
```

**Option B - Manual download:**
1. Visit https://github.com/XmeleeLabs/mcp-server-nowcapital
2. Click "Code" → "Download ZIP"
3. Extract to a location you'll remember (e.g., `C:\Projects\` or `~/Projects/`)

**Important:** Note the full path to where you saved the code - you'll need it in the next step.

#### Step 3: Configure Claude Desktop

You need to tell Claude Desktop where to find this server by editing a configuration file.

**Locate your config file:**
- **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**Tips for finding the file:**
- On Windows: Press `Win+R`, type `%APPDATA%\Claude`, press Enter
- On Mac: In Finder, press `Cmd+Shift+G`, paste the path above
- If the file doesn't exist, create it as an empty JSON file: `{}`

**Add this configuration** (replace the placeholders):

**For Windows:**
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
        "C:\\Users\\YourName\\mcp-server-nowcapital\\server.py"
      ],
      "env": {
        "NOWCAPITAL_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

**For Mac/Linux:**
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
        "/Users/YourName/mcp-server-nowcapital/server.py"
      ],
      "env": {
        "NOWCAPITAL_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

**Configuration notes:**
- Replace the path with the **absolute path** to where you saved `server.py`
- Windows paths use double backslashes (`\\`) or forward slashes (`/`)
- Replace `your_api_key_here` with your actual NowCapital.ca API key
- If the file already has other MCP servers, add this entry inside the `mcpServers` object

#### Step 4: Verify Installation

1. **Restart Claude Desktop completely** (quit and reopen, don't just close the window)
2. **Check the MCP server status:**
   - Click your profile icon in the bottom-left corner
   - Select **Settings** → **Developer**
   - Look for "nowcapital-retirement" - it should show status as **"running"**
   - If you see "error" or it's not listed, check the [Troubleshooting](#troubleshooting) section

**Test it with this prompt:**
```
I'm 60 years old with $800,000 in retirement savings. 
How much can I safely spend per month in retirement?
```

Claude should automatically use the retirement planning tools to provide detailed calculations including tax implications and government benefits.

---

### Method 2: Manual Installation (Advanced)

Use this method if you prefer manual control or are already familiar with Python development.

**Requirements:**
- Python 3.10 or higher
- git (optional, for cloning)

#### Step 1: Clone and Setup

**Windows (PowerShell):**
```powershell
git clone https://github.com/XmeleeLabs/mcp-server-nowcapital.git
cd mcp-server-nowcapital
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Mac/Linux (Terminal):**
```bash
git clone https://github.com/XmeleeLabs/mcp-server-nowcapital.git
cd mcp-server-nowcapital
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Step 2: Configure Claude Desktop

Edit your `claude_desktop_config.json` (locations above) and add:

**Windows:**
```json
{
  "mcpServers": {
    "nowcapital-retirement": {
      "command": "C:\\Users\\YourName\\mcp-server-nowcapital\\venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\YourName\\mcp-server-nowcapital\\server.py"
      ],
      "env": {
        "NOWCAPITAL_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

**Mac/Linux:**
```json
{
  "mcpServers": {
    "nowcapital-retirement": {
      "command": "/Users/YourName/mcp-server-nowcapital/venv/bin/python",
      "args": [
        "/Users/YourName/mcp-server-nowcapital/server.py"
      ],
      "env": {
        "NOWCAPITAL_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

Replace both paths with your actual installation location and add your API key.

#### Step 3: Test the Server (Optional)

Before using with Claude, you can test the server directly:

**Windows:**
```powershell
$env:NOWCAPITAL_API_KEY="your_api_key_here"
fastmcp dev server.py
```

**Mac/Linux:**
```bash
export NOWCAPITAL_API_KEY="your_api_key_here"
fastmcp dev server.py
```

This opens a test interface in your browser where you can verify the tools are working.

---

## Example Usage

Once installed, you can ask Claude questions naturally. Claude will automatically determine which tools to use - you don't need to specify tool names.

**Simple spending calculation:**
```
I'm 55 with $600,000 saved. What's my maximum safe monthly retirement spending?
```

**Detailed projection:**
```
Show me a year-by-year retirement plan for someone who is 60 with $800,000 
in savings, planning to retire at 65.
```

**Risk analysis (Premium feature):**
```
I'm 65, have $850,000 saved, and plan to spend $4,500/month. 
What are the chances my money will last through retirement?
```
*Note: Monte Carlo simulations require a Premium API key and take 5-15 seconds to complete.*

**Advanced scenarios (Premium features):**
```
I'm 62 with $1M saved. Model my retirement with these phases:
- First 10 years: spending $5,000/month (active travel years)
- Next 10 years: reduce spending by 2% annually (slowing down)
- Remaining years: reduce by another 2% annually (staying home more)
Also, I'll receive a $50,000 inheritance at age 70.
```
*Note: Expense phases and additional income events require a Premium API key.*

**Exploring options:**
```
What retirement planning parameters can I customize in my calculations?
```

**Default assumptions:**
- Monte Carlo simulations use FP Canada Baseline assumptions:
  - 4.5% expected returns
  - 2.3% inflation (CPI)
  - 9% return volatility
  - 1.2% inflation volatility
  - -0.05 correlation between returns and inflation

## Troubleshooting

### Server shows "error" status or isn't listed

**First, try a complete restart:**

Claude Desktop sometimes keeps background processes running even after you close the window. You need to fully terminate all Claude processes:

**Windows:**
1. Press `Ctrl+Shift+Esc` to open Task Manager
2. Look for any "Claude" processes in the list
3. Right-click each one and select "End Task"
4. Start Claude Desktop again

**Mac:**
1. Press `Cmd+Space`, type "Activity Monitor", press Enter
2. Search for "Claude" in the process list
3. Select each Claude process and click the ⓧ button (Force Quit)
4. Start Claude Desktop again

**Linux:**
```bash
pkill -f claude
# Then restart Claude Desktop
```

After killing all processes and restarting, check the status:
- Click your profile (bottom-left) → Settings → Developer
- Look for "nowcapital-retirement" - it should show "running"

**If still not working:**

1. **Verify the config file location** - Make sure you edited the correct file
   - Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
2. **Check JSON syntax** - Use a JSON validator (jsonlint.com) to verify your config
   - Common issues: missing commas, trailing commas, unescaped backslashes in Windows paths
3. **Verify the path** - Ensure the path to `server.py` is correct and absolute
   - Windows: Use either `C:\\path\\to\\file` or `C:/path/to/file`
   - Test the path: try opening the file directly to confirm it exists
4. **Check Claude Desktop logs** for specific error messages:
   - Mac: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\logs\`
   - Look for the most recent log file and search for "nowcapital" or "error"

### Claude says it can't access the tools

1. **Verify your API key** - Log into NowCapital.ca to validate the key (API Access)
2. **Check your internet connection** - The server needs to reach api.nowcapital.ca
3. **Restart Claude Desktop** - Completely quit and reopen the application

### "Feature not available" or premium feature errors

If you see errors about Monte Carlo simulations, expense phases, or additional income events:
- These are **Premium features** that require a Premium API key
- Demo/Free keys only support basic calculations (sustainable spending and detailed projections)
- Upgrade your API key at [NowCapital.ca](https://NowCapital.ca) to unlock these features

### "Module not found" errors (Manual installation)

Make sure you activated the virtual environment before running:
- Windows: `.\venv\Scripts\Activate.ps1`
- Mac/Linux: `source venv/bin/activate`

### Path issues on Windows

If your path has spaces, ensure the entire path is properly escaped in JSON. Consider moving the server to a path without spaces (e.g., `C:\Projects\`).

## Advanced: HTTP Server Mode

For integration with other AI clients like Gemini or AnythingLLM, you can reach the NowCapital.ca MCP servers via HTTP mode.

### Gemini CLI Configuration

Edit your Gemini settings file:
- Mac/Linux: `~/.gemini/settings.json`
- Windows: `%USERPROFILE%\.gemini\settings.json`

Add:
```json
{
  "mcpServers": {
    "nowcapital-retirement": {
      "httpUrl": "https://mcp.nowcapital.ca/mcp",
      "headers": {
        "X-API-Key": "your_api_key_here"
      }
    }
  }
}
```

### AnythingLLM Configuration

```json
{
  "mcpServers": {
    "nowcapital-retirement": {
      "type": "streamable",
      "url": "https://mcp.nowcapital.ca/mcp"
    }
  }
}
```

For Gemini and AnythingLLM, include your API key in the request headers or provide the API KEY in your prompt.

## Support & Community

**Need help?**
- 📧 Email: support@nowcapital.ca
- 🎥 YouTube: [@NowCapital-ca](https://www.youtube.com/@NowCapital-ca)
- 📘 Facebook: [NowCapital](https://www.facebook.com/profile.php?id=61584898631313)
- 📷 Instagram: [@nowcapital.ca](https://www.instagram.com/nowcapital.ca)

**Found a bug or have a feature request?**
Open an issue on [GitHub](https://github.com/XmeleeLabs/mcp-server-nowcapital/issues)

## Privacy & Security

- Your API key is stored locally in the Claude configuration file
- Retirement calculations are performed on NowCapital.ca servers
- No financial data is stored by this MCP server
- All communication uses HTTPS encryption

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.