#!/usr/bin/env python3
"""
Test script for enhanced MCP server parameters.
Tests through MCP protocol like test_augmented.py does.
"""

import subprocess
import json
import os
import sys

# Configuration
SERVER_SCRIPT = os.path.join(os.path.dirname(__file__), "server.py")
PYTHON_EXE = sys.executable
API_KEY = os.environ.get("NOWCAPITAL_API_KEY", "sk_poc_test_123")

def call_mcp_tool(arguments, test_name):
    """Helper function to call MCP tool and return result"""
    print(f"\n=== {test_name} ===")
    
    env = os.environ.copy()
    env["NOWCAPITAL_API_KEY"] = API_KEY
    if "NOWCAPITAL_API_BASE_URL" not in env:
        env["NOWCAPITAL_API_BASE_URL"] = os.environ.get("NOWCAPITAL_API_BASE_URL", "http://localhost:8002/api")
    
    process = subprocess.Popen(
        [PYTHON_EXE, SERVER_SCRIPT],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    
    try:
        # Initialize
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
        process.stdout.readline()  # Read init response
        
        # Send initialized notification
        process.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }) + "\n")
        process.stdin.flush()
        
        # Call tool
        tool_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "calculate_sustainable_spend",
                "arguments": arguments
            }
        }
        
        process.stdin.write(json.dumps(tool_req) + "\n")
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        
        if not response_line:
            return {"error": "No response received"}
        
        resp_json = json.loads(response_line)
        
        if "error" in resp_json:
            return {"error": f"Server error: {resp_json['error']}"}
        elif "result" in resp_json:
            content = resp_json["result"]["content"][0]["text"]
            return json.loads(content)
        else:
            return {"error": "Unexpected response format"}
            
    except Exception as e:
        return {"error": str(e)}
    finally:
        process.terminate()

def test_basic_scenario():
    """Test basic scenario to ensure backward compatibility"""
    result = call_mcp_tool({
        "current_age": 58,
        "retirement_age": 65,
        "savings_rrsp": 500000,
        "savings_tfsa": 150000,
        "province": "ON"
    }, "Test 1: Basic Scenario (Backward Compatibility)")
    
    if "error" in result:
        print(f"❌ FAILED: {result['error']}")
        return False
    else:
        print(f"✅ PASSED - Max spend: ${result.get('max_monthly_spend', 0):,.2f}/month")
        return True

def test_with_contributions():
    """Test with pre-retirement contributions (previously hardcoded to 0)"""
    result = call_mcp_tool({
        "current_age": 50,
        "retirement_age": 65,
        "savings_rrsp": 300000,
        "savings_tfsa": 100000,
        "rrsp_contribution": 26000,
        "tfsa_contribution": 7000,
        "non_registered_contribution": 5000,
        "province": "ON"
    }, "Test 2: With Annual Contributions")
    
    if "error" in result:
        print(f"❌ FAILED: {result['error']}")
        return False
    else:
        print(f"✅ PASSED - Max spend: ${result.get('max_monthly_spend', 0):,.2f}/month")
        return True

def test_db_pension_advanced():
    """Test advanced DB pension parameters"""
    result = call_mcp_tool({
        "current_age": 58,
        "retirement_age": 65,
        "savings_rrsp": 200000,
        "savings_tfsa": 100000,
        "db_enabled": True,
        "db_pension_income": 50000,
        "db_start_age": 65,
        "db_index_before_retirement": True,
        "db_index_after_retirement_to_cpi": True,
        "db_cpp_clawback_fraction": 0.6,
        "db_survivor_benefit_percentage": 0.60,
        "has_10_year_guarantee": True,
        "province": "ON"
    }, "Test 3: DB Pension with Advanced Parameters")
    
    if "error" in result:
        print(f"❌ FAILED: {result['error']}")
        return False
    else:
        print(f"✅ PASSED - Max spend: ${result.get('max_monthly_spend', 0):,.2f}/month")
        return True

