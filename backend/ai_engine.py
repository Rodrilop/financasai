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

def chat_with_ai(question: str, analysis: dict) -> str:
    """Answer user questions about their finances."""
    try:
        context = f"""Dados financeiros do usuário:
- Renda: R$ {analysis.get('total_income',0):.2f}
- Gastos: R$ {analysis.get('total_expenses',0):.2f}
- Saldo: R$ {analysis.get('balance',0):.2f}
- Por categoria: {analysis.get('category_totals',{})}
- Por prioridade: {analysis.get('priority_totals',{})}"""

        prompt = f"""{context}

Pergunta do usuário: {question}

Responda em português, de forma clara e objetiva. Se não tiver dados suficientes, diga o que o usuário precisa informar."""

        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        
        return response.text
    except Exception as e:
        return f"Não foi possível processar sua pergunta no momento. Erro: {str(e)}"
