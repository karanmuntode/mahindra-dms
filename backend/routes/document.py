from flask import Blueprint, request, jsonify
from models import db, Document, User
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from sqlalchemy import or_

import os
import uuid
import logging

import cloudinary
import cloudinary.uploader

doc_bp = Blueprint('document', __name__)

# ================= CLOUDINARY CONFIG =================
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'docx', 'xlsx'}

DOCUMENT_TYPES = [
    "Packaging Signoff",
    "SOP",
    "L0",
    "L1",
    "L2",
    "L3",
    "Control Plan",
    "PFMEA",
    "Drawing",
    "Inspection Report",
    "Work Instruction",
    "Quality Plan",
    "ECN",
    "BOM",
    "Test Report"
]


# ================= HELPERS =================
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_current_user():
    try:
        username = get_jwt_identity()
        return User.query.filter_by(username=username).first() if username else None
    except Exception:
        return None


# ================= DOCUMENT TYPES =================
@doc_bp.route('/types', methods=['GET'])
def get_doc_types():
    return jsonify({"types": DOCUMENT_TYPES}), 200


# ================= UPLOAD =================
@doc_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload():
    try:
        user = get_current_user()

        if not user:
            return jsonify({"msg": "Invalid user / token"}), 401

        if not user.is_approved:
            return jsonify({"msg": "Access denied — account not approved"}), 403

        if 'file' not in request.files:
            return jsonify({"msg": "No file provided"}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"msg": "No file selected"}), 400

        if not allowed_file(file.filename):
            return jsonify({
                "msg": f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            }), 400

        part_no = request.form.get('part_no', '').strip()
        unique_id = request.form.get('unique_id', '').strip()
        doc_type = request.form.get('doc_type', '').strip()

        if not part_no or not unique_id:
            return jsonify({
                "msg": "Part No and Unique ID are required"
            }), 400

        if not doc_type or doc_type not in DOCUMENT_TYPES:
            return jsonify({
                "msg": f"Invalid document type. Choose from: {', '.join(DOCUMENT_TYPES)}"
            }), 400

        # Duplicate check
        existing = Document.query.filter_by(
            part_no=part_no,
            unique_id=unique_id,
            location=user.location,
            doc_type=doc_type
        ).first()

        if existing:
            return jsonify({
                "msg": "Document already exists for this Part No, Unique ID, Type and Location"
            }), 409

        # ================= CLOUDINARY UPLOAD =================
        original_name = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4()}_{original_name}"

        upload_result = cloudinary.uploader.upload(
            file,
            public_id=unique_name,
            resource_type="raw"
        )

        file_url = upload_result.get("secure_url")

        # ================= SAVE TO DB =================
        doc = Document(
            part_no=part_no,
            unique_id=unique_id,

            # store public_id here
            filename=unique_name,

            original_name=original_name,

            # IMPORTANT:
            # your models.py must contain:
            # file_url = db.Column(db.String(500))
            file_url=file_url,

            location=user.location,
            doc_type=doc_type,
            uploaded_by=user.username
        )

        db.session.add(doc)
        db.session.commit()

        logging.info(f"{user.username} uploaded {unique_name}")

        return jsonify({
            "msg": "Document uploaded successfully",
            "doc": doc.to_dict()
        }), 201

    except Exception as e:
        print("UPLOAD ERROR:", str(e))
        logging.error(f"Upload error: {e}")

        return jsonify({
            "msg": "Upload failed",
            "error": str(e)
        }), 500


# ================= AUTOCOMPLETE =================
@doc_bp.route('/autocomplete', methods=['GET'])
@jwt_required()
def autocomplete():
    try:
        user = get_current_user()

        if not user:
            return jsonify({"msg": "Unauthorized"}), 401

        doc_type = request.args.get('doc_type', '').strip()
        query = request.args.get('q', '').strip()

        if not doc_type or not query:
            return jsonify({"suggestions": []}), 200

        q = Document.query.filter_by(
            location=user.location,
            doc_type=doc_type
        )

        q = q.filter(
            or_(
                Document.part_no.ilike(f"%{query}%"),
                Document.unique_id.ilike(f"%{query}%"),
                Document.original_name.ilike(f"%{query}%")
            )
        ).limit(8)

        docs = q.all()

        suggestions = []
        seen = set()

        for d in docs:
            key = f"{d.part_no}-{d.unique_id}"

            if key not in seen:
                suggestions.append({
                    "label": f"{d.part_no} — {d.unique_id}",
                    "part_no": d.part_no,
                    "unique_id": d.unique_id
                })

                seen.add(key)

        return jsonify({"suggestions": suggestions}), 200

    except Exception as e:
        return jsonify({
            "suggestions": [],
            "error": str(e)
        }), 500


