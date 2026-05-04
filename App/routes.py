from flask import Blueprint, render_template, request
import mysql.connector

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return "Flask app is running."


@main.route("/map")
def map_view():
    species = request.args.get("species")
    date = request.args.get("date")

    try:
        conn = mysql.connector.connect(
            host="db",
            user="root",
            password="root",
            database="flora_project"
        )

        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                scientific_name,
                decimal_latitude,
                decimal_longitude,
                event_date
            FROM occurrences
            WHERE decimal_latitude IS NOT NULL
            AND decimal_longitude IS NOT NULL
        """

        params = []

        if species:
            query += " AND scientific_name LIKE %s"
            params.append(f"%{species}%")

        if date:
            query += " AND DATE(event_date) = %s"
            params.append(date)

        cursor.execute(query, params)
        data = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template("map.html", data=data, species=species, date=date)

    except Exception as e:
        return f"Database connection failed: {e}"


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


@main.route("/species")
def species():
    return render_template("species.html")


@main.route("/species_new")
def species_new():
    return render_template("species_new.html")


@main.route("/species_detail")
def species_detail():
    return render_template("species_detail.html")


@main.route("/traits")
def traits():
    return render_template("traits.html")


@main.route("/traits_detail")
def traits_detail():
    return render_template("traits_detail.html")


@main.route("/traits_findby")
def traits_findby():
    return render_template("traits_findby.html")


@main.route("/observations")
def observations():
    return render_template("observations.html")


@main.route("/observations_new")
def observations_new():
    return render_template("observations_new.html")


@main.route("/reserves")
def reserves():
    return render_template("reserves.html")


@main.route("/at_risk")
def at_risk():
    return render_template("at_risk.html")