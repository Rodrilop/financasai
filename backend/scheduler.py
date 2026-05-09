import os
import logging
import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from database import get_connection

logger = logging.getLogger("financasai.scheduler")

def check_and_send_retention_alerts():
    """
    Verifica se usuários PRO lançaram gastos hoje. 
    Se não, envia um lembrete via WhatsApp.
    """
    logger.info("Iniciando verificação de retenção proativa...")
    conn = get_connection()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 1. Busca todos os usuários PRO que tenham telefone cadastrado
    users = conn.execute("SELECT id, phone, name FROM users WHERE is_pro = 1 AND phone IS NOT NULL").fetchall()
    
    token = os.getenv("WHATSAPP_CLOUD_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    
    if not token or not phone_id:
        logger.error("Tokens de WhatsApp não configurados para o scheduler.")
        conn.close()
        return

    for user in users:
        user_id = user["id"]
        phone = user["phone"]
        name = user["name"] or "ali"
        
        # 2. Verifica se houve algum gasto registrado hoje
        expense = conn.execute("SELECT id FROM expenses WHERE user_id = ? AND date = ?", (user_id, today)).fetchone()
        
        if not expense:
            # 3. Envia o lembrete (Nudge)
            logger.info(f"Enviando lembrete para {name} ({phone})")
            url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
            headers = {"Authorization": f"Bearer {token}"}
            
            message = (
                f"Olá {name}! 👋\n\nNotei que você ainda não registrou nenhum gasto hoje. "
                "Para manter sua saúde financeira em dia, não esqueça de anotar até os pequenos gastos! ☕🥐\n\n"
                "Quer registrar algo agora? Basta me mandar uma mensagem aqui ou uma foto do cupom!"
            )
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": phone,
                "type": "text",
                "text": {"body": message}
            }
            
            try:
                requests.post(url, json=payload, headers=headers)
            except Exception as e:
                logger.error(f"Erro ao enviar WhatsApp para {user_id}: {e}")

    conn.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Executa todos os dias às 20:00 (ajustável)
    scheduler.add_job(check_and_send_retention_alerts, 'cron', hour=20, minute=0)
    # Para teste: executa também a cada 1 hora se quiser (comentado para prod)
    # scheduler.add_job(check_and_send_retention_alerts, 'interval', hours=1)
    
    scheduler.start()
    logger.info("Scheduler de retenção iniciado (Job às 20:00).")
