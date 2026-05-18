from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')  # admin / subadmin / user
    location = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    otp = db.Column(db.String(10), nullable=True)
    otp_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "location": self.location,
            "is_approved": self.is_approved,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    part_no = db.Column(db.String(100), nullable=False)
    unique_id = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    original_name = db.Column(db.String(200), nullable=True)
    location = db.Column(db.String(100), nullable=False)
    doc_type = db.Column(db.String(100), nullable=False, default='SOP')  # NEW: document type
    uploaded_by = db.Column(db.String(100), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_url = db.Column(db.String(500), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('part_no', 'unique_id', 'location', 'doc_type', name='unique_doc_per_location_type'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "part_no": self.part_no,
            "unique_id": self.unique_id,
            "filename": self.filename,
            "original_name": self.original_name,
            "location": self.location,
            "doc_type": self.doc_type,
            "uploaded_by": self.uploaded_by,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None
        }
