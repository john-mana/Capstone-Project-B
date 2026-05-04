from flask import Blueprint
from .db import get_connection

main = Blueprint("main", __name__)

@main.route("/")
def index():
    return "Flask app is running."


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