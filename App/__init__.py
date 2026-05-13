from flask import Flask, render_template
from dotenv import load_dotenv
import os


def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

    from .routes import main
    app.register_blueprint(main)

    # generic pages with no logic - just render the template
    # auth and admin pages are handled in routes.py because they need real logic
    page_aliases = {
        "contact": "contact.html",
        "forgot_password": "forgot_password.html",
        "home": "home.html",
        "observations": "observations.html",
        "observations_new": "observations_new.html",
        "reserves": "reserves.html",
    }

    for endpoint, template_name in page_aliases.items():
        app.add_url_rule(
            f"/{endpoint}",
            endpoint=endpoint,
            view_func=lambda template_name=template_name: render_template(template_name),
            methods=["GET", "POST"],
        )

    return app