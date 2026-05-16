"""
Run this script once to create the default admin user.
Usage: python create_admin.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db, User
from werkzeug.security import generate_password_hash

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin@1234"
ADMIN_EMAIL = "admin@mahindra.com"
ADMIN_LOCATION = "Igatpuri"

with app.app_context():
    if User.query.filter_by(username=ADMIN_USERNAME).first():
        print(f"Admin '{ADMIN_USERNAME}' already exists.")
    else:
        admin = User(
            username=ADMIN_USERNAME,
            password=generate_password_hash(ADMIN_PASSWORD),
            email=ADMIN_EMAIL,
            role="admin",
            location=ADMIN_LOCATION,
            is_admin=True,
            is_approved=True,
            otp_verified=True
        )
        db.session.add(admin)
        db.session.commit()
        print(f"✅ Admin created!")
        print(f"   Username : {ADMIN_USERNAME}")
        print(f"   Password : {ADMIN_PASSWORD}")
        print(f"   Email    : {ADMIN_EMAIL}")
