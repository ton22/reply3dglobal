import logging
from flask import redirect, url_for
from flask_login import current_user
from app import app, db

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Import routes after app initialization to avoid circular imports
import auth
import inventory
import projects
import movements
import reports
import settings

# Add root route
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

if __name__ == "__main__":
    with app.app_context():
        # Create database tables if they don't exist
        db.create_all()
        
        # Initialize basic data if not exists
        from initialize_data import initialize_all
        initialize_all()
        
    app.run(host="0.0.0.0", port=5001, debug=True)
