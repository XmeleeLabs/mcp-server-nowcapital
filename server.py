
import os
import requests
import json
import sys
from fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("NowCapitalRetirement Planner")

@mcp.tool()
def calculate_sustainable_spend(
    current_age: int, 
    retirement_age: int, 
    total_savings: float = 0,
    savings_rrsp: float = 0,
    savings_tfsa: float = 0,
    savings_non_reg: float = 0,
    province: str = "ON",
    # Advanced Options (Person 1)
    name: str = "User",
    death_age: int = 92,
    non_reg_acb: float | None = None,
    # Couple Options (Person 2)
    spouse_name: str = "Spouse",
    spouse_age: int | None = None,
    spouse_retirement_age: int | None = None,
    spouse_total_savings: float = 0,
    spouse_savings_rrsp: float = 0,
    spouse_savings_tfsa: float = 0,
    spouse_savings_non_reg: float = 0
) -> dict:
    """
    Calculates the maximum monthly amount a user (and optional spouse) can spend in retirement.
    
    Args:
        current_age: Age today.
        retirement_age: Desired retirement age.
        total_savings: (Optional) Lump sum of savings. Used if specific account values are not provided.
        savings_rrsp: (Optional) Specific amount in RRSP.
        savings_tfsa: (Optional) Specific amount in TFSA.
        savings_non_reg: (Optional) Specific amount in Non-Registered accounts.
        province: Canadian province code (e.g., 'ON', 'BC').
        name: (Optional) Name of the primary person.
        death_age: (Optional) Age of death for planning (default 92).
        non_reg_acb: (Optional) Adjusted Cost Base for Non-Registered assets.
        spouse_name: (Optional) Name of spouse.
        spouse_age: (Optional) Provide this to trigger a COUPLE simulation.
        spouse_retirement_age: (Optional) Defaults to primary retirement age if missing.
        spouse_total_savings: (Optional) Lump sum savings for spouse.
        spouse_savings_rrsp: (Optional) Spouse RRSP.
        spouse_savings_tfsa: (Optional) Spouse TFSA.
        spouse_savings_non_reg: (Optional) Spouse Non-Reg.
    """
    
    # 1. Authentication Check
    api_key = os.environ.get("NOWCAPITAL_API_KEY")
    if not api_key:
        return {"error": "API Key missing. Please set the NOWCAPITAL_API_KEY environment variable."}

    api_url = os.environ.get("NOWCAPITAL_API_BASE_URL")
    if not api_url:
        return {"error": "API URL missing. Please set the NOWCAPITAL_API_BASE_URL environment variable."}

    # Helper to calculate splits
    def distribute_savings(total, r, t, n):
        r, t, n = float(r), float(t), float(n)
        if (r + t + n) == 0 and total > 0:
            return (total * 0.50), (total * 0.20), (total * 0.30)
        return r, t, n

    # --- Person 1 Data ---
    p1_rrsp, p1_tfsa, p1_non_reg = distribute_savings(total_savings, savings_rrsp, savings_tfsa, savings_non_reg)
    p1_total = p1_rrsp + p1_tfsa + p1_non_reg
    
    # Logic for ACB (Adjusted Cost Base)
    # If not provided, assume 90% of value (some growth) if existing, else equal to value (new cash)
    if non_reg_acb is not None:
        p1_cost_basis = float(non_reg_acb)
    else:
        p1_cost_basis = p1_non_reg * 0.9 if p1_non_reg > 0 else 0

    # --- Person 2 Data (Determine Compatibility) ---
    is_couple = spouse_age is not None
    p2_age = spouse_age if is_couple else current_age
    p2_retire = spouse_retirement_age if spouse_retirement_age else retirement_age
    
    p2_rrsp, p2_tfsa, p2_non_reg = distribute_savings(spouse_total_savings, spouse_savings_rrsp, spouse_savings_tfsa, spouse_savings_non_reg)
    p2_total = p2_rrsp + p2_tfsa + p2_non_reg
    
    # 3. Construct the Payload
    payload = {
        "person1_ui": {
            "name": name,
            "current_age": current_age,
            "retirement_age": retirement_age,
            "death_age": death_age, 
            "province": province,
            "rrsp": p1_rrsp,
            "tfsa": p1_tfsa,
            "non_registered": p1_non_reg,
            "cost_basis": p1_cost_basis,
            # Defaults
            "lira": 0.0,
            "rrsp_contribution": 0.0,
            "tfsa_contribution": 0.0,
            "non_registered_contribution": 0.0,
            "cpp_start_age": 65, 
            "oas_start_age": 65, 
            "base_cpp_amount": 10000, 
            "base_oas_amount": 8000, 
            "lif_conversion_age": 71,
            "rrif_conversion_age": 71,
            "lif_type": 1,
            "non_registered_growth_capital_gains_pct": 90.0,
            "non_registered_dividend_yield_pct": 2.0,
            "non_registered_eligible_dividend_proportion_pct": 70.0,
            "db_enabled": False,
            "db_pension_income": 0.0,
        },
        "person2_ui": {
            "name": spouse_name,
            "current_age": p2_age,
            "retirement_age": p2_retire,
            "death_age": death_age,
            "rrsp": p2_rrsp,
            "tfsa": p2_tfsa,
            "non_registered": p2_non_reg,
            "cost_basis": p2_non_reg * 0.9, # Default for spouse ACB
            # Defaults
            "rrsp_contribution": 0, "tfsa_contribution": 0, "non_registered_contribution": 0,
            "cpp_start_age": 65, "oas_start_age": 65, "base_cpp_amount": 10000 if is_couple else 0, "base_oas_amount": 8000 if is_couple else 0,
             "lif_conversion_age": 71, "rrif_conversion_age": 71, "lif_type": 1,
            "db_enabled": False
        },
        "inputs": {
            "expected_returns": 5.0, 
            "cpi": 2.0,              
            "province": province,
            "individual": not is_couple, # Switch API mode
            "income_split": is_couple,   # Enable splitting if couple
            "rrif_min_withdrawal": False,
            "allocation": 100,       
            "base_tfsa_amount": 7000.0
        },
        "withdrawal_strategy": {
            "person1": {
                "weights": [{"type": "fallback", "order": ["rrsp", "non_registered", "tfsa"]}]
            },
            "person2": {
                "weights": [{"type": "fallback", "order": ["rrsp", "non_registered", "tfsa"]}]
            }
        }
    }

    # 4. Call the Backend API
    try:
        response = requests.post(
            f"{api_url}/calculate-max-spend",
            json=payload,
            headers={"X-API-Key": api_key},
            timeout=10
        )
        
        response.raise_for_status()
        data = response.json()
        
        # 5. Interpret Result
        max_monthly = data.get("max_spend_monthly", 0.0)
        
        household_total = p1_total + p2_total
        narrative_intro = f"Based on household assets of ${household_total:,.2f}"
        if is_couple:
            narrative_intro += f" (Couple: {name} & {spouse_name})"
        else:
            narrative_intro += f" (Individual: {name})"

        return {
            "max_monthly_spend": max_monthly,
            "currency": "CAD",
            "mode": "Couple" if is_couple else "Individual",
            "analysis": {
                "p1_total": p1_total,
                "p2_total": p2_total,
                "monthly_spend": max_monthly
            },
            "narrative": (
                f"{narrative_intro}, "
                f"you can sustainably spend approximately **${max_monthly:,.2f} per month** (after-tax, inflation-adjusted) "
                f"until age {death_age}."
            )
        }

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
             return {"error": "Access Denied: Your NOWCAPITAL_API_KEY is invalid or missing permission."}
        return {"error": f"Simulation Failed: The backend returned an error ({e})."}
    except Exception as e:
        return {"error": f"System Error: Could not connect to calculations engine ({str(e)})."}

if __name__ == "__main__":
    # Allow running in SSE mode for debugging or direct HTTP access
    if "sse" in sys.argv:
        mcp.run(transport="sse")
    else:
        mcp.run()
