import re

from analytics import generate_waste_report
from CustomerService import run_customer_service
from database import customer_location, sync_all_inventory_items
from inventory import (
    display_customer_purchase_history,
    display_inventory,
    display_inventory_customer,
    register_food_item,
)
from sales import buy_food_item, view_sales_ledger
from Update_del import update_items_seller
from userAuth import login_user, sign_up_user


current_user = None
ALLOWED_DOMAINS = ["@gmail.com", "@yahoo.com", "@outlook.com", "@hotmail.com", "@icloud.com"]


def is_valid_email(email):
    """Validate email syntax and restrict the domain to common public providers."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, email):
        return False, "Invalid email address structure (e.g., example@domain.com)."

    email_lower = email.lower()
    if not any(email_lower.endswith(domain) for domain in ALLOWED_DOMAINS):
        allowed_list = ", ".join(ALLOWED_DOMAINS)
        return False, f"Email domain not allowed. Please use one of: {allowed_list}"

    return True, ""


def auth_menu():
    """Display the authentication menu until the user logs in or exits."""
    global current_user

    while True:
        print("\n" * 2 + "=" * 60)
        print("   WELCOME TO JIMATRASA (SDG 2)")
        print("=" * 60)
        print("1. Login")
        print("2. Sign Up")
        print("3. Exit Application")
        print("=" * 60)

        choice = input("Select an option (1-3): ").strip()

        if choice == "1":
            email = input("Enter email: ").strip()
            valid, err_msg = is_valid_email(email)
            if not valid:
                print(f"\n[!] Login Error: {err_msg}")
                continue

            password = input("Enter password: ").strip()
            result = login_user(email, password)

            if result["success"]:
                current_user = result["user"]
                print(
                    f"\n[✓] Login successful! Welcome, {current_user['full_name']} "
                    f"({current_user['role'].capitalize()})."
                )
                break

            print(f"\n[!] Login failed: {result.get('error', 'Unknown error')}")

        elif choice == "2":
            email = input("Enter email: ").strip()
            valid, err_msg = is_valid_email(email)
            if not valid:
                print(f"\n[!] Registration Error: {err_msg}")
                continue

            password = input("Enter password (minimum 6 characters): ").strip()
            if len(password) < 6:
                print("\n[!] Registration Error: Password must contain at least 6 characters.")
                continue

            full_name = input("Enter full name: ").strip()

            print("\nSelect Role:")
            print("1. Customer")
            print("2. Seller")
            role_choice = input("Enter role choice (1-2): ").strip()

            if role_choice not in ["1", "2"]:
                print("\n[!] Registration Error: Please select role 1 or 2.")
                continue

            role = "seller" if role_choice == "2" else "customer"
            store_name = None
            store_location = None

            if role == "seller":
                store_name = input("Enter your Store Name: ").strip()
                store_location = customer_location()
                if not store_name or not store_location:
                    print("\n[!] Registration Error: Store Name and Location cannot be empty.")
                    continue

            result = sign_up_user(
                email,
                password,
                full_name,
                role=role,
                store_name=store_name,
                store_location=store_location,
            )

            if result["success"]:
                print(f"\n[✓] {result['message']} Please log in to continue.")
            else:
                print(f"\n[!] Registration failed: {result['error']}")

        elif choice == "3":
            print("\nExiting application. Goodbye!")
            raise SystemExit

        else:
            print("\n[!] Invalid selection. Please choose 1, 2, or 3.")


def display_menu():
    """Display the role-specific main menu."""
    role = current_user["role"]
    name = current_user["full_name"]

    print("\n" * 2 + "=" * 60)
    print(f" JIMATRASA - Logged in as: {name} ({role.upper()})")
    print("=" * 60)

    if role == "seller":
        print("1. Register Imperfect / Near-Expiry Food Item")
        print("2. Update My Store Inventory & Dynamic Discounts")
        print("3. View My Store Inventory & Dynamic Discounts")
        print("4. View Sales & Revenue Summary Ledger")
        print("5. Generate Food Waste Diversion & SDG Impact Report")
        print("6. Logout")
        print("7. Exit Application")
    elif role == "customer":
        print("1. View Available Food Items / Market")
        print("2. Buy Food Item (Purchase)")
        print("3. View My Purchase History")
        print("4. Customer Service Chat")
        print("5. Logout")
        print("6. Exit Application")

    print("=" * 60)


def main():
    """Run inventory synchronization, authentication, and the main menu loop."""
    global current_user

    sync_all_inventory_items()
    auth_menu()

    while True:
        display_menu()
        role = current_user["role"]
        choice = input("Enter your choice: ").strip()

        if role == "seller":
            if choice == "1":
                register_food_item(store_id=current_user["store_id"])
            elif choice == "2":
                update_items_seller(store_id=current_user["store_id"])
            elif choice == "3":
                display_inventory(store_id=current_user["store_id"])
            elif choice == "4":
                view_sales_ledger(store_id=current_user["store_id"])
            elif choice == "5":
                generate_waste_report(store_id=current_user["store_id"])
            elif choice == "6":
                print("\nLogging out...")
                current_user = None
                auth_menu()
            elif choice == "7":
                print("\nThank you for supporting SDG 2 Zero Hunger! Exiting...")
                break
            else:
                print("\n[!] Invalid selection! Please select a valid option from the menu.")

        elif role == "customer":
            if choice == "1":
                display_inventory_customer(customer_location())
            elif choice == "2":
                buy_food_item(customer_id=current_user["id"])
            elif choice == "3":
                display_customer_purchase_history(customer_id=current_user["id"])
            elif choice == "4":
                run_customer_service()
            elif choice == "5":
                print("\nLogging out...")
                current_user = None
                auth_menu()
            elif choice == "6":
                print("\nThank you for supporting SDG 2 Zero Hunger! Exiting...")
                break
            else:
                print("\n[!] Invalid selection! Please select a valid option from the menu.")


if __name__ == "__main__":
    main()
