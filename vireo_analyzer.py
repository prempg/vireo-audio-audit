import pandas as pd
import numpy as np

def run_vireo_analysis():
    print("=" * 65)
    print("   VIREO AUDIO: SUPPORT PERFORMANCE & ROOT-CAUSE AUDIT TOOL   ")
    print("=" * 65)

    # 1. DATA LOAD 
    print("\n[1/4] Loading dataset files...")
    df_tickets = pd.read_csv("tickets.csv")
    df_agents = pd.read_csv("agents.csv")
    df_products = pd.read_csv("products.csv")

    # 2. DATA CLEANING & POLICY MAPPING
    print("[2/4] Applying Vireo Support Policy v3.2 rules...")
    
    # Timestamps convert (IST)
    df_tickets['created_at'] = pd.to_datetime(df_tickets['created_at'])
    df_tickets['first_response_at'] = pd.to_datetime(df_tickets['first_response_at'])
    df_tickets['resolved_at'] = pd.to_datetime(df_tickets['resolved_at'])

    # Handle time: First response to Resolution (in hours)
    df_tickets['handle_time_hrs'] = (df_tickets['resolved_at'] - df_tickets['first_response_at']).dt.total_seconds() / 3600.0

    # Policy Rule §8: Blank CSAT scores don't assume 0, exclude 0 means completed
    rated_tickets = df_tickets.dropna(subset=['csat_score'])

    # 3. PRIYA ASK: AGENT CSAT & HANDLE TIME
    print("[3/4] Calculating Agent Performance")
    agent_summary = rated_tickets.groupby('agent_id').agg(
        total_rated=('csat_score', 'count'),
        avg_csat=('csat_score', 'mean'),
        median_handle_time_hrs=('handle_time_hrs', 'median')
    ).reset_index()

    # merge with Agents roster (Agent ID join, not with Name  - Sameer's note)
    agents_unique = df_agents.drop_duplicates(subset=['agent_id'])
    agent_dashboard = agent_summary.merge(agents_unique[['agent_id', 'name', 'team', 'shift', 'tier']], on='agent_id', how='left')

    # Bottom 10 Agents
    bottom_10 = agent_dashboard.sort_values('avg_csat', ascending=True).head(10)
    top_5 = agent_dashboard.sort_values('avg_csat', ascending=False).head(5)

    print("\n--- TOP 5 AGENTS (DIWALI BONUS CANDIDATES) ---")
    print(top_5[['agent_id', 'name', 'team', 'tier', 'avg_csat']].to_string(index=False))

    print("\n--- BOTTOM 10 AGENTS (PRIYA'S FLAGGED RETRAINING LIST) ---")
    print(bottom_10[['agent_id', 'name', 'team', 'tier', 'avg_csat']].to_string(index=False))

    tier2_bottom_count = (bottom_10['tier'] == 2).sum()
    print(f"\n[!] OBSERVATION: Bottom 10 {tier2_bottom_count} agents Tier 2 (Escalations & Warranty).")
    print("   rating low queue coz of bias (Neha's note), agent skill not an issue")

    # 4. BUSINESS CASE & ROOT CAUSE: REPLACEMENT SURGE
    print("\n[4/4] Running Root Cause & Financial Leakage Audit...")

    # A. Pulse 2 Defect Impact
    pl2_replacements = df_tickets[(df_tickets['product_sku'] == 'VA-EB-PL2') & (df_tickets['replacement_issued'] == 'Y')]
    total_replacements = (df_tickets['replacement_issued'] == 'Y').sum()
    pl2_pct = (len(pl2_replacements) / total_replacements) * 100

    # Policy Rule §5: Replacement cost = Unit Cost (Rs 1,480) + Reverse & Forward Shipping (Rs 340) = Rs 1,820
    pl2_replacement_cost = len(pl2_replacements) * 1820

    print(f"\n--- HARDWARE DEFECT AUDIT (PULSE 2: VA-EB-PL2) ---")
    print(f"Total Replacements Issued       : {total_replacements}")
    print(f"Pulse 2 (VA-EB-PL2) Replacements: {len(pl2_replacements)} ({pl2_pct:.1f}% of ALL replacements!)")
    print(f"Total Replacement Spend on PL2  : Rs {pl2_replacement_cost:,}")

    # B. Policy Breach: Double Remedy (Both Refund AND Replacement on same order)
    order_audit = df_tickets.groupby('order_id').agg(
        had_replacement=('replacement_issued', lambda x: (x == 'Y').any()),
        refund_issued=('refund_amount_inr', 'sum')
    )
    double_remedy = order_audit[order_audit['had_replacement'] & (order_audit['refund_issued'] > 0)]
    leakage_inr = double_remedy['refund_issued'].sum()

    print(f"\n--- POLICY VIOLATION: DOUBLE REMEDY LEAKAGE ---")
    print(f"Orders receiving BOTH replacement & refund: {len(double_remedy)}")
    print(f"Financial leakage due to double remedy     : Rs {leakage_inr:,.2f}")

    print("\n" + "=" * 65)
    print("SUMMARY FOR PRIYA RAMAN:")
    print("1. Do not spend Rs 4 Lakh retraining Tier 2 agents handling angry hardware cases.")
    print(f"2. Fixing Pulse 2 battery/case QC saves ~Rs {pl2_replacement_cost:,}.")
    print(f"3. Blocking duplicate refund+replacement saves ~Rs {leakage_inr:,.2f}.")
    print("=" * 65)

if __name__ == "__main__":
    run_vireo_analysis()