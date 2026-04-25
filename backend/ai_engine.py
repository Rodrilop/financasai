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

        from datetime import datetime
        hoje = datetime.now().strftime("%Y-%m-%d")

        instruction = f"""Você é o Assistente Financeiro IA Pessoal (Consultor Autônomo) do app FinançasAI.
Hoje é dia {hoje}. Você tem acesso aos dados do usuário e ferramentas (tools). 
SEMPRE que o usuário informar que fez um gasto/compra (ex: "gastei X", "comprei Y", "adicione uma despesa de Z"), você DEVE usar a ferramenta 'add_expense_tool' para salvar a despesa.
Se a data não for especificada, ou o usuário usar termos como "hoje" ou "agora", utilize obrigatoriamente a data de hoje ({hoje}).
Se o usuário usar termos como "ontem", calcule a data correta baseada no dia de hoje ({hoje}).
Se for impossível deduzir a data, assuma a data de hoje para não travar o fluxo.
Não diga apenas como ele pode fazer isso, FAÇA você mesmo pela ferramenta.
Após adicionar, confirme gentilmente a ação e informe a data que registrou. Seja conciso e amigável."""

        model = genai.GenerativeModel(
            model_name=model_name,
            tools=[add_expense_tool],
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
