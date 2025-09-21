from flask import Blueprint
import os

# Point to the global templates folder (one level up)
mainBp = Blueprint(
    "mainBp",
    __name__,
    template_folder="../../templates"   # 👈 fix path
)

from . import routes
