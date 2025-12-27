
import os
import requests
import json
import sys
from fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("NowCapital Retirement Planner")

@mcp.tool()
def calculate_sustainable_spend(
    current_age: int, 
    retirement_age: int, 
    province: str = "ON",
    total_savings: float = 0,
    savings_rrsp: float = 0,
    savings_tfsa: float = 0,
    savings_non_reg: float = 0,
    # Advanced Options (Person 1)
    name: str = "User",
    death_age: int = 92,
    non_reg_acb: float | None = None,
    lira: float = 0,
    tfsa_contribution_room: float = 0,
    rrsp_contribution_room: float = 0,
    cpp_start_age: int = 65,
    oas_start_age: int = 65,
    base_cpp_amount: float = 17196.0,  # Max CPP for 2025
    base_oas_amount: float = 8876.0,   # OAS for 2025
    db_enabled: bool = False,
    db_pension_income: float = 0,
    db_start_age: int = 65,
    db_index_before_retirement: bool = True,
    db_index_after_retirement: float = 0.0,
    enable_rrsp_meltdown: bool = False,
    lif_conversion_age: int = 71,
    rrif_conversion_age: int = 71,
    lif_type: int = 1,
    # DB Pension Advanced (Person 1)
    db_index_after_retirement_to_cpi: bool = False,
    db_cpp_clawback_fraction: float = 0.0,
    db_survivor_benefit_percentage: float = 0.0,
    pension_plan_type: str = "Generic",
    has_10_year_guarantee: bool = False,
    has_supplementary_death_benefit: bool = False,
    db_share_to_spouse: float = 0.0,
    db_is_survivor_pension: bool = False,
    # Contributions (Person 1)
    rrsp_contribution: float = 0.0,
    tfsa_contribution: float = 0.0,
    non_registered_contribution: float = 0.0,
    # Investment Assumptions (Person 1 & Global)
    non_registered_growth_capital_gains_pct: float = 90.0,
    non_registered_dividend_yield_pct: float = 2.0,
    non_registered_eligible_dividend_proportion_pct: float = 70.0,
    # Additional Events (Person 1)
    additional_events: list[dict] | None = None,
    
    # Couple Options (Person 2)
    spouse_name: str = "Spouse",
    spouse_age: int | None = None,
    spouse_retirement_age: int | None = None,
    spouse_death_age: int = 92,
    spouse_total_savings: float = 0,
    spouse_savings_rrsp: float = 0,
    spouse_savings_tfsa: float = 0,
    spouse_savings_non_reg: float = 0,
    spouse_non_reg_acb: float | None = None,
    spouse_lira: float = 0,
    spouse_tfsa_contribution_room: float = 0,
    spouse_rrsp_contribution_room: float = 0,
    spouse_cpp_start_age: int = 65,
    spouse_oas_start_age: int = 65,
    spouse_base_cpp_amount: float = 0.0, 
    spouse_base_oas_amount: float = 8876.0, 
    spouse_db_enabled: bool = False,
    spouse_db_pension_income: float = 0,
    spouse_db_start_age: int = 65,
    spouse_db_index_before_retirement: bool = True,
    spouse_db_index_after_retirement: float = 0.0,
    spouse_enable_rrsp_meltdown: bool = False,
    spouse_lif_conversion_age: int = 71,
    spouse_rrif_conversion_age: int = 71,
    spouse_lif_type: int = 1,
    # DB Pension Advanced (Person 2/Spouse)
    spouse_db_index_after_retirement_to_cpi: bool = False,
    spouse_db_cpp_clawback_fraction: float = 0.0,
    spouse_db_survivor_benefit_percentage: float = 0.0,
    spouse_pension_plan_type: str = "Generic",
    spouse_has_10_year_guarantee: bool = False,
    spouse_has_supplementary_death_benefit: bool = False,
    spouse_db_share_to_spouse: float = 0.0,
    spouse_db_is_survivor_pension: bool = False,
    # Contributions (Person 2/Spouse)
    spouse_rrsp_contribution: float = 0.0,
    spouse_tfsa_contribution: float = 0.0,
    spouse_non_registered_contribution: float = 0.0,
    # Investment Assumptions (Person 2/Spouse)
    spouse_non_registered_growth_capital_gains_pct: float = 90.0,
    spouse_non_registered_dividend_yield_pct: float = 2.0,
    spouse_non_registered_eligible_dividend_proportion_pct: float = 70.0,
    # Additional Events (Person 2/Spouse)
    spouse_additional_events: list[dict] | None = None,
    
    # Global/Scenario Inputs
    income_split: bool | None = None,
    expected_returns: float = 5.0,
    cpi: float = 2.0,
    allocation: float = 50.0,  # For couples: % of expenses covered by person 1 (default 50% = equal split)
    base_tfsa_amount: float = 7000.0,
    survivor_expense_percent: float = 100.0,
    expense_phases: list[dict] | None = None
) -> dict:
    """
    Calculates the maximum monthly amount a user (and optional spouse) can spend in retirement.
    
    Args:
        current_age: Age today.
        retirement_age: Desired retirement age.
        province: Canadian province and territory code (e.g., 'ON', 'BC').
        total_savings: (Optional) Lump sum of savings. Used if specific account values are not provided.
        savings_rrsp: (Optional) Specific amount in RRSP.
        savings_tfsa: (Optional) Specific amount in TFSA.
        savings_non_reg: (Optional) Specific amount in Non-Registered accounts.
        name: (Optional) Name of the primary person.
        death_age: (Optional) Age of death for planning (default 92).
        non_reg_acb: (Optional) Adjusted Cost Base for Non-Registered assets. Used to calculate capital gains tax. If not provided, assumes ACB equals current balance (no unrealized gains).
        lira: (Optional) Locked-in Retirement Account balance.
        tfsa_contribution_room: (Optional) Available TFSA contribution room.
        rrsp_contribution_room: (Optional) Available RRSP contribution room.
        cpp_start_age: (Optional) Age to start CPP (60-70).
        oas_start_age: (Optional) Age to start OAS (65-70).
        base_cpp_amount: (Optional) Expected annual CPP amount at age 65 (max $17,196 for 2025).
        base_oas_amount: (Optional) Expected annual OAS amount at age 65 ($8,876 for 2025).
        db_enabled: (Optional) Person 1 has a Defined Benefit pension.
        db_pension_income: (Optional) Annual DB pension income (future dollars at start age).
        db_start_age: (Optional) Age DB pension starts.
        db_index_before_retirement: (Optional) Does DB pension index to inflation before retirement?
        db_index_after_retirement: (Optional) Annual indexing % after retirement (e.g. 0.0 for no indexing).
        enable_rrsp_meltdown: (Optional) Strategy to withdraw RRSP funds earlier than minimum requirements to reduce future RRIF minimums and OAS clawback risk.
        lif_conversion_age: (Optional) Age to convert LIRA to LIF (max 71).
        rrif_conversion_age: (Optional) Age to convert RRSP to RRIF (max 71).
        lif_type: (Optional) LIF type (default 1).
        db_index_after_retirement_to_cpi: (Optional) Index DB to CPI after retirement instead of fixed %.
        db_cpp_clawback_fraction: (Optional) Bridge benefit clawback when CPP starts (0.0-1.0). e.g., 1.0 means the full bridge benefit is clawed back dollar-for-dollar when CPP starts; 0.5 means 50% clawback.
        db_survivor_benefit_percentage: (Optional) % of pension continuing to survivor (e.g., 0.60).
        pension_plan_type: (Optional) Pension plan type.
        has_10_year_guarantee: (Optional) Pension has 10-year guarantee.
        has_supplementary_death_benefit: (Optional) Pension has death benefit.
        db_share_to_spouse: (Optional) Pension share to spouse.
        db_is_survivor_pension: (Optional) Whether this is a survivor pension.
        rrsp_contribution: (Optional) Annual RRSP contributions made BEFORE retirement (stops at retirement_age).
        tfsa_contribution: (Optional) Annual TFSA contributions made BEFORE retirement (stops at retirement_age).
        non_registered_contribution: (Optional) Annual non-registered contributions made BEFORE retirement (stops at retirement_age).
        non_registered_growth_capital_gains_pct: (Optional) % of growth treated as capital gains (vs interest).
        non_registered_dividend_yield_pct: (Optional) % of non-reg balance that is dividend yield.
        non_registered_eligible_dividend_proportion_pct: (Optional) % of dividends that are eligible.
        additional_events: (Optional) List of additional income/expense events for Person 1.
             Each event is a dict: {'year': int, 'type': 'income'|'expense', 'amount': float, 'is_cpi_indexed': bool, 'tax_treatment': 'non_taxable'|'employment'|'self_employment'}.
        spouse_name: (Optional) Name of spouse.
        spouse_age: (Optional) Provide this to trigger a COUPLE simulation.
        spouse_retirement_age: (Optional) Defaults to primary retirement age if missing.
        spouse_death_age: (Optional) Spouse's life expectancy for planning (default 92).
        spouse_total_savings: (Optional) Lump sum savings for spouse.
        spouse_savings_rrsp: (Optional) Spouse RRSP.
        spouse_savings_tfsa: (Optional) Spouse TFSA.
        spouse_savings_non_reg: (Optional) Spouse Non-Reg.
        spouse_non_reg_acb: (Optional) Spouse Non-Reg ACB. Used to calculate capital gains tax. If not provided, assumes ACB equals current balance (no unrealized gains).
        spouse_lira: (Optional) Spouse LIRA.
        spouse_cpp_start_age: (Optional) Spouse CPP start age.
        spouse_oas_start_age: (Optional) Spouse OAS start age.
        spouse_base_cpp_amount: (Optional) Spouse expected annual CPP (max $17,196 for 2025).
        spouse_base_oas_amount: (Optional) Spouse expected annual OAS ($8,876 for 2025).
        spouse_db_enabled: (Optional) Spouse has DB pension.
        spouse_db_pension_income: (Optional) Spouse DB annual income.
        spouse_db_start_age: (Optional) Spouse DB start age.
        spouse_db_index_before_retirement: (Optional) Spouse DB indexes before retirement.
        spouse_db_index_after_retirement: (Optional) Spouse DB indexing % after retirement.
        spouse_enable_rrsp_meltdown: (Optional) Spouse RRSP meltdown strategy. Withdraw RRSP funds earlier than minimum requirements to reduce future RRIF minimums and OAS clawback risk.
        spouse_lif_conversion_age: (Optional) Spouse LIRA to LIF conversion age.
        spouse_rrif_conversion_age: (Optional) Spouse RRSP to RRIF conversion age.
        spouse_lif_type: (Optional) Spouse LIF type.
        spouse_db_index_after_retirement_to_cpi: (Optional) Spouse DB indexes to CPI after retirement.
        spouse_db_cpp_clawback_fraction: (Optional) Spouse DB bridge benefit clawback (0.0-1.0). e.g., 1.0 means the full bridge benefit is clawed back
        spouse_db_survivor_benefit_percentage: (Optional) Spouse DB survivor benefit % (e.g., 0.60).
        spouse_pension_plan_type: (Optional) Spouse pension plan type.
        spouse_has_10_year_guarantee: (Optional) Spouse pension has 10-year guarantee.
        spouse_has_supplementary_death_benefit: (Optional) Spouse pension has death benefit.
        spouse_db_share_to_spouse: (Optional) Spouse pension share allocation.
        spouse_db_is_survivor_pension: (Optional) Spouse is receiving survivor pension.
        spouse_rrsp_contribution: (Optional) Spouse annual RRSP contributions (pre-retirement). Stops at spouse_retirement_age.
        spouse_tfsa_contribution: (Optional) Spouse annual TFSA contributions (pre-retirement). Stops at spouse_retirement_age.
        spouse_non_registered_contribution: (Optional) Spouse annual non-registered contributions (pre-retirement). Stops at spouse_retirement_age.
        spouse_non_registered_growth_capital_gains_pct: (Optional) Spouse % growth as capital gains.
        spouse_non_registered_dividend_yield_pct: (Optional) Spouse dividend yield %.
        spouse_non_registered_eligible_dividend_proportion_pct: (Optional) Spouse % eligible dividends.
        spouse_additional_events: (Optional) List of additional income/expense events for Spouse. See additional_events for structure.
        income_split: (Optional) Enable pension income splitting (defaults to True for couples if not specified). Allows splitting eligible pension income between spouses to minimize household taxes. Only applies to RRIF/LIF income and DB pensions (age 65+). 
        expected_returns: (Optional) Nominal expected portfolio return %.
        cpi: (Optional) Inflation rate %.
        allocation: (Optional) For couples: % of household expenses covered by person 1 (default 50%). Person 2 covers the remaining %. Example: 60 means person 1 pays 60% of expenses, spouse pays 40%. This determines how household expenses are split for tax optimization purposes. 
        base_tfsa_amount: (Optional) Annual new TFSA room.
        survivor_expense_percent: (Optional) % of expenses when one spouse passes (default 100%). "100% means expenses stay the same when one spouse passes; 70% means expenses drop to 70% of couple amount.
        expense_phases: (Optional) List of spending phases, e.g., [{'duration_years': 10, 'expense_change_pct': -2}]. Each expense phase percentage is applied ANNUALLY and compounds over the duration. The change is relative to the previous year's spending level, creating an upward or downward slope. The returned max_monthly_spend represents the spending level in YEAR 1 of retirement, with subsequent years adjusted according to the expense phases. Example: If max_monthly_spend returns $10,000 with expense_phases=[{'duration_years': 10, 'expense_change_pct': -2}], you spend $10,000/month in year 1, $9,800 in year 2, $9,604 in year 3, etc., decreasing 2% annually for 10 years (approximately 18% total decrease by year 10). Use positive values to increase spending over time, negative to decrease, and 0 to maintain flat spending. All amounts are inflation-adjusted.
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
    p1_total = p1_rrsp + p1_tfsa + p1_non_reg + lira
    
    # Logic for ACB (Adjusted Cost Base)
    if non_reg_acb is not None:
        p1_cost_basis = float(non_reg_acb)
    else:
        p1_cost_basis = p1_non_reg * 0.9 if p1_non_reg > 0 else 0

    # --- Person 2 Data (Determine Compatibility) ---
    is_couple = spouse_age is not None
    p2_age = spouse_age if is_couple else current_age
    p2_retire = spouse_retirement_age if spouse_retirement_age else retirement_age
    
    p2_rrsp, p2_tfsa, p2_non_reg = distribute_savings(spouse_total_savings, spouse_savings_rrsp, spouse_savings_tfsa, spouse_savings_non_reg)
    p2_total = p2_rrsp + p2_tfsa + p2_non_reg + spouse_lira
    
    if spouse_non_reg_acb is not None:
        p2_cost_basis = float(spouse_non_reg_acb)
    else:
        p2_cost_basis = p2_non_reg * 0.9 if p2_non_reg > 0 else 0

    # Determine income splitting default
    final_income_split = income_split if income_split is not None else is_couple

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
            "lira": lira,
            "cost_basis": p1_cost_basis,
            "rrsp_contribution_room": rrsp_contribution_room,
            "tfsa_contribution_room": tfsa_contribution_room,
            
            # Retirement Benefits
            "cpp_start_age": cpp_start_age, 
            "oas_start_age": oas_start_age, 
            "base_cpp_amount": base_cpp_amount,
            "base_oas_amount": base_oas_amount, 
            
            # DB Pension
            "db_enabled": db_enabled,
            "db_pension_income": db_pension_income,
            "db_start_age": db_start_age,
            "db_index_before_retirement": db_index_before_retirement,
            "db_index_after_retirement": db_index_after_retirement,
            "db_index_after_retirement_to_cpi": db_index_after_retirement_to_cpi,
            "db_cpp_clawback_fraction": db_cpp_clawback_fraction,
            "db_survivor_benefit_percentage": db_survivor_benefit_percentage,
            "pension_plan_type": pension_plan_type,
            "has_10_year_guarantee": has_10_year_guarantee,
            "has_supplementary_death_benefit": has_supplementary_death_benefit,
            "db_share_to_spouse": db_share_to_spouse,
            "db_is_survivor_pension": db_is_survivor_pension,

            # Advanced Logic
            "enable_rrsp_meltdown": enable_rrsp_meltdown,
            "lif_conversion_age": lif_conversion_age,
            "rrif_conversion_age": rrif_conversion_age,
            "lif_type": lif_type,
            "non_registered_growth_capital_gains_pct": non_registered_growth_capital_gains_pct,
            "non_registered_dividend_yield_pct": non_registered_dividend_yield_pct,
            "non_registered_eligible_dividend_proportion_pct": non_registered_eligible_dividend_proportion_pct,
            
            # Contributions
            "rrsp_contribution": rrsp_contribution,
            "tfsa_contribution": tfsa_contribution,
            "non_registered_contribution": non_registered_contribution,
        },
        "person2_ui": {
            "name": spouse_name,
            "current_age": p2_age,
            "retirement_age": p2_retire,
            "death_age": spouse_death_age,
            "rrsp": p2_rrsp,
            "tfsa": p2_tfsa,
            "non_registered": p2_non_reg,
            "lira": spouse_lira,
            "cost_basis": p2_cost_basis,
            "rrsp_contribution_room": spouse_rrsp_contribution_room,
            "tfsa_contribution_room": spouse_tfsa_contribution_room,
            
            "cpp_start_age": spouse_cpp_start_age, 
            "oas_start_age": spouse_oas_start_age, 
            "base_cpp_amount": spouse_base_cpp_amount if is_couple else 0,
            "base_oas_amount": spouse_base_oas_amount if is_couple else 0,
            
            "db_enabled": spouse_db_enabled,
            "db_pension_income": spouse_db_pension_income,
            "db_start_age": spouse_db_start_age,
            "db_index_before_retirement": spouse_db_index_before_retirement,
            "db_index_after_retirement": spouse_db_index_after_retirement,
            "db_index_after_retirement_to_cpi": spouse_db_index_after_retirement_to_cpi,
            "db_cpp_clawback_fraction": spouse_db_cpp_clawback_fraction,
            "db_survivor_benefit_percentage": spouse_db_survivor_benefit_percentage,
            "pension_plan_type": spouse_pension_plan_type,
            "has_10_year_guarantee": spouse_has_10_year_guarantee,
            "has_supplementary_death_benefit": spouse_has_supplementary_death_benefit,
            "db_share_to_spouse": spouse_db_share_to_spouse,
            "db_is_survivor_pension": spouse_db_is_survivor_pension,
            
            "enable_rrsp_meltdown": spouse_enable_rrsp_meltdown,
            "lif_conversion_age": spouse_lif_conversion_age,
            "rrif_conversion_age": spouse_rrif_conversion_age,
            "lif_type": spouse_lif_type,
            "non_registered_growth_capital_gains_pct": spouse_non_registered_growth_capital_gains_pct,
            "non_registered_dividend_yield_pct": spouse_non_registered_dividend_yield_pct,
            "non_registered_eligible_dividend_proportion_pct": spouse_non_registered_eligible_dividend_proportion_pct,
            
            "rrsp_contribution": spouse_rrsp_contribution,
            "tfsa_contribution": spouse_tfsa_contribution,
            "non_registered_contribution": spouse_non_registered_contribution,
        },
        "inputs": {
            "expected_returns": expected_returns, 
            "cpi": cpi,              
            "province": province,
            "individual": not is_couple,
            "income_split": final_income_split,
            "rrif_min_withdrawal": False,
            "allocation": allocation,       
            "base_tfsa_amount": base_tfsa_amount,
            "survivor_expense_percent": survivor_expense_percent,
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

    # Add expense_phases if provided
    if expense_phases is not None:
        payload["inputs"]["expense_phases"] = expense_phases

    # Add additional_events if provided
    if additional_events is not None:
        payload["person1_ui"]["additional_events"] = additional_events
        
    if spouse_additional_events is not None:
        payload["person2_ui"]["additional_events"] = spouse_additional_events


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
            
        # Add notes about advanced features used
        features_used = []
        if db_enabled: features_used.append(f"DB Pension (${db_pension_income:,.0f}/yr)")
        if lira > 0: features_used.append("LIRA")
        if enable_rrsp_meltdown: features_used.append("RRSP Meltdown")
        
        feature_str = ""
        if features_used:
            feature_str = f" [Includes: {', '.join(features_used)}]"

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
                f"{narrative_intro}{feature_str}, "
                f"you can sustainably spend approximately **${max_monthly:,.2f} per month** (after-tax, inflation-adjusted, in today's dollars) "
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
    import argparse
    
    # Set up argument parsing to switch between modes
    parser = argparse.ArgumentParser(description="NowCapital MCP Server")
    parser.add_argument(
        "--transport", 
        default="stdio", 
        choices=["stdio", "http", "sse"], 
        help="Transport mode: 'stdio' (default), 'http' (Streamable), or 'sse' (Legacy)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind to (only for http/sse)"
    )
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Host to bind to (only for http/sse)"
    )
    
    args = parser.parse_args()

    if args.transport == "http":
        print(f"🚀 Starting Streamable HTTP Server on {args.host}:{args.port}")
        print(f"🔗 MCP Endpoint: http://{args.host}:{args.port}/mcp")
        mcp.run(transport="http", host=args.host, port=args.port)
        
    elif args.transport == "sse":
        print(f"📡 Starting SSE Server (Legacy) on {args.host}:{args.port}")
        print(f"🔗 MCP Endpoint: http://{args.host}:{args.port}/sse")
        mcp.run(transport="sse", host=args.host, port=args.port)
        
    else:
        # Default: Run in standard input/output mode
        mcp.run(transport="stdio")