# 🍕 Tasky Crunchy Bakery – AI Ordering Agent

This project is  to build a system that automatically transforms OpenAPI specifications into fully
functional MCP servers.
Users can order pizzas, sides, desserts, and ultimate cheese items using **natural language**, and the system will calculate **total price** and **delivery ETA**.

The assistant uses **Google Gemini** for intelligent text parsing and connects to a **backend API** for menu and order processing.

---

## 📌 Features

* Order using normal sentences (example: *“ chicken tikka and  brownie”*)
* Supports:

  * Veg & Non-Veg Pizzas
  * Sides
  * Desserts
  * Ultimate Cheese items
* Live **price calculation**
* **Consolidated ETA** for the full order
* Backend integration for menu & order creation
* Gemini AI used as fallback for item parsing

---

## 🧱 Project Structure

```
pizza-ai/
├── ordering_agent.py        # Main ordering logic
├── scheduling_agent.py      # Handles order scheduling
├── mcp_server/
│   └── mcp.json             # MCP configuration
├── backend/                 # Backend service (API)
├── .env                     # Environment variables
└── README.md
```

---

## ⚙️ Requirements

* Python 3.9+
* Backend server running (menu & order APIs)
* Google Gemini API key

---

## 🔑 Environment Setup

Create a `.env` file in the project root:

```
GOOGLE_API_KEY=your_google_gemini_api_key
```

---

## 📦 Install Dependencies

```bash
pip install requests python-dotenv google-generativeai
```

---

## ▶️ How to Run

Start Backend

```bash
uvicorn backend.app:app --reload
```

Run Ordering Agent
python agents/ordering_agent.py

```bash
python agents/ordering_agent.py
```

---

## 💬 Example Conversation

```
You: pizza
Bot: Veg or Non-Veg?

You: non veg
Bot: Choose pizzas: Chicken Tikka, Chicken Supreme

You: 2 chicken tikka
Bot: Current total: ₹500

You: brownie
Bot: Current total: ₹620

You: no
Bot: Order Summary shown with final ETA
```

---

## ⏱️ ETA Logic

* Each item is ordered individually from the backend
* Final ETA = **maximum ETA** among all ordered items

This gives a realistic delivery time for the whole order.

---

## 🧮 Price Logic

* Prices are loaded from the backend menu
* Total price is updated **after every item addition**
* Final consolidated total is shown before order placement

---

## 🤖 AI Usage (Gemini)

* Gemini is used only when rule-based parsing fails
* It extracts items and quantities from user sentences
* Keeps the system flexible for natural language input
