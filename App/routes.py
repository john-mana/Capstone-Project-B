import os
import socket

from flask import Blueprint, redirect, render_template, request, url_for
from flask import current_app

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


# =========================
# Home
# =========================

@main.route("/")
def index():
    return redirect(url_for("main.home"))


@main.route("/home")
def home():
    return render_template("home.html")


# =========================
# Authentication
# =========================

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


# =========================
# Admin Controls
# =========================

@main.route("/admin_controls")
def admin_controls():
    return render_template("admin_controls.html")


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


# =========================
# Database Test
# =========================

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


# =========================
# Traits
# =========================

@main.route("/traits_findby")
def traits_findby():
    return render_template("traits_findby.html")


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


# =========================
# Query Builder
# =========================

@main.route("/query_builder", methods=["GET"])
def query_builder():
    # ---------------------
    # Read filters from GET
    # ---------------------
    filters = {k: request.args.get(k, "").strip() for k in QUERY_FILTERS}

    # ---------------------
    # Pagination
    # ---------------------
    per_page = int(request.args.get("per_page", 25))
    if per_page not in (10, 25, 50, 100):
        per_page = 25

    page_num = int(request.args.get("page", 1))
    if page_num < 1:
        page_num = 1

    offset = (page_num - 1) * per_page

    context = {
        "filters": filters,
        "results": [],
        "total_results": 0,
        "total_pages": 1,
        "page_num": page_num,
        "per_page": per_page,

        # required by template JS
        "species_options": [],
        "vernacular_options": [],
        "reserve_options": [],
        "dataset_options": [],
        "locality_options": [],
        "habitat_options": [],
        "basis_options": [],

        "username": "Development user",
        "is_admin": False,
        "error": None,
    }

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # ---------------------
        # Build WHERE clause
        # ---------------------
        where = []
        params = []

        def like(col, val):
            where.append(f"{col} LIKE %s")
            params.append(f"%{val}%")

        if filters["species"]:
            like("o.scientific_name", filters["species"])

        if filters["vernacular_name"]:
            where.append("""
                (
                    sp.vernacular_name = %s
                    OR sp.vernacular_name LIKE %s
                    OR sp.vernacular_name LIKE %s
                    OR sp.vernacular_name LIKE %s
                )
            """)
            params.extend([
                filters["vernacular_name"],
                f"{filters['vernacular_name']} %",
                f"% {filters['vernacular_name']}",
                f"% {filters['vernacular_name']} %"
            ])

        if filters["reserve"]:
            like("r.asset_name", filters["reserve"])

        if filters["dataset"]:
            like("d.dataset_name", filters["dataset"])

        #if filters["locality"]:
            #like("o.locality", filters["locality"])

        #if filters["habitat"]:
            #like("o.habitat", filters["habitat"])

        #if filters["basis"]:
            #like("o.basis_of_record", filters["basis"])

        if filters["native"]:
            where.append("sp.native_flag = %s")
            params.append(filters["native"])

        #if filters["rare"]:
            #like("sp.threatened_species_status", filters["rare"])

        if filters["start_year"]:
            where.append("YEAR(o.event_date) >= %s")
            params.append(filters["start_year"])

        if filters["end_year"]:
            where.append("YEAR(o.event_date) <= %s")
            params.append(filters["end_year"])

        where_clause = "WHERE " + " AND ".join(where) if where else ""

        # ---------------------
        # Count matching rows
        # ---------------------
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
        total_pages = max(1, (total_results + per_page - 1) // per_page)

        if page_num > total_pages:
            page_num = total_pages
            offset = (page_num - 1) * per_page

        # ---------------------
        # Results query
        # Use the simpler, known-good shape
        # ---------------------
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
                sp.native_flag,
                NULL AS threatened_species_status,
                NULL AS decimal_latitude,
                NULL AS decimal_longitude,
                NULL AS locality,
                NULL AS habitat,
                NULL AS basis_of_record,
                NULL AS recorded_by,
                NULL AS occurrence_remarks
            FROM occurrences o
            LEFT JOIN species sp ON o.species_id = sp.species_id
            LEFT JOIN reserves r ON o.reserve_id = r.reserve_id
            LEFT JOIN datasets d ON o.dataset_id = d.dataset_id
            {where_clause}
            ORDER BY o.event_date DESC
            LIMIT %s OFFSET %s
            """,
            params + [per_page, offset],
        )


        context["results"] = cursor.fetchall()
        context["total_results"] = total_results
        context["total_pages"] = total_pages
        context["page_num"] = page_num

        # ---------------------
        # Dropdown options
        # ---------------------
        cursor.execute(
            "SELECT DISTINCT scientific_name FROM occurrences "
            "WHERE scientific_name IS NOT NULL ORDER BY scientific_name LIMIT 1000"
        )
        context["species_options"] = [r["scientific_name"] for r in cursor.fetchall()]

        cursor.execute(
            "SELECT DISTINCT vernacular_name FROM species "
            "WHERE vernacular_name IS NOT NULL ORDER BY vernacular_name LIMIT 1000"
        )
        context["vernacular_options"] = [r["vernacular_name"] for r in cursor.fetchall()]

        cursor.execute(
            "SELECT DISTINCT asset_name FROM reserves "
            "WHERE asset_name IS NOT NULL ORDER BY asset_name"
        )
        context["reserve_options"] = [r["asset_name"] for r in cursor.fetchall()]

        cursor.execute(
            "SELECT DISTINCT dataset_name FROM datasets "
            "WHERE dataset_name IS NOT NULL ORDER BY dataset_name"
        )
        context["dataset_options"] = [r["dataset_name"] for r in cursor.fetchall()]

        context["locality_options"] = []

        context["habitat_options"] = []

        context["basis_options"] = []

        conn.close()

    except Exception as e:
        context["error"] = str(e)

    return render_template("query_builder.html", **context)