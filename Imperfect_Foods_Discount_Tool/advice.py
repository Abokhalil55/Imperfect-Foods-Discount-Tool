# ==============================================================================
# Storage Recommendations & Preservation Alerts
# ==============================================================================

from database import inventory


def view_storage_advice():
    """Generates spoilage warnings and preservation tips for inventory items."""
    if not inventory:
        print("\n[!] No inventory items available.")
        return

    print("\n" + "="*70)
    print("     STORAGE RECOMMENDATIONS & SPOILAGE PREVENTION ALERTS")
    print("="*70)
    for item in inventory:
        print(f"\nItem: {item['name']} (Category: {item['category']}) | Days Left: {item['days_left']}")
        if item['days_left'] == 1:
            print("  ⚠️ URGENT ACTION: Consume today or freeze immediately!")
        elif item['days_left'] <= 3:
            print("  ⚡ WARNING: Store in airtight container / refrigerated area.")
        else:
            print("  ✅ STABLE: Keep in dry, cool temperature.")

        if item['category'] == 'Produce':
            print("  💡 Tip: Keep away from ethylene-producing fruits like apples.")
        elif item['category'] == 'Bakery':
            print("  💡 Tip: Freeze unused portions; do not refrigerate bread to prevent drying.")
        elif item['category'] == 'Dairy':
            print("  💡 Tip: Maintain strict refrigeration at or below 4°C.")
        else:
            print("  💡 Tip: Follow package re-sealing guidelines.")
    print("="*70)