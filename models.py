from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):   # <-- ahora hereda de UserMixin
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default="cliente")

    # Opcionales: asegúrate de que existan en la BD o elimínalos
    bio = db.Column(db.Text)  
    foto_perfil = db.Column(db.String(255))

    def __repr__(self):
        return f"<User {self.email}>"

    # relación inversa con Carrito
    carritos = db.relationship("Carrito", back_populates="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



class Producto(db.Model):
    __tablename__ = "producto"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    imagen = db.Column(db.String(200))

    # relación con User (vendedor)
    vendedor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)


class Carrito(db.Model):
    __tablename__ = "carrito"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("producto.id"), nullable=False)
    cantidad = db.Column(db.Integer, default=1)

    # relaciones
    user = db.relationship("User", back_populates="carritos")
    producto = db.relationship("Producto")

class Wishlist(db.Model):
    __tablename__ = 'wishlist'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)

    user = db.relationship('User', backref='wishlist_items')
    producto = db.relationship('Producto', backref='wishlist_items')


class Pedido(db.Model):
    __tablename__ = 'pedido'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=db.func.current_timestamp())
    estado = db.Column(db.String(50), default='pendiente')

    user = db.relationship('User', backref='pedidos')

    def __repr__(self):
        return f'<Pedido {self.id} - User {self.user_id} - Estado {self.estado}>'


class Reseña(db.Model):
    __tablename__ = 'reseña'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    comentario = db.Column(db.Text, nullable=False)
    calificacion = db.Column(db.Integer, nullable=False)  # por ejemplo, de 1 a 5
    fecha = db.Column(db.DateTime, default=db.func.current_timestamp())

    user = db.relationship('User', backref='reseñas')
    producto = db.relationship('Producto', backref='reseñas')

    def __repr__(self):
        return f'<Reseña {self.id} - User {self.user_id} - Producto {self.producto_id}>'  