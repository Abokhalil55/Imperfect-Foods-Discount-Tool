import json
import math
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
PYTHON_APP = ROOT / "Imperfect_Foods_Discount_Tool"
load_dotenv(PYTHON_APP / ".env", override=True)
sys.path.insert(0, str(PYTHON_APP))

from CustomerService import chat
from analytics import generate_waste_report
from database import (
    add_item,
    delete_store_item,
    get_available_inventory,
    get_customer_purchase_history,
    get_inventory,
    get_sales_history,
    process_item_and_notifications,
    record_sale,
    update_item_stock,
)
from evaluator import evaluate_added_item
from pricing import calculate_dynamic_discount
from userAuth import login_user, sign_up_user


LOCATIONS = ["Cyberjaya", "Petaling Jaya", "Putrajaya", "Puchong"]
CATEGORIES = [
    "Produce",
    "Bakery & Grains",
    "Dairy & Chilled Items",
    "Prepared / Packaged Meals",
]


def public_user(user):
    return {key: user.get(key) for key in ["id", "full_name", "email", "role", "store_id"]}


def number(value, field):
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be a number.")
    if not math.isfinite(result):
        raise ValueError(f"{field} must be a valid number.")
    return result


def normalize_market_item(item):
    store = item.get("stores") or {}
    if isinstance(store, list):
        store = store[0] if store else {}
    clean = dict(item)
    clean.pop("stores", None)
    clean["store_name"] = store.get("name", "Unknown store")
    return clean


