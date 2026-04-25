import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(override=True)

# Configurar o client do Google Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

def generate_recommendations(analysis: dict) -> str:
    """Use Google Gemini to generate personalized financial recommendations."""
    try:
        cat = analysis.get("category_totals", {})
        prio = analysis.get("priority_totals", {})
        income = analysis.get("total_income", 0)
        expenses = analysis.get("total_expenses", 0)
        balance = analysis.get("balance", 0)
        inv_sug = analysis.get("investment_suggested", 0)
        profile = analysis.get("investor_profile", "moderado")
        alerts = analysis.get("alerts", [])
        alert_msgs = " | ".join(a["message"] for a in alerts)

        prompt = f"""Você é um especialista em educação financeira pessoal brasileiro. 
Analise os dados financeiros abaixo e forneça recomendações práticas, claras e motivadoras em português.

DADOS DO MÊS:
- Renda total: R$ {income:.2f}
- Total de gastos: R$ {expenses:.2f}
- Saldo disponível: R$ {balance:.2f}
- Valor sugerido para investir: R$ {inv_sug:.2f}
- Perfil de investidor: {profile}
- Gastos Essenciais: R$ {prio.get('Essencial',0):.2f}
- Gastos Importantes: R$ {prio.get('Importante',0):.2f}  
- Gastos Opcionais: R$ {prio.get('Opcional',0):.2f}
- Categorias: {cat}
- Alertas ativos: {alert_msgs if alert_msgs else 'Nenhum'}

Forneça:
1. Uma avaliação geral da saúde financeira (2 linhas)
2. 3 a 5 recomendações práticas de corte de gastos (baseadas nos dados reais)
3. Dica de investimento alinhada ao perfil ({profile})
4. Uma frase motivacional de encerramento

Seja direto, use linguagem simples e mencione valores reais quando relevante. Máximo 300 palavras."""

        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        
        return response.text
    except Exception as e:
        return f"⚠️ IA temporariamente indisponível. Veja os alertas automáticos abaixo.\n\nErro: {str(e)}"