# ================= SEARCH =================
@doc_bp.route('/search', methods=['POST'])
@jwt_required()
def search():
    try:
        user = get_current_user()

        if not user:
            return jsonify({"msg": "Unauthorized"}), 401

        data = request.json or {}

        doc_type = data.get('doc_type', '').strip()
        part_no = data.get('part_no', '').strip()
        unique_id = data.get('unique_id', '').strip()

        page = int(data.get('page', 1))
        per_page = int(data.get('per_page', 10))

        if not doc_type:
            return jsonify({
                "msg": "Please select a document type first"
            }), 400

        query = Document.query.filter_by(
            location=user.location,
            doc_type=doc_type
        )

        if part_no:
            query = query.filter(
                Document.part_no.ilike(f"%{part_no}%")
            )

        if unique_id:
            query = query.filter(
                Document.unique_id.ilike(f"%{unique_id}%")
            )

        total = query.count()

        docs = query.order_by(
            Document.uploaded_at.desc()
        ).offset(
            (page - 1) * per_page
        ).limit(
            per_page
        ).all()

        return jsonify({
            "results": [d.to_dict() for d in docs],
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        }), 200

    except Exception as e:
        return jsonify({
            "msg": "Search failed",
            "error": str(e)
        }), 500


# ================= ADMIN LIST =================
@doc_bp.route('/all', methods=['GET'])
@jwt_required()
def list_all():
    try:
        user = get_current_user()

        if not user or not user.is_admin:
            return jsonify({"msg": "Admin only"}), 403

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        doc_type = request.args.get('doc_type', '').strip()
        location = request.args.get('location', '').strip()

        query = Document.query

        if doc_type:
            query = query.filter_by(doc_type=doc_type)

        if location:
            query = query.filter_by(location=location)

        total = query.count()

        docs = query.order_by(
            Document.uploaded_at.desc()
        ).offset(
            (page - 1) * per_page
        ).limit(
            per_page
        ).all()

        return jsonify({
            "results": [d.to_dict() for d in docs],
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        }), 200

    except Exception as e:
        return jsonify({
            "msg": "Error fetching documents",
            "error": str(e)
        }), 500


# ================= DELETE =================
@doc_bp.route('/delete/<int:id>', methods=['DELETE'])
@jwt_required()
def delete(id):
    try:
        user = get_current_user()

        doc = db.session.get(Document, id)

        if not doc:
            return jsonify({"msg": "Document not found"}), 404

        if not user.is_admin and doc.location != user.location:
            return jsonify({"msg": "Unauthorized"}), 403

        # Delete from Cloudinary
        try:
            cloudinary.uploader.destroy(
                doc.filename,
                resource_type="raw"
            )
        except Exception as cloud_err:
            print("Cloudinary delete error:", str(cloud_err))

        db.session.delete(doc)
        db.session.commit()

        return jsonify({
            "msg": "Document deleted successfully"
        }), 200

    except Exception as e:
        return jsonify({
            "msg": "Delete failed",
            "error": str(e)
        }), 500


# ================= DOWNLOAD =================
@doc_bp.route('/download/<int:id>', methods=['GET'])
@jwt_required()
def download(id):
    try:
        user = get_current_user()
        doc = db.session.get(Document, id)

        if not doc:
            return jsonify({"msg": "Document not found"}), 404

        if not user.is_admin and doc.location != user.location:
            return jsonify({"msg": "Unauthorized"}), 403

        return jsonify({
            "download_url": doc.file_url
        }), 200

    except Exception as e:
        return jsonify({"msg": "Download failed", "error": str(e)}), 500