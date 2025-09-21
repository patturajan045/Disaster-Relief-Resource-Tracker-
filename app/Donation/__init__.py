from flask import Blueprint

donationBp = Blueprint('donation',__name__)

from . import routes