from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="victim", nullable=False)  # admin | volunteer | donor | victim
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    location = db.relationship("UserLocation", back_populates="user", uselist=False, cascade="all, delete")
    relief_requests = db.relationship("ReliefRequest", back_populates="requester", cascade="all, delete")
    volunteer_profile = db.relationship("VolunteerProfile", back_populates="user", uselist=False, cascade="all, delete")
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.org_id"), nullable=True)
    organization = db.relationship("Organization", back_populates="members")
    resources_added = db.relationship("Resource", back_populates="user", cascade="all, delete")
    disasters_reported = db.relationship("Disaster", back_populates="reporter", cascade="all, delete")
    donations = db.relationship("Donation", back_populates="user", cascade="all, delete")
    notifications = db.relationship("Notification", back_populates="user", cascade="all, delete")
    audit_logs = db.relationship("AuditLog", back_populates="user", cascade="all, delete")
    tasks = db.relationship("TaskAssignment", back_populates="volunteer", cascade="all, delete")
    sent_messages = db.relationship("Message", foreign_keys="Message.sender_id", back_populates="sender", cascade="all, delete")
    received_messages = db.relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver", cascade="all, delete")

    # Password helpers
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.name}, Role: {self.role}>"


class UserLocation(db.Model):
    __tablename__ = "user_locations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="location")

    def __repr__(self):
        return f"<UserLocation user_id={self.user_id} | ({self.latitude}, {self.longitude})>"



