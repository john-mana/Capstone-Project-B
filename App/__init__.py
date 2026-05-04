from flask import Flask, render_template
from dotenv import load_dotenv
import os


def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

    from .routes import SIMPLE_PAGES, main
    app.register_blueprint(main)

    for endpoint, template_name in SIMPLE_PAGES.items():
        app.add_url_rule(
            f"/{endpoint}",
            endpoint=endpoint,
            view_func=lambda template_name=template_name: render_template(template_name),
            methods=["GET", "POST"],
        )

    return app
