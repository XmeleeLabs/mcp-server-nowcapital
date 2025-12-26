import subprocess
import json
import os
import sys

# Configuration
SERVER_SCRIPT = os.path.join(os.path.dirname(__file__), "server.py")
PYTHON_EXE = sys.executable 
API_KEY = "sk_poc_test_123"

def test_augmented_mcp_server():
    print(f"Testing Augmented MCP Server at: {SERVER_SCRIPT}")
    
    env = os.environ.copy()
    env["NOWCAPITAL_API_KEY"] = API_KEY
    # Ensure URL is set (assuming local backend or mocked in real scenario, 
    # but existing test used an env var or default? older test usage: 
    # checking validate_poc.py... it sets API_KEY but assumes URL is set in env or code?)
    # existing server.py checks NOWCAPITAL_API_BASE_URL. 
    # I should set it if not present, or assume the user has it set. 
    # For safety in this test script, I'll set a default local one if missing.
    if "NOWCAPITAL_API_BASE_URL" not in env:
        env["NOWCAPITAL_API_BASE_URL"] = "http://localhost:8002/api"

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
        # A. Handshake
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
        
        process.stdin.write(json.dumps(init_req) + "\n")
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        if not response_line:
             print(f"Error reading init response. Stderr: {process.stderr.read()}")
             return

        process.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }) + "\n")
        process.stdin.flush()
        print("Handshake complete.")

        # B. Call the Tool with ADVANCED arguments
        print("Sending 'tools/call' with advanced params (DB Pension + LIRA + Split)...")
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
                    "province": "BC",
                    
                    # New Advanced Inputs
                    "lira": 100000,
                    "db_enabled": True,
                    "db_pension_income": 25000,
                    "db_start_age": 65,
                    "db_index_after_retirement": 0.02, # 2% indexing
                    
                    # Couple
                    "spouse_name": "Partner",
                    "spouse_age": 58,
                    "spouse_retirement_age": 63,
                    "spouse_total_savings": 300000,
                    "spouse_db_enabled": False,
                    
                    # Global
                    "income_split": True,
                    "expected_returns": 6.0
                }
            }
        }
        
        process.stdin.write(json.dumps(tool_req) + "\n")
        process.stdin.flush()
        
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
    test_augmented_mcp_server()
