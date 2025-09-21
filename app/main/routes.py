# app/main/routes.py
from flask import render_template, abort
from . import mainBp


# ---- Home Route (Login Page by default) ----
@mainBp.route('/')
def main():
    return render_template("login.html")


# ---- Dynamic Page Loader ----
@mainBp.route('/<page>')
def load_page(page):
    """
    Dynamically loads templates (e.g., /register -> register.html)
    Falls back with 404 if template does not exist
    """
    return render_template(f"{page}.html")
    

@mainBp.route('/index')
def dashboard():
    """Example route for a user dashboard"""
    return render_template("index.html")




