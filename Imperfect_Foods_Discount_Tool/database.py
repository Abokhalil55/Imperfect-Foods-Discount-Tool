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


inventory = []
sales_history = []
intrest_customers = []


def print_data1():
    print(f"inventory = {inventory}")
    print(f'\n\nsales_history = {sales_history}')
    print(f'intrest_customers = {intrest_customers}')

def add_item(item):
    supabase.table('inventory').insert(item).execute()
    print("Done added to supabase")


def get_inventory(location):
    response = (
        supabase.table('inventory')
        .select('*')
        .eq('location', location)
        .order('id')  # Keep items sorted cleanly by ID
        .execute()
    )
    return response.data


def get_item_by_id(item_id, location):
    """Fetch a single item from Supabase by ID and location."""
    response = (
        supabase.table('inventory')
        .select('*')
        .eq('id', item_id)
        .eq('location', location)
        .execute()
    )
    return response.data[0] if response.data else None


def update_item_stock(item_id, new_quantity, new_status):
    """Update inventory quantity and status in Supabase."""
    supabase.table('inventory').update({
        'quantity': new_quantity,
        'status': new_status
    }).eq('id', item_id).execute()


def record_sale(sale_data):
    """Insert a completed transaction record into Supabase sales_history table."""
    supabase.table('sales_history').insert(sale_data).execute()


def get_sales_history(location):
    """Fetch completed sales history from Supabase with item categories."""
    response = (
        supabase.table('sales_history')
        .select('*, inventory(category)')
        .eq('location', location)
        .order('created_at', desc=True)
        .execute()
    )
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