# utils.py
import random
from flask import g
from models import Log, db
import logging
import string
from datetime import datetime

def generate_sku(name, item_type_id):
    """
    Gera um SKU único com no máximo 4 caracteres.
    Formato: Combina as 2 primeiras letras do nome + último dígito do tipo + número aleatório
    Exemplo: "PLA1" para Filamento PLA tipo 1
    """
    if not name:
        name = "ITEM"
    
    # Pegar as 2 primeiras letras do nome (convertido para maiúsculas)
    prefix = name.strip().upper()[:2]
    
    # Pegar o último dígito do tipo de item
    type_digit = str(item_type_id)[-1]
    
    # Adicionar um dígito aleatório para aumentar a aleatoriedade
    random_digit = random.choice(string.digits)
    
    # Combinar para formar o SKU de 4 caracteres
    sku = f"{prefix}{type_digit}{random_digit}"
    
    return sku

def generate_barcode(item_id=None):
    """
    Gera um código de barras único.
    Formato: Prefixo da empresa (999) + timestamp + ID do item (ou aleatório se for novo)
    """
    # Prefixo da empresa (3 dígitos)
    prefix = "999"
    
    # Timestamp atual em formato compacto (até 10 dígitos)
    timestamp = datetime.now().strftime("%y%m%d%H%M")
    
    # Item ID ou número aleatório (3 dígitos)
    if item_id:
        suffix = str(item_id).zfill(3)[-3:]
    else:
        suffix = ''.join(random.choices(string.digits, k=3))
    
    # Combinar para formar o código de barras
    barcode = f"{prefix}{timestamp}{suffix}"
    
    return barcode

class DatabaseLogger(logging.Handler):
    def emit(self, record):
        try:
            log = Log(
                log_level=record.levelname,
                message=self.format(record),
                user_id=getattr(g, 'user_id', None)
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            # Se houver erro ao salvar o log, não queremos que isso atrapalhe o sistema
            print(f"Erro ao salvar log no banco: {str(e)}")

def setup_database_logger():
    """Configura o logger para gravar no banco de dados"""
    logger = logging.getLogger('app')
    
    # Configurar o formato do log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Criar e configurar o handler
    db_handler = DatabaseLogger()
    db_handler.setLevel(logging.INFO)
    db_handler.setFormatter(formatter)
    
    # Adicionar o handler ao logger
    logger.addHandler(db_handler)
    logger.setLevel(logging.INFO)
    
    return logger