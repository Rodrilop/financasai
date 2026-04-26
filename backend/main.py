from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())

from database import get_connection, init_db, ensure_user_settings, get_schema_info
from analyzer import compute_analysis, get_settings, get_all_income
from market import get_market_data, get_allocation, get_user_portfolio_data
from ai_engine import generate_recommendations, chat_with_ai, generate_proactive_alert
from apscheduler.schedulers.background import BackgroundScheduler
from auth import get_password_hash, verify_password, create_access_token, get_current_user

app = FastAPI(title="FinançasAI API")

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all exceptions globally and log them."""
    logger.error(f"Global Error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Erro interno no servidor."})

def run_proactive_agent():
    """Background task to generate autonomous alerts for all users."""
    conn = get_connection()
    try:
        users = conn.execute("SELECT DISTINCT user_id FROM settings").fetchall()
        for row in users:
            uid = row["user_id"]
            analysis = compute_analysis(uid)
            alert = generate_proactive_alert(uid, analysis)
            if alert:
                conn.execute("INSERT INTO notifications (user_id, title, message) VALUES (?,?,?)", (uid, alert["title"], alert["message"]))
        conn.commit()
    except Exception as e:
        logger.error(f"Proactive Error: {e}")
    finally:
        conn.close()

@app.on_event("startup")
def startup():
    init_db()
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_proactive_agent, 'interval', hours=24)
    scheduler.start()

# ── Models ──────────────────────────────────────────────────────────────────

class SettingsIn(BaseModel):
    salary: float = Field(0, ge=0)
    reference_month: str = Field("", max_length=7)
    emergency_reserve_goal: float = Field(0, ge=0)
    investment_pct: float = Field(20, ge=0, le=100)
    investor_profile: str = Field("moderado", max_length=20)
    budget_essential_pct: float = Field(50, ge=0, le=100)
    budget_important_pct: float = Field(30, ge=0, le=100)
    budget_optional_pct: float = Field(20, ge=0, le=100)

class IncomeIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)

class ExpenseIn(BaseModel):
    description: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=50)
    priority: str = Field(..., min_length=1, max_length=20)
    date: str = Field(..., max_length=10)
    notes: Optional[str] = Field("", max_length=500)

class PortfolioItemIn(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10)
    quantity: float = Field(..., gt=0)
    average_price: float = Field(..., gt=0)

class BulkDeleteIn(BaseModel):
    ids: List[int]

class ChatIn(BaseModel):
    question: str = Field(..., min_length=1)
    month: Optional[str] = None
    image_base64: Optional[str] = None
    audio_base64: Optional[str] = None

class UserRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)

class UserLogin(BaseModel):
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)

# ── Auth ─────────────────────────────────────────────────────────────────────

@app.post("/api/auth/register")
def register(user: UserRegister):
    conn = get_connection()
    existing = conn.execute("SELECT id FROM users WHERE email=?", (user.email,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    hashed = get_password_hash(user.password)
    cur = conn.execute(
        "INSERT INTO users (name, email, hashed_password) VALUES (?, ?, ?)",
        (user.name, user.email, hashed)
    )
    conn.commit()
    new_user_id = cur.lastrowid
    conn.close()
    # Create isolated settings row for the new user
    ensure_user_settings(new_user_id)
    return {"ok": True}

@app.post("/api/auth/login")
def login(user: UserLogin):
    conn = get_connection()
    db_user = conn.execute("SELECT * FROM users WHERE email=?", (user.email,)).fetchone()
    conn.close()
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    # Ensure settings exist (safety net for pre-existing users)
    ensure_user_settings(db_user["id"])
    access_token = create_access_token(data={"sub": db_user["email"]})
    return {"access_token": access_token, "token_type": "bearer", "name": db_user["name"]}

# ── Settings ─────────────────────────────────────────────────────────────────

@app.get("/api/settings")
def read_settings(user: dict = Depends(get_current_user)):
    """Return the authenticated user's settings."""
    return get_settings(user["id"])

