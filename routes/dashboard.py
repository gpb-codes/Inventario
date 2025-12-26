from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import Producto, User, db

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# -------------------- Router principal --------------------
@dashboard_bp.route("/")
@login_required
def index():
    if current_user.rol == "cliente":
        return redirect(url_for("dashboard.cliente"))
    if current_user.rol == "vendedor":
        return redirect(url_for("dashboard.vendedor"))
    if current_user.rol == "admin":
        return redirect(url_for("dashboard.admin"))
    return "Rol no reconocido", 403


# -------------------- Dashboard Cliente --------------------
@dashboard_bp.route("/cliente")
@login_required
def cliente():
    if current_user.rol != "cliente":
        return "Acceso denegado", 403

    productos = Producto.query.all()
    return render_template("dashboard/cliente.html", productos=productos)


# -------------------- Dashboard Vendedor --------------------
@dashboard_bp.route("/vendedor")
@login_required
def vendedor():
    if current_user.rol != "vendedor":
        return "Acceso denegado", 403

    productos = Producto.query.filter_by(vendedor_id=current_user.id).all()
    return render_template("dashboard/vendedor.html", productos=productos)


# -------------------- Dashboard Admin --------------------
@dashboard_bp.route("/admin")
@login_required
def admin():
    if current_user.rol != "admin":
        return "Acceso denegado", 403

    usuarios = User.query.all()
    productos = Producto.query.all()

    return render_template("dashboard/admin.html", usuarios=usuarios, productos=productos)


from flask import request, flash
from models import db

# -------------------- Cambiar rol de usuario --------------------
@dashboard_bp.route("/cambiar_rol/<int:user_id>", methods=["POST"])
@login_required
def cambiar_rol(user_id):
    if current_user.rol != "admin":
        return "Acceso denegado", 403

    usuario = User.query.get(user_id)
    if not usuario:
        flash("Usuario no encontrado")
        return redirect(url_for("dashboard.admin"))

    # Obtener el nuevo rol desde el formulario
    nuevo_rol = request.form.get("rol")
    if nuevo_rol not in ["cliente", "vendedor", "admin"]:
        flash("Rol inválido")
        return redirect(url_for("dashboard.admin"))

    usuario.rol = nuevo_rol
    db.session.commit()

    flash(f"El rol de {usuario.nombre} fue cambiado a {nuevo_rol}")
    return redirect(url_for("dashboard.admin"))

# -------------------- Bloquear/Desbloquear usuario --------------------
@dashboard_bp.route("/toggle_usuario/<int:user_id>", methods=["POST"])
@login_required
def toggle_usuario(user_id):
    if current_user.rol != "admin":
        return "Acceso denegado", 403

    usuario = User.query.get(user_id)
    if not usuario:
        flash("Usuario no encontrado")
        return redirect(url_for("dashboard.admin"))

    if usuario.rol != "bloqueado":
        usuario.rol = "bloqueado"
        flash(f"Usuario {usuario.nombre} bloqueado")
    else:
        usuario.rol = "cliente"
        flash(f"Usuario {usuario.nombre} desbloqueado")

    db.session.commit()
    return redirect(url_for("dashboard.admin"))

