from flask import Blueprint, render_template
from .db import get_connection

main = Blueprint("main", __name__)

@main.route("/")
def index():
    return render_template("login.html")


@main.route("/db-test")
def db_test():
    try:
        conn = get_connection()

        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM occurrences")
            result = cursor.fetchone()

        conn.close()

        return f"Database connected successfully. Total occurrences: {result['total']}"

    except Exception as e:
        return f"Database connection failed: {e}"


# 👇 ADD THESE ROUTES

@main.route("/contact")
def contact():
    return render_template("contact.html")


@main.route("/login")
def login():
    return render_template("login.html")


@main.route("/register")
def register():
    return render_template("register.html")

@main.route("/admin_controls")
def admin_controls():
    return render_template("admin_controls.html")

@main.route("/home")
def home():
    return render_template("home.html")


@main.route("/query_builder")
def query_builder():
    return render_template(
        "query_builder.html",
        species_options=[],
    )

# =========================
# Species
# =========================
@main.route("/species")
def species():
    return render_template("species.html")


@main.route("/species_new")
def species_new():
    return render_template("species_new.html")


@main.route("/species_detail")
def species_detail():
    return render_template("species_detail.html")


# =========================
# Traits
# =========================
@main.route("/traits")
def traits():
    return render_template("traits.html")


@main.route("/traits_detail")
def traits_detail():
    return render_template("traits_detail.html")


@main.route("/traits_findby")
def traits_findby():
    return render_template("traits_findby.html")


# =========================
# Observations
# =========================
@main.route("/observations")
def observations():
    return render_template("observations.html")


@main.route("/observations_new")
def observations_new():
    return render_template("observations_new.html")


# =========================
# Reserves
# =========================
@main.route("/reserves")
def reserves():
    return render_template("reserves.html")


# =========================
# At Risk Species
# =========================
@main.route("/at_risk")
def at_risk():
    return render_template("at_risk.html")