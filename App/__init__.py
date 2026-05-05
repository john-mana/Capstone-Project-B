from flask import Flask, render_template
from dotenv import load_dotenv
import os


def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

    from .routes import main
    app.register_blueprint(main)

    page_aliases = {
        "admin_controls": "admin_controls.html",
        "at_risk": "at_risk.html",
        "contact": "contact.html",
        "forgot_password": "forgot_password.html",
        "home": "home.html",
        "login": "login.html",
        "observations": "observations.html",
        "observations_new": "observations_new.html",
        "register": "register.html",
        "reserves": "reserves.html",
        "species": "species.html",
        "species_detail": "species_detail.html",
        "species_new": "species_new.html",
        "traits_findby": "traits_findby.html",
    }

    for endpoint, template_name in page_aliases.items():
        app.add_url_rule(
            f"/{endpoint}",
            endpoint=endpoint,
            view_func=lambda template_name=template_name: render_template(template_name),
            methods=["GET", "POST"],
        )

    return app
