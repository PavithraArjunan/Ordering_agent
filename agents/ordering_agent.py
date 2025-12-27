import os
import json
import re
import requests
from pathlib import Path
from dotenv import load_dotenv
from google import genai

from scheduling_agent import SchedulingAgent

# ================= FORCE LOAD .env =================
ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE, override=True)

API_KEY = os.environ.get("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY not found")
# ================================================


VEG_ITEMS = ["margherita", "tandoori_paneer", "veggie_supreme", "mexican_fiesta"]
NON_VEG_ITEMS = ["chicken_tikka", "chicken_supreme", "triple_chicken_feast"]
SIDES = ["sprinkled_fries", "chicken_wings"]
DESSERTS = ["brownie", "choco_volcano"]
ULTIMATE_CHEESE = ["margherita_uc", "chicken_tikka_uc"]


class OrderingAgent:
    def __init__(self, mcp_path, backend_url):
        with open(mcp_path, "r") as f:
            self.mcp = json.load(f)

        self.backend_url = backend_url
        self.scheduler = SchedulingAgent()
        self.client = genai.Client(api_key=API_KEY)

        self.menu = self.load_menu()
        self.menu_prices = self.build_price_map()

        self.reset_state()
        self.cart = {}  # item_id -> qty

    # ================= MENU =================
    def load_menu(self):
        try:
            res = requests.get(f"{self.backend_url}/menu")
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print("Menu load error:", e)
            return {"categories": []}

    def build_price_map(self):
        price_map = {}
        for cat in self.menu.get("categories", []):
            for item in cat.get("items", []):
                price_map[item["id"]] = item["price"]
        return price_map

    def get_item_name_by_id(self, item_id):
        for cat in self.menu.get("categories", []):
            for item in cat.get("items", []):
                if item["id"] == item_id:
                    return item["name"]
        return item_id.replace("_", " ").title()

    # ================= STATE =================
    def reset_state(self):
        self.state = {
            "flow": None,
            "category": None
        }

    # ================= CART =================
    def get_cart_total(self):
        total = 0
        for item, qty in self.cart.items():
            total += self.menu_prices.get(item, 0) * qty
        return total

    def show_cart_brief(self):
        print(f"🧮 Current total: ₹{self.get_cart_total()}\n")

    def display_cart_summary(self):
        print("\n" + "=" * 60)
        print("🧾 ORDER SUMMARY")
        print("=" * 60)

        total = 0
        for item, qty in self.cart.items():
            price = self.menu_prices.get(item, 0)
            item_total = price * qty
            total += item_total
            print(f"{self.get_item_name_by_id(item):.<35} {qty} x ₹{price} = ₹{item_total}")

        print("-" * 60)
        print(f"{'TOTAL':.<35} ₹{total}")
        print("=" * 60)

    # ================= PARSING =================
    def extract_items_with_quantities(self, text, allowed_items):
        found = {}
        for item in allowed_items:
            name = item.replace("_", " ")
            display = self.get_item_name_by_id(item)

            patterns = [
                rf"(\d+)\s+{re.escape(name)}",
                rf"{re.escape(name)}\s+(\d+)",
                rf"(\d+)\s+{re.escape(display)}",
                rf"{re.escape(display)}\s+(\d+)",
            ]

            for p in patterns:
                m = re.search(p, text, re.I)
                if m:
                    found[item] = int(m.group(1))
                    break

            if item not in found:
                if name in text or display.lower() in text:
                    found[item] = None

        return found

    def use_gemini_for_parsing(self, text, allowed_items):
        prompt = f"""
Extract items and quantities from user input.

User input: "{text}"
Allowed items: {allowed_items}

Return ONLY JSON like:
{{"chicken_tikka":2,"margherita":1}}
"""
        try:
            res = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            match = re.search(r"\{.*\}", res.text, re.S)
            return json.loads(match.group()) if match else {}
        except:
            return {}

    # ================= BACKEND =================
    def place_order(self, item_id):
        try:
            res = requests.post(
                f"{self.backend_url}/order",
                json={"item_id": item_id}
            )
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print("Order error:", e)
            return None

    # ================= MAIN =================
    def run(self):
        print("\n🍕 Welcome to Tasky Crunchy Bakery 🍰")
        print("Choose: pizza / sides / desserts / ultimate_cheese\n")

        while True:
            user_input = input("You: ").lower().strip()

            # ===== EXIT =====
            if user_input in ["no", "exit", "quit"]:
                if self.cart:
                    self.display_cart_summary()

                    etas = []
                    print("\n📝 Placing orders...\n")
                    for item, qty in self.cart.items():
                        for _ in range(qty):
                            order = self.place_order(item)
                            if order:
                                eta = order.get("eta_minutes", 30)
                                etas.append(eta)
                                self.scheduler.schedule(order)

                    if etas:
                        print(f"⏱️ Estimated Delivery Time: {max(etas)} minutes")

                print("\n👋 Thank you!")
                break

            # ===== FLOW SELECTION =====
            if not self.state["flow"]:
                if "pizza" in user_input and "ultimate" not in user_input:
                    self.state["flow"] = "pizza"
                    print("Veg or Non-Veg?\n")
                elif "ultimate" in user_input or "cheese" in user_input:
                    self.state["flow"] = "ultimate"
                    print("Available:", ", ".join(self.get_item_name_by_id(i) for i in ULTIMATE_CHEESE), "\n")
                elif "side" in user_input:
                    self.state["flow"] = "sides"
                    print("Available:", ", ".join(self.get_item_name_by_id(i) for i in SIDES), "\n")
                elif "dessert" in user_input:
                    self.state["flow"] = "desserts"
                    print("Available:", ", ".join(self.get_item_name_by_id(i) for i in DESSERTS), "\n")
                else:
                    print("Please choose a category.\n")
                continue

            # ===== PIZZA CATEGORY =====
            if self.state["flow"] == "pizza" and not self.state["category"]:
                if "veg" in user_input:
                    self.state["category"] = "veg"
                    print("Choose:", ", ".join(self.get_item_name_by_id(i) for i in VEG_ITEMS), "\n")
                elif "non" in user_input:
                    self.state["category"] = "non"
                    print("Choose:", ", ".join(self.get_item_name_by_id(i) for i in NON_VEG_ITEMS), "\n")
                else:
                    print("Veg or Non-Veg?\n")
                continue

            # ===== ITEM SELECTION =====
            if self.state["flow"] == "pizza":
                items = VEG_ITEMS if self.state["category"] == "veg" else NON_VEG_ITEMS
            elif self.state["flow"] == "sides":
                items = SIDES
            elif self.state["flow"] == "desserts":
                items = DESSERTS
            else:
                items = ULTIMATE_CHEESE

            parsed = self.extract_items_with_quantities(user_input, items)
            if not parsed:
                parsed = self.use_gemini_for_parsing(user_input, items)

            if not parsed:
                print("Please choose valid items.\n")
                continue

            for item, qty in parsed.items():
                if qty is None:
                    qty = int(input(f"How many {self.get_item_name_by_id(item)}? "))
                self.cart[item] = self.cart.get(item, 0) + qty

            self.show_cart_brief()
            print("Anything else? [pizza / sides / desserts / ultimate_cheese / no]\n")
            self.reset_state()


if __name__ == "__main__":
    agent = OrderingAgent(
        mcp_path="mcp_server/mcp.json",
        backend_url="http://127.0.0.1:8000"
    )
    agent.run()
