from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from config import config

# Initialize extensions
login_manager = LoginManager()
login_manager.login_view = 'user.login'
db = SQLAlchemy()
mail = Mail()
migrate = Migrate()

@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))

def create_app(config_name):
    # Create and configure Flask app
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

    # Register blueprints
    from .routes.user import user as user_blueprint
    from admin.routes import admin as admin_blueprint
    app.register_blueprint(user_blueprint)
    app.register_blueprint(admin_blueprint)

    return app
