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
    """Busca cotação e dados de Ações, FIIs ou Cripto via Yahoo Finance."""
    try:
        ticker = ticker.upper().strip()
        synonyms = {
            "DOLAR": "USDBRL=X", "DÓLAR": "USDBRL=X", "EURO": "EURBRL=X",
            "BITCOIN": "BTC-USD", "IBOVESPA": "^BVSP", "SELIC": "^BCB-SELIC"
        }
        if ticker in synonyms: ticker = synonyms[ticker]
        if "." not in ticker and "-" not in ticker and "^" not in ticker:
            if len(ticker) >= 5: ticker = f"{ticker}.SA"
        
        stock = yf.Ticker(ticker)
        info = stock.info
        # Tenta várias chaves de preço (Yahoo Finance varia o nome da chave para FIIs)
        price = (info.get("currentPrice") or info.get("regularMarketPrice") or 
                 info.get("bid") or info.get("ask") or info.get("previousClose"))
        
        name = info.get("longName") or info.get("shortName") or ticker
        currency = info.get("currency", "BRL")
        
        if price:
            return f"Cotação de {name} ({ticker}): {currency} {price:.2f}"
        
        # --- FALLBACK AUTOMÁTICO DENTRO DA FERRAMENTA ---
        print(f"Yahoo falhou para {ticker}, tentando busca web...")
        web_res = search_web_tool(f"cotação {ticker} hoje valor")
        return f"O Yahoo Finance não respondeu, mas encontrei estas informações na web: {web_res}"
        
    except Exception as e:
        # Se até o erro técnico acontecer, tenta a web
        web_res = search_web_tool(f"cotação {ticker} hoje")
        return f"Erro no Yahoo, mas busquei na web: {web_res}"

def chat_with_ai(question: str, analysis: dict, user_id: int, image_base64: str = None, audio_base64: str = None) -> str:
    """Assistente com Loop de Raciocínio (Tenta várias ferramentas se necessário)."""
    try:
        from datetime import datetime
        hoje = datetime.now().strftime("%Y-%m-%d")

        # --- CASO 1: IMAGEM (GEMINI) ---
        if image_base64:
            b64_data = image_base64.split("base64,")[1] if "base64," in image_base64 else image_base64
            image_bytes = base64.b64decode(b64_data)
            model = genai.GenerativeModel('gemini-flash-latest')
            response = model.generate_content([
                "Você é um Especialista em Auditoria. Extraia o gasto desta imagem: [GASTO: valor, estabelecimento, categoria]",
                {"mime_type": "image/jpeg", "data": image_bytes}
            ])
            return response.text

        # --- CASO 2: ÁUDIO ---
        if audio_base64:
            temp_audio = f"temp_{user_id}.webm"
            audio_data = audio_base64.split("base64,")[1] if "base64," in audio_base64 else audio_base64
            with open(temp_audio, "wb") as f: f.write(base64.b64decode(audio_data))
            with open(temp_audio, "rb") as file:
                transcription = groq_client.audio.transcriptions.create(
                    file=(temp_audio, file.read()), model="whisper-large-v3")
            os.remove(temp_audio)
            question = transcription.text

        # --- CASO 3: TEXTO COM LOOP DE TOOLS ---
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_web_tool",
                    "description": "Busca informações na web quando o Yahoo Finance falha ou para notícias.",
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
                    "description": "Tenta buscar cotação de Ações e FIIs no Yahoo Finance.",
                    "parameters": {
                        "type": "object",
                        "properties": {"ticker": {"type": "string"}},
                        "required": ["ticker"]
                    }
                }
            }
        ]

        instruction = f"""Você é o Assistente Financeiro Sênior. Hoje é {hoje}.
        Sua missão é dar a resposta correta ao usuário, custe o que custar.
        
        LOGICA DE FERRAMENTAS:
        1. Se ele perguntar preço, tente primeiro 'get_market_data'.
        2. SE O MERCADO FALHAR (der erro ou não achar preço), use IMEDIATAMENTE a 'search_web_tool' para buscar o preço no Google/Notícias.
        3. Nunca diga que não conseguiu sem tentar a busca web como segunda opção.
        
        DADOS DO USUÁRIO: Renda R$ {analysis.get('total_income',0):.2f}, Gastos R$ {analysis.get('total_expenses',0):.2f}.
        """

        messages = [
            {"role": "system", "content": instruction},
            {"role": "user", "content": question}
        ]

        # LOOP DE RACIOCÍNIO (Máximo 3 rodadas)
        for _ in range(3):
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.1
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if not tool_calls:
                return response_message.content

            messages.append(response_message)
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                
                if function_name == "search_web_tool":
                    result = search_web_tool(args["query"])
                elif function_name == "get_market_data":
                    result = get_market_data(args["ticker"])
                else: result = "Erro."

                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": result,
                })
            # O loop continua para a próxima rodada com os resultados das ferramentas
        
        return "Desculpe, após várias tentativas não consegui os dados. Tente perguntar de outra forma."

    except Exception as e:
        return f"❌ Erro no Assistente IA: {str(e)}"

def generate_recommendations(analysis: dict) -> str:
    try:
        res = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": f"Renda {analysis.get('total_income')}, Gastos {analysis.get('total_expenses')}. Dê 3 dicas curtas."}],
            model="llama-3.3-70b-versatile"
        )
        return res.choices[0].message.content
    except: return "IA ocupada."

def generate_proactive_alert(user_id: int, analysis: dict) -> dict:
    try:
        res = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": "Dica financeira curta."}],
            model="llama-3.1-8b-instant"
        )
        return {"title": "Dica", "message": res.choices[0].message.content}
    except: return None
