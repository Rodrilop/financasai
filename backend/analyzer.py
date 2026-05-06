from database import get_connection
from typing import Optional

def fmt(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")

def get_settings(user_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM settings WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}

def get_income_for_month(user_id: int, month: str):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM income WHERE user_id=? AND date LIKE ? ORDER BY date DESC", 
        (user_id, f"{month}%")
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_previous_balance(user_id: int, current_month: str):
    conn = get_connection()
    inc_row = conn.execute("SELECT SUM(amount) FROM income WHERE user_id=? AND date < ?", (user_id, f"{current_month}-01")).fetchone()
    inc_total = inc_row[0] if inc_row and inc_row[0] else 0
    exp_row = conn.execute("SELECT SUM(amount) FROM expenses WHERE user_id=? AND date < ?", (user_id, f"{current_month}-01")).fetchone()
    exp_total = exp_row[0] if exp_row and exp_row[0] else 0
    conn.close()
    return inc_total - exp_total

def get_expenses_for_month(user_id: int, month: str):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM expenses WHERE user_id=? AND date LIKE ? ORDER BY date DESC",
        (user_id, f"{month}%")
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def compute_analysis(user_id: int, month: Optional[str] = None):
    settings = get_settings(user_id)
    ref_month = month or settings.get("reference_month", "")
    
    income_list = get_income_for_month(user_id, ref_month) if ref_month else []
    total_income = sum(i["amount"] for i in income_list)
    
    previous_balance = get_previous_balance(user_id, ref_month) if ref_month else 0

    expenses = get_expenses_for_month(user_id, ref_month) if ref_month else []
    total_expenses = sum(e["amount"] for e in expenses)
    
    balance = previous_balance + total_income - total_expenses

    # Category and priority breakdown
    cat_totals: dict = {}
    prio_totals = {"Essencial": 0.0, "Importante": 0.0, "Opcional": 0.0}
    for e in expenses:
        cat_totals[e["category"]] = cat_totals.get(e["category"], 0) + e["amount"]
        if e["priority"] in prio_totals:
            prio_totals[e["priority"]] += e["amount"]

    ep = settings.get("budget_essential_pct", 50)
    ip = settings.get("budget_important_pct", 30)
    op = settings.get("budget_optional_pct", 20)
    lim_ess = total_income * ep / 100
    lim_imp = total_income * ip / 100
    lim_opt = total_income * op / 100

    alerts = []
    if total_income > 0:
        if prio_totals["Essencial"] > lim_ess:
            excess = prio_totals["Essencial"] - lim_ess
            alerts.append({"level":"danger","icon":"🚨","title":"Essenciais acima do limite",
                "message":f"Essenciais ({fmt(prio_totals['Essencial'])}) ultrapassam {ep}% da renda em {fmt(excess)}.",
                "suggestion":"Revise contas fixas: aluguel, planos e serviços."})
        if prio_totals["Importante"] > lim_imp:
            excess = prio_totals["Importante"] - lim_imp
            alerts.append({"level":"warning","icon":"⚠️","title":"Importantes acima do limite",
                "message":f"Importantes ({fmt(prio_totals['Importante'])}) ultrapassam {ip}% da renda em {fmt(excess)}.",
                "suggestion":"Revise gastos com educação, pets e outros itens importantes."})
        if prio_totals["Opcional"] > lim_opt:
            excess = prio_totals["Opcional"] - lim_opt
            alerts.append({"level":"warning","icon":"⚠️","title":"Opcionais acima do limite",
                "message":f"Opcionais ({fmt(prio_totals['Opcional'])}) ultrapassam {op}% da renda em {fmt(excess)}.",
                "suggestion":"Revise assinaturas e lazer — corte o que não usa."})
        subs = cat_totals.get("Assinaturas", 0)
        if subs > 200:
            alerts.append({"level":"info","icon":"💡","title":"Assinaturas elevadas",
                "message":f"Você tem {fmt(subs)} em assinaturas mensais.",
                "suggestion":"Cancele assinaturas usadas menos de 2x por semana."})
        lazer = cat_totals.get("Lazer", 0)
        if total_income > 0 and lazer > total_income * 0.15:
            alerts.append({"level":"warning","icon":"🎭","title":"Lazer elevado",
                "message":f"Lazer ({fmt(lazer)}) está acima de 15% da renda.",
                "suggestion":"Busque opções gratuitas ou de baixo custo para lazer."})
    else:
        alerts.append({"level":"info","icon":"ℹ️","title":"Configure sua renda",
            "message":"Adicione seu salário em Configurações para ver análises.",
            "suggestion":"Vá em ⚙️ Configurações e adicione seu salário mensal."})

    inv_pct = settings.get("investment_pct", 20)
    return {
        "total_income": total_income,
        "previous_balance": previous_balance,
        "total_expenses": total_expenses,
        "balance": balance,
        "optional_expenses": prio_totals["Opcional"],
        "category_totals": cat_totals,
        "priority_totals": prio_totals,
        "budget_limits": {"essential":lim_ess,"important":lim_imp,"optional":lim_opt,
                          "essential_pct":ep,"important_pct":ip,"optional_pct":op},
        "alerts": alerts,
        "recent_expenses": sorted(expenses, key=lambda e: e["date"], reverse=True)[:10],
        "investment_suggested": total_income * inv_pct / 100,
        "investment_pct": inv_pct,
        "emergency_goal": settings.get("emergency_reserve_goal", 0),
        "emergency_current": balance, # Current emergency is the total accumulated balance
        "investor_profile": settings.get("investor_profile", "moderado"),
        "reference_month": ref_month,
        "expense_count": len(expenses),
    }
