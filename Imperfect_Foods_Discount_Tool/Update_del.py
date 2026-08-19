from database import get_inventory, update_item_stock, get_store_name, delete_store_item
from inventory import display_inventory

def update_items_seller(store_id):
    while True:
        try:
            cat_map = int(input("\n" * 2 + "=" * 22 + '\nOwner Inventory Menu:\n' + "=" * 22 + '\n1. Mark item as SOLD OUT\n2. Delete item\n3. Back to main menu\n\nYour choice: '))
            
            # --- TASK 1: MARK ITEM AS SOLD OUT ---
            if cat_map == 1:
                display_inventory(store_id)
                inventory_items = get_inventory(store_id)
                
                if not inventory_items:
                    print(f"\n[!] No items found in your store: '{get_store_name(store_id)}'.")
                    continue

                print("\n--- [ Mark Item as SOLD OUT ] ---")

                try:
                    item_id = int(input("Enter Item ID to mark as SOLD OUT: "))
                except ValueError:
                    print("[!] Invalid ID format.")
                    continue

                selected_item = next((item for item in inventory_items if item['id'] == item_id), None)

                if not selected_item:
                    print(f"[!] Item ID {item_id} not found at {get_store_name(store_id)}.")
                    continue

                # Check if item is already sold out
                if selected_item.get('status') == 'SOLD OUT':
                    print(f"[!] Item ID {item_id} is already marked as SOLD OUT.")
                    continue

                # Confirm status update to SOLD OUT
                confirm = input(f"Are you sure you want to mark Item ID {item_id} as SOLD OUT? (y/n): ").strip().lower()
                if confirm == 'y':
                    update_item_stock(selected_item['id'], 0, 'SOLD OUT')
                    print(f"[✓] Item {selected_item['id']} has been successfully marked as SOLD OUT.")
                else:
                    print("[*] Operation canceled.")

            # --- TASK 2: DELETE ITEM ---
            elif cat_map == 2:
                display_inventory(store_id)
                inventory_items = get_inventory(store_id)

                if not inventory_items:
                    print(f"\n[!] No items found in your store: '{get_store_name(store_id)}'.")
                    continue

                print("\n--- [ Delete Inventory Item ] ---")

                try:
                    item_id = int(input("Enter Item ID to delete: "))
                except ValueError:
                    print("[!] Invalid ID format.")
                    continue

                selected_item = next((item for item in inventory_items if item['id'] == item_id), None)

                if not selected_item:
                    print(f"[!] Item ID {item_id} not found at {get_store_name(store_id)}.")
                    continue

                confirm = input(f"Are you sure you want to PERMANENTLY delete item ID {item_id}? (y/n): ").strip().lower()
                if confirm == 'y':
                    deleted_data = delete_store_item(store_id, item_id)
                    if deleted_data:
                        print(f"[✓] Item ID {item_id} successfully deleted from inventory.")
                    else:
                        print(f"[!] Failed to delete Item ID {item_id}.")
                else:
                    print("[*] Deletion canceled.")

            # --- TASK 3: BACK TO MAIN MENU ---
            elif cat_map == 3:
                print("Returning to main menu...")
                break

            else:
                print("[!] Invalid choice. Please enter 1, 2, or 3.")

        except ValueError:
            print("[!] Invalid input. Choose 1 to mark as SOLD OUT, 2 to delete, or 3 to exit.")


