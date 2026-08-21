"""Supabase data-access helpers for JimatRasa.

This module is intentionally kept simple for the university project: the rest of
JimatRasa calls small Python functions instead of repeating raw Supabase queries.
It also keeps time-sensitive inventory values (days left, expiry status and
rescue price) synchronized whenever inventory is read.
"""

import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from supabase import Client, create_client

from notifications import send_notification_email
from pricing import calculate_dynamic_discount


# Load server-side credentials from environment variables. Secrets are never
# sent to the browser; only the Python backend talks directly to Supabase.
load_dotenv(override=True)
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_API")
supabase: Client = create_client(url, key)


# -----------------------------------------------------------------------------
# Inventory CRUD helpers
# -----------------------------------------------------------------------------

def add_item(item, store_id):
    """Insert a new inventory item and attach it to the seller's store."""
    item["store_id"] = store_id
    response = supabase.table("inventory").insert(item).execute()
    print(f"Added item to store {store_id} in Supabase")
    return response.data


def _select_item(item_id, store_id=None):
    """Read one item, optionally requiring ownership by a particular store."""
    query = supabase.table("inventory").select("*").eq("id", item_id)
    if store_id is not None:
        query = query.eq("store_id", store_id)
    response = query.limit(1).execute()
    return response.data[0] if response.data else None


def get_item_by_id(item_id, store_id=None):
    """Return one inventory item by ID, optionally limited to one store."""
    return _select_item(item_id, store_id)


def update_item_stock(item_id, new_quantity, new_status, store_id=None):
    """Update one item's stock/status and verify the Supabase write.

    Supabase/PostgREST can legitimately return an empty ``data`` list for an
    UPDATE even when the row was changed. The old code interpreted that empty
    list as a failure, so the web UI reported that "Sold out" did not work.
    This function now verifies the row after the write and returns a normal
    list-shaped result when the database contains the requested values.
    """
    # Confirm the item exists before attempting the mutation. When store_id is
    # provided this also prevents one seller from changing another store's row.
    existing = _select_item(item_id, store_id)
    if not existing:
        return []

    query = (
        supabase.table("inventory")
        .update({"quantity": new_quantity, "status": new_status})
        .eq("id", item_id)
    )
    if store_id is not None:
        query = query.eq("store_id", store_id)

    response = query.execute()
    if response.data:
        return response.data

    # Verify the mutation instead of assuming an empty PostgREST payload means
    # the database operation failed.
    updated = _select_item(item_id, store_id)
    if not updated:
        return []

    quantity_matches = float(updated.get("quantity") or 0) == float(new_quantity)
    status_matches = str(updated.get("status") or "").upper() == str(new_status).upper()
    return [updated] if quantity_matches and status_matches else []


def delete_store_item(store_id, item_id):
    """Delete one store-owned inventory row and verify that it is gone.

    The sales_history foreign key uses ON DELETE SET NULL, so deleting an
    inventory listing does not destroy the historical sale record.
    """
    existing = _select_item(item_id, store_id)
    if not existing:
        return []

    response = (
        supabase.table("inventory")
        .delete()
        .eq("store_id", store_id)
        .eq("id", item_id)
        .execute()
    )
    if response.data:
        return response.data

    # As with UPDATE, verify the database state because a successful DELETE may
    # return no representation of the removed row.
    remaining = _select_item(item_id, store_id)
    return [existing] if remaining is None else []


# -----------------------------------------------------------------------------
# Time-based inventory synchronization
# -----------------------------------------------------------------------------

