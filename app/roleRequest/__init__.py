from flask import Blueprint

roleRequestBp = Blueprint("roleRequestBp", __name__)

from . import routes
