from flask import Blueprint

auditLog = Blueprint('auditLog',__name__)

from .import routes