@app.put("/api/settings")
def update_settings(data: SettingsIn, user: dict = Depends(get_current_user)):
    """Update the authenticated user's settings."""
    uid = user["id"]
    logger.info(f"Updating settings for user_id: {uid}")
    conn = get_connection()
    exists = conn.execute("SELECT id FROM settings WHERE user_id=?", (uid,)).fetchone()
    if exists:
        conn.execute("""UPDATE settings SET salary=?,reference_month=?,emergency_reserve_goal=?,
                        investment_pct=?,investor_profile=?,budget_essential_pct=?,
                        budget_important_pct=?,budget_optional_pct=? WHERE user_id=?""",
                     (data.salary, data.reference_month, data.emergency_reserve_goal,
                      data.investment_pct, data.investor_profile, data.budget_essential_pct,
                      data.budget_important_pct, data.budget_optional_pct, uid))
    else:
        conn.execute("""INSERT INTO settings
                        (user_id,salary,reference_month,emergency_reserve_goal,
                         investment_pct,investor_profile,budget_essential_pct,
                         budget_important_pct,budget_optional_pct)
                        VALUES (?,?,?,?,?,?,?,?,?)""",
                     (uid, data.salary, data.reference_month, data.emergency_reserve_goal,
                      data.investment_pct, data.investor_profile, data.budget_essential_pct,
                      data.budget_important_pct, data.budget_optional_pct))
    conn.commit()
    conn.close()
    return {"ok": True}

# ── Income ────────────────────────────────────────────────────────────────────

@app.get("/api/income")
def read_income(user: dict = Depends(get_current_user)):
    return get_all_income(user["id"])

@app.post("/api/income", status_code=201)
def add_income(data: IncomeIn, user: dict = Depends(get_current_user)):
    """Add a new income record for the authenticated user."""
    uid = user["id"]
    logger.info(f"Adding income for user_id: {uid}, amount: {data.amount}")
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO income (user_id, name, amount) VALUES (?, ?, ?)",
        (uid, data.name, data.amount)
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"id": new_id, **data.dict()}

@app.delete("/api/income/{income_id}")
def delete_income(income_id: int, user: dict = Depends(get_current_user)):
    conn = get_connection()
    conn.execute("DELETE FROM income WHERE id=? AND user_id=?", (income_id, user["id"]))
    conn.commit()
    conn.close()
    return {"ok": True}

# ── Expenses ──────────────────────────────────────────────────────────────────

@app.get("/api/expenses")
def read_expenses(user: dict = Depends(get_current_user), month: Optional[str] = None,
                  category: Optional[str] = None, priority: Optional[str] = None,
                  q: Optional[str] = None):
    """Read the authenticated user's expenses with optional filters."""
    uid = user["id"]
    conn = get_connection()
    sql = "SELECT * FROM expenses WHERE user_id=?"
    params: list = [uid]
    if month:
        sql += " AND date LIKE ?"; params.append(f"{month}%")
    if category:
        sql += " AND category=?"; params.append(category)
    if priority:
        sql += " AND priority=?"; params.append(priority)
    if q:
        sql += " AND description LIKE ?"; params.append(f"%{q}%")
    sql += " ORDER BY date DESC"
    rows = conn.execute(sql, tuple(params)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/expenses", status_code=201)
def add_expense(data: ExpenseIn, user: dict = Depends(get_current_user)):
    """Add a new expense record for the authenticated user."""
    uid = user["id"]
    logger.info(f"Adding expense for user_id: {uid}, amount: {data.amount}, category: {data.category}")
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO expenses (user_id, description, amount, category, priority, date, notes) VALUES (?,?,?,?,?,?,?)",
        (uid, data.description, data.amount, data.category, data.priority, data.date, data.notes)
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"id": new_id, **data.dict()}

@app.put("/api/expenses/{expense_id}")
def update_expense(expense_id: int, data: ExpenseIn, user: dict = Depends(get_current_user)):
    conn = get_connection()
    conn.execute(
        "UPDATE expenses SET description=?,amount=?,category=?,priority=?,date=?,notes=? WHERE id=? AND user_id=?",
        (data.description, data.amount, data.category, data.priority, data.date, data.notes,
         expense_id, user["id"])
    )
    conn.commit()
    conn.close()
    return {"id": expense_id, **data.dict()}

