# ==============================================================================
# Global In-Memory Database State
# ==============================================================================
from supabase import create_client, Client
import os 
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from pricing import calculate_dynamic_discount
from notifications import send_notification_email
load_dotenv(override=True)

url= os.getenv("SUPABASE_URL")
key= os.getenv("SUPABASE_API")
supabase: Client = create_client(url, key)


def add_item(item, store_id):
    """Add a new inventory item linked to a specific store."""
    # Ensure store_id is attached to the item payload
    item['store_id'] = store_id
    
    response = supabase.table('inventory').insert(item).execute()
    print(f"Done added item to store {store_id} in Supabase")
    return response.data


def get_inventory(store_id):
    """Fetch all inventory items for a specific store ordered by ID."""
    response = (
        supabase.table('inventory')
        .select('*')
        .eq('store_id', store_id)
        .order('id')
        .execute()
    )
    return response.data


def get_item_by_id(item_id, store_id):
    """Fetch a single item from Supabase by ID and store_id."""
    response = (
        supabase.table('inventory')
        .select('*')
        .eq('id', item_id)
        .eq('store_id', store_id)
        .execute()
    )
    return response.data[0] if response.data else None



def update_item_stock(item_id, new_quantity, new_status):
    """Update stock quantity and status for a specific inventory item by its Primary Key ID."""
    response = (
        supabase.table('inventory')
        .update({
            'quantity': new_quantity,
            'status': new_status
        })
        .eq('id', item_id)
        .execute()
    )
    return response.data


def record_sale(sale_data, store_id):
    """Insert a completed transaction record linked to a specific store into Supabase sales_history table."""
    # Ensure store_id is attached to the transaction payload
    sale_data['store_id'] = store_id
    
    response = supabase.table('sales_history').insert(sale_data).execute()
    return response.data


def get_sales_history(store_id):
    """Fetch completed sales history from Supabase with item categories for a specific store."""
    response = (
        supabase.table('sales_history')
        .select('*, inventory(category)')
        .eq('store_id', store_id)
        .order('created_at', desc=True)
        .execute()
    )
    return response.data



def get_customer_purchase_history(customer_id):
    """Fetch personal purchase history for a specific customer."""
    response = (
        supabase.table('sales_history')
        .select('*, inventory(name, category), stores(name, location)')
        .eq('customer_id', customer_id)
        .order('created_at', desc=True)
        .execute()
    )
    return response.data

def get_available_inventory(location=None):
    """Fetch available inventory items for customers to view/buy."""
    query = supabase.table('inventory').select('*, stores(name)').eq('status', 'AVAILABLE')
    
    if location:
        query = query.eq('location', location)
        
    response = query.order('id').execute()
    return response.data



def customer_location():
    print("\nSelect Selling Location:")
    print("1. Cyberjaya")
    print("2. Petaling Jaya")
    print("3. Putrajaya")
    print("4. Puchong")

    location_map = {'1': 'Cyberjaya', '2': 'Petaling Jaya', '3': 'Putrajaya', '4': 'Puchong'}
    while True:
        cat_choice = input("Select Category (1-4): ").strip()
        if cat_choice in location_map:
            location = location_map[cat_choice]
            break
        print("Invalid selection! Please enter a number between 1 and 4.")
    return location



def sync_all_inventory_items():
    """Fetches all items from Supabase, updates days_left, status, and price using initial_days_left."""
    response = supabase.table('inventory').select('*').execute()
    items = response.data
    
    now = datetime.now(timezone.utc)
    
    for item in items:
        if item.get('status') == 'expired':
            continue

        created_at = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
        
        elapsed_days = (now - created_at).days
        
        initial_days = item['initial_days_left']
        calculated_days_left = max(0, initial_days - elapsed_days)
        new_status = 'expired' if calculated_days_left == 0 else item['status']
        
        # Check if database update is required
        if calculated_days_left != item['days_left'] or new_status != item['status']:
            # 1. Update local dictionary values
            item['days_left'] = calculated_days_left
            item['status'] = new_status
            
            # Recalculate price using the updated days_left value
            item = calculate_dynamic_discount(item)
            
            # updated all values to Supabase
            supabase.table('inventory').update({
                'days_left': item['days_left'],
                'status': item['status'],
                'discount_percent': item['discount_percent'],
                'new_price': item['new_price']
            }).eq('id', item['id']).execute()

def record_user_details_supabase(email, spot, interested_in):
        response = supabase.table("notifications").insert({
            "email": email,
            "location": spot,
            "interested_in": interested_in,
        }).execute()

        return "User's info saved"

def get_store_name(store_id):
    response = supabase.table("stores").select("name").eq("id", store_id).single().execute()
    print(f'response.data["name"] = {response.data["name"]}')
    return response.data["name"] if response.data else None


def process_item_and_notifications(item):
    table_name = "notifications"

    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    supabase.table(table_name).delete().lt("created_at", seven_days_ago).execute()
    
    item_location = item.get("location")
    item_category = item.get("category", "").strip().lower()
    store_id = item.get("store_id")
    store_name = get_store_name(store_id)

    response = supabase.table(table_name).select("*").eq("location", item_location).execute()
    notification_rows = response.data or []

    matched_ids = []
    print('here')

    for row in notification_rows:

        interested_in = row.get("interested_in", "").strip().lower()

        if interested_in == item_category:
            print("here 2")
            recipient_email = row.get("email")
            
            if recipient_email:
                print("here 3")
                send_notification_email(
                    email=recipient_email,
                    store_location=item_location,
                    interested_in=row.get("interested_in"),
                    store_name=store_name
                )
                matched_ids.append(row["id"])

    if matched_ids:
        supabase.table(table_name).delete().in_("id", matched_ids).execute()
        print(f"Deleted {len(matched_ids)} fulfilled notification request(s) from '{table_name}'.")




############################################################################################################
############################################################################################################
############################################################################################################

def get_sales_by_location(location):
    """Fetch completed sales history for all stores in a specific location."""
    response = (
        supabase.table('sales_history')
        .select('*, inventory(category)')
        .eq('location', location)
        .order('created_at', desc=True)
        .execute()
    )
    return response.data    


def get_all_sales():
    """Fetch complete sales history across all stores and locations."""
    response = (
        supabase.table('sales_history')
        .select('*, inventory(category)')
        .order('created_at', desc=True)
        .execute()
    )
    return response.data


def record_sale(sale_data):
    """Insert a completed transaction into the sales_history table."""
    response = supabase.table('sales_history').insert(sale_data).execute()
    return response.data
