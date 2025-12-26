from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, Carrito, Producto, Wishlist, Pedido, Reseña
import boto3
from config import Config

perfil_bp = Blueprint("perfil", __name__, url_prefix="/perfil")

# -------------------- MinIO client --------------------
s3 = boto3.client(
    "s3",
    endpoint_url=f"http://{Config.MINIO_ENDPOINT}",
    aws_access_key_id=Config.MINIO_ACCESS_KEY,
    aws_secret_access_key=Config.MINIO_SECRET_KEY,
)

# -------------------- Perfil --------------------
@perfil_bp.route("/", methods=["GET", "POST"])
@login_required
def ver_perfil():

    # ---------- Actualizar perfil ----------
    if request.method == "POST":
        current_user.nombre = request.form.get("nombre", current_user.nombre)
        current_user.bio = request.form.get("bio", current_user.bio)

        foto = request.files.get("foto_perfil")
        if foto:
            s3.upload_fileobj(
                foto,
                Config.MINIO_BUCKET,
                foto.filename,
                ExtraArgs={"ContentType": foto.content_type},
            )
            current_user.foto_perfil = f"http://{Config.MINIO_ENDPOINT}/{Config.MINIO_BUCKET}/{foto.filename}"

        db.session.commit()
        flash("Perfil actualizado correctamente", "success")
        return redirect(url_for("perfil.ver_perfil"))

    # ---------- Variables comunes ----------
    contexto = {}

    # CLIENTE → historial de compras, wishlist, pedidos, reseñas
    if current_user.rol == "cliente":
        compras = Carrito.query.filter_by(user_id=current_user.id).all()
        total_gastado = sum(c.producto.precio * c.cantidad for c in compras)
        wishlist = Wishlist.query.filter_by(user_id=current_user.id).all()
        pedidos = Pedido.query.filter_by(user_id=current_user.id).all()
        reseñas = Reseña.query.filter_by(user_id=current_user.id).all()

        contexto.update({
            "compras": compras,
            "total_gastado": total_gastado,
            "wishlist": [w.producto for w in wishlist],
            "pedidos": pedidos,
            "reseñas": reseñas
        })

    # VENDEDOR → productos propios, clientes y compras
    elif current_user.rol == "vendedor":
        productos = Producto.query.filter_by(vendedor_id=current_user.id).all()
        productos_ids = [p.id for p in productos]
        compras = Carrito.query.filter(Carrito.producto_id.in_(productos_ids)).all()

        clientes = {}
        for c in compras:
            if c.user_id not in clientes:
                clientes[c.user_id] = {"cliente": c.user, "compras": [], "total": 0}
            clientes[c.user_id]["compras"].append(c)
            clientes[c.user_id]["total"] += c.producto.precio * c.cantidad

        contexto.update({
            "productos": productos,
            "clientes": list(clientes.values())
        })

    # ADMIN → estadísticas generales
    elif current_user.rol == "admin":
        contexto.update({
            "total_usuarios": User.query.count(),
            "total_productos": Producto.query.count(),
            "total_compras": Carrito.query.count()
        })

    return render_template("perfil.html", **contexto)


# -------------------- Editar Perfil --------------------
@perfil_bp.route("/editar", methods=["GET", "POST"])
@login_required
def editar_perfil():
    if request.method == "POST":
        # Actualizar datos básicos
        current_user.nombre = request.form.get("nombre", current_user.nombre)
        current_user.email = request.form.get("email", current_user.email)

        # Actualizar foto de perfil si se sube
        foto = request.files.get("foto_perfil")
        if foto:
            s3.upload_fileobj(
                foto,
                Config.MINIO_BUCKET,
                foto.filename,
                ExtraArgs={"ContentType": foto.content_type},
            )
            current_user.foto_perfil = f"http://{Config.MINIO_ENDPOINT}/{Config.MINIO_BUCKET}/{foto.filename}"

        # Actualizar contraseña si se envía
        password = request.form.get("password")
        if password:
            current_user.set_password(password)  # asumiendo que tu modelo User tiene este método

        db.session.commit()
        flash("Perfil actualizado correctamente", "success")
        return redirect(url_for("perfil.ver_perfil"))

    # Renderizar formulario de edición
    return render_template("editar_profile.html", user=current_user)