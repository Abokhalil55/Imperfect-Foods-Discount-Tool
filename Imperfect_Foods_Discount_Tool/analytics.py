# In your report module (e.g., reports.py or main.py)
from database import get_inventory, get_sales_history,customer_location

def generate_waste_report():
    """Calculates food waste diverted, environmental metrics, and revenue generated from Supabase."""
    location=customer_location()
    # 1. Fetch live inventory and sales data for the location
    inventory_items = get_inventory(location)
    sales_records = get_sales_history(location)

    if not inventory_items and not sales_records:
        print(f"\n[!] No inventory or sales data available for location: '{location}'.")
        return

    # 2. Compute metrics using Supabase column names
    total_saved_kg = sum(sale['quantity_bought'] for sale in sales_records) if sales_records else 0.0
    total_revenue = sum(sale['total_amount'] for sale in sales_records) if sales_records else 0.0
    
    # 2.5 kg CO2e saved per 1 kg of food waste prevented
    co2_mitigated = total_saved_kg * 2.5  
    total_transactions = len(sales_records) if sales_records else 0

    # 3. Dynamic SDG 2 Impact Index Thresholds
    if total_saved_kg >= 50.0:
        impact_index = "EXCELLENT 🌟"
    elif total_saved_kg >= 10.0:
        impact_index = "GOOD 👍"
    else:
        impact_index = "NEEDS IMPROVEMENT ⚠️"

    # 4. Print SDG 2 Impact Report
    print("\n" + "*"*58)
    print(f"      SDG 2 ZERO HUNGER & WASTE DIVERSION REPORT ({location})")
    print("*"*58)
    print(f"Total Food Saved From Landfill:   {total_saved_kg:.2f} kg")
    print(f"Revenue Recovered for Sellers:   ${total_revenue:.2f}")
    print(f"Estimated CO2 Emissions Avoided: {co2_mitigated:.2f} kg CO2e")
    print(f"Total Transactions Completed:    {total_transactions}")
    print(f"SDG 2 Impact Index:              {impact_index}")
    print("*"*58)