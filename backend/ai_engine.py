import os
import json
import base64
from datetime import datetime
import google.generativeai as genai
from groq import Groq
from dotenv import load_dotenv
from database import get_connection
import yfinance as yf

load_dotenv(override=True)

# --- INICIALIZAÇÃO DOS CLIENTES ---
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

# --- FERRAMENTAS DE SUPORTE (AUXILIARES) ---
def search_web_tool(query: str) -> str:
    """Busca informações financeiras e notícias em tempo real via DuckDuckGo."""
    try:
        from duckduckgo_search import DDGS
        results = DDGS().text(query, max_results=3)
        if not results: return "Nenhum resultado encontrado."
        return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
    except Exception as e:
        return f"Erro na pesquisa: {str(e)}"

def get_market_data_tool(ticker: str) -> str:
    """Busca cotação de Ações e FIIs com fallback automático para busca web."""
    try:
        ticker = ticker.upper().strip()
        synonyms = {"DOLAR": "USDBRL=X", "DÓLAR": "USDBRL=X", "EURO": "EURBRL=X", "BITCOIN": "BTC-USD"}
        if ticker in synonyms: ticker = synonyms[ticker]
        if "." not in ticker and "-" not in ticker and "^" not in ticker:
            if len(ticker) >= 5: ticker = f"{ticker}.SA"
        
        stock = yf.Ticker(ticker)
        info = stock.info
        price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
        if price:
            name = info.get("longName") or info.get("shortName") or ticker
            return f"Cotação de {name} ({ticker}): R$ {price:.2f}"
        
        # Fallback Web
        return f"Yahoo s/ dados para {ticker}. Web: " + search_web_tool(f"valor {ticker} hoje")
    except:
        return search_web_tool(f"cotação {ticker} hoje")

