import os
import json
import base64
import google.generativeai as genai
from groq import Groq
from dotenv import load_dotenv
from database import get_connection

load_dotenv(override=True)

# --- INICIALIZAÇÃO DOS CLIENTES ---
# Groq para Velocidade (Texto/Áudio)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))

# Gemini para Precisão Visual (Imagens/Cupons)
genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

def generate_recommendations(analysis: dict) -> str:
    """Usa o Groq (Llama 3) para gerar recomendações financeiras instantâneas."""
    try:
        income = analysis.get("total_income", 0)
        expenses = analysis.get("total_expenses", 0)
        balance = analysis.get("balance", 0)
        
        prompt = f"""Analise os dados: Renda R$ {income:.2f}, Gastos R$ {expenses:.2f}, Saldo R$ {balance:.2f}.
        Dê 3 dicas curtas e práticas de economia para este usuário brasileiro. Seja direto e motivador."""

        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
            temperature=0.7
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Erro no Groq (Recommendations): {e}")
        return "⚠️ IA temporariamente ocupada. Continue acompanhando seus gastos!"

def chat_with_ai(question: str, analysis: dict, user_id: int, image_base64: str = None, audio_base64: str = None) -> str:
    """O Maestro: Roteia para Groq (Texto/Áudio) ou Gemini (Imagem)."""
    try:
        from datetime import datetime
        hoje = datetime.now().strftime("%Y-%m-%d")

        # --- CASO 1: IMAGEM (GEMINI) ---
        if image_base64:
            b64_data = image_base64.split("base64,")[1] if "base64," in image_base64 else image_base64
            image_bytes = base64.b64decode(b64_data)
            
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content([
                "Extraia o valor total, estabelecimento e data deste cupom fiscal. Se for um gasto, responda estritamente com: [GASTO: valor, descrição, categoria]",
                {"mime_type": "image/jpeg", "data": image_bytes}
            ])
            
            content = response.text
            if "[GASTO:" in content:
                return f"📸 Li seu cupom! {content}. Deseja que eu registre agora?"
            
            return content

        # --- CASO 2: ÁUDIO (GROQ WHISPER + LLAMA) ---
        if audio_base64:
            temp_audio = f"temp_audio_{user_id}.webm"
            audio_data = audio_base64.split("base64,")[1] if "base64," in audio_base64 else audio_base64
            with open(temp_audio, "wb") as f:
                f.write(base64.b64decode(audio_data))
            
            with open(temp_audio, "rb") as file:
                transcription = groq_client.audio.transcriptions.create(
                    file=(temp_audio, file.read()),
                    model="whisper-large-v3",
                )
            os.remove(temp_audio)
            question = transcription.text
            print(f"🎙️ Transcrição Groq: {question}")

        # --- CASO 3: TEXTO (GROQ LLAMA 3) ---
        instruction = f"Você é o assistente do FinançasAI. Hoje é {hoje}. Seja conciso. Se o usuário informar um gasto, identifique o valor e descrição."
        
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": instruction},
                {"role": "user", "content": f"Dados: Renda R$ {analysis.get('total_income',0):.2f}. Usuário: {question}"}
            ],
            model="llama3-70b-8192",
            temperature=0.5
        )
        
        return response.choices[0].message.content

    except Exception as e:
        return f"❌ Erro no Maestro IA: {str(e)}"

def generate_proactive_alert(user_id: int, analysis: dict) -> dict:
    """Analisador autônomo usando Groq (Llama 3)."""
    try:
        income = analysis.get("total_income", 0)
        expenses = analysis.get("total_expenses", 0)
        
        prompt = f"Renda: {income}, Gastos: {expenses}. Crie uma dica financeira curta de 10 palavras."

        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192"
        )
        return {"title": "Insight Rápido", "message": response.choices[0].message.content}
    except:
        return None
