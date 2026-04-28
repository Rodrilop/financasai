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
        return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
    except Exception as e:
        return f"Erro na pesquisa: {e}"

def get_market_data(ticker: str) -> str:
    """Busca cotação e dados de Ações, FIIs ou Cripto via Yahoo Finance."""
    try:
        ticker = ticker.upper().strip()
        
        # Mapeamento de nomes comuns para tickers
        synonyms = {
            "DOLAR": "USDBRL=X",
            "DÓLAR": "USDBRL=X",
            "EURO": "EURBRL=X",
            "BITCOIN": "BTC-USD",
            "IBOVESPA": "^BVSP",
            "SELIC": "^BCB-SELIC" # Exemplo, mas Selic é melhor via busca web
        }
        
        if ticker in synonyms:
            ticker = synonyms[ticker]
        
        # Lógica para ativos brasileiros (.SA)
        # Se tem 5 ou 6 caracteres e não tem ponto nem hífen, provavelmente é B3
        if "." not in ticker and "-" not in ticker and "^" not in ticker:
            if len(ticker) >= 5: # Ex: PETR4, MXRF11
                ticker = f"{ticker}.SA"
        
        stock = yf.Ticker(ticker)
        # Tenta pegar o preço de várias chaves possíveis do Yahoo Finance
        info = stock.info
        price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose") or info.get("ask")
        
        name = info.get("longName") or info.get("shortName") or ticker
        currency = info.get("currency", "BRL")
        
        if price:
            return f"Cotação de {name} ({ticker}): {currency} {price:.2f}"
        
        return f"Não consegui o preço exato para '{ticker}'. Tente usar a ferramenta 'search_web_tool' para buscar no Google."
    except Exception as e:
        return f"Erro técnico ao buscar '{ticker}': {str(e)}. Tente a busca web."

def generate_recommendations(analysis: dict) -> str:
    """Gera recomendações usando Groq Llama 3.3."""
    try:
        income = analysis.get("total_income", 0)
        expenses = analysis.get("total_expenses", 0)
        prompt = f"Analise: Renda {income}, Gastos {expenses}. Dê 3 dicas financeiras curtas."
        res = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile"
        )
        return res.choices[0].message.content
    except:
        return "⚠️ IA ocupada."

def chat_with_ai(question: str, analysis: dict, user_id: int, image_base64: str = None, audio_base64: str = None) -> str:
    """Maestro Híbrido com Suporte a Ferramentas (Search e Market)."""
    try:
        from datetime import datetime
        hoje = datetime.now().strftime("%Y-%m-%d")

        # --- CASO 1: IMAGEM (GEMINI) ---
        if image_base64:
            b64_data = image_base64.split("base64,")[1] if "base64," in image_base64 else image_base64
            image_bytes = base64.b64decode(b64_data)
            model = genai.GenerativeModel('gemini-flash-latest')
            response = model.generate_content([
                "Extraia os dados deste cupom fiscal. Retorne: [GASTO: valor, estabelecimento, categoria]",
                {"mime_type": "image/jpeg", "data": image_bytes}
            ])
            return response.text

        # --- CASO 2: ÁUDIO (WHISPER) ---
        if audio_base64:
            temp_audio = f"temp_{user_id}.webm"
            audio_data = audio_base64.split("base64,")[1] if "base64," in audio_base64 else audio_base64
            with open(temp_audio, "wb") as f: f.write(base64.b64decode(audio_data))
            with open(temp_audio, "rb") as file:
                transcription = groq_client.audio.transcriptions.create(
                    file=(temp_audio, file.read()), model="whisper-large-v3")
            os.remove(temp_audio)
            question = transcription.text

        # --- CASO 3: TEXTO COM TOOLS (GROQ) ---
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_web_tool",
                    "description": "Busca notícias financeiras e fatos do mundo.",
                    "parameters": {
                        "type": "object",
                        "properties": {"query": {"type": "string"}},
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_market_data",
                    "description": "Busca cotação de Ações e FIIs (ex: PETR4, IVVB11).",
                    "parameters": {
                        "type": "object",
                        "properties": {"ticker": {"type": "string", "description": "Símbolo da ação"}},
                        "required": ["ticker"]
                    }
                }
            }
        ]

        messages = [
            {"role": "system", "content": f"Você é o Maestro do FinançasAI. Hoje é {hoje}. Se necessário, use ferramentas para responder sobre cotações ou notícias."},
            {"role": "user", "content": f"Contexto: Renda R$ {analysis.get('total_income',0):.2f}. Pergunta: {question}"}
        ]

        # Chamada Groq com suporte a Tools
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls:
            messages.append(response_message)
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                
                if function_name == "search_web_tool":
                    result = search_web_tool(args["query"])
                elif function_name == "get_market_data":
                    result = get_market_data(args["ticker"])
                else:
                    result = "Ferramenta não encontrada."

                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": result,
                })
            
            # Segunda chamada para consolidar a resposta
            final_response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages
            )
            return final_response.choices[0].message.content

        return response_message.content

    except Exception as e:
        return f"❌ Erro no Maestro IA: {str(e)}"

def generate_proactive_alert(user_id: int, analysis: dict) -> dict:
    try:
        res = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": "Crie uma dica financeira de 10 palavras."}],
            model="llama-3.1-8b-instant"
        )
        return {"title": "Insight", "message": res.choices[0].message.content}
    except: return None
