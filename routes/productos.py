from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import db, Producto, Carrito, User
import boto3
from config import Config

# ======================================================
# BLUEPRINT
# ======================================================
from flask import Blueprint
import boto3
from config import Config

productos_bp = Blueprint("productos", __name__, url_prefix="/productos")

# Cliente MinIO
s3 = boto3.client(
    "s3",
    endpoint_url=f"http://{Config.MINIO_ENDPOINT}",
    aws_access_key_id=Config.MINIO_ACCESS_KEY,
    aws_secret_access_key=Config.MINIO_SECRET_KEY,
)

# ================================
# Filtro Jinja para mostrar precios en CLP
# ================================
@productos_bp.app_template_filter("clp")
def formato_clp(valor):
    try:
        # Formato con punto como separador de miles (estilo Chile)
        return f"${valor:,.0f} CLP".replace(",", ".")
    except (ValueError, TypeError):
        return valor

# ======================================================
# LISTAR PRODUCTOS (todos los usuarios)
# ======================================================
@productos_bp.route("/")
def listar_productos():
    productos = Producto.query.all()
    return render_template("index.html", productos=productos)

# ======================================================
# AGREGAR PRODUCTO (admin y vendedor)
# ======================================================
@productos_bp.route("/agregar", methods=["GET", "POST"])
@login_required
def agregar_producto():
    if current_user.rol not in ["admin", "vendedor"]:
        abort(403)

    if request.method == "POST":
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        precio = float(request.form["precio"])
        stock = int(request.form["stock"])
        imagen = request.files.get("imagen")

        url_imagen = None
        if imagen:
            s3.upload_fileobj(imagen, Config.MINIO_BUCKET, imagen.filename)
            url_imagen = f"http://{Config.MINIO_ENDPOINT}/{Config.MINIO_BUCKET}/{imagen.filename}"

        producto = Producto(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            stock=stock,
            imagen=url_imagen,
            vendedor_id=current_user.id
        )

        db.session.add(producto)
        db.session.commit()
        flash("Producto agregado correctamente")
        return redirect(url_for("dashboard.vendedor"))

    return render_template("agregar.html")

# ======================================================
# EDITAR PRODUCTO (admin y vendedor)
# ======================================================
# ======================================================
# EDITAR PRODUCTO (admin y vendedor)
# ======================================================
@productos_bp.route("/<int:id>/editar", methods=["GET", "POST"])
@login_required
def editar_producto(id):
    # Permitir solo admin y vendedor
    if current_user.rol not in ["admin", "vendedor"]:
        abort(403)

    producto = Producto.query.get_or_404(id)

    if request.method == "POST":
        # Actualizar campos del producto
        producto.nombre = request.form.get("nombre", producto.nombre)
        producto.descripcion = request.form.get("descripcion", producto.descripcion)
        producto.precio = float(request.form.get("precio", producto.precio))
        producto.stock = int(request.form.get("stock", producto.stock))

        # Subir imagen si se adjunta
        imagen = request.files.get("imagen")
        if imagen:
            s3.upload_fileobj(imagen, Config.MINIO_BUCKET, imagen.filename)
            producto.imagen = f"http://{Config.MINIO_ENDPOINT}/{Config.MINIO_BUCKET}/{imagen.filename}"

        db.session.commit()
        flash("Producto actualizado correctamente")

        # Redirigir según rol
        if current_user.rol == "admin":
            return redirect(url_for("dashboard.admin"))
        else:
            return redirect(url_for("dashboard.vendedor"))

    return render_template("editar.html", producto=producto)
# ======================================================
# ELIMINAR PRODUCTO (admin y vendedor)
# ======================================================
@productos_bp.route("/<int:id>/eliminar", methods=["POST"])
@login_required
def eliminar_producto(id):
    if current_user.rol not in ["admin", "vendedor"]:
        abort(403)

    producto = Producto.query.get_or_404(id)

    if current_user.rol == "vendedor" and producto.vendedor_id != current_user.id:
        abort(403)

    db.session.delete(producto)
    db.session.commit()

    flash("Producto eliminado correctamente")
    return redirect(url_for("dashboard.vendedor"))

