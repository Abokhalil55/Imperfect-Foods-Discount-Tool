# In your advice / storage module
from database import get_inventory,customer_location

def view_storage_advice():
    """Generates spoilage warnings and preservation tips for inventory items directly from Supabase."""

    # 1. Fetch live items for the location from Supabase
    location=customer_location()
    inventory_items = get_inventory(location)

    if not inventory_items:
        print(f"\n[!] No inventory items available for location: '{location}'.")
        return

    print("\n" + "="*70)
    print(f"   STORAGE RECOMMENDATIONS & SPOILAGE PREVENTION ALERTS ({location})")
    print("="*70)
    
    for item in inventory_items:
        print(f"\nItem: {item['name']} (Category: {item['category']}) | Days Left: {item['days_left']}")
        
        # Spoilage warning levels based on days_left
        if item['days_left'] == 1:
            print("  ⚠️ URGENT ACTION: Consume today or freeze immediately!")
        elif item['days_left'] <= 3:
            print("  ⚡ WARNING: Store in airtight container / refrigerated area.")
        else:
            print("  ✅ STABLE: Keep in dry, cool temperature.")

        # Preservation tips based on category
        category = item.get('category', '').capitalize()
        if category == 'Produce':
            print("  💡 Tip: Keep away from ethylene-producing fruits.")
        elif category == 'Bakery':
            print("  💡 Tip: Freeze unused portions; do not refrigerate bread to prevent drying.")
        elif category == 'Dairy':
            print("  💡 Tip: Maintain strict refrigeration at or below 4°C.")
        else:
            print("  💡 Tip: Follow package re-sealing guidelines.")
            
    print("="*70)