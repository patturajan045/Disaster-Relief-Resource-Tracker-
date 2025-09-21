from flask import Blueprint

dashboard_bp = Blueprint('dashboardBp', __name__)

from . import routes
