from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models import db
from datetime import timedelta
from extensions import limiter
import logging
import os

# Import Blueprints
from routes.auth import auth_bp
from routes.document import doc_bp
from routes.admin import admin_bp

app = Flask(__name__)
limiter.init_app(app)

# ================= CONFIG =================
import os
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'change-this-in-production')
raw_url = os.getenv('DATABASE_URL', 'sqlite:///database.db')
if raw_url.startswith("postgres://"):
    raw_url = raw_url.replace("postgres://", "postgresql+pg8000://", 1)
elif raw_url.startswith("postgresql://"):
    raw_url = raw_url.replace("postgresql://", "postgresql+pg8000://", 1)
# Remove sslmode from URL — pg8000 handles SSL differently
if "?sslmode=" in raw_url:
    raw_url = raw_url.split("?sslmode=")[0]
app.config['SQLALCHEMY_DATABASE_URI'] = raw_url
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"connect_args": {"ssl_context": True}}
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25MB

# ================= INIT ===================
db.init_app(app)
jwt = JWTManager(app)
CORS(app, resources={r"/*": {"origins": "*"}})

# ============ REGISTER ROUTES ============
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(doc_bp, url_prefix='/document')
app.register_blueprint(admin_bp, url_prefix='/admin')

# ============== HOME ROUTE ===============
@app.route('/')
def home():
    return {"status": "Mahindra DMS Backend Running", "version": "2.0"}, 200

# ============ CREATE DB ==================
with app.app_context():
    db.create_all()
    # Auto create admin if not exists
    from models import User
    from werkzeug.security import generate_password_hash
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password=generate_password_hash('Admin@1234'),
            email='admin@mahindra.com',
            role='admin',
            location='Nashik Plant 1',
            is_admin=True,
            is_approved=True,
            otp_verified=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin created on Railway!")

# ============ LOGGING ====================
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

@app.route('/reset-admin')
def reset_admin():
    from models import User
    from werkzeug.security import generate_password_hash
    admin = User.query.filter_by(username='admin').first()
    if admin:
        admin.password = generate_password_hash('Admin@1234')
        admin.is_approved = True
        admin.is_admin = True
        admin.role = 'admin'
        db.session.commit()
        return {"msg": "Admin password reset to Admin@1234"}
    else:
        admin = User(
            username='admin',
            password=generate_password_hash('Admin@1234'),
            email='admin@mahindra.com',
            role='admin',
            location='Nashik Plant 1',
            is_admin=True,
            is_approved=True,
            otp_verified=True
        )
        db.session.add(admin)
        db.session.commit()
        return {"msg": "Admin created with password Admin@1234"}
        
# ============== RUN ======================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
