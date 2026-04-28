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
        synonyms = {
            "DOLAR": "USDBRL=X", "DÓLAR": "USDBRL=X", "EURO": "EURBRL=X",
            "BITCOIN": "BTC-USD", "IBOVESPA": "^BVSP", "SELIC": "^BCB-SELIC"
        }
        if ticker in synonyms: ticker = synonyms[ticker]
        if "." not in ticker and "-" not in ticker and "^" not in ticker:
            if len(ticker) >= 5: ticker = f"{ticker}.SA"
        
        stock = yf.Ticker(ticker)
        info = stock.info
        price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose") or info.get("ask")
        name = info.get("longName") or info.get("shortName") or ticker
        currency = info.get("currency", "BRL")
        
        if price:
            return f"Cotação de {name} ({ticker}): {currency} {price:.2f}"
        return f"Não consegui o preço exato para '{ticker}'."
    except Exception as e:
        return f"Erro técnico ao buscar '{ticker}': {str(e)}"

def generate_recommendations(analysis: dict) -> str:
    """Gera recomendações usando Groq Llama 3.3."""
    try:
        income = analysis.get("total_income", 0)
        expenses = analysis.get("total_expenses", 0)
        prompt = f"""Como seu Assistente Financeiro, analisei seus dados: 
        Renda R$ {income:.2f}, Gastos R$ {expenses:.2f}. 
        Forneça 3 recomendações estratégicas para melhorar o saldo livre."""
        res = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7
        )
        return res.choices[0].message.content
    except:
        return "⚠️ IA temporariamente ocupada."

def chat_with_ai(question: str, analysis: dict, user_id: int, image_base64: str = None, audio_base64: str = None) -> str:
    """Assistente Financeiro Híbrido com Prompts Enriquecidos."""
    try:
        from datetime import datetime
        hoje = datetime.now().strftime("%Y-%m-%d")

        # --- CASO 1: IMAGEM (ESPECIALISTA EM VISÃO GEMINI) ---
        if image_base64:
            b64_data = image_base64.split("base64,")[1] if "base64," in image_base64 else image_base64
            image_bytes = base64.b64decode(b64_data)
            
            vision_prompt = """Você é um Especialista em Auditoria Fiscal e Visão Computacional.
            Sua missão é extrair dados de cupons e notas fiscais com 100% de precisão.
            Identifique: Valor Total, Nome do Estabelecimento e Data.
            Responda de forma organizada e pergunte se o usuário deseja registrar o gasto."""
            
            model = genai.GenerativeModel('gemini-flash-latest')
            response = model.generate_content([
                vision_prompt,
                {"mime_type": "image/jpeg", "data": image_bytes}
            ])
            return response.text

        # --- CASO 2: ÁUDIO (TRANSCRIÇÃO WHISPER) ---
        if audio_base64:
            temp_audio = f"temp_{user_id}.webm"
            audio_data = audio_base64.split("base64,")[1] if "base64," in audio_base64 else audio_base64
            with open(temp_audio, "wb") as f: f.write(base64.b64decode(audio_data))
            with open(temp_audio, "rb") as file:
                transcription = groq_client.audio.transcriptions.create(
                    file=(temp_audio, file.read()), model="whisper-large-v3")
            os.remove(temp_audio)
            question = transcription.text

        # --- CASO 3: TEXTO (CONSULTOR FINANCEIRO & ANALISTA DE MERCADO) ---
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_web_tool",
                    "description": "Busca notícias financeiras e tendências de mercado.",
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
                    "description": "Busca cotações em tempo real de Ações, FIIs e Moedas.",
                    "parameters": {
                        "type": "object",
                        "properties": {"ticker": {"type": "string"}},
                        "required": ["ticker"]
                    }
                }
            }
        ]

        instruction = f"""Você é o Assistente Financeiro Pessoal Senior do FinançasAI. 
        Hoje é {hoje}. Você é um especialista em economia brasileira, investimentos e gestão de orçamento.

        PERSONA:
        - Seja profissional, mas acolhedor.
        - Se o usuário perguntar sobre o mercado, use 'get_market_data' para cotações e 'search_web_tool' para contexto.
        - Cruze os dados do usuário (Renda R$ {analysis.get('total_income',0):.2f}) com suas respostas para dar conselhos personalizados.
        - Se identificar um gasto na fala do usuário, confirme o valor e a categoria.
        """

        messages = [
            {"role": "system", "content": instruction},
            {"role": "user", "content": question}
        ]

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
                else: result = "Erro."

                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": result,
                })
            
            final_response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages
            )
            return final_response.choices[0].message.content

        return response_message.content

    except Exception as e:
        return f"❌ Erro no Assistente IA: {str(e)}"

def generate_proactive_alert(user_id: int, analysis: dict) -> dict:
    try:
        res = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": "Dê uma dica financeira curta."}],
            model="llama-3.1-8b-instant"
        )
        return {"title": "Dica do Assistente", "message": res.choices[0].message.content}
    except: return None
