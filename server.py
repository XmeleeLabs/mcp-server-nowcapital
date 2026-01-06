import os
import requests
import json
import sys
import argparse
import time
import csv
import io
from fastmcp import FastMCP, Context

# Initialize FastMCP Server
mcp = FastMCP("NowCapital Retirement Planner")

def get_api_key(ctx: Context | None, user_arg: str | None) -> str | None:
    """
    Retrieves the API Key using a hybrid approach.
    Priority:
    1. Explicit Argument (if user provided it in chat)
    2. HTTP Headers via Context (if FastMCP gateway forwards them)
    3. Environment Variable (server-side fallback)
    """
    # 1. Explicit Argument
    if user_arg:
        return user_arg

    # 2. Context / Headers (The "FastMCP Gateway" method)
    if ctx:
        # Different FastMCP implementations/versions expose headers differently.
        # We check the most common locations for forwarded headers.
        
        # Check A: Direct 'headers' attribute
        headers = getattr(ctx, "headers", None)
        
        # Check B: 'meta' dictionary (common in MCP for request metadata)
        if not headers and hasattr(ctx, "meta"):
            headers = ctx.meta.get("headers")
            
        # Check C: 'request' object
        if not headers and hasattr(ctx, "request") and hasattr(ctx.request, "headers"):
            headers = ctx.request.headers

        if headers:
            # Look for standard Auth headers
            # Case-insensitive lookup is best, but dicts are usually case-sensitive.
            # We try common variations.
            for key, val in headers.items():
                k_lower = key.lower()
                if k_lower == "authorization":
                    # Remove 'Bearer ' prefix if present
                    return val.replace("Bearer ", "").replace("bearer ", "").strip()
                if k_lower == "x-api-key":
                    return val.strip()

    # 3. Environment Variable (Local/Server-side key)
    return os.environ.get("NOWCAPITAL_API_KEY")

def construct_payload(
    current_age: int, 
    retirement_age: int, 
    province: str,
    total_savings: float,
    savings_rrsp: float,
    savings_tfsa: float,
    savings_non_reg: float,
    name: str,
    death_age: int,
    non_reg_acb: float | None,
    lira: float,
    tfsa_contribution_room: float,
    rrsp_contribution_room: float,
    cpp_start_age: int,
    oas_start_age: int,
    base_cpp_amount: float,
    base_oas_amount: float,
    db_enabled: bool,
    db_pension_income: float,
    db_start_age: int,
    db_index_before_retirement: bool,
    db_index_after_retirement: float,
    enable_rrsp_meltdown: bool,
    lif_conversion_age: int,
    rrif_conversion_age: int,
    lif_type: int,
    db_index_after_retirement_to_cpi: bool,
    db_cpp_clawback_fraction: float,
    db_survivor_benefit_percentage: float,
    pension_plan_type: str,
    has_10_year_guarantee: bool,
    has_supplementary_death_benefit: bool,
    db_share_to_spouse: float,
    db_is_survivor_pension: bool,
    rrsp_contribution: float,
    tfsa_contribution: float,
    non_registered_contribution: float,
    non_registered_growth_capital_gains_pct: float,
    non_registered_dividend_yield_pct: float,
    non_registered_eligible_dividend_proportion_pct: float,
    additional_events: list[dict] | None,
    spouse_name: str,
    spouse_age: int | None,
    spouse_retirement_age: int | None,
    spouse_death_age: int,
    spouse_total_savings: float,
    spouse_savings_rrsp: float,
    spouse_savings_tfsa: float,
    spouse_savings_non_reg: float,
    spouse_non_reg_acb: float | None,
    spouse_lira: float,
    spouse_tfsa_contribution_room: float,
    spouse_rrsp_contribution_room: float,
    spouse_cpp_start_age: int,
    spouse_oas_start_age: int,
    spouse_base_cpp_amount: float, 
    spouse_base_oas_amount: float, 
    spouse_db_enabled: bool,
    spouse_db_pension_income: float,
    spouse_db_start_age: int,
    spouse_db_index_before_retirement: bool,
    spouse_db_index_after_retirement: float,
    spouse_enable_rrsp_meltdown: bool,
    spouse_lif_conversion_age: int,
    spouse_rrif_conversion_age: int,
    spouse_lif_type: int,
    spouse_db_index_after_retirement_to_cpi: bool,
    spouse_db_cpp_clawback_fraction: float,
    spouse_db_survivor_benefit_percentage: float,
    spouse_pension_plan_type: str,
    spouse_has_10_year_guarantee: bool,
    spouse_has_supplementary_death_benefit: bool,
    spouse_db_share_to_spouse: float,
    spouse_db_is_survivor_pension: bool,
    spouse_rrsp_contribution: float,
    spouse_tfsa_contribution: float,
    spouse_non_registered_contribution: float,
    spouse_non_registered_growth_capital_gains_pct: float,
    spouse_non_registered_dividend_yield_pct: float,
    spouse_non_registered_eligible_dividend_proportion_pct: float,
    spouse_additional_events: list[dict] | None,
    income_split: bool | None,
    expected_returns: float,
    cpi: float,
    allocation: float,
    base_tfsa_amount: float,
    survivor_expense_percent: float,
    expense_phases: list[dict] | None,
    enable_belt_tightening: bool = False
) -> dict:
    # Helper to calculate splits
    def distribute_savings(total, r, t, n):
        r, t, n = float(r), float(t), float(n)
        if (r + t + n) == 0 and total > 0:
            return (total * 0.50), (total * 0.20), (total * 0.30)
        return r, t, n

    # --- Person 1 Data ---
    p1_rrsp, p1_tfsa, p1_non_reg = distribute_savings(total_savings, savings_rrsp, savings_tfsa, savings_non_reg)
    
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
    
    if spouse_non_reg_acb is not None:
        p2_cost_basis = float(spouse_non_reg_acb)
    else:
        p2_cost_basis = p2_non_reg * 0.9 if p2_non_reg > 0 else 0

    # Determine income splitting default
    final_income_split = income_split if income_split is not None else is_couple

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
            "cpp_start_age": cpp_start_age, 
            "oas_start_age": oas_start_age, 
            "base_cpp_amount": base_cpp_amount,
            "base_oas_amount": base_oas_amount, 
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
            "enable_rrsp_meltdown": enable_rrsp_meltdown,
            "lif_conversion_age": lif_conversion_age,
            "rrif_conversion_age": rrif_conversion_age,
            "lif_type": lif_type,
            "non_registered_growth_capital_gains_pct": non_registered_growth_capital_gains_pct,
            "non_registered_dividend_yield_pct": non_registered_dividend_yield_pct,
            "non_registered_eligible_dividend_proportion_pct": non_registered_eligible_dividend_proportion_pct,
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

    if expense_phases is not None:
        payload["inputs"]["expense_phases"] = expense_phases
    if additional_events is not None:
        payload["person1_ui"]["additional_events"] = additional_events
    if spouse_additional_events is not None:
        payload["person2_ui"]["additional_events"] = spouse_additional_events

    return payload