def chat_with_ai(question: str, analysis: dict, user_id: int) -> str:
    """Answer user questions and execute financial actions (Agent)."""
    try:
        def add_expense_tool(description: str, amount: float, category: str, priority: str, date: str) -> dict:
            """Adiciona uma nova despesa no sistema do usuário. Use esta ferramenta APENAS quando o usuário disser que gastou/comprou algo.
            
            Args:
                description: Descrição curta do gasto (ex: 'Almoço no Ifood', 'Conta de Luz', 'Tênis').
                amount: Valor numérico positivo do gasto. Extraia do texto do usuário.
                category: Categoria do gasto. Tente classificar em uma destas: Alimentação, Transporte, Moradia, Saúde, Lazer, Educação, Assinaturas, Outros. Padrão: Outros.
                priority: Nível de importância. Tente classificar em: Essencial, Importante, Opcional. Padrão: Opcional.
                date: Data do gasto no formato YYYY-MM-DD. Se hoje, use a data atual.
            """
            from database import get_connection
            try:
                conn = get_connection()
                conn.execute(
                    "INSERT INTO expenses (user_id, description, amount, category, priority, date, notes) VALUES (?,?,?,?,?,?,?)",
                    (user_id, description, float(amount), category, priority, date, "Criado pelo Agente IA")
                )
                conn.commit()
                conn.close()
                return {"status": "success", "message": f"Despesa salva com sucesso: {description} (R$ {amount:.2f})"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        def update_salary_tool(new_salary: float) -> dict:
            """Atualiza o salário mensal fixo do usuário. Use quando o usuário falar sobre novo salário, aumento ou mudança de salário."""
            from database import get_connection
            try:
                conn = get_connection()
                conn.execute("UPDATE settings SET salary=? WHERE user_id=?", (float(new_salary), user_id))
                conn.commit()
                conn.close()
                return {"status": "success", "message": f"Salário atualizado para R$ {new_salary:.2f}"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        def add_extra_income_tool(name: str, amount: float) -> dict:
            """Adiciona uma renda extra (dinheiro recebido que não é o salário fixo). Ex: freela, venda, prêmio."""
            from database import get_connection
            try:
                conn = get_connection()
                conn.execute("INSERT INTO income (user_id, name, amount) VALUES (?,?,?)", (user_id, name, float(amount)))
                conn.commit()
                conn.close()
                return {"status": "success", "message": f"Renda extra '{name}' de R$ {amount:.2f} adicionada."}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        def update_investment_goal_tool(investment_pct: float) -> dict:
            """Atualiza a meta de investimentos mensal do usuário (percentual da renda, ex: 20, 30)."""
            from database import get_connection
            try:
                conn = get_connection()
                conn.execute("UPDATE settings SET investment_pct=? WHERE user_id=?", (float(investment_pct), user_id))
                conn.commit()
                conn.close()
                return {"status": "success", "message": f"Meta de investimento atualizada para {investment_pct}%"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        def update_emergency_goal_tool(emergency_goal_value: float) -> dict:
            """Atualiza a meta total da reserva de emergência em Reais (R$)."""
            from database import get_connection
            try:
                conn = get_connection()
                conn.execute("UPDATE settings SET emergency_reserve_goal=? WHERE user_id=?", (float(emergency_goal_value), user_id))
                conn.commit()
                conn.close()
                return {"status": "success", "message": f"Meta da reserva de emergência atualizada para R$ {emergency_goal_value:.2f}"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        def update_budget_rules_tool(essential_pct: float, important_pct: float, optional_pct: float) -> dict:
            """Atualiza a regra de divisão do orçamento (ex: 50, 30, 20). Os três valores devem somar 100."""
            from database import get_connection
            try:
                conn = get_connection()
                conn.execute("UPDATE settings SET budget_essential_pct=?, budget_important_pct=?, budget_optional_pct=? WHERE user_id=?", 
                             (float(essential_pct), float(important_pct), float(optional_pct), user_id))
                conn.commit()
                conn.close()
                return {"status": "success", "message": f"Regras atualizadas para {essential_pct}/{important_pct}/{optional_pct}"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        def update_investor_profile_tool(profile: str) -> dict:
            """Atualiza o perfil de investidor do usuário. Valores válidos APENAS: 'conservador', 'moderado', 'agressivo'."""
            from database import get_connection
            try:
                conn = get_connection()
                conn.execute("UPDATE settings SET investor_profile=? WHERE user_id=?", (profile.lower(), user_id))
                conn.commit()
                conn.close()
                return {"status": "success", "message": f"Perfil atualizado para {profile}"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        from datetime import datetime
        hoje = datetime.now().strftime("%Y-%m-%d")

        instruction = f"""Você é o Assistente Financeiro IA Pessoal (Consultor Autônomo) do app FinançasAI.
Hoje é dia {hoje}. Você tem acesso aos dados do usuário e dezenas de ferramentas (tools) para CONTROLE TOTAL do aplicativo.
SEMPRE que o usuário informar uma intenção (adicionar gasto, mudar salário, adicionar renda extra, alterar perfil, mudar metas), você DEVE obrigatoriamente usar a ferramenta correspondente para executar a ação.
Não diga "vá nas configurações e mude", FAÇA você mesmo utilizando suas tools.
Se a data de um gasto não for especificada, ou o usuário usar termos como "hoje" ou "agora", utilize obrigatoriamente a data de hoje ({hoje}).
Se o usuário pedir para executar mais de uma ação na mesma frase (ex: "mude meu salário para X e adicione uma despesa de Y"), você deve usar AS DUAS ferramentas consecutivamente ou na mesma chamada.
Após executar as ações, confirme gentilmente o que foi feito. Seja conciso, humano e amigável."""

        tools_list = [
            add_expense_tool, update_salary_tool, add_extra_income_tool, 
            update_investment_goal_tool, update_emergency_goal_tool, 
            update_budget_rules_tool, update_investor_profile_tool
        ]

        model = genai.GenerativeModel(
            model_name=model_name,
            tools=tools_list,
            system_instruction=instruction
        )
        
        chat = model.start_chat(enable_automatic_function_calling=True)
        
        context = f"""[Contexto Financeiro Atual]
- Hoje: {hoje}
- Renda: R$ {analysis.get('total_income',0):.2f}
- Gastos Totais: R$ {analysis.get('total_expenses',0):.2f}
- Saldo Livre: R$ {analysis.get('balance',0):.2f}

O usuário diz: {question}"""

        response = chat.send_message(context)
        return response.text
    except Exception as e:
        return f"Erro ao processar com a IA ou salvar o dado. Tente novamente mais tarde. Detalhes: {str(e)}"
