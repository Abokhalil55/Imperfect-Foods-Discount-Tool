# ==============================================================================
# Global In-Memory Database State
# ==============================================================================
from supabase import create_client, Client
import os 
from dotenv import load_dotenv

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
