from flask import Blueprint, request, jsonify, session, render_template
from datetime import datetime
from app.models import db, VolunteerProfile, AuditLog

from .import volunteerProfileBp

# ---------------- Helpers ----------------
def get_current_user():
    return session.get("user")

def is_volunteer_user(user):
    """Allow volunteer, admin, or super_admin"""
    if not user:
        return False
    role = user.get("role", "").strip().lower()
    return role in ["volunteer", "admin", "super_admin"]

def log_action(user_id, action, details):
    db.session.add(
        AuditLog(
            user_id=int(user_id) if user_id else None,
            action=action,
            details=details,
            created_at=datetime.utcnow()
        )
    )
    db.session.commit()

# ---------------- Routes ----------------

# Render Volunteer Page
@volunteerProfileBp.route("/", methods=["GET"])
def volunteer_page():
    user = get_current_user()
    if not is_volunteer_user(user):
        return "Unauthorized", 401
    return render_template("volunteer.html", user=user)

# API: Get my volunteer profile
@volunteerProfileBp.route("/me", methods=["GET"])
def get_profile():
    user = get_current_user()
    if not is_volunteer_user(user):
        return jsonify({"error": "Unauthorized"}), 401

    volunteer = VolunteerProfile.query.filter_by(user_id=int(user["id"])).first()
    if not volunteer:
        return jsonify({"error": "Profile not found"}), 404

    return jsonify({
        "id": volunteer.id,
        "skills": volunteer.skills,
        "experience_years": volunteer.experience_years,
        "availability": volunteer.availability,
        "location": volunteer.location,
        "preferred_role": volunteer.preferred_role,
        "languages": volunteer.languages,
        "phone_number": volunteer.phone_number
    }), 200

# API: Update volunteer profile
@volunteerProfileBp.route("/update", methods=["PUT", "POST"])
def update_profile():
    user = get_current_user()
    if not is_volunteer_user(user):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    volunteer = VolunteerProfile.query.filter_by(user_id=int(user["id"])).first()

    if not volunteer:
        volunteer = VolunteerProfile(user_id=int(user["id"]))

    volunteer.skills = data.get("skills")
    volunteer.experience_years = data.get("experience_years")
    volunteer.availability = data.get("availability", False)
    volunteer.location = data.get("location")
    volunteer.preferred_role = data.get("preferred_role")
    volunteer.languages = data.get("languages")
    volunteer.phone_number = data.get("phone_number")

    db.session.add(volunteer)
    db.session.commit()
    log_action(user["id"], "UPDATE_VOLUNTEER", "Volunteer profile updated")

    return jsonify({"message": "Profile saved"}), 200

# API: Delete volunteer profile
@volunteerProfileBp.route("/delete", methods=["DELETE"])
def delete_profile():
    user = get_current_user()
    if not is_volunteer_user(user):
        return jsonify({"error": "Unauthorized"}), 401

    volunteer = VolunteerProfile.query.filter_by(user_id=int(user["id"])).first()
    if not volunteer:
        return jsonify({"error": "Volunteer profile not found"}), 404

    profile_info = {
        "skills": volunteer.skills,
        "experience_years": volunteer.experience_years,
        "availability": volunteer.availability,
        "location": volunteer.location,
        "preferred_role": volunteer.preferred_role,
        "languages": volunteer.languages,
        "phone_number": volunteer.phone_number
    }

    db.session.delete(volunteer)
    db.session.commit()

    log_action(user["id"], "DELETE_VOLUNTEER_PROFILE", f"Deleted volunteer profile {profile_info}")

    return jsonify({"message": "Volunteer profile deleted successfully"}), 200
