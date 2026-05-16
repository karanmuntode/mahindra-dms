# Mahindra DMS v2.0 — Document Management System

## What's New / Fixed

### Bug Fixes
- Fixed deprecated `User.query.get(id)` → `db.session.get(User, id)` (SQLAlchemy 2.0 compat)
- Fixed search returning `.length === 0` check on response object (was checking wrong field)
- Fixed duplicate constraint now includes `doc_type` field
- Fixed JWT secret key being overwritten in app.py (was set twice, second one was weaker)
- Fixed `send_otp` function name mismatch (was `send_otp_email` in service but called wrong name)
- Fixed missing email field in signup form (was in backend but not in HTML)
- Fixed admin `count-users` endpoint not used properly (now stats endpoint returns all data)
- Fixed `per_page` pagination for all admin endpoints

### New Features
- **Document Types** — Upload and search require selecting type first:
  Packaging Signoff, SOP, L0, L1, L2, L3, Control Plan, PFMEA, Drawing,
  Inspection Report, Work Instruction, Quality Plan, ECN, BOM, Test Report
- **Autocomplete Search** — Real-time suggestions as you type (after selecting doc type)
- **Proper Pagination** — All tables/search results paginated (10 per page, smart page controls)
- **Admin Dashboard** — 4 stat cards + 4 charts (user status, docs by type, docs by location, users by location)
- **Admin Document Management** — View/filter/delete all documents with pagination
- **Toggle Approval** — Suspend/reactivate users without deleting
- **Revoke Subadmin** — Revert subadmin back to user role
- **Light Blue & White Theme** — Complete redesign with professional SaaS look
- **Toast Notifications** — Non-blocking feedback in admin panel
- **Drag & Drop Upload** — With file preview and clear button
- **OTP Modal** — Inline 6-digit OTP entry with auto-focus
- **Document original filename** — Preserved for downloads

---

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
python create_admin.py      # creates default admin user
python app.py               # starts on port 5000
```

**Default Admin Credentials:**
- Username: `admin`
- Password: `Admin@1234`
- Email: `admin@mahindra.com`

### Frontend
Serve the `frontend/` folder via any static server or open HTML files directly.

**Important:** Update `BASE_URL` in all HTML files to your server IP:
```javascript
const BASE_URL = "http://YOUR_SERVER_IP:5000";
```

---

## Architecture

```
backend/
├── app.py              # Flask app, CORS, JWT, blueprints
├── models.py           # User, Document (with doc_type field)
├── extensions.py       # Flask-Limiter
├── create_admin.py     # One-time admin creation script
├── requirements.txt
├── routes/
│   ├── auth.py         # Signup, login, OTP, reset password
│   ├── admin.py        # User management, stats, approval
│   └── document.py     # Upload, search, autocomplete, download, delete
├── ml/
│   └── recommend.py    # TF-IDF similarity recommendations
├── utils/
│   └── email_service.py # SMTP OTP emails
└── uploads/            # Stored files

frontend/
├── index.html          # Landing page + Login + Signup (light blue theme)
├── dashboard.html      # User panel (upload, search with autocomplete + pagination)
└── admin.html          # Admin panel (dashboard, users, documents, charts)
```

---

## Document Types

| Type | Description |
|------|-------------|
| Packaging Signoff | Sign-off documents for packaging |
| SOP | Standard Operating Procedures |
| L0 – L3 | Level-based documents |
| Control Plan | Manufacturing control plans |
| PFMEA | Process Failure Mode & Effects Analysis |
| Drawing | Engineering drawings |
| Inspection Report | Quality inspection reports |
| Work Instruction | Step-by-step work instructions |
| Quality Plan | Quality assurance plans |
| ECN | Engineering Change Notices |
| BOM | Bill of Materials |
| Test Report | Test and validation reports |

---

## Roles & Permissions

| Feature | User | Subadmin | Admin |
|---------|------|----------|-------|
| Upload (own location) | ✅ | ✅ | ✅ |
| Search (own location) | ✅ | ✅ | ✅ |
| Download | ✅ | ✅ | ✅ |
| Delete (own location) | ✅ | ✅ | ✅ (all) |
| Approve users | ❌ | ✅ | ✅ |
| View all users | ❌ | ✅ | ✅ |
| Delete users | ❌ | ✅ | ✅ |
| Promote to subadmin | ❌ | ❌ | ✅ |
| View all docs | ❌ | ❌ | ✅ |
| Dashboard stats | ❌ | ❌ | ✅ |

---

## Email Configuration (Optional)
Set environment variables for OTP emails:
```bash
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=your-email@gmail.com
export SMTP_PASS=your-app-password
```
If not configured, OTP is printed to console — signup still works.
