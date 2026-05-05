import os
import socket

from flask import Blueprint, redirect, render_template, request, url_for

from .db import get_connection

main = Blueprint("main", __name__)

QUERY_FILTERS = (
    "species",
    "vernacular_name",
    "reserve",
    "native",
    "rare",
    "start_year",
    "end_year",
    "dataset",
    "locality",
    "habitat",
    "basis",
)


def database_port_open(timeout=1):
    host = os.getenv("DB_HOST")
    port = int(os.getenv("DB_PORT", 3306))

    if not host:
        return False

    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


@main.route("/")
def index():
    return redirect(url_for("main.home"))


@main.route("/home")
def home():
    return render_template("home.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    return render_template("login.html")


@main.route("/register", methods=["GET", "POST"])
def register():
    return render_template("register.html")


@main.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    return render_template("forgot_password.html")


@main.route("/contact", methods=["GET", "POST"])
def contact():
    return render_template("contact.html")


@main.route("/species")
def species():
    return render_template("species.html")


@main.route("/species_new")
def species_new():
    return render_template("species_new.html")


@main.route("/species_detail")
def species_detail():
    return render_template("species_detail.html")


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


@main.route("/admin_controls")
def admin_controls():
    return render_template("admin_controls.html")


@main.route("/traits_findby")
def traits_findby():
    return render_template("traits_findby.html")


@main.route("/logout")
def logout():
    return redirect(url_for("main.login"))


@main.route("/flora_dashboard")
@main.route("/fauna_dashboard")
@main.route("/report")
@main.route("/map")
@main.route("/settings")
def placeholder_page():
    return render_template("home.html")


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


@main.route("/traits")
def traits():
    search = request.args.get("q", "").strip()
    rows = []
    error = None

    try:
        conn = get_connection()

        with conn.cursor() as cursor:
            params = []
            where_clause = ""

            if search:
                where_clause = """
                AND (
                    trait_type_name LIKE %s
                    OR trait_name LIKE %s
                    OR trait_info LIKE %s
                    OR trait_unit LIKE %s
                    OR trait_type LIKE %s
                    OR trait_label LIKE %s
                )
                """
                params = [f"%{search}%"] * 6

            cursor.execute(
                f"""
                SELECT
                    trait_type_name,
                    trait_name,
                    trait_info,
                    trait_unit,
                    trait_type,
                    trait_label
                FROM traits
                WHERE of_interest = 1
                {where_clause}
                ORDER BY column_number, trait_type_name, trait_name
                """,
                params,
            )
            rows = cursor.fetchall()

        conn.close()
    except Exception as exc:
        error = str(exc)

    return render_template("traits.html", traits=rows, search=search, error=error)


@main.route("/traits_detail")
def traits_detail():
    trait_name = request.args.get("trait", "").strip()
    trait = None
    value_rows = []
    trait_options = []
    summary = {
        "value_count": 0,
        "species_count": 0,
        "latest_observation_date": None,
    }
    max_species_count = 0
    error = None

    try:
        conn = get_connection()

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT trait_name, trait_label
                FROM traits
                WHERE of_interest = 1
                ORDER BY column_number, trait_name
                """
            )
            trait_options = cursor.fetchall()

            if not trait_name:
                conn.close()
                return render_template(
                    "traits_detail.html",
                    trait=None,
                    trait_name=trait_name,
                    trait_options=trait_options,
                    value_rows=value_rows,
                    summary=summary,
                    max_species_count=max_species_count,
                    error=error,
                )

            cursor.execute(
                """
                SELECT
                    trait_id,
                    trait_type_name,
                    trait_name,
                    trait_info,
                    trait_unit,
                    trait_type,
                    trait_label,
                    column_number
                FROM traits
                WHERE trait_name = %s
                LIMIT 1
                """,
                [trait_name],
            )
            trait = cursor.fetchone()

            if trait:
                cursor.execute(
                    """
                    SELECT
                        COUNT(DISTINCT COALESCE(
                            NULLIF(TRIM(stj.working_value), ''),
                            NULLIF(TRIM(stj.original_value), '')
                        )) AS value_count,
                        COUNT(DISTINCT stj.species_id) AS species_count,
                        MAX(o.event_date) AS latest_observation_date
                    FROM species_traits_junction stj
                    LEFT JOIN occurrences o ON o.species_id = stj.species_id
                    WHERE stj.trait_id = %s
                    """,
                    [trait["trait_id"]],
                )
                summary = cursor.fetchone()

                cursor.execute(
                    """
                    SELECT
                        COALESCE(
                            NULLIF(TRIM(stj.working_value), ''),
                            NULLIF(TRIM(stj.original_value), ''),
                            '(blank)'
                        ) AS trait_value,
                        COUNT(DISTINCT stj.species_id) AS species_count,
                        MAX(o.event_date) AS latest_observation_date
                    FROM species_traits_junction stj
                    LEFT JOIN occurrences o ON o.species_id = stj.species_id
                    WHERE stj.trait_id = %s
                    GROUP BY trait_value
                    ORDER BY species_count DESC, trait_value
                    """,
                    [trait["trait_id"]],
                )
                value_rows = cursor.fetchall()
                if value_rows:
                    max_species_count = max(row["species_count"] for row in value_rows)

        conn.close()
    except Exception as exc:
        error = str(exc)

    return render_template(
        "traits_detail.html",
        trait=trait,
        trait_name=trait_name,
        trait_options=trait_options,
        value_rows=value_rows,
        summary=summary,
        max_species_count=max_species_count,
        error=error,
    )


@main.route("/query_builder", methods=["GET", "POST"])
def query_builder():
    filters = {key: "" for key in QUERY_FILTERS}

    if request.method == "POST":
        for key in filters:
            filters[key] = request.form.get(key, "")

    per_page = int(request.args.get("per_page", 25))
    page_num = int(request.args.get("page", 1))
    offset = (page_num - 1) * per_page

    context = {
        "results": [],
        "filters": filters,
        "total_results": 0,
        "page_num": page_num,
        "total_pages": 1,
        "per_page": per_page,
        "species_options": [],
        "reserve_options": [],
        "dataset_options": [],
        "vernacular_options": [],
        "locality_options": [],
        "habitat_options": [],
        "basis_options": [],
        "username": "Development user",
        "is_admin": False,
    }

    if not database_port_open():
        return render_template("query_builder.html", **context)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        where = []
        params = []

        if filters["species"]:
            where.append("o.scientific_name LIKE %s")
            params.append(f"%{filters['species']}%")
        if filters["vernacular_name"]:
            where.append("sp.vernacular_name LIKE %s")
            params.append(f"%{filters['vernacular_name']}%")
        if filters["reserve"]:
            where.append("r.asset_name LIKE %s")
            params.append(f"%{filters['reserve']}%")
        if filters["native"]:
            where.append("sp.native_flag = %s")
            params.append(filters["native"])
        if filters["rare"]:
            where.append("sp.threatened_species_status LIKE %s")
            params.append(f"%{filters['rare']}%")
        if filters["start_year"]:
            where.append("YEAR(o.event_date) >= %s")
            params.append(filters["start_year"])
        if filters["end_year"]:
            where.append("YEAR(o.event_date) <= %s")
            params.append(filters["end_year"])
        if filters["dataset"]:
            where.append("d.dataset_name LIKE %s")
            params.append(f"%{filters['dataset']}%")
        if filters["locality"]:
            where.append("o.locality LIKE %s")
            params.append(f"%{filters['locality']}%")
        if filters["habitat"]:
            where.append("o.habitat LIKE %s")
            params.append(f"%{filters['habitat']}%")
        if filters["basis"]:
            where.append("o.basis_of_record LIKE %s")
            params.append(f"%{filters['basis']}%")

        where_clause = "WHERE " + " AND ".join(where) if where else ""

        cursor.execute(
            f"""
            SELECT COUNT(*) AS total
            FROM occurrences o
            LEFT JOIN species sp ON o.species_id = sp.species_id
            LEFT JOIN reserves r ON o.reserve_id = r.reserve_id
            LEFT JOIN datasets d ON o.dataset_id = d.dataset_id
            {where_clause}
            """,
            params,
        )
        total_results = cursor.fetchone()["total"]

        cursor.execute(
            f"""
            SELECT
                o.scientific_name,
                sp.vernacular_name,
                r.asset_name AS reserve_name,
                YEAR(o.event_date) AS year,
                MONTH(o.event_date) AS month,
                DAY(o.event_date) AS day,
                d.dataset_name,
                o.decimal_latitude,
                o.decimal_longitude,
                o.locality,
                o.habitat,
                o.basis_of_record,
                o.recorded_by,
                o.occurrence_remarks,
                sp.native_flag = 'Exotic' AS exotic,
                sp.threatened_species_status
            FROM occurrences o
            LEFT JOIN species sp ON o.species_id = sp.species_id
            LEFT JOIN reserves r ON o.reserve_id = r.reserve_id
            LEFT JOIN datasets d ON o.dataset_id = d.dataset_id
            {where_clause}
            LIMIT %s OFFSET %s
            """,
            params + [per_page, offset],
        )
        results = cursor.fetchall()

        cursor.execute(
            "SELECT DISTINCT scientific_name FROM occurrences "
            "WHERE scientific_name IS NOT NULL ORDER BY scientific_name LIMIT 2000"
        )
        species_options = [row["scientific_name"] for row in cursor.fetchall()]

        cursor.execute(
            "SELECT DISTINCT asset_name FROM reserves "
            "WHERE asset_name IS NOT NULL ORDER BY asset_name"
        )
        reserve_options = [row["asset_name"] for row in cursor.fetchall()]

        cursor.execute(
            "SELECT DISTINCT dataset_name FROM datasets "
            "WHERE dataset_name IS NOT NULL ORDER BY dataset_name"
        )
        dataset_options = [row["dataset_name"] for row in cursor.fetchall()]

        cursor.execute(
            "SELECT DISTINCT vernacular_name FROM species "
            "WHERE vernacular_name IS NOT NULL ORDER BY vernacular_name LIMIT 2000"
        )
        vernacular_options = [row["vernacular_name"] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        context.update(
            {
                "results": results,
                "total_results": total_results,
                "total_pages": max(1, -(-total_results // per_page)),
                "species_options": species_options,
                "reserve_options": reserve_options,
                "dataset_options": dataset_options,
                "vernacular_options": vernacular_options,
            }
        )
    except Exception:
        pass

    return render_template("query_builder.html", **context)
