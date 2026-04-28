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
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if not results: return "Nenhum resultado encontrado."
            return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
    except Exception as e:
        return f"Erro na pesquisa: {str(e)}"

def get_market_data_tool(ticker: str) -> str:
    """Busca cotação com detecção flexível de palavras-chave (Dólar, Selic, etc)."""
    try:
        q = ticker.upper().strip()
        
        # 1. Detecção por Palavras-Chave (Flexível)
        target_ticker = q
        if "SELIC" in q:
            return "Busca Web: " + search_web_tool("taxa selic hoje valor atualizado")
        elif "DOLAR" in q or "DÓLAR" in q or "USD" in q:
            target_ticker = "USDBRL=X"
        elif "EURO" in q or "EUR" in q:
            target_ticker = "EURBRL=X"
        elif "BITCOIN" in q or "BTC" in q:
            target_ticker = "BTC-USD"
        
        # 2. Sufixo para B3 (se for um ticker puro de 5-6 letras)
        if target_ticker == q and "." not in q and "-" not in q and 4 <= len(q) <= 6:
            target_ticker = f"{q}.SA"
        
        # 3. Consulta Yahoo
        stock = yf.Ticker(target_ticker)
        # Forçamos o download rápido dos dados
        data = stock.history(period="1d")
        if not data.empty:
            price = data['Close'].iloc[-1]
            return f"Cotação de {target_ticker}: R$ {price:.2f}"
        
        # Se falhou o histórico, tenta o info (mais lento)
        price = stock.info.get("currentPrice") or stock.info.get("regularMarketPrice")
        if price:
            return f"Cotação de {target_ticker}: R$ {price:.2f}"
        
        # 4. Fallback Web Definitivo
        return f"Sem dados para {target_ticker}. Busca Web: " + search_web_tool(f"valor {q} hoje")
    except Exception as e:
        return f"Erro na consulta ({str(e)}). Tentando Web: " + search_web_tool(f"valor {ticker} hoje")

# --- MOTOR PRINCIPAL ---
def chat_with_ai(question: str, analysis: dict, user_id: int, image_base64: str = None, audio_base64: str = None) -> str:
    """Assistente Financeiro Supremo 2.0: Multimodal, Granular e Persistente."""
    try:
        hoje = datetime.now().strftime("%Y-%m-%d")

        # --- CASO 0: IMAGEM (GROQ VISION / GEMINI FALLBACK) ---
        if image_base64:
            try:
                # Tenta primeiro com Groq Vision (Custo Zero e Mais Rápido)
                b64_data = image_base64.split("base64,")[1] if "base64," in image_base64 else image_base64
                
                try:
                    # Groq Vision 11B - O mais estável e rápido
                    response = groq_client.chat.completions.create(
                        model="llama-3.2-11b-vision-preview",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "Extraia deste cupom: Valor Total, Estabelecimento e Categoria."},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"}}
                                ]
                            }
                        ]
                    )
                    return response.choices[0].message.content
                except Exception as groq_v_err:
                    print(f"⚠️ Groq Vision falhou: {groq_v_err}")
                    # Fallback para Gemini Flash Latest (Alias confirmado na sua conta)
                    model = genai.GenerativeModel('models/gemini-flash-latest')
                    image_bytes = base64.b64decode(b64_data)
                    res = model.generate_content([
                        "Extraia deste cupom fiscal: Valor Total, Estabelecimento e Categoria.",
                        {"mime_type": "image/jpeg", "data": image_bytes}
                    ])
                    return res.text
            except Exception as vision_err:
                return f"❌ Erro nos motores de Visão: {str(vision_err)}"

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
                    "description": "Registra um gasto.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "desc": {"type": "string"}, "val": {"type": "number"},
                            "cat": {"type": "string"}
                        },
                        "required": ["desc", "val", "cat"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_salary",
                    "description": "Atualiza a renda mensal.",
                    "parameters": {
                        "type": "object",
                        "properties": {"val": {"type": "number"}}, "required": ["val"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "market_info",
                    "description": "Consulta cotações (Dólar, Selic, Ações).",
                    "parameters": {
                        "type": "object",
                        "properties": {"q": {"type": "string"}}, "required": ["q"]
                    }
                }
            }
        ]

        instruction = f"""Você é o Assistente Financeiro. Hoje é {hoje}.
        Renda Atual: R$ {analysis.get('total_income',0):.2f}.

        REGRAS OBRIGATÓRIAS:
        1. Para Dólar, Selic ou Ações, USE 'market_info'.
        2. Para aumentos de salário, calcule (Renda Atual + aumento) e use 'update_salary'.
        3. SEMPRE use o formato JSON nativo para ferramentas. NÃO use tags <function>.
        """

        messages = [{"role": "system", "content": instruction}, {"role": "user", "content": question}]

        # LOOP DE RACIOCÍNIO (Máximo 3 rodadas)
        for _ in range(3):
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages, tools=tools, tool_choice="auto", temperature=0
            )
            msg = response.choices[0].message
            if not msg.tool_calls: return msg.content
            
            messages.append(msg)
            for tool in msg.tool_calls:
                args = json.loads(tool.function.arguments)
                name = tool.function.name
                res = "OK."
                
                try:
                    if name == "add_expense":
                        db_exec("INSERT INTO expenses (user_id, description, amount, category, priority, date) VALUES (?,?,?,?,?,?)",
                               (user_id, args["desc"], args["val"], args["cat"], "Importante", hoje))
                        res = f"Gasto registrado."
                    elif name == "update_salary":
                        db_exec("UPDATE users SET salary = ? WHERE id = ?", (args["val"], user_id))
                        res = f"Renda atualizada."
                    elif name == "market_info":
                        res = get_market_data_tool(args["q"])
                except Exception as e: res = f"Erro: {str(e)}"

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