def run_action(data):
    action = data.get("action")

    if action == "login":
        result = login_user(data.get("email", "").strip(), data.get("password", ""))
        if not result.get("success"):
            return {"success": False, "error": result.get("error", "Login failed.")}, 401
        return {"success": True, "user": public_user(result["user"])}, 200

    elif action == "signup":
        role = data.get("role", "customer")
        location = data.get("store_location")
        if role not in ["customer", "seller"]:
            return {"success": False, "error": "Role must be customer or seller."}, 400
        if role == "seller" and location not in LOCATIONS:
            return {"success": False, "error": "Choose a supported store location."}, 400
        result = sign_up_user(
            data.get("email", "").strip(),
            data.get("password", ""),
            data.get("full_name", "").strip(),
            role,
            data.get("store_name", "").strip() or None,
            location,
        )
        if not result.get("success"):
            return {"success": False, "error": result.get("error", "Signup failed.")}, 400
        return {"success": True, "message": result["message"], "user": public_user(result["data"])}, 200

    elif action == "seller_inventory":
        return {"success": True, "items": get_inventory(data.get("store_id"))}, 200

    elif action == "add_item":
        quantity = number(data.get("quantity"), "Quantity")
        price = number(data.get("original_price"), "Original price")
        days_left = number(data.get("days_left"), "Days left")
        if not days_left.is_integer():
            return {"success": False, "error": "Days left must be a whole number."}, 400
        category = data.get("category")
        grade = data.get("grade")
        location = data.get("location")
        if category not in CATEGORIES or grade not in ["A", "B", "C"] or location not in LOCATIONS:
            return {"success": False, "error": "Choose a valid category, grade, and location."}, 400
        item = {
            "store_id": data.get("store_id"),
            "location": location,
            "name": data.get("name", "").strip(),
            "category": category,
            "quantity": quantity,
            "initial_quantity": quantity,
            "original_price": price,
            "initial_days_left": int(days_left),
            "days_left": int(days_left),
            "grade": grade,
            "discount_percent": 0.0,
            "new_price": 0.0,
            "status": "AVAILABLE",
        }
        evaluation = evaluate_added_item(item)
        if evaluation.get("status") != "APPROVED":
            return {
                "success": True,
                "approved": False,
                "reason": evaluation.get("reason", "The item was rejected."),
                "discount": 0,
                "new_price": 0,
            }, 200
        calculate_dynamic_discount(item)
        created = add_item(item, data.get("store_id"))
        process_item_and_notifications(item)
        return {
            "success": True,
            "approved": True,
            "discount": item["discount_percent"],
            "new_price": item["new_price"],
            "item": created[0] if created else item,
        }, 200

    elif action == "mark_sold_out":
        updated = update_item_stock(data.get("item_id"), 0, "SOLD OUT")
        if not updated:
            return {"success": False, "error": "Item was not found or could not be updated."}, 404
        return {"success": True, "item": updated[0]}, 200

    elif action == "delete_item":
        deleted = delete_store_item(data.get("store_id"), data.get("item_id"))
        if not deleted:
            return {"success": False, "error": "Item was not found or could not be deleted."}, 404
        return {"success": True}, 200

    elif action == "market":
        location = data.get("location")
        if location not in LOCATIONS:
            return {"success": False, "error": "Choose a supported location."}, 400
        items = [normalize_market_item(item) for item in get_available_inventory(location)]
        return {"success": True, "items": items}, 200

    elif action == "buy":
        quantity = number(data.get("quantity"), "Quantity")
        if quantity <= 0:
            return {"success": False, "error": "Quantity must be greater than zero.", "code": "invalid_quantity"}, 400
        location = data.get("location")
        items = get_available_inventory(location)
        selected = next((item for item in items if str(item.get("id")) == str(data.get("item_id"))), None)
        if not selected:
            return {"success": False, "error": "This item is no longer available."}, 404
        available = float(selected.get("quantity", 0))
        if quantity > available:
            return {"success": False, "error": f"Only {available:g} kg/units are available.", "code": "insufficient_stock"}, 400
        remaining = available - quantity
        status = "SOLD OUT" if remaining == 0 else "AVAILABLE"
        total = round(quantity * float(selected["new_price"]), 2)
        update_item_stock(selected["id"], remaining, status)
        sale = {
            "store_id": selected["store_id"],
            "item_id": selected["id"],
            "customer_id": data.get("customer_id"),
            "item_name": selected["name"],
            "location": location,
            "quantity_bought": quantity,
            "unit_price": selected["new_price"],
            "total_amount": total,
        }
        saved = record_sale(sale)
        return {
            "success": True,
            "receipt": saved[0] if saved else sale,
            "remaining_quantity": remaining,
            "status": status,
        }, 200

    elif action == "purchase_history":
        history = []
        for record in get_customer_purchase_history(data.get("customer_id")):
            inventory = record.get("inventory") or {}
            store = record.get("stores") or {}
            clean = dict(record)
            clean.pop("inventory", None)
            clean.pop("stores", None)
            clean["item_name"] = record.get("item_name") or inventory.get("name", "Unknown item")
            clean["category"] = inventory.get("category", "")
            clean["store_name"] = store.get("name", "Unknown store")
            clean["location"] = record.get("location") or store.get("location", "")
            history.append(clean)
        return {"success": True, "purchases": history}, 200

    elif action == "sales":
        sales = []
        for record in get_sales_history(data.get("store_id")):
            clean = dict(record)
            inventory = clean.pop("inventory", None) or {}
            clean["category"] = inventory.get("category", "N/A")
            sales.append(clean)
        return {
            "success": True,
            "sales": sales,
            "total_revenue": sum(float(sale.get("total_amount", 0)) for sale in sales),
            "total_quantity_sold": sum(float(sale.get("quantity_bought", 0)) for sale in sales),
        }, 200

    elif action == "impact":
        return {"success": True, "impact": generate_waste_report(data.get("store_id"))}, 200

    elif action == "chat":
        message = data.get("message", "").strip()
        history = data.get("history") or []
        if not message:
            return {"success": False, "error": "Enter a message first."}, 400
        return {"success": True, "reply": chat(message, history)}, 200

    return {"success": False, "error": "Unknown API action."}, 400


class handler(BaseHTTPRequestHandler):
    def send_json(self, payload, status=200):
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        static_files = {
            "/": ("Ui/index.html", "text/html; charset=utf-8"),
            "/Ui/index.html": ("Ui/index.html", "text/html; charset=utf-8"),
            "/Ui/style.css": ("Ui/style.css", "text/css; charset=utf-8"),
            "/Ui/app.js": ("Ui/app.js", "text/javascript; charset=utf-8"),
        }
        if self.path in static_files:
            relative_path, content_type = static_files[self.path]
            body = (ROOT / relative_path).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_json({"success": True, "message": "SecondShelf API is ready."})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length) or b"{}")
            payload, status = run_action(data)
            self.send_json(payload, status)
        except ValueError as error:
            self.send_json({"success": False, "error": str(error)}, 400)
        except Exception as error:
            self.send_json({"success": False, "error": str(error)}, 500)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print(f"SecondShelf web app: http://127.0.0.1:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()
