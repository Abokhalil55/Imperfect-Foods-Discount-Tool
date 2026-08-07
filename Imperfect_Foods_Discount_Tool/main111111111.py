# ==============================================================================
# BIT2083 FUNDAMENTALS OF COMPUTATIONAL THINKING
# Final Project: Imperfect Foods Discount & Sales Management System
# SDG Target: SDG 2 - Zero Hunger
# ==============================================================================

# Global databases (in-memory storage)
inventory = []
sales_history = []

def display_menu():
    """1. Display Main Menu System"""
    print("\n" + "="*60)
    print("    IMPERFECT FOODS DISCOUNT & SALES SYSTEM (SDG 2)")
    print("="*60)
    print("1. Register Imperfect / Near-Expiry Food Item")
    print("2. View All Inventory & Dynamic Discounts")
    print("3. Buy Food Item (Customer Purchase / Process Sale)")
    print("4. View Storage Advice & Spoilage Alert (NEW)")
    print("5. View Sales & Revenue Summary Ledger (NEW)")
    print("6. Generate Food Waste Diversion & SDG Impact Report")
    print("7. Exit Application")
    print("="*60)

def register_food_item():
    """2. Enter or Record Food Information with Error Handling"""
    print("\n--- [ Register Food Item ] ---")
    item_name = input("Enter Food Item Name (e.g., Banana, Spinach): ").strip()
    
    # NEW FEATURE 1: Category Selection
    print("\nSelect Food Category:")
    print("1. Produce (Fruits & Vegetables)")
    print("2. Bakery & Grains")
    print("3. Dairy & Chilled Items")
    print("4. Prepared / Packaged Meals")
    
    category_map = {'1': 'Produce', '2': 'Bakery', '3': 'Dairy', '4': 'Prepared Food'}
    while True:
        cat_choice = input("Select Category (1-4): ").strip()
        if cat_choice in category_map:
            category = category_map[cat_choice]
            break
        print("Invalid selection! Please enter a number between 1 and 4.")

    while True:
        try:
            quantity_kg = float(input("Enter Initial Stock Quantity (in kg/units): "))
            if quantity_kg <= 0:
                print("Quantity must be greater than 0.")
                continue
            break
        except ValueError:
            print("Invalid input! Please enter a numerical value for quantity.")

    while True:
        try:
            original_price = float(input("Enter Original Price per kg/unit ($): "))
            if original_price <= 0:
                print("Price must be greater than 0.")
                continue
            break
        except ValueError:
            print("Invalid input! Please enter a valid price.")

    while True:
        try:
            days_left = int(input("Enter Days Remaining Until Expiry (1-7): "))
            if days_left < 1:
                print("Days remaining must be at least 1 day.")
                continue
            break
        except ValueError:
            print("Invalid input! Please enter an integer number of days.")

    print("\nCosmetic Grade / Flaw Severity:")
    print("1. Grade A - Minor cosmetic flaw (Slight discoloration)")
    print("2. Grade B - Moderate flaw (Odd shape, minor bruising)")
    print("3. Grade C - High flaw / Critical near expiry")
    
    while True:
        grade_choice = input("Select Cosmetic Grade (1-3): ").strip()
        if grade_choice in ['1', '2', '3']:
            grade = 'A' if grade_choice == '1' else 'B' if grade_choice == '2' else 'C'
            break
        print("Invalid choice! Please select 1, 2, or 3.")

    item = {
        'id': len(inventory) + 1,
        'name': item_name,
        'category': category,
        'quantity': quantity_kg,
        'initial_quantity': quantity_kg,
        'original_price': original_price,
        'days_left': days_left,
        'grade': grade,
        'discount_percent': 0.0,
        'new_price': 0.0,
        'status': 'AVAILABLE'
    }
    
    # Calculate discount immediately upon registration
    calculate_dynamic_discount(item)
    inventory.append(item)
    print(f"\nSUCCESS: '{item_name}' (ID: {item['id']}) registered and priced at ${item['new_price']:.2f} ({item['discount_percent']}% OFF)!")

