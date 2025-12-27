from pydantic import BaseModel
from typing import List


class MenuItem(BaseModel):
    id: str
    name: str
    type: str
    price: int
    customizable: bool


class Category(BaseModel):
    id: str
    name: str
    items: List[MenuItem]


class MenuResponse(BaseModel):
    categories: List[Category]
