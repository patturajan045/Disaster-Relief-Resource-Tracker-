from flask import request, jsonify, session
from app.models import db, UserLocation, AuditLog
from . import userLocationBp

# ----------------------------
# Audit Log Helper
# ----------------------------
def log_action(user_id, action, details=""):
    audit = AuditLog(user_id=user_id, action=action, details=details)
    db.session.add(audit)
    db.session.commit()


# ----------------------------
# Create or Update User Location
# ----------------------------
@userLocationBp.route('/', methods=['POST'])
def update_or_create_location():
    # Get logged-in user from session
    user_session = session.get("user")
    if not user_session:
        return jsonify({"message": "Unauthorized"}), 401

    user_id = int(user_session["id"])  # stored as string in session
    data = request.get_json()

    if not data or "latitude" not in data or "longitude" not in data:
        return jsonify({"message": "Invalid request"}), 400

    # Check if location exists
    location = UserLocation.query.filter_by(user_id=user_id).first()

    if location:
        # Update existing location
        old_lat, old_lng = location.latitude, location.longitude
        location.latitude = data["latitude"]
        location.longitude = data["longitude"]
        action_type = "UPDATE_LOCATION"
        details = f"Updated location from ({old_lat}, {old_lng}) → ({data['latitude']}, {data['longitude']})"
    else:
        # Create new location
        location = UserLocation(
            user_id=user_id,
            latitude=data["latitude"],
            longitude=data["longitude"]
        )
        action_type = "CREATE_LOCATION"
        details = f"Created location: ({data['latitude']}, {data['longitude']})"

    db.session.add(location)
    db.session.commit()

    # Log action
    log_action(user_id, action_type, details)

    return jsonify({
        "message": "📍 Location saved successfully",
        "latitude": location.latitude,
        "longitude": location.longitude
    })


# ----------------------------
# Get User Location
# ----------------------------
@userLocationBp.route('/', methods=['GET'])
def get_location():
    user_session = session.get("user")
    if not user_session:
        return jsonify({"message": "Unauthorized"}), 401

    user_id = int(user_session["id"])
    location = UserLocation.query.filter_by(user_id=user_id).first()

    if not location:
        return jsonify({"message": "No location found"}), 404

    return jsonify({
        "latitude": location.latitude,
        "longitude": location.longitude,
        "last_updated": location.updated_at
    })
