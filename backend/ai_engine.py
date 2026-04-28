import os
import json
import base64
import google.generativeai as genai
from groq import Groq
from dotenv import load_dotenv
from database import get_connection
import yfinance as yf

load_dotenv(override=True)

# --- INICIALIZAÇÃO DOS CLIENTES ---
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

def search_web_tool(query: str) -> str:
    """Busca notícias financeiras e informações do mundo via DuckDuckGo."""
    try:
        from duckduckgo_search import DDGS
        results = DDGS().text(query, max_results=3)
        if not results: return "Nenhum resultado encontrado na web."
        return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
    except Exception as e:
        return f"Erro na pesquisa web: {str(e)}"

def get_market_data(ticker: str) -> str:
    """Busca cotação via Yahoo Finance com fallback para Busca Web."""
    try:
        ticker = ticker.upper().strip()
        synonyms = {"DOLAR": "USDBRL=X", "DÓLAR": "USDBRL=X", "EURO": "EURBRL=X", "BITCOIN": "BTC-USD"}
        if ticker in synonyms: ticker = synonyms[ticker]
        if "." not in ticker and "-" not in ticker and "^" not in ticker:
            if len(ticker) >= 5: ticker = f"{ticker}.SA"
        
        stock = yf.Ticker(ticker)
        info = stock.info
        price = (info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose"))
        if price:
            name = info.get("longName") or info.get("shortName") or ticker
            return f"Cotação de {name} ({ticker}): R$ {price:.2f}"
        
        # Fallback Web
        web = search_web_tool(f"valor atual {ticker} hoje")
        return f"Não achei no Yahoo, mas na web diz: {web}"
    except Exception as e:
        return f"Erro: {str(e)}"

def chat_with_ai(question: str, analysis: dict, user_id: int, image_base64: str = None, audio_base64: str = None) -> str:
    """O Assistente Total: Gerencia gastos, renda, carteira e pesquisas."""
    try:
        from datetime import datetime
        hoje = datetime.now().strftime("%Y-%m-%d")

        # --- CASO 0: IMAGEM (GEMINI VISION) ---
        if image_base64:
            try:
                b64_data = image_base64.split("base64,")[1] if "base64," in image_base64 else image_base64
                image_bytes = base64.b64decode(b64_data)
                model = genai.GenerativeModel('gemini-flash-latest')
                res = model.generate_content([
                    "Analise esta imagem de cupom fiscal e extraia: Valor Total, Estabelecimento e Categoria. Responda de forma curta.",
                    {"mime_type": "image/jpeg", "data": image_bytes}
                ])
                return res.text
            except Exception as vision_err:
                print(f"❌ Erro Vision: {vision_err}")

        # --- CASO 1: ÁUDIO (WHISPER) ---
        if audio_base64:
            try:
                temp_audio = f"temp_{user_id}_{datetime.now().timestamp()}.webm"
                audio_data = audio_base64.split("base64,")[1] if "base64," in audio_base64 else audio_base64
                with open(temp_audio, "wb") as f: 
                    f.write(base64.b64decode(audio_data))
                
                with open(temp_audio, "rb") as file:
                    transcription = groq_client.audio.transcriptions.create(
                        file=(temp_audio, file.read()), 
                        model="whisper-large-v3"
                    )
                
                os.remove(temp_audio)
                if transcription.text:
                    question = transcription.text
                    print(f"🎙️ Transcrição Groq Sucesso: {question}")
            except Exception as audio_err:
                print(f"❌ Erro na transcrição Groq: {audio_err}")

        # --- LÓGICA DE BANCO DE DADOS ---
        def db_execute(query: str, params: tuple):
            conn = get_connection()
            conn.execute(query, params)
            conn.commit()
            conn.close()

        # --- TOOLS DEFINITIONS ---
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "manage_finance",
                    "description": "Adiciona gasto, deleta gasto ou atualiza salário.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["add_expense", "delete_expense", "update_salary"]},
                            "amount": {"type": "number"},
                            "description": {"type": "string"},
                            "category": {"type": "string"},
                            "expense_id": {"type": "integer"}
                        },
                        "required": ["action"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "manage_portfolio",
                    "description": "Adiciona ativos (ações/FIIs) à carteira do usuário.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticker": {"type": "string"},
                            "quantity": {"type": "number"},
                            "average_price": {"type": "number"}
                        },
                        "required": ["ticker", "quantity", "average_price"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "market_info",
                    "description": "Busca cotações ou notícias financeiras.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query_or_ticker": {"type": "string"}
                        },
                        "required": ["query_or_ticker"]
                    }
                }
            }
        ]

        instruction = f"""Você é o Assistente Financeiro Supremo do FinançasAI. Hoje é {hoje}.
        
        DADOS ATUAIS DO USUÁRIO (USE ESTES DADOS PARA RESPONDER):
        - Renda/Salário Atual: R$ {analysis.get('total_income',0):.2f}
        - Gastos Totais do Mês: R$ {analysis.get('total_expenses',0):.2f}
        - Saldo Livre: R$ {analysis.get('balance',0):.2f}

        REGRAS DE OURO:
        1. Se o usuário perguntar qual o seu salário ou gastos, USE OS DADOS ACIMA. Não diga que não sabe.
        2. Se ele disser que o salário 'aumentou X' ou 'diminuiu Y', faça o cálculo (Renda Atual + X) e use 'manage_finance' para atualizar.
        3. Após usar qualquer ferramenta, explique ao usuário o que foi feito de forma amigável.
        4. Sempre responda em Português do Brasil.
        """

        messages = [{"role": "system", "content": instruction}, {"role": "user", "content": question}]

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
                res = "Ação realizada."
                
                try:
                    if name == "manage_finance":
                        if args["action"] == "add_expense":
                            db_execute("INSERT INTO expenses (user_id, description, amount, category, priority, date) VALUES (?,?,?,?,?,?)",
                                       (user_id, args["description"], args["amount"], args.get("category", "Geral"), "Importante", hoje))
                            res = f"Gasto de R$ {args['amount']} em '{args['description']}' salvo!"
                        elif args["action"] == "update_salary":
                            db_execute("UPDATE users SET salary = ? WHERE id = ?", (args["amount"], user_id))
                            res = f"Salário atualizado para R$ {args['amount']}!"
                    elif name == "manage_portfolio":
                        db_execute("INSERT INTO portfolio (user_id, ticker, quantity, average_price) VALUES (?,?,?,?)",
                                   (user_id, args["ticker"].upper(), args["quantity"], args["average_price"]))
                        res = f"Ativo {args['ticker']} adicionado à sua carteira!"
                    elif name == "market_info":
                        res = get_market_data(args["query_or_ticker"])
                except Exception as e:
                    res = f"Erro na ferramenta: {str(e)}"

                messages.append({"tool_call_id": tool.id, "role": "tool", "name": name, "content": res})
        return response.choices[0].message.content if 'response' in locals() else "Ação processada com sucesso!"
    except Exception as e: return f"❌ Erro: {str(e)}"

def generate_recommendations(analysis: dict) -> str:
    try:
        res = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": f"Analise: Renda {analysis.get('total_income')}. Dê 1 dica."}],
            model="llama-3.1-8b-instant"
        )
        return res.choices[0].message.content
    except: return "Dica: Economize 10% hoje."

def generate_proactive_alert(u, a): return None
