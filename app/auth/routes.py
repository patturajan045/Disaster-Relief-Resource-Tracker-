from flask import request, jsonify, session, render_template, redirect, url_for
from app.models import db, User, AuditLog
from . import authBp
from datetime import datetime

# -------- Auth Route --------
@authBp.route("/", methods=["POST"])
def auth():
    data = request.json
    action = data.get("action")  # "register" or "login"

    # ------------------ REGISTER ------------------
    if action == "register":
        if User.query.filter_by(email=data["email"].strip().lower()).first():
            return jsonify({"error": "Email already exists"}), 400

        role = data.get("role", "victim").strip().lower()
        new_user = User(
            name=data["name"],
            email=data["email"].strip().lower(),
            phone=data.get("phone"),
            role=role
        )
        new_user.set_password(data["password"])
        db.session.add(new_user)
        db.session.commit()

        # Log registration
        log = AuditLog(
            user_id=new_user.id,
            action="REGISTER",
            details=f"User {new_user.email} registered with role '{new_user.role}'"
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({"message": "✅ User registered successfully", "role": new_user.role})

    # ------------------ LOGIN ------------------
    elif action == "login":
        email = data["email"].strip().lower()
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(data["password"]):
            session["user"] = {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "role": user.role.strip().lower()
            }

            # Log login
            log = AuditLog(
                user_id=user.id,
                action="LOGIN",
                details=f"User {user.email} logged in"
            )
            db.session.add(log)
            db.session.commit()

            return jsonify({
                "message": "✅ Login successful",
                "role": session["user"]["role"],
                "email": user.email
            })

        return jsonify({"error": "Invalid credentials"}), 401

    else:
        return jsonify({"error": "Invalid action. Use 'register' or 'login'"}), 400


# -------- Render Login Page --------
@authBp.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")


# -------- Logout --------
@authBp.route("/logout", methods=["GET", "POST"])
def logout():
    session.pop("user", None)
    return redirect(url_for("authBp.login_page"))  # redirect to login.html


# -------- Get Current User --------
@authBp.route("/current", methods=["GET"])
def get_current_user():
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401
    return jsonify({"user": session["user"]}), 200