@app.delete("/api/expenses/{expense_id}")
def delete_expense(expense_id: int, user: dict = Depends(get_current_user)):
    conn = get_connection()
    conn.execute("DELETE FROM expenses WHERE id=? AND user_id=?", (expense_id, user["id"]))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.post("/api/expenses/bulk-delete")
def bulk_delete(data: BulkDeleteIn, user: dict = Depends(get_current_user)):
    uid = user["id"]
    conn = get_connection()
    conn.execute(
        f"DELETE FROM expenses WHERE user_id=? AND id IN ({','.join('?'*len(data.ids))})",
        tuple([uid] + data.ids)
    )
    conn.commit()
    conn.close()
    return {"deleted": len(data.ids)}

# ── Analysis ──────────────────────────────────────────────────────────────────

@app.get("/api/analysis")
def analysis(user: dict = Depends(get_current_user), month: Optional[str] = None):
    return compute_analysis(user["id"], month)

@app.get("/api/analysis/recommendations")
def recommendations(request: Request, month: Optional[str] = None, user: dict = Depends(get_current_user)):
    data = compute_analysis(user["id"], month)
    text = generate_recommendations(data)
    return {"text": text}

@app.post("/api/chat")
def chat(request: Request, data: ChatIn, user: dict = Depends(get_current_user)):
    analysis_data = compute_analysis(user["id"], data.month)
    answer = chat_with_ai(data.question, analysis_data, user["id"], data.image_base64, data.audio_base64)
    return {"answer": answer}

# ── Market & Investments ──────────────────────────────────────────────────────

@app.get("/api/market")
def market(user: dict = Depends(get_current_user)):
    return get_market_data()

@app.get("/api/investments")
def investments(user: dict = Depends(get_current_user), month: Optional[str] = None):
    data = compute_analysis(user["id"], month)
    profile = data.get("investor_profile", "moderado")
    amount = data.get("investment_suggested", 0)
    alloc = get_allocation(profile, amount)
    return {**alloc, "investment_suggested": amount,
            "emergency_goal": data.get("emergency_goal", 0),
            "balance": data.get("balance", 0)}

@app.get("/api/portfolio")
def get_portfolio(user: dict = Depends(get_current_user)):
    return get_user_portfolio_data(user["id"])

@app.post("/api/portfolio")
def add_portfolio_item(item: PortfolioItemIn, user: dict = Depends(get_current_user)):
    conn = get_connection()
    try:
        # Check if already exists to update or insert
        row = conn.execute("SELECT id, quantity, average_price FROM portfolio WHERE user_id=? AND ticker=?", (user["id"], item.ticker.upper())).fetchone()
        if row:
            # Calculate new average price
            new_qty = row["quantity"] + item.quantity
            new_avg = ((row["quantity"] * row["average_price"]) + (item.quantity * item.average_price)) / new_qty
            conn.execute("UPDATE portfolio SET quantity=?, average_price=? WHERE id=?", (new_qty, new_avg, row["id"]))
        else:
            conn.execute("INSERT INTO portfolio (user_id, ticker, quantity, average_price) VALUES (?,?,?,?)",
                         (user["id"], item.ticker.upper(), item.quantity, item.average_price))
        conn.commit()
        return {"status": "success"}
    finally:
        conn.close()

@app.delete("/api/portfolio/{item_id}")
def delete_portfolio_item(item_id: int, user: dict = Depends(get_current_user)):
    conn = get_connection()
    conn.execute("DELETE FROM portfolio WHERE id=? AND user_id=?", (item_id, user["id"]))
    conn.commit()
    conn.close()
    return {"status": "success"}

# ── Notifications & Proactive Agent ───────────────────────────────────────────

@app.get("/api/notifications")
def get_notifications(user: dict = Depends(get_current_user)):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 50", (user["id"],)).fetchall()
    conn.close()
    return [{"id": r["id"], "title": r["title"], "message": r["message"], "is_read": bool(r["is_read"]), "created_at": r["created_at"]} for r in rows]

@app.put("/api/notifications/{notif_id}/read")
def read_notification(notif_id: int, user: dict = Depends(get_current_user)):
    conn = get_connection()
    conn.execute("UPDATE notifications SET is_read=1 WHERE id=? AND user_id=?", (notif_id, user["id"]))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.post("/api/agent/trigger")
