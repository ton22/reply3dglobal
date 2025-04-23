# Configurações do Gunicorn para desenvolvimento local
bind = "127.0.0.1:5000"  # Endereço e porta
workers = 4  # Número de workers
worker_class = "sync"  # Tipo de worker
timeout = 120  # Tempo máximo de resposta
keepalive = 5  # Conexões keep-alive
errorlog = "-"  # Log de erros no console
loglevel = "info"  # Nível de log
accesslog = "-"  # Log de acesso no console
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"' 