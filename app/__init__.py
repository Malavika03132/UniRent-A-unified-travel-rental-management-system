import os
from flask import Flask, session, g
from config import Config
from app.models import db, User

def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    )
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    
    # Context processor for session user and currency formatting
    @app.context_processor
    def inject_context():
        user = None
        user_id = session.get('user_id')
        if user_id:
            try:
                user = db.session.get(User, user_id)
            except Exception:
                user = None
        return dict(
            current_user=user,
            format_currency=lambda val: f"₹{val:,.0f}" if val is not None else "₹0"
        )
        
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.traveler import traveler_bp
    from app.routes.owner import owner_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(traveler_bp, url_prefix='/traveler')
    app.register_blueprint(owner_bp, url_prefix='/owner')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    with app.app_context():
        # Create tables if not present (especially for SQLite out-of-the-box mode)
        try:
            db.create_all()
        except Exception as e:
            print(f"Warning during db.create_all(): {e}")
            
    return app
