from flask import Blueprint, render_template, request
import mysql.connector

main = Blueprint("main", __name__)


@main.route("/")
def home():
    return "Flask app is running."


@main.route("/map")
def map_view():
    species = request.args.get("species")
    date = request.args.get("date")

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