# --- MOTOR PRINCIPAL ---
def chat_with_ai(question: str, analysis: dict, user_id: int, image_base64: str = None, audio_base64: str = None) -> str:
    """Assistente Financeiro Supremo 2.0: Multimodal, Granular e Persistente."""
    try:
        hoje = datetime.now().strftime("%Y-%m-%d")

        # --- 1. PROCESSAMENTO DE IMAGEM (GEMINI) ---
        if image_base64:
            try:
                b64_data = image_base64.split("base64,")[1] if "base64," in image_base64 else image_base64
                image_bytes = base64.b64decode(b64_data)
                model = genai.GenerativeModel('gemini-flash-latest')
                res = model.generate_content([
                    "Extraia deste cupom fiscal: Valor Total, Estabelecimento e Categoria. Responda curto e organize os dados.",
                    {"mime_type": "image/jpeg", "data": image_bytes}
                ])
                return res.text
            except Exception as e: return f"Erro Vision: {e}"

        # --- 2. PROCESSAMENTO DE ÁUDIO (WHISPER) ---
        if audio_base64:
            try:
                temp_audio = f"temp_{user_id}_{datetime.now().timestamp()}.webm"
                audio_data = audio_base64.split("base64,")[1] if "base64," in audio_base64 else audio_base64
                with open(temp_audio, "wb") as f: f.write(base64.b64decode(audio_data))
                with open(temp_audio, "rb") as file:
                    transcription = groq_client.audio.transcriptions.create(
                        file=(temp_audio, file.read()), model="whisper-large-v3")
                os.remove(temp_audio)
                question = transcription.text
            except Exception as e: print(f"Erro Áudio: {e}")

        # --- 3. DEFINIÇÃO DE FERRAMENTAS GRANULARES ---
        def db_exec(q, p):
            conn = get_connection()
            conn.execute(q, p)
            conn.commit()
            conn.close()

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "add_expense",
                    "description": "Registra um gasto no banco de dados.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "desc": {"type": "string"}, "val": {"type": "number"},
                            "cat": {"type": "string"}, "data": {"type": "string", "description": "YYYY-MM-DD"}
                        },
                        "required": ["desc", "val", "cat"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_expense",
                    "description": "Deleta um gasto pelo ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {"id": {"type": "integer"}}, "required": ["id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_salary",
                    "description": "Atualiza a renda mensal principal.",
                    "parameters": {
                        "type": "object",
                        "properties": {"val": {"type": "number"}}, "required": ["val"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_portfolio",
                    "description": "Adiciona Ação/FII à carteira.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tk": {"type": "string", "description": "Ticker (ex: PETR4)"},
                            "qtd": {"type": "number"}, "prc": {"type": "number"}
                        },
                        "required": ["tk", "qtd", "prc"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_settings",
                    "description": "Atualiza metas (reserva, investimentos) ou perfil (conservador/moderado/arrojado).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "meta_reserva": {"type": "number"}, "meta_invest": {"type": "number"},
                            "perfil": {"type": "string", "enum": ["conservador", "moderado", "arrojado"]}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "market_search",
                    "description": "Consulta cotações ou notícias na internet.",
                    "parameters": {
                        "type": "object",
                        "properties": {"q": {"type": "string"}}, "required": ["q"]
                    }
                }
            }
        ]

        instruction = f"""Você é o Assistente Supremo do FinançasAI. 
        DADOS ATUAIS (USE PARA RESPONDER): Renda R$ {analysis.get('total_income',0):.2f}, Gastos R$ {analysis.get('total_expenses',0):.2f}.
        
        REGRAS:
        - Se o usuário disser que o salário 'aumentou X', some X à renda atual e use 'update_salary'.
        - Se ele quiser investir, use 'add_portfolio'.
        - Se quiser apagar algo, use 'delete_expense'.
        - Use 'market_search' para cotações ou notícias.
        - Responda amigavelmente após realizar a ação.
        """

        messages = [{"role": "system", "content": instruction}, {"role": "user", "content": question}]

        # LOOP DE RACIOCÍNIO (Máximo 3 rodadas)
        for _ in range(3):
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages, tools=tools, tool_choice="auto", temperature=0.1
            )
            msg = response.choices[0].message
            if not msg.tool_calls: return msg.content
            
            messages.append(msg)
            for tool in msg.tool_calls:
                args = json.loads(tool.function.arguments)
                name = tool.function.name
                res = "Operação concluída."
                
                try:
                    if name == "add_expense":
                        db_exec("INSERT INTO expenses (user_id, description, amount, category, priority, date) VALUES (?,?,?,?,?,?)",
                               (user_id, args["desc"], args["val"], args["cat"], "Importante", args.get("data", hoje)))
                        res = f"Gasto de R$ {args['val']} em '{args['desc']}' registrado."
                    elif name == "delete_expense":
                        db_exec("DELETE FROM expenses WHERE id=? AND user_id=?", (args["id"], user_id))
                        res = f"Gasto ID {args['id']} removido."
                    elif name == "update_salary":
                        db_exec("UPDATE users SET salary = ? WHERE id = ?", (args["val"], user_id))
                        res = f"Renda atualizada para R$ {args['val']}."
                    elif name == "add_portfolio":
                        db_exec("INSERT INTO portfolio (user_id, ticker, quantity, average_price) VALUES (?,?,?,?)",
                               (user_id, args["tk"].upper(), args["qtd"], args["prc"]))
                        res = f"Ativo {args['tk']} adicionado à carteira."
                    elif name == "update_settings":
                        if "perfil" in args: db_exec("UPDATE settings SET investor_profile=? WHERE user_id=?", (args["perfil"], user_id))
                        if "meta_reserva" in args: db_exec("UPDATE settings SET emergency_reserve_goal=? WHERE user_id=?", (args["meta_reserva"], user_id))
                        res = "Configurações atualizadas."
                    elif name == "market_search":
                        res = get_market_data_tool(args["q"])
                except Exception as e: res = f"Erro na ferramenta: {str(e)}"

                messages.append({"tool_call_id": tool.id, "role": "tool", "name": name, "content": res})
        
        return response.choices[0].message.content
    except Exception as e: return f"❌ Erro Assistente: {str(e)}"

def generate_recommendations(analysis: dict) -> str:
    try:
        res = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": f"Dê uma dica para renda de R$ {analysis.get('total_income')}."}],
            model="llama-3.1-8b-instant"
        )
        return res.choices[0].message.content
    except: return "Economize 10% do seu saldo livre hoje."

def generate_proactive_alert(user_id, analysis): return None
