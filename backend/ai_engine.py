import os
import json
import base64
from openai import OpenAI
from dotenv import load_dotenv
from database import get_connection

load_dotenv(override=True)

# Configurar o client da NVIDIA (padrão OpenAI)
api_key = os.getenv("NVIDIA_API_KEY", "")
base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
model_name = os.getenv("NVIDIA_MODEL", "deepseek-ai/deepseek-v4-pro")

client = OpenAI(
    base_url=base_url,
    api_key=api_key
)

def generate_recommendations(analysis: dict) -> str:
    """Use NVIDIA DeepSeek to generate personalized financial recommendations."""
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

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "Você é um especialista em educação financeira pessoal brasileiro."},
                {"role": "user", "content": prompt}
            ],
            temperature=1,
            top_p=0.95,
            max_tokens=16384,
            extra_body={"chat_template_kwargs": {"thinking": False}},
            stream=True
        )
        
        full_text = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                full_text += chunk.choices[0].delta.content
        
        return full_text
    except Exception as e:
        return f"⚠️ IA (NVIDIA DeepSeek) temporariamente indisponível.\n\nErro: {str(e)}"

def chat_with_ai(question: str, analysis: dict, user_id: int, image_base64: str = None, audio_base64: str = None) -> str:
    """Answer user questions and execute tools using NVIDIA DeepSeek."""
    try:
        from datetime import datetime
        hoje = datetime.now().strftime("%Y-%m-%d")

        # --- DEFINIÇÃO DE FERRAMENTAS ---
        def add_expense_tool(description: str, amount: float, category: str, priority: str, date: str) -> dict:
            try:
                conn = get_connection()
                conn.execute("INSERT INTO expenses (user_id, description, amount, category, priority, date) VALUES (?,?,?,?,?,?)",
                             (user_id, description, amount, category, priority, date))
                conn.commit()
                conn.close()
                return {"status": "success", "message": f"Despesa '{description}' de R$ {amount:.2f} adicionada."}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        def search_web_tool(query: str) -> dict:
            try:
                from duckduckgo_search import DDGS
                results = DDGS().text(query, max_results=3)
                search_context = "\n".join([f"- {r['title']}: {r['body']} (Fonte: {r['href']})" for r in results])
                return {"status": "success", "results": search_context}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "add_expense_tool",
                    "description": "Adiciona um novo gasto ou despesa no sistema.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "amount": {"type": "number"},
                            "category": {"type": "string"},
                            "priority": {"type": "string", "enum": ["Essencial", "Importante", "Opcional"]},
                            "date": {"type": "string", "description": "Formato YYYY-MM-DD"}
                        },
                        "required": ["description", "amount", "category", "priority", "date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_web_tool",
                    "description": "Busca notícias ou cotações financeiras na internet.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"}
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

        available_functions = {
            "add_expense_tool": add_expense_tool,
            "search_web_tool": search_web_tool
        }

        instruction = f"""Você é o Assistente Financeiro IA Pessoal (Consultor Autônomo) do app FinançasAI.
Hoje é dia {hoje}. Você tem acesso aos dados do usuário e dezenas de ferramentas (tools) para CONTROLE TOTAL do aplicativo.
SEMPRE que o usuário informar uma intenção (adicionar gasto, mudar salário, adicionar renda extra, alterar perfil, mudar metas, comprar ações/ativos) ou ENVIAR UMA IMAGEM de recibo/nota fiscal, você DEVE obrigatoriamente usar a ferramenta correspondente para executar a ação.
Não diga "vá nas configurações e mude", FAÇA você mesmo utilizando suas tools.
IMPORTANTE: Se o usuário perguntar sobre o cenário macroeconômico atual (Selic, Inflação) ou pedir conselhos se deve comprar/vender uma Ação/FII específico hoje, VOCÊ DEVE usar a ferramenta 'search_web_tool' ANTES de responder para buscar notícias atualizadas na internet.
Se a data de um gasto não for especificada, utilize a data de hoje ({hoje}).
Após executar as ações, confirme gentilmente o que foi feito. Seja conciso, humano e amigável."""
        
        context_text = f"""[Contexto] Renda: R$ {analysis.get('total_income',0):.2f} | Saldo: R$ {analysis.get('balance',0):.2f}
Usuário: {question}"""

        messages = [
            {"role": "system", "content": instruction}
        ]

        user_content = [{"type": "text", "text": context_text}]

        if image_base64:
            # Garante que o base64 esteja no formato correto (remover prefixo se existir)
            b64_data = image_base64
            if "base64," in image_base64:
                b64_data = image_base64.split("base64,")[1]
            
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"}
            })
            user_content.append({
                "type": "text", 
                "text": "O usuário anexou uma imagem (provavelmente um cupom fiscal). Leia-o e extraia o valor, data e descrição."
            })

        if audio_base64:
            # Em uma implementação real com NVIDIA, usaríamos um modelo de STT aqui.
            # Por enquanto, vamos sinalizar para o modelo que há uma intenção de voz.
            user_content.append({
                "type": "text",
                "text": "[O usuário enviou uma mensagem de áudio que está sendo processada...]"
            })

        messages.append({"role": "user", "content": user_content})

        # Seleção dinâmica de modelo: Se houver imagem, usa um modelo Vision.
        current_model = model_name
        if image_base64:
            current_model = "meta/llama-3.2-11b-vision-instruct"

        # Loop de execução de ferramentas (Máximo 2 rodadas)
        for _ in range(2):
            # Só enviamos 'thinking' se for o modelo DeepSeek
            extra_params = {"extra_body": {"chat_template_kwargs": {"thinking": False}}} if current_model == model_name else {}
            
            response = client.chat.completions.create(
                model=current_model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=1,
                **extra_params
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if not tool_calls:
                return response_message.content

            messages.append(response_message)
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)

                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(function_response),
                })
        
        # Resposta final após ferramentas
        final_response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            extra_body={"chat_template_kwargs": {"thinking": False}}
        )
        return final_response.choices[0].message.content

    except Exception as e:
        return f"Erro ao processar com a IA NVIDIA DeepSeek. Detalhes: {str(e)}"

def generate_proactive_alert(user_id: int, analysis: dict) -> dict:
    """Analisador autônomo de dados usando DeepSeek."""
    try:
        income = analysis.get("total_income", 0)
        expenses = analysis.get("total_expenses", 0)
        if income == 0 and expenses == 0: return None

        prompt = f"Analise: Renda R$ {income:.2f}, Gastos R$ {expenses:.2f}. Se houver risco, crie um alerta curto com Título e Mensagem. Se estiver ok, responda 'IGNORE'."

        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=1,
            extra_body={"chat_template_kwargs": {"thinking": False}},
            stream=True
        )
        
        text = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                text += chunk.choices[0].delta.content
        
        text = text.strip()
        if "IGNORE" in text.upper(): return None
            
        return {"title": "Dica Financeira", "message": text}
    except Exception as e:
        return None
