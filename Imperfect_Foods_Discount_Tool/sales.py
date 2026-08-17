# ==============================================================================
# Sales Transactions & Ledger Module
# ==============================================================================

from database import get_sales_history, update_item_stock, record_sale, customer_location, get_available_inventory
from inventory import display_inventory_customer


def buy_food_item(customer_id):
    """Handles item purchase workflow and syncs directly with Supabase."""
    location = customer_location()

    
    inventory_items = get_available_inventory(location)
    
    if not inventory_items:
        print(f"\n[!] No items available to buy for location: '{location}'.")
        return

    # Display items formatted for customer view
    display_inventory_customer(location)
    print("\n--- [ Buy / Sell Food Item ] ---")

    try:
        item_id = int(input("Enter Item ID to purchase: "))
    except ValueError:
        print("[!] Invalid ID format.")
        return

    selected_item = next((item for item in inventory_items if item['id'] == item_id), None)

    if not selected_item:
        print(f"[!] Item ID {item_id} not found at {location}.")
        return

    if selected_item['status'] == 'SOLD OUT' or selected_item['quantity'] <= 0:
        print(f"[!] Sorry, '{selected_item['name']}' is SOLD OUT!")
        return

    while True:
        try:
            buy_qty = float(input(f"Enter quantity to buy (Available: {selected_item['quantity']} kg/u): "))
            if buy_qty <= 0:
                print("Quantity must be greater than 0.")
                continue
            if buy_qty > selected_item['quantity']:
                print(f"[!] Insufficient stock! Maximum available is {selected_item['quantity']}.")
                continue
            break
        except ValueError:
            print("[!] Please enter a valid numerical quantity.")

    total_cost = buy_qty * selected_item['new_price']
    new_quantity = selected_item['quantity'] - buy_qty
    new_status = 'SOLD OUT' if new_quantity == 0 else 'AVAILABLE'

    # Update item stock in inventory database
    update_item_stock(selected_item['id'], new_quantity, new_status)

    sale_data = {
        'store_id': selected_item['store_id'],
        'item_id': selected_item['id'],
        'customer_id': customer_id,
        'item_name': selected_item['name'],
        'location': location,
        'quantity_bought': buy_qty,
        'unit_price': selected_item['new_price'],
        'total_amount': total_cost
    }
    
    record_sale(sale_data)

    print("\n" + "*"*45)
    print("         PURCHASE SUCCESSFUL! 🛒")
    print("*"*45)
    print(f"Item Purchased:  {selected_item['name']}")
    print(f"Quantity Bought: {buy_qty} kg/u")
    print(f"Unit Price:      ${selected_item['new_price']:.2f}")
    print(f"Total Amount:    ${total_cost:.2f}")
    print(f"Remaining Stock: {new_quantity} kg/u ({new_status})")
    print("*"*45)


def view_sales_ledger(store_id):


    """Displays completed sales history and revenue metrics from Supabase."""
    
    # Fetch sales history from Supabase
    sales = get_sales_history(store_id)

    if not sales:
        print(f"\n[!] No purchases/sales have been made yet for '{store_id}'.")
        return

    total_revenue = sum(sale['total_amount'] for sale in sales)
    total_quantity_sold = sum(sale['quantity_bought'] for sale in sales)

    print("\n\n" + "="*90)
    print(f"                     COMPLETED SALES LEDGER ({store_id})")
    print("="*90)
    print(f"{'Item Name':<15} | {'Location':<17} | {'Category':<12} | {'Sold Qty':<10} | {'Price/u':<8} | {'Total ($)':<10}")
    print("="*90)

    for sale in sales:
        # Extract category from join relation (if inventory record still exists)
        category = sale.get('inventory', {}).get('category', 'N/A') if sale.get('inventory') else 'N/A'
        
        sold_qty_str = f"{sale['quantity_bought']:.1f} kg/u"
        unit_price_str = f"${sale['unit_price']:.2f}"
        total_amount_str = f"${sale['total_amount']:.2f}"

        print(f"{sale['item_name']:<15} | {sale['location']:<17} | {category:<12} | {sold_qty_str:<10} | {unit_price_str:<8} | {total_amount_str:<10}")

    print("="*90)
    print(f"TOTAL UNITS SOLD:    {total_quantity_sold:.1f} kg/units")
    print(f"TOTAL REVENUE EARNED: ${total_revenue:.2f}")
    print("="*90)