def json_to_csv(data_list):
    """Converts a list of dicts to a CSV string to save tokens."""
    if not data_list:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data_list[0].keys())
    writer.writeheader()
    writer.writerows(data_list)
    return output.getvalue()

@mcp.tool()
def calculate_sustainable_spend(
    current_age: int, 
    retirement_age: int, 
    ctx: Context = None,
    user_api_key: str | None = None,
    province: str = "ON",
    total_savings: float = 0,
    savings_rrsp: float = 0,
    savings_tfsa: float = 0,
    savings_non_reg: float = 0,
    name: str = "User",
    death_age: int = 92,
    non_reg_acb: float | None = None,
    lira: float = 0,
    tfsa_contribution_room: float = 0,
    rrsp_contribution_room: float = 0,
    cpp_start_age: int = 65,
    oas_start_age: int = 65,
    base_cpp_amount: float = 17196.0,
    base_oas_amount: float = 8876.0,
    db_enabled: bool = False,
    db_pension_income: float = 0,
    db_start_age: int = 65,
    db_index_before_retirement: bool = True,
    db_index_after_retirement: float = 0.0,
    enable_rrsp_meltdown: bool = False,
    lif_conversion_age: int = 71,
    rrif_conversion_age: int = 71,
    lif_type: int = 1,
    db_index_after_retirement_to_cpi: bool = False,
    db_cpp_clawback_fraction: float = 0.0,
    db_survivor_benefit_percentage: float = 0.0,
    pension_plan_type: str = "Generic",
    has_10_year_guarantee: bool = False,
    has_supplementary_death_benefit: bool = False,
    db_share_to_spouse: float = 0.0,
    db_is_survivor_pension: bool = False,
    rrsp_contribution: float = 0.0,
    tfsa_contribution: float = 0.0,
    non_registered_contribution: float = 0.0,
    non_registered_growth_capital_gains_pct: float = 100.0,
    non_registered_dividend_yield_pct: float = 0.0,
    non_registered_eligible_dividend_proportion_pct: float = 0.0,
    additional_events: list[dict] | None = None,
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
    spouse_db_index_after_retirement_to_cpi: bool = False,
    spouse_db_cpp_clawback_fraction: float = 0.0,
    spouse_db_survivor_benefit_percentage: float = 0.0,
    spouse_pension_plan_type: str = "Generic",
    spouse_has_10_year_guarantee: bool = False,
    spouse_has_supplementary_death_benefit: bool = False,
    spouse_db_share_to_spouse: float = 0.0,
    spouse_db_is_survivor_pension: bool = False,
    spouse_rrsp_contribution: float = 0.0,
    spouse_tfsa_contribution: float = 0.0,
    spouse_non_registered_contribution: float = 0.0,
    spouse_non_registered_growth_capital_gains_pct: float = 100.0,
    spouse_non_registered_dividend_yield_pct: float = 0.0,
    spouse_non_registered_eligible_dividend_proportion_pct: float = 0.0,
    spouse_additional_events: list[dict] | None = None,
    income_split: bool | None = None,
    expected_returns: float = 4.5,
    cpi: float = 2.3,
    allocation: float = 50.0,
    base_tfsa_amount: float = 7000.0,
    survivor_expense_percent: float = 100.0,
    expense_phases: list[dict] | None = None
) -> dict:
    """
    Calculates the maximum sustainable monthly spending (after-tax) for a user (and optional spouse) until death.
    Use this tool when the user asks "How much can I spend?" or wants a single summary number.

    Args:
        # --- Basic Information ---
        current_age: Age today (e.g., 60).
        retirement_age: Desired retirement age (e.g., 65).
        province: Canadian province code: 'ON', 'BC', 'AB', 'QC', 'MB', 'SK', 'NS', 'NB', 'PE', 'NL'.
        total_savings: (Optional) Lump sum of savings. Used if specific account values (RRSP/TFSA) are not provided.
        name: (Optional) Name of the primary person.
        death_age: (Optional) Age of death for planning (default 92).

        # --- Savings Accounts ---
        savings_rrsp: (Optional) RRSP balance.
        savings_tfsa: (Optional) TFSA balance.
        savings_non_reg: (Optional) Non-Registered (Cash/Margin) balance.
        lira: (Optional) Locked-in Retirement Account (LIRA) balance.
        non_reg_acb: (Optional) Adjusted Cost Base for Non-Registered assets. Used to calculate capital gains tax. If not provided, assumes ACB equals current balance (no unrealized gains).

        # --- Annual Contributions (Pre-Retirement Only) ---
        rrsp_contribution: (Optional) Annual RRSP contribution (stops at retirement_age).
        tfsa_contribution: (Optional) Annual TFSA contribution (stops at retirement_age).
        non_registered_contribution: (Optional) Annual Non-Reg contribution (stops at retirement_age).
        rrsp_contribution_room: (Optional) Available RRSP contribution room.
        tfsa_contribution_room: (Optional) Available TFSA contribution room.

        # --- Government Benefits ---
        cpp_start_age: (Optional) Age to start CPP (Standard is 65. Range 60-70).
        oas_start_age: (Optional) Age to start OAS (Standard is 65. Range 65-70).
        base_cpp_amount: (Optional) Expected annual CPP amount at age 65 (max ~$16k).
        base_oas_amount: (Optional) Expected annual OAS amount at age 65 (max ~$8k).

        # --- Defined Benefit (DB) Pension ---
        db_enabled: (Optional) Set to True if Person 1 has a DB pension.
        db_pension_income: (Optional) Annual DB pension income (in future dollars at start age).
        db_start_age: (Optional) Age DB pension payments begin.
        db_index_before_retirement: (Optional) True if pension indexes to inflation before retirement.
        db_index_after_retirement: (Optional) Annual indexing % after retirement (e.g., 2.0 for 2%).
        db_index_after_retirement_to_cpi: (Optional) True to index strictly to CPI after retirement.
        db_cpp_clawback_fraction: (Optional) Bridge benefit clawback fraction (0.0 to 1.0). 1.0 means the bridge benefit is fully removed when CPP starts.
        db_survivor_benefit_percentage: (Optional) % of pension income the spouse receives after death (e.g., 0.60 for 60%).

        # --- Investment Assumptions ---
        expected_returns: (Optional) Nominal expected portfolio return % (default 4.5).
        cpi: (Optional) Inflation rate % (default 2.3).
        non_registered_growth_capital_gains_pct: (Optional) % of Non-Reg return that is Capital Gains (vs Interest/Dividends). Default 100.0.
        non_registered_dividend_yield_pct: (Optional) % of Non-Reg balance that is dividend yield (default 0.0).

        # --- Advanced Strategy ---
        enable_rrsp_meltdown: (Optional) True to withdraw extra RRSP funds early to reduce future tax liability.
        income_split: (Optional) True to enable pension income splitting between spouses (Optimizes taxes). Default True for couples.
        lif_conversion_age: (Optional) Age to convert LIRA to LIF (max 71).
        rrif_conversion_age: (Optional) Age to convert RRSP to RRIF (max 71).

        # --- Complex Cash Flow Events ---
        additional_events: (Optional) List of dictionaries for one-time or recurring cash flows.
            Structure: [{'year': int, 'type': 'income'|'expense', 'amount': float, 'is_cpi_indexed': bool, 'tax_treatment': 'non_taxable'|'employment'|'self_employment'}]
            Example: [{'year': 2030, 'type': 'income', 'amount': 50000, 'is_cpi_indexed': False, 'tax_treatment': 'non_taxable'}]

        expense_phases: (Optional) List of spending phases that adjust the sustainable spend over time.
            Structure: [{'duration_years': int, 'expense_change_pct': float}]
            Note: expense_change_pct compounds ANNUALLY. -2.0 means spending drops by 2% every year for the duration.

        # --- Spouse / Couple Inputs ---
        spouse_age: (Optional) Providing this TRIGGERS a couple simulation.
        spouse_name: (Optional) Spouse's name.
        spouse_retirement_age: (Optional) Spouse's retirement age (defaults to Person 1's if missing).
        spouse_total_savings: (Optional) Spouse's lump sum savings.
        spouse_savings_rrsp: (Optional) Spouse's RRSP balance.
        spouse_savings_tfsa: (Optional) Spouse's TFSA balance.
        spouse_savings_non_reg: (Optional) Spouse's Non-Reg balance.
        spouse_db_enabled: (Optional) True if Spouse has a DB pension.
        spouse_db_pension_income: (Optional) Spouse's DB annual income.
        allocation: (Optional) Percentage of total household expenses covered by Person 1 (0-100). Default 50.0.
        survivor_expense_percent: (Optional) Percentage of household expenses remaining after one spouse dies (default 100.0). 70.0 means expenses drop by 30%.
    """
    final_api_key = get_api_key(ctx, user_api_key)
    if not final_api_key:
        return {"error": "Authentication Failed. Please provide your 'user_api_key' as an argument."}

    api_url = os.environ.get("NOWCAPITAL_API_BASE_URL")
    if not api_url:
        return {"error": "API URL missing. Please set the NOWCAPITAL_API_BASE_URL environment variable."}

    payload = construct_payload(
        current_age, retirement_age, province, total_savings, savings_rrsp, savings_tfsa, savings_non_reg,
        name, death_age, non_reg_acb, lira, tfsa_contribution_room, rrsp_contribution_room, cpp_start_age,
        oas_start_age, base_cpp_amount, base_oas_amount, db_enabled, db_pension_income, db_start_age,
        db_index_before_retirement, db_index_after_retirement, enable_rrsp_meltdown, lif_conversion_age,
        rrif_conversion_age, lif_type, db_index_after_retirement_to_cpi, db_cpp_clawback_fraction,
        db_survivor_benefit_percentage, pension_plan_type, has_10_year_guarantee, has_supplementary_death_benefit,
        db_share_to_spouse, db_is_survivor_pension, rrsp_contribution, tfsa_contribution, non_registered_contribution,
        non_registered_growth_capital_gains_pct, non_registered_dividend_yield_pct, non_registered_eligible_dividend_proportion_pct,
        additional_events, spouse_name, spouse_age, spouse_retirement_age, spouse_death_age, spouse_total_savings,
        spouse_savings_rrsp, spouse_savings_tfsa, spouse_savings_non_reg, spouse_non_reg_acb, spouse_lira,
        spouse_tfsa_contribution_room, spouse_rrsp_contribution_room, spouse_cpp_start_age, spouse_oas_start_age,
        spouse_base_cpp_amount, spouse_base_oas_amount, spouse_db_enabled, spouse_db_pension_income,
        spouse_db_start_age, spouse_db_index_before_retirement, spouse_db_index_after_retirement, spouse_enable_rrsp_meltdown,
        spouse_lif_conversion_age, spouse_rrif_conversion_age, spouse_lif_type, spouse_db_index_after_retirement_to_cpi,
        spouse_db_cpp_clawback_fraction, spouse_db_survivor_benefit_percentage, spouse_pension_plan_type,
        spouse_has_10_year_guarantee, spouse_has_supplementary_death_benefit, spouse_db_share_to_spouse,
        spouse_db_is_survivor_pension, spouse_rrsp_contribution, spouse_tfsa_contribution, spouse_non_registered_contribution,
        spouse_non_registered_growth_capital_gains_pct, spouse_non_registered_dividend_yield_pct,
        spouse_non_registered_eligible_dividend_proportion_pct, spouse_additional_events, income_split,
        expected_returns, cpi, allocation, base_tfsa_amount, survivor_expense_percent, expense_phases
    )

    try:
        response = requests.post(f"{api_url}/calculate-max-spend", json=payload, headers={"X-API-Key": final_api_key}, timeout=10)
        response.raise_for_status()
        data = response.json()
        max_monthly = data.get("max_spend_monthly", 0.0)
        return {
            "max_monthly_spend": max_monthly,
            "currency": "CAD",
            "narrative": f"You can sustainably spend approximately **${max_monthly:,.2f} per month** until age {death_age}."
        }
    except Exception as e:
        return {"error": f"Request Failed: {str(e)}"}

