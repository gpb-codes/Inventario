from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, User
from flask_login import login_user, logout_user, login_required, current_user
import re
import os

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# -------------------- Registro --------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not nombre or not email or not password:
            flash("Todos los campos son obligatorios")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(email=email).first():
            flash("El correo ya está registrado")
            return redirect(url_for("auth.register"))

        # Rol por defecto
        rol = "cliente"

        # ⚠️ Auto-asignación de rol en desarrollo
        if os.getenv("FLASK_ENV") == "development":
            if re.search(r"@gabrielstore\.cl$", email):
                rol = "admin"
            elif re.search(r"@vendedor.gabrielstore\.cl$", email):
                rol = "vendedor"

        nuevo_usuario = User(
            nombre=nombre,
            email=email,
            rol=rol
        )
        nuevo_usuario.set_password(password)

        db.session.add(nuevo_usuario)
        db.session.commit()

        flash("Usuario registrado correctamente. Inicia sesión.")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


# -------------------- Login --------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Debes ingresar correo y contraseña")
            return redirect(url_for("auth.login"))

        usuario = User.query.filter_by(email=email).first()

        if usuario and usuario.check_password(password):
            login_user(usuario)
            flash("Sesión iniciada correctamente")
            return redirect(url_for("dashboard.index"))

        flash("Correo o contraseña incorrectos")
        return redirect(url_for("auth.login"))

    return render_template("login.html")


# -------------------- Logout --------------------
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada correctamente")
    return redirect(url_for("auth.login"))