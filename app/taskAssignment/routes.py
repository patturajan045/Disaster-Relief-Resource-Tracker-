# app/taskAssignment/routes.py
from flask import request, jsonify, session, render_template
from app.models import db, TaskAssignment, User, ReliefRequest, AuditLog
from . import taskAssignmentBp
from datetime import datetime


# -------- Helper: Create Audit Log --------
def log_action(user_id, action, details=None):
    audit = AuditLog(user_id=user_id, action=action, details=details)
    db.session.add(audit)
    db.session.commit()


# -------- Helper: Role Check --------
def get_current_admin():
    """Allow only admin, camp_manager, super_admin"""
    user = session.get("user")
    if not user:
        return None, jsonify({"error": "Not logged in"}), 401
    if user["role"] not in {"admin", "camp_manager", "super_admin"}:
        return None, jsonify({"error": "Unauthorized"}), 403
    return User.query.get(int(user["id"])), None, None


# -------- Render Page --------
@taskAssignmentBp.route("/", methods=["GET"])
def task_page():
    return render_template("taskAssignment.html")


# -------- Create --------
@taskAssignmentBp.route("/", methods=["POST"])
def create_task_assignment():
    admin, err, status = get_current_admin()
    if err:
        return err, status

    data = request.get_json()
    try:
        volunteer_id = data.get("volunteer_id")
        relief_request_id = data.get("relief_request_id")

        volunteer = User.query.get(volunteer_id)
        if not volunteer:
            return jsonify({"error": "Volunteer not found"}), 404

        relief_request = ReliefRequest.query.get(relief_request_id)
        if not relief_request:
            return jsonify({"error": "Relief request not found"}), 404

        new_task = TaskAssignment(
            volunteer_id=volunteer_id,
            relief_request_id=relief_request_id,
            status=data.get("status", "Assigned")
        )
        db.session.add(new_task)
        db.session.commit()

        log_action(admin.id, "CREATE_TASK", f"Task assigned for ReliefRequest {relief_request_id}")
        return jsonify({"message": "✅ Task created", "id": new_task.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# -------- Read All --------
@taskAssignmentBp.route("/api", methods=["GET"])
def get_all_tasks():
    tasks = TaskAssignment.query.all()
    result = [
        {
            "id": t.id,
            "volunteer_id": t.volunteer_id,
            "relief_request_id": t.relief_request_id,
            "status": t.status,
            "assigned_at": t.assigned_at.isoformat()
        }
        for t in tasks
    ]
    return jsonify(result), 200


# -------- Update --------
@taskAssignmentBp.route("/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    admin, err, status = get_current_admin()
    if err:
        return err, status

    data = request.get_json()
    t = TaskAssignment.query.get_or_404(task_id)
    try:
        t.status = data.get("status", t.status)
        db.session.commit()
        log_action(admin.id, "UPDATE_TASK", f"Task {t.id} updated to {t.status}")
        return jsonify({"message": "✅ Task updated"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# -------- Delete --------
@taskAssignmentBp.route("/api/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    admin, err, status = get_current_admin()
    if err:
        return err, status

    t = TaskAssignment.query.get_or_404(task_id)
    try:
        db.session.delete(t)
        db.session.commit()
        log_action(admin.id, "DELETE_TASK", f"Task {t.id} deleted")
        return jsonify({"message": "✅ Task deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
