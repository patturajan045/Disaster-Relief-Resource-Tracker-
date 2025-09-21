from flask import Blueprint, render_template
from datetime import datetime
from sqlalchemy import func
from app.models import db, User, Disaster, ReliefRequest, Resource, TaskAssignment

from . import dashboard_bp


@dashboard_bp.route("/", methods=["GET"])
def dashboard_home():
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Stats
    total_users = User.query.count()
    new_users_today = User.query.filter(User.created_at >= today_start).count()

    total_disasters = Disaster.query.count()
    active_disasters = Disaster.query.filter(Disaster.reported_on >= today_start).count()

    total_relief_requests = ReliefRequest.query.count()
    pending_relief_requests = ReliefRequest.query.filter_by(status="Pending").count()

    total_resources = Resource.query.count()
    total_tasks = TaskAssignment.query.count()

    # Recent disasters
    recent_disasters = Disaster.query.order_by(Disaster.reported_on.desc()).limit(5).all()

    # Package everything into a dict
    data = {
        "total_users": total_users,
        "new_users_today": new_users_today,
        "total_disasters": total_disasters,
        "active_disasters": active_disasters,
        "total_relief_requests": total_relief_requests,
        "pending_relief_requests": pending_relief_requests,
        "total_resources": total_resources,
        "total_tasks": total_tasks,
        "recent_disasters": recent_disasters,
    }

    return render_template("dashboard.html", data=data)
