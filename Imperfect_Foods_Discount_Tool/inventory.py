from database import (
    add_item,
    customer_location,
    get_available_inventory,
    get_customer_purchase_history,
    get_inventory,
    process_item_and_notifications,
)
from evaluator import evaluate_added_item
from pricing import calculate_dynamic_discount


def register_food_item(store_id):
    """Enter or record food information with store association and user validation."""
    print("\n--- [ Register Food Item ] ---")
    location = customer_location()

    print("\nSelect Food Category:")
    print("1. Produce (Fruits & Vegetables)")
    print("2. Bakery & Grains")
    print("3. Dairy & Chilled Items")
    print("4. Prepared / Packaged Meals")

    category_map = {
        "1": "Produce",
        "2": "Bakery & Grains",
        "3": "Dairy & Chilled Items",
        "4": "Prepared / Packaged Meals",
    }
    while True:
        cat_choice = input("Select Category (1-4): ").strip()
        if cat_choice in category_map:
            category = category_map[cat_choice]
            break
        print("Invalid selection! Please enter a number between 1 and 4.")

    item_name = input("Enter Food Item Name (e.g., Banana, Spinach): ").strip()

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
            original_price = float(input("Enter Original Price per kg/unit (MYR): "))
            if original_price <= 0:
                print("Price must be greater than 0.")
                continue
            break
        except ValueError:
            print("Invalid input! Please enter a valid price.")

    while True:
        try:
            days_left = int(input("Enter Days Remaining Until Expiry (1-7): "))
            if not 1 <= days_left <= 7:
                print("Days remaining must be between 1 and 7.")
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
        if grade_choice in ["1", "2", "3"]:
            grade = "A" if grade_choice == "1" else "B" if grade_choice == "2" else "C"
            break
        print("Invalid choice! Please select 1, 2, or 3.")

    item = {
        "store_id": store_id,
        "location": location,
        "name": item_name,
        "category": category,
        "quantity": quantity_kg,
        "initial_quantity": quantity_kg,
        "original_price": original_price,
        "initial_days_left": days_left,
        "days_left": days_left,
        "grade": grade,
        "discount_percent": 0.0,
        "new_price": 0.0,
        "status": "AVAILABLE",
    }

    result = evaluate_added_item(item)
    if result["status"] == "APPROVED":
        calculate_dynamic_discount(item)
        add_item(item, store_id)
        process_item_and_notifications(item)
        print(
            f"\nSUCCESS: '{item_name}' (category: {item['category']}) registered and priced at "
            f"RM {item['new_price']:.2f} ({item['discount_percent']}% OFF)!"
        )
    else:
        print(
            f"\nFAILED: '{item_name}' (category: {item['category']}) failed to register. "
            f"\nReason: {result['reason']}"
        )


def display_inventory(store_id):
    """View all registered inventory items from Supabase in a formatted table."""
    inventory_items = get_inventory(store_id)

    if not inventory_items:
        print(f"\n[!] Inventory for '{store_id}' is currently empty. Please register items first.")
        return

    print(f"\n\nstore_id: {store_id}")
    print("=" * 145)
    print(
        f"{'ID':<4} | {'Location':<17} | {'Category':<17} | {'Name':<15} | "
        f"{'Days Left':<8} | {'Stock':<10} | {'Orig MYR':<10} | {'Disc %':<8} | "
        f"{'Sale MYR':<10} | {'Status':<10}"
    )
    print("=" * 145)

    for item in inventory_items:
        stock_str = f"{item['quantity']:.1f} kg/u"
        disc_str = f"{item['discount_percent']:.1f} %"
        orig_price_str = f"RM {item['original_price']:.2f}"
        sale_price_str = f"RM {item['new_price']:.2f}"

        print(
            f"{item['id']:<4} | {item['location']:<17} | {item['category']:<17} | "
            f"{item['name']:<15} | {item['days_left']:<8} | {stock_str:<10} | "
            f"{orig_price_str:<10} | {disc_str:<8} | {sale_price_str:<10} | "
            f"{item['status']:<10}"
        )

    print("=" * 145)


def display_inventory_customer(location):
    """View available customer inventory from Supabase in a formatted table."""
    inventory_items = get_available_inventory(location)

    if not inventory_items:
        print(f"\n[!] Inventory for '{location}' is currently empty. Please register items first.")
        return

    print(f"\n\nLocation: {location}")
    print("=" * 165)
    print(
        f"{'ID':<4} | {'Store Name':<20} | {'Category':<25} | {'Name':<15} | "
        f"{'Days left':<15} | {'Stock':<10} | {'Orig MYR':<10} | {'Disc %':<8} | "
        f"{'Sale MYR':<10} | {'Status':<10}"
    )
    print("=" * 165)

    for item in inventory_items:
        store_info = item.get("stores") or {}
        if isinstance(store_info, list):
            store_info = store_info[0] if store_info else {}
        store_name = item.get("store_name") or store_info.get("name", "N/A")

        stock_str = f"{item['quantity']:.1f} kg/u"
        disc_str = f"{item['discount_percent']:.1f} %"
        orig_price_str = f"RM {item['original_price']:.2f}"
        sale_price_str = f"RM {item['new_price']:.2f}"

        print(
            f"{item['id']:<4} | {store_name:<20} | {item['category']:<25} | "
            f"{item['name']:<15} | {item['days_left']:<15} | {stock_str:<10} | "
            f"{orig_price_str:<10} | {disc_str:<8} | {sale_price_str:<10} | "
            f"{item['status']:<10}"
        )

    print("=" * 165)


def display_customer_purchase_history(customer_id):
    """View personal purchase history for a specific customer in a formatted table."""
    history_items = get_customer_purchase_history(customer_id)

    if not history_items:
        print("\n[!] No purchase history found for your account.")
        return

    print("\n--- [ My Purchase History ] ---")
    print("=" * 128)
    print(
        f"{'ID':<4} | {'Store Name':<20} | {'Item Name':<15} | {'Location':<15} | "
        f"{'Bought':<10} | {'Unit MYR':<10} | {'Total MYR':<10} | {'Date':<19}"
    )
    print("=" * 128)

    for record in history_items:
        store_info = record.get("stores") or {}
        store_name = store_info.get("name") or record.get("store_name", "N/A")

        qty_str = f"{record['quantity_bought']:.1f} kg/u"
        unit_price_str = f"RM {record['unit_price']:.2f}"
        total_price_str = f"RM {record['total_amount']:.2f}"

        raw_date = str(record.get("created_at", ""))
        date_str = raw_date[:16].replace("T", " ") if raw_date else "N/A"

        print(
            f"{record['id']:<4} | "
            f"{store_name:<20} | "
            f"{record['item_name']:<15} | "
            f"{record['location']:<15} | "
            f"{qty_str:<10} | "
            f"{unit_price_str:<10} | "
            f"{total_price_str:<10} | "
            f"{date_str:<19}"
        )

    print("=" * 128)
