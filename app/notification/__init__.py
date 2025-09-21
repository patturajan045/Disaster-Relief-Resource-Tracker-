from flask import Blueprint

notificationBp = Blueprint('notificationsBp',__name__)

from . import routes