from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user
from models import db, User
from config import Config

# -------------------- Login Manager --------------------
login_manager = LoginManager()
login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except (ValueError, TypeError):
        return None


# -------------------- Factory App --------------------
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)

    # -------------------- Blueprints --------------------
    from routes.auth import auth_bp
    from routes.productos import productos_bp
    from routes.perfil import perfil_bp
    from routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(productos_bp)
    app.register_blueprint(perfil_bp)
    app.register_blueprint(dashboard_bp)

    # -------------------- Ruta principal --------------------
    @app.route("/")
    def home():
        if current_user.is_authenticated:
            if current_user.rol == "admin":
                return redirect(url_for("dashboard.admin"))
            elif current_user.rol == "vendedor":
                return redirect(url_for("dashboard.vendedor"))
            else:
                return redirect(url_for("productos.listar_productos"))

        return redirect(url_for("auth.login"))

    return app


# -------------------- Main --------------------
app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # solo para desarrollo
    app.run(debug=True)
