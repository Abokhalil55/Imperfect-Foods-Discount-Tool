# ==============================================================================
# BIT2083 FUNDAMENTALS OF COMPUTATIONAL THINKING
# Final Project: Imperfect Foods Discount & Sales Management System
# SDG Target: SDG 2 - Zero Hunger
# ==============================================================================

from inventory import register_food_item, display_inventory
from sales import buy_food_item, view_sales_ledger
from advice import view_storage_advice
from analytics import generate_waste_report


def display_menu():
    """Display Main Menu System"""
    print("\n"*3 + "="*60)
    print("    IMPERFECT FOODS DISCOUNT & SALES SYSTEM (SDG 2)")
    print("="*60)
    print("1. Register Imperfect / Near-Expiry Food Item")
    print("2. View All Inventory & Dynamic Discounts")
    print("3. Buy Food Item (Customer Purchase / Process Sale)")
    print("4. View Storage Advice & Spoilage Alert")
    print("5. View Sales & Revenue Summary Ledger")
    print("6. Generate Food Waste Diversion & SDG Impact Report")
    print("7. Exit Application")
    print("="*60)


def main():
    """Main Program Loop Controller"""
    while True:
        display_menu()
        choice = input("Enter your choice (1-7): ").strip()

        if choice == '1':
            register_food_item()
        elif choice == '2':
            display_inventory()
        elif choice == '3':
            buy_food_item()
        elif choice == '4':
            view_storage_advice()
        elif choice == '5':
            view_sales_ledger()
        elif choice == '6':
            generate_waste_report()
        elif choice == '7':
            print("\nThank you for supporting SDG 2 Zero Hunger! Exiting...")
            break
        else:
            print("\n[!] Invalid selection! Please choose a number between 1 and 7.")


if __name__ == "__main__":
    main()