# ======================================================
# AGREGAR STOCK (admin y vendedor)
# ======================================================
@productos_bp.route("/<int:id>/agregar_stock", methods=["POST"])
@login_required
def agregar_stock(id):
    if current_user.rol not in ["admin", "vendedor"]:
        abort(403)

    producto = Producto.query.get_or_404(id)

    if current_user.rol == "vendedor" and producto.vendedor_id != current_user.id:
        abort(403)

    cantidad = int(request.form.get("cantidad", 0))
    if cantidad <= 0:
        flash("Cantidad inválida")
        return redirect(url_for("dashboard.vendedor"))

    producto.stock += cantidad
    db.session.commit()

    flash("Stock actualizado correctamente")
    return redirect(url_for("dashboard.vendedor"))

# ======================================================
# CARRITO (solo cliente)
# ======================================================
@productos_bp.route("/carrito")
@login_required
def ver_carrito():
    if current_user.rol != "cliente":
        abort(403)

    items = Carrito.query.filter_by(user_id=current_user.id).all()
    total = sum(item.producto.precio * item.cantidad for item in items)
    return render_template("carrito.html", items=items, total=total)

@productos_bp.route("/agregar_carrito/<int:producto_id>", methods=["POST"])
@login_required
def agregar_carrito(producto_id):
    if current_user.rol != "cliente":
        abort(403)

    cantidad = int(request.form.get("cantidad", 1))
    producto = Producto.query.get_or_404(producto_id)

    if cantidad > producto.stock:
        flash("No hay suficiente stock disponible", "error")
        return redirect(url_for("productos.listar_productos"))

    item = Carrito.query.filter_by(
        user_id=current_user.id,
        producto_id=producto_id
    ).first()

    if item:
        item.cantidad += cantidad
    else:
        item = Carrito(
            user_id=current_user.id,
            producto_id=producto_id,
            cantidad=cantidad
        )
        db.session.add(item)

    db.session.commit()
    flash(f"{cantidad} unidad(es) de {producto.nombre} agregadas al carrito")
    return redirect(url_for("productos.listar_productos"))

@productos_bp.route("/carrito/eliminar/<int:id>", methods=["POST"])
@login_required
def eliminar_del_carrito(id):
    if current_user.rol != "cliente":
        abort(403)

    item = Carrito.query.get_or_404(id)
    if item.user_id != current_user.id:
        abort(403)

    db.session.delete(item)
    db.session.commit()

    flash("Producto eliminado del carrito")
    return redirect(url_for("productos.ver_carrito"))

@productos_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    if current_user.rol != "cliente":
        abort(403)

    items = Carrito.query.filter_by(user_id=current_user.id).all()
    if not items:
        flash("El carrito está vacío", "error")
        return redirect(url_for("productos.ver_carrito"))

    if request.method == "POST":
        total = 0
        errores = []

        for item in items:
            producto = Producto.query.get(item.producto_id)
            if not producto:
                errores.append(f"El producto {item.producto_id} no existe.")
                continue
            if producto.stock < item.cantidad:
                errores.append(f"No hay suficiente stock de {producto.nombre}. Disponible: {producto.stock}")

        if errores:
            for e in errores:
                flash(e, "error")
            return redirect(url_for("productos.ver_carrito"))

        for item in items:
            producto = Producto.query.get(item.producto_id)
            producto.stock -= item.cantidad
            total += producto.precio * item.cantidad

        Carrito.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()

        flash(f"Compra realizada correctamente. Total: ${total}", "success")
        return redirect(url_for("productos.ver_carrito"))

    return render_template("checkout.html", items=items)

# ======================================================
# PERFIL (todos)
# ======================================================
@productos_bp.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    if request.method == "POST":
        current_user.nombre = request.form.get("nombre", current_user.nombre)
        current_user.bio = request.form.get("bio", current_user.bio)

        foto = request.files.get("foto_perfil")
        if foto:
            s3.upload_fileobj(foto, Config.MINIO_BUCKET, foto.filename)
            current_user.foto_perfil = (
                f"http://{Config.MINIO_ENDPOINT}/{Config.MINIO_BUCKET}/{foto.filename}"
            )

        db.session.commit()
        flash("Perfil actualizado")
        return redirect(url_for("productos.perfil"))

    clientes = []
    if current_user.rol == "vendedor":
        productos = Producto.query.filter_by(vendedor_id=current_user.id).all()
        productos_ids = [p.id for p in productos]
        compras = Carrito.query.filter(Carrito.producto_id.in_(productos_ids)).all()
        clientes_ids = list(set(c.user_id for c in compras))
        clientes = User.query.filter(User.id.in_(clientes_ids)).all()

    return render_template("perfil.html", clientes=clientes)