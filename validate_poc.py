import subprocess
import json
import os
import sys

# Configuration
SERVER_SCRIPT = os.path.join(os.path.dirname(__file__), "server.py")
PYTHON_EXE = sys.executable 
API_KEY = "sk_poc_test_123"

def test_mcp_server():
    print(f"Testing MCP Server at: {SERVER_SCRIPT}")
    print(f"Using API Key: {API_KEY}")
    
    # 1. Start Subprocess
    # We pass the environment variable for the API key here
    env = os.environ.copy()
    env["NOWCAPITAL_API_KEY"] = API_KEY
    
    # Run the server in default STDIO mode
    process = subprocess.Popen(
        [PYTHON_EXE, SERVER_SCRIPT],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    
    print("Server process started. Performing handshake...")

    try:
        # A. Handshake: Initialize
        # MCP requires an 'initialize' request to start
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05", # Standard version
                "capabilities": {},
                "clientInfo": {"name": "tester", "version": "0.1"}
            }
        }
        
        process.stdin.write(json.dumps(init_req) + "\n")
        process.stdin.flush()
        
        # Read Initialize Response
        response_line = process.stdout.readline()
        if not response_line:
             err = process.stderr.read()
             print(f"Error reading init response. Stderr: {err}")
             return

        # B. Send Initialized Notification (Required to complete handshake)
        process.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }) + "\n")
        process.stdin.flush()
        print("Handshake complete.")

        # C. Call the Tool
        print("Sending 'tools/call' request (calculate_sustainable_spend)...")
        tool_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "calculate_sustainable_spend",
                "arguments": {
                    "current_age": 60,
                    "retirement_age": 65,
                    "total_savings": 500000,
                    "province": "ON"
                }
            }
        }
        
        process.stdin.write(json.dumps(tool_req) + "\n")
        process.stdin.flush()
        
        # Read Response
        # This will block until the backend API returns (or timeouts)
        response_line = process.stdout.readline()
        
        print("\n" + "="*30)
        print("   SERVER RESPONSE   ")
        print("="*30)
        
        if not response_line:
             print("Error: No response received.")
             print("Stderr:", process.stderr.read())
             return

        resp_json = json.loads(response_line)
        
        if "error" in resp_json:
            print(f"❌ FAIL: Server returned error: {resp_json['error']}")
        elif "result" in resp_json:
            # Result content is usually a list of text/image objects
            content = resp_json["result"]["content"][0]["text"]
            print("✅ SUCCESS! The Agent would see this:")
            print("-" * 20)
            print(content)
            print("-" * 20)
            
    except Exception as e:
        print(f"Test Exception: {e}")
    finally:
        process.terminate()

if __name__ == "__main__":
    test_mcp_server()
