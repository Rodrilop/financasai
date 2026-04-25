from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os

from database import get_connection, init_db
from analyzer import compute_analysis, get_settings, get_all_income
from market import get_market_data, get_allocation
from ai_engine import generate_recommendations, chat_with_ai

app = FastAPI(title="FinançasAI API")

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    init_db()

# ── Models ──────────────────────────────────────────────────────────────────

class SettingsIn(BaseModel):
    salary: float = 0
    reference_month: str = ""
    emergency_reserve_goal: float = 0
    investment_pct: float = 20
    investor_profile: str = "moderado"
    budget_essential_pct: float = 50
    budget_important_pct: float = 30
    budget_optional_pct: float = 20

class IncomeIn(BaseModel):
    name: str
    amount: float

class ExpenseIn(BaseModel):
    description: str
    amount: float
    category: str
    priority: str
    date: str
    notes: Optional[str] = ""

class BulkDeleteIn(BaseModel):
    ids: List[int]

class ChatIn(BaseModel):
    question: str
    month: Optional[str] = None

# ── Settings ─────────────────────────────────────────────────────────────────

@app.get("/api/settings")
def read_settings():
    return get_settings()

@app.put("/api/settings")
def update_settings(data: SettingsIn):
    conn = get_connection()
    conn.execute("""UPDATE settings SET salary=?,reference_month=?,emergency_reserve_goal=?,
                    investment_pct=?,investor_profile=?,budget_essential_pct=?,
                    budget_important_pct=?,budget_optional_pct=? WHERE id=1""",
                 (data.salary, data.reference_month, data.emergency_reserve_goal,
                  data.investment_pct, data.investor_profile, data.budget_essential_pct,
                  data.budget_important_pct, data.budget_optional_pct))
    conn.commit(); conn.close()
    return {"ok": True}

# ── Income ────────────────────────────────────────────────────────────────────

@app.get("/api/income")
def read_income():
    return get_all_income()

@app.post("/api/income", status_code=201)
def add_income(data: IncomeIn):
    conn = get_connection()
    cur = conn.execute("INSERT INTO income (name,amount) VALUES (?,?)", (data.name, data.amount))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"id": new_id, **data.dict()}

@app.delete("/api/income/{income_id}")
def delete_income(income_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM income WHERE id=?", (income_id,))
    conn.commit(); conn.close()
    return {"ok": True}

# ── Expenses ──────────────────────────────────────────────────────────────────

@app.get("/api/expenses")
def read_expenses(month: Optional[str] = None, category: Optional[str] = None,
                  priority: Optional[str] = None, q: Optional[str] = None):
    conn = get_connection()
    sql = "SELECT * FROM expenses WHERE 1=1"
    params = []
    if month:
        sql += " AND date LIKE ?"; params.append(f"{month}%")
    if category:
        sql += " AND category=?"; params.append(category)
    if priority:
        sql += " AND priority=?"; params.append(priority)
    if q:
        sql += " AND description LIKE ?"; params.append(f"%{q}%")
    sql += " ORDER BY date DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/expenses", status_code=201)
def add_expense(data: ExpenseIn):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO expenses (description,amount,category,priority,date,notes) VALUES (?,?,?,?,?,?)",
        (data.description, data.amount, data.category, data.priority, data.date, data.notes)
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"id": new_id, **data.dict()}

@app.put("/api/expenses/{expense_id}")
def update_expense(expense_id: int, data: ExpenseIn):
    conn = get_connection()
    conn.execute(
        "UPDATE expenses SET description=?,amount=?,category=?,priority=?,date=?,notes=? WHERE id=?",
        (data.description, data.amount, data.category, data.priority, data.date, data.notes, expense_id)
    )
    conn.commit(); conn.close()
    return {"id": expense_id, **data.dict()}

@app.delete("/api/expenses/{expense_id}")
def delete_expense(expense_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
    conn.commit(); conn.close()
    return {"ok": True}

@app.post("/api/expenses/bulk-delete")
def bulk_delete(data: BulkDeleteIn):
    conn = get_connection()
    conn.execute(f"DELETE FROM expenses WHERE id IN ({','.join('?'*len(data.ids))})", data.ids)
    conn.commit(); conn.close()
    return {"deleted": len(data.ids)}

# ── Analysis ──────────────────────────────────────────────────────────────────

@app.get("/api/analysis")
def analysis(month: Optional[str] = None):
    return compute_analysis(month)

@app.get("/api/analysis/recommendations")
def recommendations(month: Optional[str] = None):
    data = compute_analysis(month)
    text = generate_recommendations(data)
    return {"text": text}

@app.post("/api/chat")
def chat(data: ChatIn):
    analysis = compute_analysis(data.month)
    answer = chat_with_ai(data.question, analysis)
    return {"answer": answer}

# ── Market & Investments ──────────────────────────────────────────────────────

@app.get("/api/market")
def market():
    return get_market_data()

@app.get("/api/investments")
def investments(month: Optional[str] = None):
    data = compute_analysis(month)
    profile = data.get("investor_profile", "moderado")
    amount = data.get("investment_suggested", 0)
    alloc = get_allocation(profile, amount)
    return {**alloc, "investment_suggested": amount,
            "emergency_goal": data.get("emergency_goal", 0),
            "balance": data.get("balance", 0)}

@app.get("/health")
def health():
    return {"status": "ok"}
