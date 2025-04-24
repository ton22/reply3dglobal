#!/usr/bin/env python
import os
import sys
from app import app, db
from initialize_data import initialize_all

def run_flask():
    """Inicia o aplicativo usando o servidor de desenvolvimento do Flask"""
    print("Iniciando em modo de desenvolvimento...")
    with app.app_context():
        db.create_all()
        initialize_all()
    app.run(host="0.0.0.0", port=5001, debug=True)

def run_gunicorn():
    """Inicia o aplicativo usando Gunicorn"""
    print("Iniciando em modo de produção...")
    import gunicorn.app.base
    
    class StandaloneApplication(gunicorn.app.base.BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            for key, value in self.options.items():
                if key in self.cfg.settings and value is not None:
                    self.cfg.set(key.lower(), value)

        def load(self):
            return self.application

    with app.app_context():
        db.create_all()
        initialize_all()

    options = {
        'bind': '127.0.0.1:5001',
        'workers': 4,
        'worker_class': 'sync',
        'timeout': 120,
        'keepalive': 5,
        'loglevel': 'info'
    }

    StandaloneApplication(app, options).run()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--prod' or sys.argv[1] == '-p':
            run_gunicorn()
        elif sys.argv[1] == '--help' or sys.argv[1] == '-h':
            print("""
Uso: python run.py [opção]

Opções:
  --dev, -d     Inicia em modo de desenvolvimento (padrão)
  --prod, -p    Inicia em modo de produção com Gunicorn
  --help, -h    Mostra esta mensagem de ajuda
            """)
        elif sys.argv[1] == '--dev' or sys.argv[1] == '-d':
            run_flask()
        else:
            print("Opção inválida. Use --help para ver as opções disponíveis.")
    else:
        run_flask()  # Modo de desenvolvimento como padrão 