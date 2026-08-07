from database import inventory
from pricing import calculate_dynamic_discount
from evaluator import evaluate_added_item

def register_food_item():
    """Enter or record food information with user validation."""
    print("\n--- [ Register Food Item ] ---")
    item_name = input("Enter Food Item Name (e.g., Banana, Spinach): ").strip()

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
    result = evaluate_added_item(item)
    if result['status'] == 'APPROVED':
        calculate_dynamic_discount(item)
        inventory.append(item)
        print(f"\nSUCCESS: '{item_name}' (ID: {item['id']}) registered and priced at ${item['new_price']:.2f} ({item['discount_percent']}% OFF)!")
    else:
        print(f"\nFAILED: '{item_name}' (ID: {item['id']}) failed to register. \nReason: {result['reason']}")


def display_inventory():
    """View all registered inventory items in a formatted table."""
    if not inventory:
        print("\n[!] Inventory is currently empty. Please register items first.")
        return

    print("\n" + "="*95)
    print(f"{'ID':<4} | {'Name':<15} | {'Category':<12} | {'Stock':<10} | {'Orig $':<8} | {'Disc %':<8} | {'Sale $':<8} | {'Status':<10}")
    print("="*85)
    for item in inventory:
        stock_str = f"{item['quantity']:.1f} kg/u"
        print(f"{item['id']:<4} | {item['name']:<15} | {item['category']:<12} | {stock_str:<10} | ${item['original_price']:<7.2f} | {item['discount_percent']:<7.1f}% | ${item['new_price']:<7.2f} | {item['status']:<10}")
    print("="*95)