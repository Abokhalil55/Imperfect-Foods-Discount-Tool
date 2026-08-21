"""Seller inventory maintenance menu for the Python CLI."""

from database import delete_store_item, get_inventory, get_store_name, update_item_stock
from inventory import display_inventory


def update_items_seller(store_id):
    """Allow a seller to mark items sold out or permanently delete listings."""
    while True:
        try:
            choice = int(
                input(
                    "\n" * 2
                    + "=" * 22
                    + "\nOwner Inventory Menu:\n"
                    + "=" * 22
                    + "\n1. Mark item as SOLD OUT"
                    + "\n2. Delete item"
                    + "\n3. Back to main menu"
                    + "\n\nYour choice: "
                )
            )
        except ValueError:
            print("[!] Invalid input. Choose 1 to mark SOLD OUT, 2 to delete, or 3 to exit.")
            continue

        # Option 1: mark one seller-owned item as SOLD OUT.
        if choice == 1:
            display_inventory(store_id)
            inventory_items = get_inventory(store_id)
            if not inventory_items:
                print(f"\n[!] No items found in your store: '{get_store_name(store_id)}'.")
                continue

            try:
                item_id = int(input("\nEnter Item ID to mark as SOLD OUT: "))
            except ValueError:
                print("[!] Invalid ID format.")
                continue

            selected_item = next((item for item in inventory_items if item["id"] == item_id), None)
            if not selected_item:
                print(f"[!] Item ID {item_id} was not found in {get_store_name(store_id)}.")
                continue

            if str(selected_item.get("status")).upper() == "SOLD OUT":
                print(f"[!] Item ID {item_id} is already marked SOLD OUT.")
                continue

            confirm = input(
                f"Are you sure you want to mark Item ID {item_id} as SOLD OUT? (y/n): "
            ).strip().lower()
            if confirm != "y":
                print("[*] Operation canceled.")
                continue

            # Pass store_id as an ownership check. The database helper verifies
            # the resulting Supabase row instead of trusting an empty API body.
            updated = update_item_stock(item_id, 0, "SOLD OUT", store_id=store_id)
            if updated:
                print(f"[✓] Item ID {item_id} is now SOLD OUT.")
            else:
                print(f"[!] Item ID {item_id} could not be updated.")

        # Option 2: permanently remove one seller-owned inventory listing.
        # Historical sales remain because their foreign key uses SET NULL.
        elif choice == 2:
            display_inventory(store_id)
            inventory_items = get_inventory(store_id)
            if not inventory_items:
                print(f"\n[!] No items found in your store: '{get_store_name(store_id)}'.")
                continue

            try:
                item_id = int(input("\nEnter Item ID to delete: "))
            except ValueError:
                print("[!] Invalid ID format.")
                continue

            selected_item = next((item for item in inventory_items if item["id"] == item_id), None)
            if not selected_item:
                print(f"[!] Item ID {item_id} was not found in {get_store_name(store_id)}.")
                continue

            confirm = input(
                f"Are you sure you want to PERMANENTLY delete item ID {item_id}? (y/n): "
            ).strip().lower()
            if confirm != "y":
                print("[*] Deletion canceled.")
                continue

            deleted = delete_store_item(store_id, item_id)
            if deleted:
                print(f"[✓] Item ID {item_id} successfully deleted from inventory.")
            else:
                print(f"[!] Item ID {item_id} could not be deleted.")

        # Option 3: leave this submenu without ending the application.
        elif choice == 3:
            print("Returning to main menu...")
            break
        else:
            print("[!] Invalid choice. Please enter 1, 2, or 3.")
