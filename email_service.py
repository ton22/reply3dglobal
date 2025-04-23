import os
import logging
from datetime import datetime

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

# Configuração de logging
logger = logging.getLogger(__name__)

def send_email(to_email, subject, html_content=None, text_content=None):
    """
    Envia um e-mail usando SendGrid
    
    Args:
        to_email (str): E-mail do destinatário
        subject (str): Assunto do e-mail
        html_content (str, optional): Conteúdo HTML do e-mail
        text_content (str, optional): Conteúdo em texto simples do e-mail
        
    Returns:
        bool: True se o e-mail foi enviado com sucesso, False caso contrário
    """
    # Obter a chave de API do SendGrid
    api_key = os.environ.get('SENDGRID_API_KEY')
    
    # Se não tiver a chave, registrar erro e retornar False
    if not api_key:
        logger.error("SENDGRID_API_KEY não está configurada.")
        return False
        
    # Configurar e-mail do remetente (geralmente o e-mail da empresa ou do sistema)
    from_email = os.environ.get('SENDGRID_FROM_EMAIL', 'noreply@3dglobalstore.com')
    
    # Criar mensagem
    message = Mail(
        from_email=Email(from_email),
        to_emails=To(to_email),
        subject=subject
    )
    
    # Adicionar conteúdo (HTML ou texto)
    if html_content:
        message.content = Content("text/html", html_content)
    elif text_content:
        message.content = Content("text/plain", text_content)
    else:
        logger.error("Tentativa de enviar e-mail sem conteúdo")
        return False
    
    try:
        # Inicializar o cliente SendGrid e enviar e-mail
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        # Verificar se o e-mail foi enviado com sucesso (status 2xx)
        if 200 <= response.status_code < 300:
            logger.info(f"E-mail enviado com sucesso para {to_email}")
            return True
        else:
            logger.error(f"Erro ao enviar e-mail. Status: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Exceção ao enviar e-mail: {str(e)}")
        return False

def send_stock_alert(item_name, current_stock, min_stock, unit_symbol, email):
    """
    Envia um alerta de estoque baixo por e-mail
    
    Args:
        item_name (str): Nome do item
        current_stock (float): Estoque atual
        min_stock (float): Estoque mínimo
        unit_symbol (str): Símbolo da unidade de medida
        email (str): E-mail do destinatário
        
    Returns:
        bool: True se o e-mail foi enviado com sucesso, False caso contrário
    """
    # Criar assunto
    subject = f"[ALERTA] Estoque Baixo: {item_name}"
    
    # Criar conteúdo HTML
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
        <h2 style="color: #d9534f;">Alerta de Estoque Baixo</h2>
        <p>Este é um alerta automático do sistema 3D Global Store.</p>
        <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <p><strong>Item com estoque baixo:</strong> {item_name}</p>
            <p><strong>Estoque atual:</strong> {current_stock} {unit_symbol}</p>
            <p><strong>Estoque mínimo:</strong> {min_stock} {unit_symbol}</p>
            <p><strong>Percentual:</strong> {round((current_stock/min_stock)*100, 1)}%</p>
        </div>
        <p>É recomendado verificar o estoque e fazer um novo pedido de compra se necessário.</p>
        <p style="margin-top: 20px; font-size: 12px; color: #777;">
            Enviado em {datetime.now().strftime('%d/%m/%Y %H:%M')} por 3D Global Store.<br>
            <em>Este é um e-mail automático, por favor não responda.</em>
        </p>
    </div>
    """
    
    # Enviar e-mail
    return send_email(email, subject, html_content=html_content)