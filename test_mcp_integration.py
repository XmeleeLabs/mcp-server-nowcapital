import subprocess
import json
import os
import sys
import time
import re

# Configuration
SERVER_SCRIPT = os.path.join(os.path.dirname(__file__), "server.py")
PYTHON_EXE = os.path.expanduser("~/virt/bin/python3") 

# Load API Key from secret file or environment
SECRET_FILE = os.path.join(os.path.dirname(__file__), "../retire_backend/secrets/key.env")
API_KEY = os.environ.get("NOWCAPITAL_API_KEY")
if not API_KEY and os.path.exists(SECRET_FILE):
    try:
        with open(SECRET_FILE, "r") as f:
            for line in f:
                if "API_KEY=" in line:
                    match = re.search(r"API_KEY=['\"]?([^'\"]+)", line)
                    if match:
                        API_KEY = match.group(1)
                        break
    except Exception as e:
        print(f"Warning: Could not read secret file: {e}")

if not API_KEY:
    print("Error: NOWCAPITAL_API_KEY not found in env or secrets file.")
    sys.exit(1)

# API URL provided by user
API_BASE_URL = "http://192.168.1.58:8002"

def send_request(process, req_data):
    """Helper to send JSON-RPC request and get response."""
    process.stdin.write(json.dumps(req_data) + "\n")
    process.stdin.flush()
    return process.stdout.readline()

def test_mcp_integration():
    print(f"Testing MCP Server Integration at: {SERVER_SCRIPT}")
    print(f"Target Backend: {API_BASE_URL}")
    
    env = os.environ.copy()
    env["NOWCAPITAL_API_KEY"] = API_KEY
    env["NOWCAPITAL_API_BASE_URL"] = API_BASE_URL

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
        # 1. Handshake
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "tester", "version": "0.1"}
            }
        }
        
        resp_line = send_request(process, init_req)
        if not resp_line:
             print(f"Error reading init response. Stderr: {process.stderr.read()}")
             return

        # Send initialized notification
        process.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }) + "\n")
        process.stdin.flush()
        print("✅ Handshake complete.")

        # 2. Test calculate_detailed_spend_plan (Sync)
        print("\nTesting 'calculate_detailed_spend_plan'...")
        tool_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "calculate_detailed_spend_plan",
                "arguments": {
                    "current_age": 60,
                    "retirement_age": 65,
                    "total_savings": 500000,
                    "province": "ON",
                    "spouse_age": 58,
                    "spouse_total_savings": 300000
                }
            }
        }
        
        resp_line = send_request(process, tool_req)
        resp = json.loads(resp_line)
        
        if "error" in resp:
            print(f"❌ FAIL: {resp['error']}")
        elif "result" in resp:
            content = resp["result"]["content"][0]["text"]
            data = json.loads(content)
            
            if "person1_yearly_data_csv" in data:
                csv_content = data["person1_yearly_data_csv"]
                print(f"   CSV Preview: {csv_content[:50]}...")
                if "year,total_taxes" in csv_content.lower():
                    print("✅ SUCCESS: Received CSV data.")
                    csv_lines = csv_content.strip().split('\n')
                    print(f"   CSV Rows: {len(csv_lines)} (Expected > 30)")
                else:
                    print(f"❌ FAIL: CSV Header mismatch. Content: {csv_content[:50]}")
            else:
                print(f"❌ FAIL: Unexpected response format. Keys found: {list(data.keys())}")

        # 3. Test start_monte_carlo_simulation (Async Start)
        print("\nTesting 'start_monte_carlo_simulation'...")
        tool_req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "start_monte_carlo_simulation",
                "arguments": {
                    "target_monthly_spend": 5000,
                    "current_age": 60,
                    "retirement_age": 65,
                    "total_savings": 500000,
                    "province": "ON",
                    "spouse_age": 58,
                    "spouse_total_savings": 300000,
                    "num_trials": 100 # Reduced for test speed
                }
            }
        }
        
        resp_line = send_request(process, tool_req)
        resp = json.loads(resp_line)
        job_id = None
        
        if "error" in resp:
             print(f"❌ FAIL: {resp['error']}")
        elif "result" in resp:
            content = resp["result"]["content"][0]["text"]
            data = json.loads(content)
            print(f"   Response: {data}")
            
            if data.get("status") == "PENDING" and "job_id" in data:
                job_id = data["job_id"]
                print(f"✅ SUCCESS: Simulation started. Job ID: {job_id}")
            else:
                print(f"❌ FAIL: Unexpected response format: {data}")

        # 4. Test get_monte_carlo_results (Async Poll)
        if job_id:
            print(f"\nTesting 'get_monte_carlo_results' for Job ID: {job_id}")
            print("   Waiting a moment for simulation to process...")
            
            # The tool itself has a loop, but we want to test that functionality.
            # We'll call it immediately.
            
            tool_req = {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "get_monte_carlo_results",
                    "arguments": {
                        "job_id": job_id
                    }
                }
            }
            
            resp_line = send_request(process, tool_req)
            resp = json.loads(resp_line)
            
            if "error" in resp:
                print(f"❌ FAIL: {resp['error']}")
            elif "result" in resp:
                content = resp["result"]["content"][0]["text"]
                data = json.loads(content)
                
                print(f"   Status: {data.get('status')}")
                
                if data.get("status") == "SUCCESS":
                    print("✅ SUCCESS: Retrieved final results!")
                    result_keys = data.get("result", {}).keys()
                    print(f"   Result Keys: {list(result_keys)}")
                elif data.get("status") == "PROCESSING":
                    print("⚠️  Status is PROCESSING. The tool's internal wait loop worked, but sim is slow.")
                else:
                    print(f"❌ FAIL: Unexpected status: {data}")

    except Exception as e:
        print(f"Test Exception: {e}")
        import traceback
        traceback.print_exc()
    finally:
        process.terminate()
        print("\nTest finished.")

if __name__ == "__main__":
    test_mcp_integration()