class Disaster(db.Model):
    __tablename__ = "disasters"

    # --- Columns ---
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False, index=True)
    location = db.Column(db.String(200), nullable=False, index=True)
    severity = db.Column(db.String(20), nullable=False, default="Low", index=True)
    affected_population = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)

    reported_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    reported_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # --- Relationships ---
    reporter = db.relationship(
        "User",
        back_populates="disasters_reported",
        lazy="joined"  # eager load reporter for performance in serialization
    )

    relief_requests = db.relationship(
        "ReliefRequest",
        back_populates="disaster",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    resources = db.relationship(
        "Resource",
        back_populates="disaster",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    donations = db.relationship(
        "Donation",
        back_populates="disaster",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    relief_camps = db.relationship(
        "ReliefCamp",
        back_populates="disaster",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # --- Utility Methods ---
    def __repr__(self):
        return f"<Disaster {self.name} (Severity: {self.severity})>"

    def serialize(self):
        """Serialize for JSON response."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "location": self.location,
            "severity": self.severity,
            "affected_population": self.affected_population,
            "description": self.description,
            "reported_on": self.reported_on.isoformat() if self.reported_on else None,
            "updated_on": self.updated_on.isoformat() if self.updated_on else None,
            "reported_by": self.reported_by,
            "reported_by_name": self.reporter.name if self.reporter else "Unknown"
        }



class ReliefRequest(db.Model):
    __tablename__ = "relief_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    disaster_id = db.Column(db.Integer, db.ForeignKey("disasters.id"), nullable=False)
    resource_needed = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(
        db.Enum("Pending", "Approved", "Fulfilled", name="request_status"),
        default="Pending",
        nullable=False,
        index=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    requester = db.relationship("User", back_populates="relief_requests")
    disaster = db.relationship("Disaster", back_populates="relief_requests")
    tasks = db.relationship("TaskAssignment", back_populates="relief_request", cascade="all, delete")

    def __repr__(self):
        return f"<ReliefRequest {self.resource_needed} x {self.quantity} for Disaster {self.disaster_id}>"


class Resource(db.Model):
    __tablename__ = "resources"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)
    unit = db.Column(db.String(50), nullable=True)

    disaster_id = db.Column(db.Integer, db.ForeignKey("disasters.id"), nullable=True)
    added_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    disaster = db.relationship("Disaster", back_populates="resources")
    user = db.relationship("User", back_populates="resources_added")

    def __repr__(self):
        return f"<Resource {self.name} ({self.quantity} {self.unit or ''})>"


class Donation(db.Model):
    __tablename__ = "donations"

    id = db.Column(db.Integer, primary_key=True)
    donor_name = db.Column(db.String(120), nullable=False)
    resource_type = db.Column(db.String(120), nullable=True)
    quantity = db.Column(db.Integer, nullable=True)
    unit = db.Column(db.String(50), nullable=True)
    amount = db.Column(db.Float, nullable=True)
    disaster_id = db.Column(db.Integer, db.ForeignKey("disasters.id"), nullable=True)
    donated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    donated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    disaster = db.relationship("Disaster", back_populates="donations")
    user = db.relationship("User", back_populates="donations")

    def __repr__(self):
        return f"<Donation {self.donor_name} - {self.resource_type or 'Money'}>"



# The rest of the models (VolunteerProfile, Organization, ReliefCamp, Notification, AuditLog, TaskAssignment, Message)
# remain the same as your previous file and do not need changes

class VolunteerProfile(db.Model):
    __tablename__ = "volunteer_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    skills = db.Column(db.String(255), nullable=True)
    experience_years = db.Column(db.Integer, default=0)
    availability = db.Column(db.Boolean, default=True)
    location = db.Column(db.String(100), nullable=True)
    preferred_role = db.Column(db.String(50), nullable=True)
    languages = db.Column(db.String(255), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)

    user = db.relationship("User", back_populates="volunteer_profile")

    def __repr__(self):
        return f"<VolunteerProfile user_id={self.user_id}, skills={self.skills}>"



class Organization(db.Model):
    __tablename__ = "organizations"

    org_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False, unique=True, index=True)
    type = db.Column(db.String(50), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    members = db.relationship("User", back_populates="organization", cascade="all, delete")
    relief_camps = db.relationship("ReliefCamp", back_populates="organization", cascade="all, delete")

    def __repr__(self):
        return f"<Organization {self.name} ({self.type})>"



class ReliefCamp(db.Model):
    __tablename__ = "relief_camps"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    current_occupancy = db.Column(db.Integer, default=0)

    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.org_id"), nullable=False)
    disaster_id = db.Column(db.Integer, db.ForeignKey("disasters.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship("Organization", back_populates="relief_camps")
    disaster = db.relationship("Disaster", back_populates="relief_camps")

    def __repr__(self):
        return f"<ReliefCamp {self.name} ({self.current_occupancy}/{self.capacity})>"



class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False)
    related_id = db.Column(db.Integer, nullable=True)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification to User {self.user_id}: {self.message}>"



class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog User={self.user_id}, Action={self.action}>"



class TaskAssignment(db.Model):
    __tablename__ = "task_assignments"

    id = db.Column(db.Integer, primary_key=True)
    volunteer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    relief_request_id = db.Column(db.Integer, db.ForeignKey("relief_requests.id", ondelete="CASCADE"), nullable=False)
    status = db.Column(
        db.Enum("Assigned", "In Progress", "Completed", "Failed", name="task_status"),
        default="Assigned",
        nullable=False
    )
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    volunteer = db.relationship("User", back_populates="tasks")
    relief_request = db.relationship("ReliefRequest", back_populates="tasks")

    def __repr__(self):
        return f"<TaskAssignment Volunteer={self.volunteer_id} Request={self.relief_request_id}>"



class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_read = db.Column(db.Boolean, default=False)

    sender = db.relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = db.relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")

    def __repr__(self):
        return f"<Message from {self.sender_id} to {self.receiver_id}>"
    
class PromotionLog(db.Model):
    __tablename__ = "promotion_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    promoted_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    old_role = db.Column(db.String(50), nullable=False)
    new_role = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", foreign_keys=[user_id])
    promoter = db.relationship("User", foreign_keys=[promoted_by])

class RoleRequest(db.Model):
    __tablename__ = "role_requests"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    requested_role = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending | approved | rejected
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    user = db.relationship("User", foreign_keys=[user_id])
    admin = db.relationship("User", foreign_keys=[admin_id])

    


