# ==============================================================================
# Sales Transactions & Ledger Module
# ==============================================================================

from database import inventory, sales_history
from inventory import display_inventory


def buy_food_item():
    """Handles item purchase workflow and updates sales records."""
    if not inventory:
        print("\n[!] No items available to buy.")
        return

    display_inventory()
    print("\n--- [ Buy / Sell Food Item ] ---")

    try:
        item_id = int(input("Enter Item ID to purchase: "))
    except ValueError:
        print("[!] Invalid ID format.")
        return

    selected_item = next((item for item in inventory if item['id'] == item_id), None)

    if not selected_item:
        print("[!] Item ID not found.")
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
    selected_item['quantity'] -= buy_qty

    if selected_item['quantity'] == 0:
        selected_item['status'] = 'SOLD OUT'

    sale_record = {
        'item_name': selected_item['name'],
        'category': selected_item['category'],
        'quantity_sold': buy_qty,
        'unit_price': selected_item['new_price'],
        'total_spent': round(total_cost, 2),
        'discount_applied': selected_item['discount_percent']
    }
    sales_history.append(sale_record)

    print("\n" + "*"*45)
    print("         PURCHASE SUCCESSFUL! 🛒")
    print("*"*45)
    print(f"Item Purchased:  {selected_item['name']}")
    print(f"Quantity Bought: {buy_qty} kg/u")
    print(f"Unit Price:      ${selected_item['new_price']:.2f}")
    print(f"Total Amount:    ${total_cost:.2f}")
    print(f"Remaining Stock: {selected_item['quantity']} kg/u ({selected_item['status']})")
    print("*"*45)


def view_sales_ledger():
    """Displays completed sales history and revenue metrics."""
    if not sales_history:
        print("\n[!] No purchases/sales have been made yet.")
        return

    total_revenue = sum(sale['total_spent'] for sale in sales_history)
    total_qty_sold = sum(sale['quantity_sold'] for sale in sales_history)

    print("\n" + "="*75)
    print("                   COMPLETED SALES LEDGER")
    print("="*75)
    print(f"{'Item Name':<15} | {'Category':<12} | {'Sold Qty':<10} | {'Price/u':<8} | {'Total ($)':<10}")
    print("="*75)
    for sale in sales_history:
        print(f"{sale['item_name']:<15} | {sale['category']:<12} | {sale['quantity_sold']:<10.1f} | ${sale['unit_price']:<7.2f} | ${sale['total_spent']:<10.2f}")
    print("="*75)
    print(f"TOTAL UNITS SOLD:    {total_qty_sold:.1f} kg/units")
    print(f"TOTAL REVENUE EARNED: ${total_revenue:.2f}")
    print("="*75)