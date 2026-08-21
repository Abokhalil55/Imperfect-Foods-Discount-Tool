"""Seller inventory maintenance helpers shared by the CLI and web API.

The original project used this module only for the command-line seller menu.
The web interface now calls the same non-interactive helper functions through
``api/index.py`` so both interfaces use one inventory-maintenance workflow.
"""

from database import (
    delete_store_item,
    get_inventory,
    get_item_by_id,
    get_store_name,
    update_item_stock,
)
from inventory import display_inventory


def mark_item_sold_out(item_id, store_id=None):
    """Mark one inventory item as SOLD OUT and set its quantity to zero.

    ``store_id`` is used when available to verify that the item belongs to the
    seller performing the action. The web API and CLI both use this helper, so
    the business rule is defined in one place rather than being duplicated.

    Returns a small result dictionary that can be consumed by either the web
    API or the interactive CLI.
    """
    # The CLI always supplies store_id. The current web button historically
    # sent only item_id, so get_item_by_id keeps that route compatible while
    # api/index.py can also pass store_id when it is available.
    if store_id is not None:
        inventory_items = get_inventory(store_id)
        selected_item = next(
            (item for item in inventory_items if str(item.get("id")) == str(item_id)),
            None,
        )
    else:
        selected_item = get_item_by_id(item_id)

    if not selected_item:
        return {
            "success": False,
            "error": "Item was not found or does not belong to this store.",
        }

    if str(selected_item.get("status") or "").upper() == "SOLD OUT":
        return {
            "success": True,
            "item": selected_item,
            "message": "Item is already marked SOLD OUT.",
        }

    # The database helper performs the actual Supabase UPDATE and verifies the
    # stored row afterward. Setting quantity to zero keeps status and stock
    # consistent for the seller dashboard and customer market.
    updated = update_item_stock(item_id, 0, "SOLD OUT", store_id=store_id)
    if not updated:
        return {
            "success": False,
            "error": "Item could not be marked SOLD OUT.",
        }

    return {
        "success": True,
        "item": updated[0],
        "message": "Item marked SOLD OUT successfully.",
    }


def delete_item_seller(store_id, item_id):
    """Permanently delete one seller-owned inventory listing from Supabase.

    Historical sales are preserved because ``sales_history.item_id`` uses
    ``ON DELETE SET NULL``. Both the CLI and web API use this helper.
    """
    if store_id is None:
        return {"success": False, "error": "Store ID is required."}

    # Check ownership before deleting so one store cannot intentionally remove
    # another seller's listing through this shared helper.
    inventory_items = get_inventory(store_id)
    selected_item = next(
        (item for item in inventory_items if str(item.get("id")) == str(item_id)),
        None,
    )
    if not selected_item:
        return {
            "success": False,
            "error": "Item was not found or does not belong to this store.",
        }

    deleted = delete_store_item(store_id, item_id)
    if not deleted:
        return {"success": False, "error": "Item could not be deleted."}

    return {
        "success": True,
        "item": selected_item,
        "message": "Item deleted successfully.",
    }


def update_items_seller(store_id):
    """Interactive CLI menu for marking items sold out or deleting listings."""
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

        # Option 1: display the seller's inventory and route the selected item
        # through the same helper used by the web Sold Out button.
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

            selected_item = next(
                (item for item in inventory_items if item["id"] == item_id),
                None,
            )
            if not selected_item:
                print(f"[!] Item ID {item_id} was not found in {get_store_name(store_id)}.")
                continue

            if str(selected_item.get("status") or "").upper() == "SOLD OUT":
                print(f"[!] Item ID {item_id} is already marked SOLD OUT.")
                continue

            confirm = input(
                f"Are you sure you want to mark Item ID {item_id} as SOLD OUT? (y/n): "
            ).strip().lower()
            if confirm != "y":
                print("[*] Operation canceled.")
                continue

            result = mark_item_sold_out(item_id, store_id=store_id)
            if result["success"]:
                print(f"[✓] Item ID {item_id} is now SOLD OUT.")
            else:
                print(f"[!] {result['error']}")

        # Option 2: permanently remove one seller-owned inventory listing using
        # the same shared helper used by the web Delete button.
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

            selected_item = next(
                (item for item in inventory_items if item["id"] == item_id),
                None,
            )
            if not selected_item:
                print(f"[!] Item ID {item_id} was not found in {get_store_name(store_id)}.")
                continue

            confirm = input(
                f"Are you sure you want to PERMANENTLY delete item ID {item_id}? (y/n): "
            ).strip().lower()
            if confirm != "y":
                print("[*] Deletion canceled.")
                continue

            result = delete_item_seller(store_id, item_id)
            if result["success"]:
                print(f"[✓] Item ID {item_id} successfully deleted from inventory.")
            else:
                print(f"[!] {result['error']}")

        # Option 3: leave this submenu without ending the application.
        elif choice == 3:
            print("Returning to main menu...")
            break
        else:
            print("[!] Invalid choice. Please enter 1, 2, or 3.")