def test_survivor_expense():
    """Test survivor expense percent for couple"""
    result = call_mcp_tool({
        "current_age": 60,
        "retirement_age": 65,
        "savings_rrsp": 500000,
        "savings_tfsa": 150000,
        "spouse_age": 58,
        "spouse_savings_rrsp": 400000,
        "spouse_savings_tfsa": 120000,
        "survivor_expense_percent": 70.0,
        "province": "ON"
    }, "Test 4: Couple with Survivor Expense 70%")
    
    if "error" in result:
        print(f"❌ FAILED: {result['error']}")
        return False
    else:
        print(f"✅ PASSED - Max spend: ${result.get('max_monthly_spend', 0):,.2f}/month ({result.get('mode', 'N/A')})")
        return True

def test_expense_phases():
    """Test expense phases (go-go, slow-go, no-go retirement)"""
    result = call_mcp_tool({
        "current_age": 60,
        "retirement_age": 65,
        "savings_rrsp": 800000,
        "savings_tfsa": 200000,
        "expense_phases": [
            {"duration_years": 10, "expense_change_pct": 0.0},
            {"duration_years": 10, "expense_change_pct": -30.0},
            {"duration_years": 7, "expense_change_pct": -50.0}
        ],
        "province": "ON"
    }, "Test 5: Expense Phases (Go-Go, Slow-Go, No-Go)")
    
    if "error" in result:
        print(f"❌ FAILED: {result['error']}")
        return False
    else:
        print(f"✅ PASSED - Max spend: ${result.get('max_monthly_spend', 0):,.2f}/month")
        return True

def test_spouse_symmetry():
    """Test spouse-specific parameters (previously hardcoded)"""
    result = call_mcp_tool({
        "current_age": 60,
        "retirement_age": 65,
        "savings_rrsp": 500000,
        "savings_non_reg": 100000,
        "non_registered_growth_capital_gains_pct": 90.0,
        "non_registered_dividend_yield_pct": 2.0,
        "spouse_age": 58,
        "spouse_savings_rrsp": 400000,
        "spouse_savings_non_reg": 150000,
        "spouse_non_registered_growth_capital_gains_pct": 50.0,
        "spouse_non_registered_dividend_yield_pct": 4.0,
        "spouse_rrsp_contribution": 15000,
        "spouse_tfsa_contribution": 7000,
        "province": "ON"
    }, "Test 6: Spouse with Different Investment Assumptions")
    
    if "error" in result:
        print(f"❌ FAILED: {result['error']}")
        return False
    else:
        print(f"✅ PASSED - Max spend: ${result.get('max_monthly_spend', 0):,.2f}/month ({result.get('mode', 'N/A')})")
        return True

def test_additional_events():
    """Test additional income/expense events"""
    result = call_mcp_tool({
        "current_age": 60,
        "retirement_age": 65,
        "savings_rrsp": 500000,
        "additional_events": [
            {
                "year": 2026,
                "type": "income",
                "amount": 50000.0,
                "is_cpi_indexed": False,
                "tax_treatment": "non_taxable"
            }
        ],
        "spouse_age": 58,
        "spouse_additional_events": [
            {
                "year": 2027,
                "type": "expense",
                "amount": 20000.0,
                "is_cpi_indexed": True
            }
        ],
        "province": "ON"
    }, "Test 7: Additional Income/Expense Events")
    
    if "error" in result:
        print(f"❌ FAILED: {result['error']}")
        return False
    else:
        print(f"✅ PASSED - Max spend: ${result.get('max_monthly_spend', 0):,.2f}/month")
        return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("MCP Server Enhanced Parameters Test Suite")
    print("=" * 60)
    
    if not os.environ.get("NOWCAPITAL_API_KEY"):
        print("\n⚠️  WARNING: NOWCAPITAL_API_KEY not set")
        print("Using test key - may not work with real backend")
    
    tests = [
        test_basic_scenario,
        test_with_contributions,
        test_db_pension_advanced,
        test_survivor_expense,
        test_expense_phases,
        test_spouse_symmetry,
        test_additional_events
    ]
    
    results = []
    for test_func in tests:
        try:
            passed = test_func()
            results.append(passed)
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("=" * 60)

if __name__ == "__main__":
    main()
