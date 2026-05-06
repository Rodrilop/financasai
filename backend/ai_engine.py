import os
import json
import base64
from datetime import datetime
from dotenv import load_dotenv
from database import get_connection
import yfinance as yf

load_dotenv(override=True)

GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ── Clientes lazy (inicializam somente quando há chave disponível) ──────────
_groq_client   = None
_gemini_client = None

def _get_groq():
    global _groq_client
    if _groq_client is None and GROQ_API_KEY:
        from groq import Groq
        _groq_client = Groq(api_key=GROQ_API_KEY)
    return _groq_client

def _get_gemini():
    global _gemini_client
    if _gemini_client is None and GEMINI_API_KEY:
        from google import genai
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_client


# ── FERRAMENTAS DE SUPORTE ─────────────────────────────────────────────────
def search_web_tool(query: str) -> str:
    """Busca informações em tempo real via DuckDuckGo."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if not results:
                return "Nenhum resultado encontrado."
            return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
    except Exception as e:
        return f"Erro na pesquisa: {str(e)}"


def get_market_data_tool(ticker: str) -> str:
    """Consulta cotações (Dólar, Euro, Bitcoin, Selic, ações B3)."""
    try:
        q = ticker.upper().strip()
        target_ticker = q

        if "SELIC" in q:
            return "Busca Web: " + search_web_tool("taxa selic hoje valor atualizado")
        elif "DOLAR" in q or "DÓLAR" in q or "USD" in q:
            target_ticker = "USDBRL=X"
        elif "EURO" in q or "EUR" in q:
            target_ticker = "EURBRL=X"
        elif "BITCOIN" in q or "BTC" in q:
            target_ticker = "BTC-USD"

        if target_ticker == q and "." not in q and "-" not in q and 4 <= len(q) <= 6:
            target_ticker = f"{q}.SA"

        stock = yf.Ticker(target_ticker)
        data  = stock.history(period="1d")
        if not data.empty:
            price = data['Close'].iloc[-1]
            return f"Cotação de {target_ticker}: R$ {price:.2f}"

        price = stock.info.get("currentPrice") or stock.info.get("regularMarketPrice")
        if price:
            return f"Cotação de {target_ticker}: R$ {price:.2f}"

        return f"Sem dados para {target_ticker}. " + search_web_tool(f"valor {q} hoje")
    except Exception as e:
        return f"Erro ({str(e)}). " + search_web_tool(f"valor {ticker} hoje")


# ── HELPER DB ──────────────────────────────────────────────────────────────
def _db_exec(sql: str, params: tuple):
    conn = get_connection()
    conn.execute(sql, params)
    conn.commit()
    conn.close()


# ── EXECUTOR DE TOOLS (compartilhado pelos dois motores) ───────────────────
def _execute_tool(name: str, args: dict, user_id: int, hoje: str) -> tuple[str, str | None]:
    """
    Executa uma tool call e retorna (tool_result_text, summary_key_or_None).
    summary_key é usado para construir a resposta final sintética.
    """
    if name == "add_expense":
        desc = args.get("desc", "Despesa")
        val  = float(args.get("val", 0))
        cat  = args.get("cat", "Outros")
        _db_exec(
            "INSERT INTO expenses (user_id, description, amount, category, priority, date) VALUES (?,?,?,?,?,?)",
            (user_id, desc, val, cat, "Importante", hoje)
        )
        return (
            f"Despesa '{desc}' de R$ {val:.2f} registrada com sucesso na categoria '{cat}'.",
            f"add_expense:{desc}:{val}"
        )
    elif name == "update_salary":
        val = float(args.get("val", 0))
        _db_exec("UPDATE users SET salary = ? WHERE id = ?", (val, user_id))
        return (
            f"Renda atualizada para R$ {val:.2f} com sucesso.",
            f"update_salary:{val}"
        )
    elif name == "market_info":
        result = get_market_data_tool(args.get("q", ""))
        return result, None
    return "OK.", None


def _build_final_response(summaries: list[str]) -> str:
    """Gera resposta final amigável a partir dos summaries de execução."""
    lines = []
    for s in summaries:
        if s.startswith("add_expense:"):
            _, desc, val = s.split(":", 2)
            lines.append(f"• Despesa **{desc}** de **R$ {float(val):.2f}** registrada com sucesso! ✅")
        elif s.startswith("update_salary:"):
            _, val = s.split(":", 1)
            lines.append(f"• Renda atualizada para **R$ {float(val):.2f}** ✅")
    if lines:
        return "Pronto! Aqui está o que foi feito:\n\n" + "\n".join(lines) + "\n\nAcesse **Despesas** no menu para conferir."
    return "✅ Ação executada com sucesso!"


# ── MOTOR GROQ (primário) ──────────────────────────────────────────────────
def _chat_groq(question: str, analysis: dict, user_id: int, hoje: str) -> str:
    groq = _get_groq()
    if groq is None:
        raise RuntimeError("GROQ_API_KEY não configurada.")

    tools = [
        {"type": "function", "function": {
            "name": "add_expense",
            "description": "Registra um gasto/despesa no banco de dados do usuário.",
            "parameters": {"type": "object", "properties": {
                "desc": {"type": "string", "description": "Descrição da despesa"},
                "val":  {"type": "number", "description": "Valor em reais"},
                "cat":  {"type": "string", "description": "Categoria (ex: Alimentação, Transporte, etc)"}
            }, "required": ["desc", "val", "cat"]}
        }},
        {"type": "function", "function": {
            "name": "update_salary",
            "description": "Atualiza a renda mensal do usuário.",
            "parameters": {"type": "object", "properties": {
                "val": {"type": "number", "description": "Novo valor da renda em reais"}
            }, "required": ["val"]}
        }},
        {"type": "function", "function": {
            "name": "market_info",
            "description": "Consulta cotações (Dólar, Euro, Bitcoin, Selic, ações B3).",
            "parameters": {"type": "object", "properties": {
                "q": {"type": "string", "description": "Ativo a consultar (ex: DÓLAR, PETR4, BTC, SELIC)"}
            }, "required": ["q"]}
        }},
    ]

    instruction = (
        f"Você é o Assistente Financeiro do FinançasAI. Hoje é {hoje}.\n"
        f"Renda do usuário: R$ {analysis.get('total_income', 0):.2f}. "
        f"Gastos este mês: R$ {analysis.get('total_expenses', 0):.2f}.\n\n"
        "REGRAS:\n"
        "- Use 'add_expense' para registrar qualquer gasto mencionado.\n"
        "- Use 'update_salary' para atualizar salário/renda.\n"
        "- Use 'market_info' para cotações.\n"
        "- Responda sempre em português brasileiro, de forma amigável e concisa.\n"
        "- Após executar uma ferramenta, confirme o resultado ao usuário."
    )

    messages = [
        {"role": "system", "content": instruction},
        {"role": "user", "content": question}
    ]

    summaries: list[str] = []

    for _ in range(4):
        resp = groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0
        )
        msg           = resp.choices[0].message
        finish_reason = resp.choices[0].finish_reason

        # Resposta final em linguagem natural
        if not msg.tool_calls:
            content = (msg.content or "").strip()
            # Sanidade: se o modelo retornou JSON bruto em vez de texto
            if content.startswith("{") and any(kw in content for kw in ['"name":', '"function":']):
                break
            return content

        # Adiciona mensagem do assistente com tool_calls
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ]
        })

        # Executa cada tool call
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            try:
                tool_result, summary = _execute_tool(name, args, user_id, hoje)
                if summary:
                    summaries.append(summary)
            except Exception as e:
                tool_result = f"Erro ao executar {name}: {str(e)}"

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "name": name,
                "content": tool_result
            })

        if finish_reason != "tool_calls":
            break

    # Fallback sintético
    if summaries:
        return _build_final_response(summaries)

    # Último conteúdo do assistente
    for m in reversed(messages):
        if m.get("role") == "assistant" and m.get("content"):
            return m["content"]
    return "Desculpe, não consegui processar. Tente novamente."


# ── MOTOR GEMINI (fallback) ────────────────────────────────────────────────
def _chat_gemini(question: str, analysis: dict, user_id: int, hoje: str) -> str:
    """Usa Gemini 2.0 Flash com function calling nativo via google.genai SDK."""
    from google.genai import types as gtypes

    client = _get_gemini()
    if client is None:
        return "❌ Nenhuma chave de API configurada. Configure GROQ_API_KEY ou GEMINI_API_KEY no arquivo .env."

    # Define as tools para o Gemini
    add_expense_fn = gtypes.FunctionDeclaration(
        name="add_expense",
        description="Registra um gasto/despesa no banco de dados do usuário.",
        parameters=gtypes.Schema(
            type=gtypes.Type.OBJECT,
            properties={
                "desc": gtypes.Schema(type=gtypes.Type.STRING, description="Descrição da despesa"),
                "val":  gtypes.Schema(type=gtypes.Type.NUMBER, description="Valor em reais"),
                "cat":  gtypes.Schema(type=gtypes.Type.STRING, description="Categoria (ex: Alimentação, Transporte)"),
            },
            required=["desc", "val", "cat"]
        )
    )
    update_salary_fn = gtypes.FunctionDeclaration(
        name="update_salary",
        description="Atualiza a renda mensal do usuário.",
        parameters=gtypes.Schema(
            type=gtypes.Type.OBJECT,
            properties={
                "val": gtypes.Schema(type=gtypes.Type.NUMBER, description="Novo valor da renda em reais"),
            },
            required=["val"]
        )
    )
    market_info_fn = gtypes.FunctionDeclaration(
        name="market_info",
        description="Consulta cotações financeiras (Dólar, Euro, Bitcoin, Selic, ações B3).",
        parameters=gtypes.Schema(
            type=gtypes.Type.OBJECT,
            properties={
                "q": gtypes.Schema(type=gtypes.Type.STRING, description="Ativo a consultar"),
            },
            required=["q"]
        )
    )

    gemini_tools = gtypes.Tool(function_declarations=[add_expense_fn, update_salary_fn, market_info_fn])

    system_instruction = (
        f"Você é o Assistente Financeiro do FinançasAI. Hoje é {hoje}.\n"
        f"Renda do usuário: R$ {analysis.get('total_income', 0):.2f}. "
        f"Gastos este mês: R$ {analysis.get('total_expenses', 0):.2f}.\n\n"
        "Use as ferramentas disponíveis para registrar gastos, atualizar renda ou consultar cotações. "
        "Responda sempre em português brasileiro, de forma amigável e concisa."
    )

    contents = [gtypes.Content(role="user", parts=[gtypes.Part(text=question)])]
    summaries: list[str] = []

    for _ in range(4):
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=gtypes.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[gemini_tools],
                temperature=0
            )
        )

        candidate = resp.candidates[0]
        parts      = candidate.content.parts if candidate.content else []

        # Verifica se há function calls
        fn_calls = [p for p in parts if p.function_call is not None]
        text_parts = [p.text for p in parts if p.text]

        if not fn_calls:
            # Resposta final em linguagem natural
            return "\n".join(text_parts) if text_parts else _build_final_response(summaries) if summaries else "✅ Pronto!"

        # Adiciona a resposta do modelo ao histórico
        contents.append(candidate.content)

        # Executa cada function call
        fn_responses = []
        for p in fn_calls:
            fc   = p.function_call
            name = fc.name
            args = dict(fc.args) if fc.args else {}
            try:
                tool_result, summary = _execute_tool(name, args, user_id, hoje)
                if summary:
                    summaries.append(summary)
            except Exception as e:
                tool_result = f"Erro: {str(e)}"

            fn_responses.append(
                gtypes.Part(function_response=gtypes.FunctionResponse(
                    name=name,
                    response={"result": tool_result}
                ))
            )

        contents.append(gtypes.Content(role="user", parts=fn_responses))

    # Fallback sintético
    return _build_final_response(summaries) if summaries else "Desculpe, não consegui processar. Tente novamente."


# ── MOTOR PRINCIPAL (PONTO DE ENTRADA) ────────────────────────────────────
def chat_with_ai(
    question: str,
    analysis: dict,
    user_id: int,
    image_base64: str = None,
    audio_base64: str = None
) -> str:
    """Assistente Financeiro: Groq primário → Gemini fallback. Multimodal."""
    try:
        hoje = datetime.now().strftime("%Y-%m-%d")

        # ── VISÃO: Imagem de cupom fiscal ─────────────────────────────────
        if image_base64:
            b64_data = image_base64.split("base64,")[1] if "base64," in image_base64 else image_base64

            # Tenta Groq Vision primeiro
            groq = _get_groq()
            if groq:
                try:
                    resp = groq.chat.completions.create(
                        model="llama-3.2-11b-vision-preview",
                        messages=[{"role": "user", "content": [
                            {"type": "text",      "text": "Extraia deste cupom: Valor Total, Estabelecimento e Categoria."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"}}
                        ]}]
                    )
                    return resp.choices[0].message.content
                except Exception as gv_err:
                    print(f"Groq Vision falhou: {gv_err}")

            # Fallback: Gemini Vision
            client = _get_gemini()
            if client:
                from google.genai import types as gtypes
                image_bytes = base64.b64decode(b64_data)
                resp = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[
                        "Extraia deste cupom fiscal: Valor Total, Estabelecimento e Categoria.",
                        gtypes.Part(inline_data=gtypes.Blob(mime_type="image/jpeg", data=image_bytes))
                    ]
                )
                return resp.text

            return "❌ Nenhuma chave de API de Visão configurada."

        # ── ÁUDIO: Transcrição Whisper ─────────────────────────────────────
        if audio_base64:
            groq = _get_groq()
            if groq:
                try:
                    temp_audio = f"temp_{user_id}_{datetime.now().timestamp()}.webm"
                    audio_data = audio_base64.split("base64,")[1] if "base64," in audio_base64 else audio_base64
                    with open(temp_audio, "wb") as f:
                        f.write(base64.b64decode(audio_data))
                    with open(temp_audio, "rb") as file:
                        transcription = groq.audio.transcriptions.create(
                            file=(temp_audio, file.read()), model="whisper-large-v3"
                        )
                    os.remove(temp_audio)
                    question = transcription.text
                except Exception as e:
                    print(f"Erro Áudio: {e}")

        # ── CHAT PRINCIPAL: Groq → Gemini ─────────────────────────────────
        try:
            return _chat_groq(question, analysis, user_id, hoje)
        except Exception as groq_err:
            print(f"Groq falhou ({groq_err}), usando Gemini como fallback...")
            return _chat_gemini(question, analysis, user_id, hoje)

    except Exception as e:
        return f"❌ Erro Assistente: {str(e)}"


# ── RECOMENDAÇÕES PROATIVAS ────────────────────────────────────────────────
def generate_recommendations(analysis: dict) -> str:
    try:
        groq = _get_groq()
        if groq:
            res = groq.chat.completions.create(
                messages=[{"role": "user", "content": (
                    f"Dê uma dica financeira prática para alguém com renda de R$ {analysis.get('total_income')} "
                    f"e gastos de R$ {analysis.get('total_expenses')}. Seja conciso e direto."
                )}],
                model="llama-3.1-8b-instant"
            )
            return res.choices[0].message.content

        # Fallback Gemini
        client = _get_gemini()
        if client:
            resp = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"Dê uma dica financeira prática para alguém com renda de R$ {analysis.get('total_income')} e gastos de R$ {analysis.get('total_expenses')}. Seja conciso."
            )
            return resp.text
    except Exception:
        pass
    return "Economize 10% do seu saldo livre hoje."


def generate_proactive_alert(user_id, analysis):
    return None
