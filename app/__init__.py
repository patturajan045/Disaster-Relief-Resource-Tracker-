from flask import Flask, session
from flask_migrate import Migrate
from app.models import db
import os
import secrets

def create_app():
    app = Flask(__name__)

    # 🔹 Secret key required for sessions & flash
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", secrets.token_hex(16))

    # Database setup
    app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:hp1234@localhost/flask_disaster_db"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    Migrate(app, db)

    
    # -------- Register blueprints --------
    from app.users import user_bp
    app.register_blueprint(user_bp)

    from app.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

    from app.auth import authBp
    app.register_blueprint(authBp, url_prefix='/auth')

    from app.main import mainBp
    app.register_blueprint(mainBp)

    from app.UserLocation import userLocationBp
    app.register_blueprint(userLocationBp, url_prefix='/userLocation')

    from app.Disaster import disasterBp
    app.register_blueprint(disasterBp, url_prefix='/disaster')

    from app.ReliefRequest import reliefRequestBp
    app.register_blueprint(reliefRequestBp, url_prefix="/reliefRequest")

    from app.Resource import resourceBp
    app.register_blueprint(resourceBp, url_prefix='/resources')

    from app.Donation import donationBp
    app.register_blueprint(donationBp, url_prefix='/donation')
    
    from app.volunteerProfile import volunteerProfileBp
    app.register_blueprint(volunteerProfileBp, url_prefix='/volunteer')

    from app.organization import organizationBp
    app.register_blueprint(organizationBp, url_prefix='/organization')

    from app.ReliefCamp import reliefCampBp
    app.register_blueprint(reliefCampBp, url_prefix='/reliefCamp')

    from app.notification import notificationBp
    app.register_blueprint(notificationBp, url_prefix='/notification')

    from app.auditLog import auditLog
    app.register_blueprint(auditLog, url_prefix='/auditLog')

    from app.taskAssignment import taskAssignmentBp
    app.register_blueprint(taskAssignmentBp, url_prefix='/taskAssignment')

    from app.message import messageBp
    app.register_blueprint(messageBp, url_prefix='/message')

    from app.promoteLog import promoteLogBp
    app.register_blueprint(promoteLogBp,url_prefix='/promoteLog')

    from app.roleRequest import roleRequestBp
    app.register_blueprint(roleRequestBp,url_prefix='/roleRequest')


    @app.context_processor
    def inject_user():
        """Injects user session info into all templates"""
        user = session.get("user")
        return {
            "is_login": bool(user),
            "name": user.get("name") if user else None,
            "email": user.get("email") if user else None,
            "role": user.get("role", "victim") if user else None,
        }


    @app.route('/')
    def home():
        return "FLASK MySQL App Connected!"

    return app