@mcp.tool()
def calculate_detailed_spend_plan(
    current_age: int, 
    retirement_age: int, 
    ctx: Context = None,
    user_api_key: str | None = None,
    province: str = "ON",
    total_savings: float = 0,
    savings_rrsp: float = 0,
    savings_tfsa: float = 0,
    savings_non_reg: float = 0,
    name: str = "User",
    death_age: int = 92,
    non_reg_acb: float | None = None,
    lira: float = 0,
    tfsa_contribution_room: float = 0,
    rrsp_contribution_room: float = 0,
    cpp_start_age: int = 65,
    oas_start_age: int = 65,
    base_cpp_amount: float = 17196.0,
    base_oas_amount: float = 8876.0,
    db_enabled: bool = False,
    db_pension_income: float = 0,
    db_start_age: int = 65,
    db_index_before_retirement: bool = True,
    db_index_after_retirement: float = 0.0,
    enable_rrsp_meltdown: bool = False,
    lif_conversion_age: int = 71,
    rrif_conversion_age: int = 71,
    lif_type: int = 1,
    db_index_after_retirement_to_cpi: bool = False,
    db_cpp_clawback_fraction: float = 0.0,
    db_survivor_benefit_percentage: float = 0.0,
    pension_plan_type: str = "Generic",
    has_10_year_guarantee: bool = False,
    has_supplementary_death_benefit: bool = False,
    db_share_to_spouse: float = 0.0,
    db_is_survivor_pension: bool = False,
    rrsp_contribution: float = 0.0,
    tfsa_contribution: float = 0.0,
    non_registered_contribution: float = 0.0,
    non_registered_growth_capital_gains_pct: float = 100.0,
    non_registered_dividend_yield_pct: float = 0.0,
    non_registered_eligible_dividend_proportion_pct: float = 0.0,
    additional_events: list[dict] | None = None,
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
    spouse_db_index_after_retirement_to_cpi: bool = False,
    spouse_db_cpp_clawback_fraction: float = 0.0,
    spouse_db_survivor_benefit_percentage: float = 0.0,
    spouse_pension_plan_type: str = "Generic",
    spouse_has_10_year_guarantee: bool = False,
    spouse_has_supplementary_death_benefit: bool = False,
    spouse_db_share_to_spouse: float = 0.0,
    spouse_db_is_survivor_pension: bool = False,
    spouse_rrsp_contribution: float = 0.0,
    spouse_tfsa_contribution: float = 0.0,
    spouse_non_registered_contribution: float = 0.0,
    spouse_non_registered_growth_capital_gains_pct: float = 100.0,
    spouse_non_registered_dividend_yield_pct: float = 0.0,
    spouse_non_registered_eligible_dividend_proportion_pct: float = 0.0,
    spouse_additional_events: list[dict] | None = None,
    income_split: bool | None = None,
    expected_returns: float = 4.5,
    cpi: float = 2.3,
    allocation: float = 50.0,
    base_tfsa_amount: float = 7000.0,
    survivor_expense_percent: float = 100.0,
    expense_phases: list[dict] | None = None
) -> dict:
    """
    Calculates a detailed year-by-year retirement plan, returning data in CSV format.
    Use this tool when the user asks for "detailed cash flow," "yearly breakdown," "tax details," or "tables."
    
    Returns:
        A dictionary containing 'max_spend_monthly' and 'person1_yearly_data_csv' (and person2 if couple).
        The CSV data contains columns for Age, Income, Taxes, Account Withdrawals, and Net Income for every year.

    Args:
        # --- Basic Information ---
        current_age: Age today (e.g., 60).
        retirement_age: Desired retirement age (e.g., 65).
        province: Canadian province code: 'ON', 'BC', 'AB', 'QC', 'MB', 'SK', 'NS', 'NB', 'PE', 'NL'.
        total_savings: (Optional) Lump sum of savings. Used if specific account values (RRSP/TFSA) are not provided.
        name: (Optional) Name of the primary person.
        death_age: (Optional) Age of death for planning (default 92).

        # --- Savings Accounts ---
        savings_rrsp: (Optional) RRSP balance.
        savings_tfsa: (Optional) TFSA balance.
        savings_non_reg: (Optional) Non-Registered (Cash/Margin) balance.
        lira: (Optional) Locked-in Retirement Account (LIRA) balance.
        non_reg_acb: (Optional) Adjusted Cost Base for Non-Registered assets. Used to calculate capital gains tax.

        # --- Annual Contributions (Pre-Retirement Only) ---
        rrsp_contribution: (Optional) Annual RRSP contribution (stops at retirement_age).
        tfsa_contribution: (Optional) Annual TFSA contribution (stops at retirement_age).
        non_registered_contribution: (Optional) Annual Non-Reg contribution (stops at retirement_age).
        rrsp_contribution_room: (Optional) Available RRSP contribution room.
        tfsa_contribution_room: (Optional) Available TFSA contribution room.

        # --- Government Benefits ---
        cpp_start_age: (Optional) Age to start CPP (Standard is 65. Range 60-70).
        oas_start_age: (Optional) Age to start OAS (Standard is 65. Range 65-70).
        base_cpp_amount: (Optional) Expected annual CPP amount at age 65.
        base_oas_amount: (Optional) Expected annual OAS amount at age 65.

        # --- Defined Benefit (DB) Pension ---
        db_enabled: (Optional) Set to True if Person 1 has a DB pension.
        db_pension_income: (Optional) Annual DB pension income (in future dollars at start age).
        db_start_age: (Optional) Age DB pension payments begin.
        db_index_before_retirement: (Optional) True if pension indexes to inflation before retirement.
        db_index_after_retirement: (Optional) Annual indexing % after retirement (e.g., 2.0 for 2%).
        db_cpp_clawback_fraction: (Optional) Bridge benefit clawback fraction (0.0 to 1.0).
        db_survivor_benefit_percentage: (Optional) % of pension income the spouse receives after death.

        # --- Investment Assumptions ---
        expected_returns: (Optional) Nominal expected portfolio return % (default 4.5).
        cpi: (Optional) Inflation rate % (default 2.3).
        non_registered_growth_capital_gains_pct: (Optional) % of Non-Reg return that is Capital Gains.

        # --- Advanced Strategy ---
        enable_rrsp_meltdown: (Optional) True to withdraw extra RRSP funds early.
        income_split: (Optional) True to enable pension income splitting between spouses.
        lif_conversion_age: (Optional) Age to convert LIRA to LIF.
        rrif_conversion_age: (Optional) Age to convert RRSP to RRIF.

        # --- Complex Cash Flow Events ---
        additional_events: (Optional) List of dictionaries for one-time or recurring cash flows.
            Structure: [{'year': int, 'type': 'income'|'expense', 'amount': float, 'is_cpi_indexed': bool, 'tax_treatment': 'non_taxable'|'employment'|'self_employment'}]

        expense_phases: (Optional) List of spending phases.
            Structure: [{'duration_years': int, 'expense_change_pct': float}]
            Note: expense_change_pct compounds ANNUALLY.

        # --- Spouse / Couple Inputs ---
        spouse_age: (Optional) Providing this TRIGGERS a couple simulation.
        spouse_name: (Optional) Spouse's name.
        spouse_retirement_age: (Optional) Spouse's retirement age.
        spouse_total_savings: (Optional) Spouse's lump sum savings.
        spouse_savings_rrsp: (Optional) Spouse's RRSP balance.
        spouse_savings_tfsa: (Optional) Spouse's TFSA balance.
        spouse_savings_non_reg: (Optional) Spouse's Non-Reg balance.
        spouse_db_enabled: (Optional) True if Spouse has a DB pension.
        spouse_db_pension_income: (Optional) Spouse's DB annual income.
        allocation: (Optional) Percentage of total household expenses covered by Person 1 (default 50.0).
        survivor_expense_percent: (Optional) Percentage of household expenses remaining after one spouse dies (default 100.0).
    """
    final_api_key = get_api_key(ctx, user_api_key)
    if not final_api_key:
        return {"error": "Authentication Failed."}

    api_url = os.environ.get("NOWCAPITAL_API_BASE_URL")
    if not api_url:
        return {"error": "API URL missing."}

    payload = construct_payload(
        current_age, retirement_age, province, total_savings, savings_rrsp, savings_tfsa, savings_non_reg,
        name, death_age, non_reg_acb, lira, tfsa_contribution_room, rrsp_contribution_room, cpp_start_age,
        oas_start_age, base_cpp_amount, base_oas_amount, db_enabled, db_pension_income, db_start_age,
        db_index_before_retirement, db_index_after_retirement, enable_rrsp_meltdown, lif_conversion_age,
        rrif_conversion_age, lif_type, db_index_after_retirement_to_cpi, db_cpp_clawback_fraction,
        db_survivor_benefit_percentage, pension_plan_type, has_10_year_guarantee, has_supplementary_death_benefit,
        db_share_to_spouse, db_is_survivor_pension, rrsp_contribution, tfsa_contribution, non_registered_contribution,
        non_registered_growth_capital_gains_pct, non_registered_dividend_yield_pct, non_registered_eligible_dividend_proportion_pct,
        additional_events, spouse_name, spouse_age, spouse_retirement_age, spouse_death_age, spouse_total_savings,
        spouse_savings_rrsp, spouse_savings_tfsa, spouse_savings_non_reg, spouse_non_reg_acb, spouse_lira,
        spouse_tfsa_contribution_room, spouse_rrsp_contribution_room, spouse_cpp_start_age, spouse_oas_start_age,
        spouse_base_cpp_amount, spouse_base_oas_amount, spouse_db_enabled, spouse_db_pension_income,
        spouse_db_start_age, spouse_db_index_before_retirement, spouse_db_index_after_retirement, spouse_enable_rrsp_meltdown,
        spouse_lif_conversion_age, spouse_rrif_conversion_age, spouse_lif_type, spouse_db_index_after_retirement_to_cpi,
        spouse_db_cpp_clawback_fraction, spouse_db_survivor_benefit_percentage, spouse_pension_plan_type,
        spouse_has_10_year_guarantee, spouse_has_supplementary_death_benefit, spouse_db_share_to_spouse,
        spouse_db_is_survivor_pension, spouse_rrsp_contribution, spouse_tfsa_contribution, spouse_non_registered_contribution,
        spouse_non_registered_growth_capital_gains_pct, spouse_non_registered_dividend_yield_pct,
        spouse_non_registered_eligible_dividend_proportion_pct, spouse_additional_events, income_split,
        expected_returns, cpi, allocation, base_tfsa_amount, survivor_expense_percent, expense_phases
    )

    try:
        response = requests.post(f"{api_url}/calculate-max-spend-with-yearly-data", json=payload, headers={"X-API-Key": final_api_key}, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        p1_csv = json_to_csv(data.get("person1_yearly_data", []))
        p2_csv = json_to_csv(data.get("person2_yearly_data", []))

        return {
            "max_spend_monthly": data.get("max_spend_monthly"),
            "average_real_monthly_spend": data.get("average_real_monthly_spend"),
            "person1_yearly_data_csv": p1_csv,
            "person2_yearly_data_csv": p2_csv
        }
    except Exception as e:
        return {"error": f"Request Failed: {str(e)}"}

@mcp.tool()
def start_monte_carlo_simulation(
    target_monthly_spend: float,
    current_age: int, 
    retirement_age: int, 
    ctx: Context = None,
    user_api_key: str | None = None,
    num_trials: int = 1000,
    return_std_dev: float = 0.09,
    cpi_std_dev: float = 0.012,
    return_cpi_correlation: float = -0.05,
    province: str = "ON",
    total_savings: float = 0,
    savings_rrsp: float = 0,
    savings_tfsa: float = 0,
    savings_non_reg: float = 0,
    name: str = "User",
    death_age: int = 92,
    non_reg_acb: float | None = None,
    lira: float = 0,
    tfsa_contribution_room: float = 0,
    rrsp_contribution_room: float = 0,
    cpp_start_age: int = 65,
    oas_start_age: int = 65,
    base_cpp_amount: float = 17196.0,
    base_oas_amount: float = 8876.0,
    db_enabled: bool = False,
    db_pension_income: float = 0,
    db_start_age: int = 65,
    db_index_before_retirement: bool = True,
    db_index_after_retirement: float = 0.0,
    enable_rrsp_meltdown: bool = False,
    lif_conversion_age: int = 71,
    rrif_conversion_age: int = 71,
    lif_type: int = 1,
    db_index_after_retirement_to_cpi: bool = False,
    db_cpp_clawback_fraction: float = 0.0,
    db_survivor_benefit_percentage: float = 0.0,
    pension_plan_type: str = "Generic",
    has_10_year_guarantee: bool = False,
    has_supplementary_death_benefit: bool = False,
    db_share_to_spouse: float = 0.0,
    db_is_survivor_pension: bool = False,
    rrsp_contribution: float = 0.0,
    tfsa_contribution: float = 0.0,
    non_registered_contribution: float = 0.0,
    non_registered_growth_capital_gains_pct: float = 100.0,
    non_registered_dividend_yield_pct: float = 0.0,
    non_registered_eligible_dividend_proportion_pct: float = 0.0,
    additional_events: list[dict] | None = None,
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
    spouse_db_index_after_retirement_to_cpi: bool = False,
    spouse_db_cpp_clawback_fraction: float = 0.0,
    spouse_db_survivor_benefit_percentage: float = 0.0,
    spouse_pension_plan_type: str = "Generic",
    spouse_has_10_year_guarantee: bool = False,
    spouse_has_supplementary_death_benefit: bool = False,
    spouse_db_share_to_spouse: float = 0.0,
    spouse_db_is_survivor_pension: bool = False,
    spouse_rrsp_contribution: float = 0.0,
    spouse_tfsa_contribution: float = 0.0,
    spouse_non_registered_contribution: float = 0.0,
    spouse_non_registered_growth_capital_gains_pct: float = 100.0,
    spouse_non_registered_dividend_yield_pct: float = 0.0,
    spouse_non_registered_eligible_dividend_proportion_pct: float = 0.0,
    spouse_additional_events: list[dict] | None = None,
    income_split: bool | None = None,
    expected_returns: float = 4.5,
    cpi: float = 2.3,
    allocation: float = 50.0,
    base_tfsa_amount: float = 7000.0,
    survivor_expense_percent: float = 100.0,
    expense_phases: list[dict] | None = None,
    enable_belt_tightening: bool = False
) -> dict:
    """
    Begins a Monte Carlo risk analysis to determine the Probability of Success for a retirement plan.
    Use this tool when the user asks about "risk," "chance of success," or "running out of money."
    
    Returns:
        A 'job_id' which must be passed to the 'get_monte_carlo_results' tool to see the final report.

    Args:
        # --- Simulation Specific Settings (Crucial) ---
        target_monthly_spend: The desired after-tax monthly spending amount to test (e.g., 5000).
        num_trials: (Optional) Number of simulation runs (default 1000). Higher is more precise but slower.
        return_std_dev: (Optional) Portfolio volatility (Standard Deviation). Default 0.09 (9%).
        cpi_std_dev: (Optional) Inflation volatility. Default 0.012 (1.2%).
        return_cpi_correlation: (Optional) Correlation between market returns and inflation. Default -0.05.

        # --- Basic Information ---
        current_age: Age today.
        retirement_age: Desired retirement age.
        province: Canadian province code (e.g., 'ON').
        total_savings: Total savings amount.

        # --- Account Details ---
        savings_rrsp: (Optional) RRSP balance.
        savings_tfsa: (Optional) TFSA balance.
        savings_non_reg: (Optional) Non-Registered balance.
        lira: (Optional) LIRA balance.

        # --- Contributions ---
        rrsp_contribution: (Optional) Annual RRSP contribution (stops at retirement).
        tfsa_contribution: (Optional) Annual TFSA contribution (stops at retirement).
        non_registered_contribution: (Optional) Annual Non-Reg contribution.

        # --- Pensions & Benefits ---
        cpp_start_age: (Optional) CPP start age.
        oas_start_age: (Optional) OAS start age.
        db_enabled: (Optional) True if Person 1 has a DB pension.
        db_pension_income: (Optional) Annual DB pension income.
        db_start_age: (Optional) DB pension start age.
        db_index_after_retirement: (Optional) DB indexing % (e.g. 2.0).

        # --- Spouse / Couple ---
        spouse_age: (Optional) Providing this TRIGGERS a couple simulation.
        spouse_total_savings: (Optional) Spouse's savings.
        spouse_db_enabled: (Optional) Spouse has DB pension.
        spouse_db_pension_income: (Optional) Spouse DB income.

        # --- Advanced ---
        additional_events: (Optional) List of dicts for extra cash flows (same format as calculate_sustainable_spend).
        expense_phases: (Optional) List of dicts for spending phases (same format as calculate_sustainable_spend).
        survivor_expense_percent: (Optional) % of expenses remaining after death (default 100.0).
        enable_belt_tightening: (Optional) If True, skips inflation adjustment on expenses after a year of negative returns.
    """
    final_api_key = get_api_key(ctx, user_api_key)
    if not final_api_key:
        return {"error": "Authentication Failed."}

    api_url = os.environ.get("NOWCAPITAL_API_BASE_URL")
    if not api_url:
        return {"error": "API URL missing."}

    payload = construct_payload(
        current_age, retirement_age, province, total_savings, savings_rrsp, savings_tfsa, savings_non_reg,
        name, death_age, non_reg_acb, lira, tfsa_contribution_room, rrsp_contribution_room, cpp_start_age,
        oas_start_age, base_cpp_amount, base_oas_amount, db_enabled, db_pension_income, db_start_age,
        db_index_before_retirement, db_index_after_retirement, enable_rrsp_meltdown, lif_conversion_age,
        rrif_conversion_age, lif_type, db_index_after_retirement_to_cpi, db_cpp_clawback_fraction,
        db_survivor_benefit_percentage, pension_plan_type, has_10_year_guarantee, has_supplementary_death_benefit,
        db_share_to_spouse, db_is_survivor_pension, rrsp_contribution, tfsa_contribution, non_registered_contribution,
        non_registered_growth_capital_gains_pct, non_registered_dividend_yield_pct, non_registered_eligible_dividend_proportion_pct,
        additional_events, spouse_name, spouse_age, spouse_retirement_age, spouse_death_age, spouse_total_savings,
        spouse_savings_rrsp, spouse_savings_tfsa, spouse_savings_non_reg, spouse_non_reg_acb, spouse_lira,
        spouse_tfsa_contribution_room, spouse_rrsp_contribution_room, spouse_cpp_start_age, spouse_oas_start_age,
        spouse_base_cpp_amount, spouse_base_oas_amount, spouse_db_enabled, spouse_db_pension_income,
        spouse_db_start_age, spouse_db_index_before_retirement, spouse_db_index_after_retirement, spouse_enable_rrsp_meltdown,
        spouse_lif_conversion_age, spouse_rrif_conversion_age, spouse_lif_type, spouse_db_index_after_retirement_to_cpi,
        spouse_db_cpp_clawback_fraction, spouse_db_survivor_benefit_percentage, spouse_pension_plan_type,
        spouse_has_10_year_guarantee, spouse_has_supplementary_death_benefit, spouse_db_share_to_spouse,
        spouse_db_is_survivor_pension, spouse_rrsp_contribution, spouse_tfsa_contribution, spouse_non_registered_contribution,
        spouse_non_registered_growth_capital_gains_pct, spouse_non_registered_dividend_yield_pct,
        spouse_non_registered_eligible_dividend_proportion_pct, spouse_additional_events, income_split,
        expected_returns, cpi, allocation, base_tfsa_amount, survivor_expense_percent, expense_phases,
        enable_belt_tightening=enable_belt_tightening
    )
    payload["target_monthly_spend"] = target_monthly_spend
    payload["inputs"]["num_trials"] = num_trials
    payload["inputs"]["expected_returns"] = expected_returns / 100
    payload["inputs"]["cpi"] = cpi / 100
    payload["inputs"]["return_std_dev"] = return_std_dev
    payload["inputs"]["cpi_std_dev"] = cpi_std_dev
    payload["inputs"]["return_cpi_correlation"] = return_cpi_correlation

    try:
        response = requests.post(f"{api_url}/monte-carlo", json=payload, headers={"X-API-Key": final_api_key}, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            "job_id": data.get("task_id"),
            "status": "PENDING",
            "message": "Simulation started. This process typically takes between 5 and 15 seconds. Use check_simulation_status to poll."
        }
    except Exception as e:
        return {"error": f"Request Failed: {str(e)}"}

@mcp.tool()
def get_monte_carlo_results(job_id: str, ctx: Context = None, user_api_key: str | None = None) -> dict:
    """
    Retrieves the status and final results of a Monte Carlo simulation.
    Use this tool immediately after 'start_monte_carlo_simulation' returns a job_id.

    Returns:
        A dictionary containing:
        - status: "SUCCESS", "PROCESSING", or "FAILURE".
        - result: If SUCCESS, contains the probability of success, median ending assets, and other risk metrics.

    Args:
        job_id: The unique identifier string returned by the 'start_monte_carlo_simulation' tool.
        user_api_key: (Optional) API Key for authentication (usually handled automatically by the environment).
    """
    final_api_key = get_api_key(ctx, user_api_key)
    if not final_api_key:
        return {"error": "Authentication Failed."}

    api_url = os.environ.get("NOWCAPITAL_API_BASE_URL")
    if not api_url:
        return {"error": "API URL missing."}

    headers = {"X-API-Key": final_api_key}
    
    current_job_id = job_id
    
    # Internal Loop (15 iterations * 2s = 30s)
    # Sufficient for simulations taking up to 30s in a single tool call
    for i in range(15):
        try:
            status_resp = requests.get(f"{api_url}/simulations/status/{current_job_id}", headers=headers, timeout=5)
            status_resp.raise_for_status()
            status_data = status_resp.json()
            
            if status_data.get("status") == "SUCCESS":
                result_resp = requests.get(f"{api_url}/simulations/result/{current_job_id}", headers=headers, timeout=5)
                result_resp.raise_for_status()
                result_body = result_resp.json()
                
                # Check for Orchestrator Link (mimicking UI logic)
                if isinstance(result_body, dict) and "result_id" in result_body and result_body.get("status") == "Orchestrator started":
                    # Found intermediate orchestrator result. Switch ID and keep polling.
                    current_job_id = result_body["result_id"]
                    time.sleep(1)
                    continue

                return {"status": "SUCCESS", "result": result_body}
            
            if status_data.get("status") == "FAILURE":
                return {"status": "FAILURE", "error": status_data.get("error")}
            
            # Still working, sleep before next internal check
            time.sleep(2)
        except Exception as e:
            return {"error": f"Polling Error: {str(e)}"}

    return {
        "status": "PROCESSING",
        "job_id": current_job_id,
        "message": "Simulation is still running. Please poll again in a few seconds."
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NowCapital MCP Server")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "http", "sse"], help="Transport mode")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    args = parser.parse_args()

    if args.transport == "http":
        mcp.run(transport="http", host=args.host, port=args.port)
    elif args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")