def sync_all_inventory_items(now=None):
    """Refresh every active item's shelf-life values using rolling 24-hour periods.

    Each item has its own ``created_at`` timestamp and ``initial_days_left``.
    Therefore an item's remaining days decrease only after *that specific item*
    has completed another 24-hour period. This is more accurate than changing
    every listing at midnight.

    The web deployment is serverless, so there is no permanently running Python
    process. Instead, this synchronization is called automatically whenever
    inventory is read by the seller, market, or support system. Stale rows are
    corrected before they are shown to the user.
    """
    response = supabase.table("inventory").select("*").execute()
    items = response.data or []
    now = now or datetime.now(timezone.utc)
    updated_count = 0

    for item in items:
        status = str(item.get("status") or "").upper()

        # Sold-out and already expired items are terminal states for the expiry
        # countdown and do not need further price recalculation.
        if status in {"SOLD OUT", "EXPIRED"}:
            continue

        created_raw = item.get("created_at")
        initial_days = item.get("initial_days_left")
        if not created_raw or initial_days is None:
            # Older/malformed rows are left untouched instead of breaking every
            # inventory screen because one row is incomplete.
            continue

        try:
            created_at = datetime.fromisoformat(str(created_raw).replace("Z", "+00:00"))
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            initial_days = int(initial_days)
        except (TypeError, ValueError):
            continue

        # Floor elapsed seconds by exactly 24 hours. Because created_at is per
        # item, each listing advances on its own 24-hour schedule.
        elapsed_seconds = max(0, (now - created_at).total_seconds())
        elapsed_24h_periods = int(elapsed_seconds // 86_400)
        calculated_days_left = max(0, initial_days - elapsed_24h_periods)
        new_status = "EXPIRED" if calculated_days_left == 0 else "AVAILABLE"

        if calculated_days_left == int(item.get("days_left") or 0) and new_status == status:
            continue

        item["days_left"] = calculated_days_left
        item["status"] = new_status
        update_payload = {"days_left": calculated_days_left, "status": new_status}

        # Only active food needs a refreshed selling price. An expired item is
        # hidden from the market, so its last price can remain historical data.
        if new_status == "AVAILABLE":
            calculate_dynamic_discount(item)
            update_payload["discount_percent"] = item["discount_percent"]
            update_payload["new_price"] = item["new_price"]

        (
            supabase.table("inventory")
            .update(update_payload)
            .eq("id", item["id"])
            .execute()
        )
        updated_count += 1

    return updated_count


def get_inventory(store_id):
    """Fetch one seller's inventory after synchronizing per-item shelf life."""
    sync_all_inventory_items()
    response = (
        supabase.table("inventory")
        .select("*")
        .eq("store_id", store_id)
        .order("id")
        .execute()
    )
    return response.data


def get_available_inventory(location=None):
    """Fetch live AVAILABLE inventory, optionally filtered by location."""
    sync_all_inventory_items()
    query = supabase.table("inventory").select("*, stores(name)").eq("status", "AVAILABLE")
    if location:
        query = query.eq("location", location)
    response = query.order("id").execute()
    return response.data


# -----------------------------------------------------------------------------
# Sales and customer history
# -----------------------------------------------------------------------------

def record_sale(sale_data):
    """Insert one completed transaction into ``sales_history``."""
    response = supabase.table("sales_history").insert(sale_data).execute()
    return response.data


def get_sales_history(store_id):
    """Fetch a seller's completed sales together with item categories."""
    response = (
        supabase.table("sales_history")
        .select("*, inventory(category)")
        .eq("store_id", store_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data


def get_customer_purchase_history(customer_id):
    """Fetch the purchase history that belongs to one customer."""
    response = (
        supabase.table("sales_history")
        .select("*, inventory(name, category), stores(name, location)")
        .eq("customer_id", customer_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data


def get_sales_by_location(location):
    """Fetch completed sales across all stores for a specific location."""
    response = (
        supabase.table("sales_history")
        .select("*, inventory(category)")
        .eq("location", location)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data


def get_all_sales():
    """Fetch complete sales history across every store and location."""
    response = (
        supabase.table("sales_history")
        .select("*, inventory(category)")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data


# -----------------------------------------------------------------------------
# CLI location helper
# -----------------------------------------------------------------------------

def customer_location():
    """Prompt a CLI user to select one of the supported Malaysian locations."""
    print("\nSelect Location:")
    print("1. Cyberjaya")
    print("2. Petaling Jaya")
    print("3. Putrajaya")
    print("4. Puchong")

    location_map = {
        "1": "Cyberjaya",
        "2": "Petaling Jaya",
        "3": "Putrajaya",
        "4": "Puchong",
    }

    while True:
        location_choice = input("Select Location (1-4): ").strip()
        if location_choice in location_map:
            return location_map[location_choice]
        print("Invalid selection! Please enter a number between 1 and 4.")


# -----------------------------------------------------------------------------
# Customer stock-interest notifications
# -----------------------------------------------------------------------------

def record_user_details_supabase(email, spot, interested_in):
    """Save one stock-interest request without inserting duplicates."""
    email = (email or "").strip().lower()
    spot = (spot or "").strip()
    interested_in = (interested_in or "").strip()

    existing = (
        supabase.table("notifications")
        .select("id")
        .eq("email", email)
        .eq("location", spot)
        .eq("interested_in", interested_in)
        .limit(1)
        .execute()
    )
    if existing.data:
        return {"status": "already_saved", "id": existing.data[0]["id"]}

    try:
        response = (
            supabase.table("notifications")
            .insert({"email": email, "location": spot, "interested_in": interested_in})
            .execute()
        )
        return {"status": "saved", "data": response.data}
    except Exception as error:
        # PostgreSQL error 23505 is the unique-constraint violation used by the
        # notification table to prevent duplicate interests.
        if "23505" in str(error) or "duplicate key" in str(error).lower():
            return {"status": "already_saved"}
        raise


def get_store_name(store_id):
    """Return the display name of a seller store."""
    response = supabase.table("stores").select("name").eq("id", store_id).single().execute()
    return response.data["name"] if response.data else None


def process_item_and_notifications(item):
    """Send matching stock alerts after a seller creates a new listing."""
    table_name = "notifications"

    # Old unfulfilled interests are kept for only seven days so the demo
    # database does not accumulate stale requests indefinitely.
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    supabase.table(table_name).delete().lt("created_at", seven_days_ago).execute()

    item_location = item.get("location")
    item_category = item.get("category", "").strip().lower()
    store_name = get_store_name(item.get("store_id"))

    response = supabase.table(table_name).select("*").eq("location", item_location).execute()
    notification_rows = response.data or []
    matched_ids = []

    for row in notification_rows:
        interested_in = row.get("interested_in", "").strip().lower()
        if interested_in != item_category:
            continue

        recipient_email = row.get("email")
        if not recipient_email:
            continue

        try:
            sent = send_notification_email(
                email=recipient_email,
                store_location=item_location,
                interested_in=row.get("interested_in"),
                store_name=store_name,
            )
            if sent:
                matched_ids.append(row["id"])
        except Exception as error:
            # A mail-service failure must not roll back an otherwise valid item
            # listing. The interest remains stored for a future retry.
            print(f"Matching stock email failed for {recipient_email}: {error}")

    if matched_ids:
        supabase.table(table_name).delete().in_("id", matched_ids).execute()
        print(f"Sent and cleared {len(matched_ids)} fulfilled notification request(s).")

    return {"sent": len(matched_ids)}
