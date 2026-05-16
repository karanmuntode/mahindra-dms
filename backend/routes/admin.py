from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Document
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)

def get_current_user():
    username = get_jwt_identity()
    return User.query.filter_by(username=username).first() if username else None

def require_admin(user):
    if not user:
        return jsonify({"msg": "Not authenticated"}), 401
    if not user.is_admin:
        return jsonify({"msg": "Admin access required"}), 403
    return None

def require_admin_or_subadmin(user):
    if not user:
        return jsonify({"msg": "Not authenticated"}), 401
    if user.role not in ["admin", "subadmin"]:
        return jsonify({"msg": "Admin access required"}), 403
    return None


# ================= DASHBOARD STATS =================
@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    try:
        user = get_current_user()
        err = require_admin(user)
        if err: return err

        total_users = User.query.count()
        approved_users = User.query.filter_by(is_approved=True).count()
        pending_users = User.query.filter_by(is_approved=False).count()
        total_docs = Document.query.count()

        # Docs by type
        docs_by_type = db.session.query(
            Document.doc_type, func.count(Document.id)
        ).group_by(Document.doc_type).all()

        # Docs by location
        docs_by_location = db.session.query(
            Document.location, func.count(Document.id)
        ).group_by(Document.location).all()

        # Users by location
        users_by_location = db.session.query(
            User.location, func.count(User.id)
        ).group_by(User.location).all()

        return jsonify({
            "total_users": total_users,
            "approved_users": approved_users,
            "pending_users": pending_users,
            "total_docs": total_docs,
            "docs_by_type": [{"type": t, "count": c} for t, c in docs_by_type],
            "docs_by_location": [{"location": l, "count": c} for l, c in docs_by_location],
            "users_by_location": [{"location": l, "count": c} for l, c in users_by_location]
        }), 200

    except Exception as e:
        return jsonify({"msg": "Error fetching stats", "error": str(e)}), 500


# ================= PENDING USERS =================
@admin_bp.route('/pending-users', methods=['GET'])
@jwt_required()
def pending_users():
    try:
        user = get_current_user()
        err = require_admin_or_subadmin(user)
        if err: return err

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        query = User.query.filter_by(is_approved=False)
        total = query.count()
        users = query.order_by(User.created_at.desc()).offset((page-1)*per_page).limit(per_page).all()

        return jsonify({
            "users": [u.to_dict() for u in users],
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        }), 200

    except Exception as e:
        return jsonify({"msg": "Error fetching users", "error": str(e)}), 500


# ================= ALL USERS =================
@admin_bp.route('/all-users', methods=['GET'])
@jwt_required()
def all_users():
    try:
        user = get_current_user()
        err = require_admin(user)
        if err: return err

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        search = request.args.get('search', '').strip()
        location_filter = request.args.get('location', '').strip()
        role_filter = request.args.get('role', '').strip()

        query = User.query
        if search:
            query = query.filter(User.username.ilike(f"%{search}%"))
        if location_filter:
            query = query.filter_by(location=location_filter)
        if role_filter:
            query = query.filter_by(role=role_filter)

        total = query.count()
        users = query.order_by(User.created_at.desc()).offset((page-1)*per_page).limit(per_page).all()

        return jsonify({
            "users": [u.to_dict() for u in users],
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        }), 200

    except Exception as e:
        return jsonify({"msg": "Error fetching users", "error": str(e)}), 500


# ================= APPROVE USER =================
@admin_bp.route('/approve/<int:user_id>', methods=['PUT'])
@jwt_required()
def approve_user(user_id):
    try:
        current_user = get_current_user()
        err = require_admin_or_subadmin(current_user)
        if err: return err

        user = db.session.get(User, user_id)  # Fixed: use db.session.get instead of deprecated .get()

        if not user:
            return jsonify({"msg": "User not found"}), 404

        if user.is_approved:
            return jsonify({"msg": "User already approved"}), 400

        user.is_approved = True
        db.session.commit()

        return jsonify({"msg": f"User '{user.username}' approved successfully"}), 200

    except Exception as e:
        return jsonify({"msg": "Approval failed", "error": str(e)}), 500


# ================= REJECT/DELETE USER =================
@admin_bp.route('/delete-user/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    try:
        current_user = get_current_user()
        err = require_admin_or_subadmin(current_user)
        if err: return err

        user = db.session.get(User, user_id)  # Fixed

        if not user:
            return jsonify({"msg": "User not found"}), 404

        if user.id == current_user.id:
            return jsonify({"msg": "Cannot delete your own account"}), 403

        if user.role == "admin":
            return jsonify({"msg": "Cannot delete main admin"}), 403

        db.session.delete(user)
        db.session.commit()

        return jsonify({"msg": "User deleted successfully"}), 200

    except Exception as e:
        return jsonify({"msg": "Error deleting user", "error": str(e)}), 500


# ================= MAKE SUBADMIN =================
@admin_bp.route('/make-subadmin/<int:user_id>', methods=['PUT'])
@jwt_required()
def make_subadmin(user_id):
    try:
        current_user = get_current_user()

        if current_user.role != "admin":
            return jsonify({"msg": "Only main admin can promote users"}), 403

        user = db.session.get(User, user_id)  # Fixed

        if not user:
            return jsonify({"msg": "User not found"}), 404

        if user.id == current_user.id:
            return jsonify({"msg": "Cannot change your own role"}), 400

        user.role = "subadmin"
        user.is_admin = True
        db.session.commit()

        return jsonify({"msg": f"'{user.username}' promoted to Subadmin"}), 200

    except Exception as e:
        return jsonify({"msg": "Promotion failed", "error": str(e)}), 500


# ================= REVOKE SUBADMIN =================
@admin_bp.route('/revoke-subadmin/<int:user_id>', methods=['PUT'])
@jwt_required()
def revoke_subadmin(user_id):
    try:
        current_user = get_current_user()

        if current_user.role != "admin":
            return jsonify({"msg": "Only main admin can change roles"}), 403

        user = db.session.get(User, user_id)  # Fixed

        if not user:
            return jsonify({"msg": "User not found"}), 404

        user.role = "user"
        user.is_admin = False
        db.session.commit()

        return jsonify({"msg": f"'{user.username}' reverted to User"}), 200

    except Exception as e:
        return jsonify({"msg": "Role change failed", "error": str(e)}), 500


# ================= TOGGLE APPROVAL =================
@admin_bp.route('/toggle-approval/<int:user_id>', methods=['PUT'])
@jwt_required()
def toggle_approval(user_id):
    try:
        current_user = get_current_user()
        err = require_admin_or_subadmin(current_user)
        if err: return err

        user = db.session.get(User, user_id)  # Fixed

        if not user:
            return jsonify({"msg": "User not found"}), 404

        user.is_approved = not user.is_approved
        db.session.commit()

        status = "approved" if user.is_approved else "suspended"
        return jsonify({"msg": f"User '{user.username}' {status}"}), 200

    except Exception as e:
        return jsonify({"msg": "Toggle failed", "error": str(e)}), 500


# ================= COUNT USERS (legacy compat) =================
@admin_bp.route('/count-users', methods=['GET'])
@jwt_required()
def count_users():
    try:
        user = get_current_user()
        err = require_admin(user)
        if err: return err

        return jsonify({
            "total_users": User.query.count(),
            "approved_users": User.query.filter_by(is_approved=True).count(),
            "pending_users": User.query.filter_by(is_approved=False).count()
        }), 200

    except Exception as e:
        return jsonify({"msg": "Error", "error": str(e)}), 500