def calculate_dynamic_discount(item):
    """3. Dynamic Pricing Logic Engine"""
    base_discount = 0.0
    
    # Days-left discount logic
    if item['days_left'] == 1:
        base_discount += 45.0
    elif item['days_left'] <= 3:
        base_discount += 30.0
    else:
        base_discount += 15.0

    # Grade defect discount logic
    if item['grade'] == 'C':
        base_discount += 25.0
    elif item['grade'] == 'B':
        base_discount += 15.0
    elif item['grade'] == 'A':
        base_discount += 5.0

    # Max discount capped at 80%
    final_discount = min(base_discount, 80.0)
    new_price = item['original_price'] * (1 - (final_discount / 100))
    
    item['discount_percent'] = final_discount
    item['new_price'] = round(new_price, 2)
    return item

def display_inventory():
    """4. View All Registered Inventory Table"""
    if not inventory:
        print("\n[!] Inventory is currently empty. Please register items first.")
        return

    print("\n" + "="*85)
    print(f"{'ID':<4} | {'Name':<15} | {'Category':<12} | {'Stock':<10} | {'Orig $':<8} | {'Disc %':<8} | {'Sale $':<8} | {'Status':<10}")
    print("="*85)
    for item in inventory:
        stock_str = f"{item['quantity']:.1f} kg/u"
        print(f"{item['id']:<4} | {item['name']:<15} | {item['category']:<12} | {stock_str:<10} | ${item['original_price']:<7.2f} | {item['discount_percent']:<7.1f}% | ${item['new_price']:<7.2f} | {item['status']:<10}")
    print("="*85)

def buy_food_item():
    """NEW FEATURE: BUY / SOLD Transaction Module"""
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

    # Search item by ID
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

    # Process Transaction
    total_cost = buy_qty * selected_item['new_price']
    selected_item['quantity'] -= buy_qty

    if selected_item['quantity'] == 0:
        selected_item['status'] = 'SOLD OUT'

    # Record to Sales History Ledger
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

def view_storage_advice():
    """NEW FEATURE 2: Storage & Preservation Recommendation System"""
    if not inventory:
        print("\n[!] No inventory items available.")
        return

    print("\n" + "="*70)
    print("     STORAGE RECOMMENDATIONS & SPOILAGE PREVENTION ALERTS")
    print("="*70)
    for item in inventory:
        print(f"\nItem: {item['name']} (Category: {item['category']}) | Days Left: {item['days_left']}")
        if item['days_left'] == 1:
            print("  ⚠️ URGENT ACTION: Consume today or freeze immediately!")
        elif item['days_left'] <= 3:
            print("  ⚡ WARNING: Store in airtight container / refrigerated area.")
        else:
            print("  ✅ STABLE: Keep in dry, cool temperature.")

        # Storage tips by Category
        if item['category'] == 'Produce':
            print("  💡 Tip: Keep away from ethylene-producing fruits like apples.")
        elif item['category'] == 'Bakery':
            print("  💡 Tip: Freeze unused portions; do not refrigerate bread to prevent drying.")
        elif item['category'] == 'Dairy':
            print("  💡 Tip: Maintain strict refrigeration at or below 4°C.")
        else:
            print("  💡 Tip: Follow package re-sealing guidelines.")
    print("="*70)

def view_sales_ledger():
    """NEW FEATURE 3: Sales History Ledger and Revenue Tracker"""
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

def generate_waste_report():
    """5. Food Waste Diversion & SDG Impact Report"""
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

def main():
    """Main Program Loop Controller"""
    while True:
        display_menu()
        choice = input("Enter your choice (1-7): ").strip()
        
        if choice == '1':
            register_food_item()
        elif choice == '2':
            display_inventory()
        elif choice == '3':
            buy_food_item()
        elif choice == '4':
            view_storage_advice()
        elif choice == '5':
            view_sales_ledger()
        elif choice == '6':
            generate_waste_report()
        elif choice == '7':
            print("\nThank you for supporting SDG 2 Zero Hunger! Exiting...")
            break
        else:
            print("\n[!] Invalid selection! Please choose a number between 1 and 7.")

if __name__ == "__main__":
    main()