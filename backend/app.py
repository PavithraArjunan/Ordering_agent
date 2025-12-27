from fastapi import FastAPI, HTTPException
from pathlib import Path
import pandas as pd
from uuid import uuid4
from pydantic import BaseModel

from models import MenuResponse

app = FastAPI(
    title="Pizza Ordering Backend",
    description="Backend API serving menu data from Excel",
    version="1.0.0"
)

MENU_FILE = Path("../data/menu.xlsx")


# =========================
# MENU LOADING
# =========================
def load_menu_from_excel():
    if not MENU_FILE.exists():
        raise FileNotFoundError("menu.xlsx not found")

    df = pd.read_excel(MENU_FILE)

    categories = {}

    for _, row in df.iterrows():
        category = row["category"]

        item = {
            "id": row["item_id"],
            "name": row["name"],
            "type": row["type"],
            "price": int(row["price"]),
            "customizable": bool(row["customizable"])
        }

        categories.setdefault(category, []).append(item)

    return {
        "categories": [
            {
                "id": cat,
                "name": cat.replace("_", " ").title(),
                "items": items
            }
            for cat, items in categories.items()
        ]
    }


@app.get("/menu", response_model=MenuResponse)
def get_menu():
    """
    Returns the full pizza menu.
    Data is loaded dynamically from Excel.
    """
    try:
        return load_menu_from_excel()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# NEW: ORDER ENDPOINT
# =========================
class OrderRequest(BaseModel):
    item_id: str


@app.post("/order")
def place_order(order: OrderRequest):
    """
    Places a pizza order (mocked).
    """
    return {
        "order_id": str(uuid4()),
        "item_id": order.item_id,
        "eta_minutes": 30,
        "status": "confirmed"
    }


# Run with:
# uvicorn backend.app:app --reload
# uvicorn app:app --reload