def trigger_agent(user: dict = Depends(get_current_user)):
    """Manual trigger to generate proactive alert for current user (for testing)."""
    analysis = compute_analysis(user["id"])
    alert = generate_proactive_alert(user["id"], analysis)
    if alert:
        conn = get_connection()
        conn.execute("INSERT INTO notifications (user_id, title, message) VALUES (?,?,?)", (user["id"], alert["title"], alert["message"]))
        conn.commit()
        conn.close()
        return {"status": "success", "alert": alert}
    return {"status": "success", "message": "Nenhuma dica necessária no momento."}

# ── WhatsApp Webhook ──────────────────────────────────────────────────────────

@app.post("/api/webhook/whatsapp")
@app.post("/api/webhook/whatsapp/{event}")
async def whatsapp_webhook(request: Request, event: str = None):
    """
    Endpoint híbrido para integração com WhatsApp:
    - Suporta Twilio (x-www-form-urlencoded)
    - Suporta Evolution API v2 (JSON - messages.upsert)
    """
    try:
        content_type = request.headers.get("Content-Type", "")
        body_text = ""
        remote_jid = "whatsapp:default" # ID do usuário no WhatsApp
        
        # 1. Caso seja Twilio (Form Data)
        if "application/x-www-form-urlencoded" in content_type:
            form_data = await request.form()
            body_text = form_data.get("Body", "")
            remote_jid = form_data.get("From", "")
            
        # 2. Caso seja Evolution API v2 (JSON)
        else:
            json_data = await request.json()
            # A Evolution API v2 envia os dados dentro de 'data' no evento 'messages.upsert'
            if json_data.get("event") == "messages.upsert":
                msg_data = json_data.get("data", {}).get("message", {})
                # Pega texto de conversa simples ou de resposta/extended
                body_text = msg_data.get("conversation") or msg_data.get("extendedTextMessage", {}).get("text", "")
                remote_jid = json_data.get("data", {}).get("key", {}).get("remoteJid", "")
            else:
                # Fallback para JSON genérico
                body_text = json_data.get("message", json_data.get("text", ""))

        if not body_text:
            return {"status": "ignored"}

        # Log para debug (opcional)
        logger.info(f"WhatsApp Message from {remote_jid}: {body_text}")

        # Processamento via Agente IA (ID 1 fixo para demonstração)
        analysis_data = compute_analysis(1)
        answer = chat_with_ai(body_text, analysis_data, 1)

        # 3. Retorno formatado conforme o provedor
        if "application/x-www-form-urlencoded" in content_type:
            from fastapi.responses import Response
            twiml = f"<?xml version='1.0' encoding='UTF-8'?><Response><Message>{answer}</Message></Response>"
            return Response(content=twiml, media_type="application/xml")
        
        # 4. Caso seja Evolution API, precisamos disparar a resposta de volta via API deles
        evo_url = os.getenv("EVOLUTION_API_URL")
        evo_key = os.getenv("EVOLUTION_API_KEY")
        evo_instance = os.getenv("EVOLUTION_INSTANCE_NAME")

        if evo_url and evo_key and evo_instance:
            import requests
            send_url = f"{evo_url}/message/sendText/{evo_instance}"
            payload = {
                "number": remote_jid,
                "text": answer,
                "delay": 1200, # delay natural de digitação em ms
                "linkPreview": True
            }
            headers = {
                "Content-Type": "application/json",
                "apikey": evo_key
            }
            try:
                resp = requests.post(send_url, json=payload, headers=headers)
                logger.info(f"Resposta da Evolution API: {resp.status_code} - {resp.text}")
            except Exception as e:
                logger.error(f"Erro ao enviar resposta via Evolution: {e}")

        return {"status": "processed", "reply": answer}

    except Exception as e:
        logger.error(f"WhatsApp Webhook Error: {e}")
        return {"error": str(e)}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/debug/schema")
def debug_schema():
    """Diagnostic: show table columns and row counts in Turso."""
    return get_schema_info()

@app.get("/api/debug/me")
def debug_me(user: dict = Depends(get_current_user)):
    """Diagnostic: return the user_id resolved from the JWT token."""
    return {"user_id": user["id"], "email": user["email"]}
