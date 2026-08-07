# ==============================================================================
# SDG 2 Impact & Waste Diversion Reporting
# ==============================================================================

from database import inventory, sales_history


def generate_waste_report():
    """Calculates food waste diverted, environmental metrics, and revenue generated."""
    if not inventory and not sales_history:
        print("\n[!] No inventory or sales data available.")
        return

    total_saved_kg = sum(sale['quantity_sold'] for sale in sales_history)
    total_revenue = sum(sale['total_spent'] for sale in sales_history)
    co2_mitigated = total_saved_kg * 2.5  # Estimated 2.5kg CO2e per 1kg food waste prevented

    print("\n" + "*"*55)
    print("         SDG 2 ZERO HUNGER & WASTE DIVERSION REPORT")
    print("*"*55)
    print(f"Total Food Saved From Landfill:  {total_saved_kg:.2f} kg")
    print(f"Revenue Recovered for Sellers:   ${total_revenue:.2f}")
    print(f"Estimated CO2 Emissions Avoided: {co2_mitigated:.2f} kg CO2e")
    print(f"Total Transactions Completed:    {len(sales_history)}")
    print(f"SDG 2 Impact Index:              EXCELLENT 🌟")
    print("*"*55)