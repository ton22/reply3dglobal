import os
import sqlite3
from datetime import datetime
import logging
from flask import Flask, g, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager, current_user

# Configuração do ambiente
ENV = os.environ.get('FLASK_ENV', 'development')
DEBUG = ENV == 'development'

class Base(DeclarativeBase):
    pass


# Create SQLAlchemy instance
db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure SQLite database for offline use
db_path = os.path.join(app.instance_path, '3d_global_store.sqlite')
os.makedirs(os.path.dirname(db_path), exist_ok=True)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", f"sqlite:///{db_path}")

# Configure SQLAlchemy options for future cloud migration
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_size": 5,
    "max_overflow": 10
}

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'



@app.template_filter('get_total_value')
def get_total_value(purchase_order):
    total = 0.0
    for item in purchase_order.items:
        item_price = item.item.unit.price if hasattr(item.item.unit, 'price') else 0
        total += float(item.quantity) * float(item_price)
    return round(total, 2)

# Add nl2br filter to Jinja2
@app.template_filter('nl2br')
def nl2br(value):
    if value is None:
        return ''
    return value.replace('\n', '<br>')

# Initialize SQLAlchemy with app
db.init_app(app)

# Set global template variables
@app.context_processor
def inject_year():
    return {'current_year': datetime.now().year}

@app.context_processor
def inject_settings():
    def get_setting(key, default=None):
        try:
            from models import Setting
            with app.app_context():
                setting = Setting.query.filter_by(key=key).first()
                return setting.value if setting else default
        except Exception:
            return default
    
    return dict(get_setting=get_setting)

# Configure logging
if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )

# Import routes after app initialization to avoid circular imports
import auth
import inventory
import projects
import movements
import reports
import settings
import main
import utils

# Initialize database logger
logger = utils.setup_database_logger()

@app.before_request
def before_request():
    if current_user.is_authenticated:
        g.user_id = current_user.id
    else:
        g.user_id = None

# Import models and create tables
with app.app_context():
    # Import models - must be done after db initialization to avoid circular imports
    from models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    db.create_all()

    # Initialize basic data if not exists
    from initialize_data import initialize_all
    initialize_all()
        
    if DEBUG:
        app.run(host="0.0.0.0", port=5001, debug=True)
    else:
        app.run(host="0.0.0.0", port=5001)
