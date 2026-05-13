import pymysql
import os
import socket
from urllib.parse import urlencode
import csv
import io
from flask import Response, send_file
import pandas as pd

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

OBSERVATION_FILTERS = QUERY_FILTERS


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


def build_observation_where(filters):
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
        where.append("sp.endangered_status_code LIKE %s")
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

    return where_clause, params


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


@main.route("/logout")
def logout():
    return redirect(url_for("main.login"))


# =========================
# Species
# =========================

@main.route("/species")
def species():
    """
    Show all species with taxonomy info.
    """
    species_list = []
    error = None

    search = request.args.get("q", "").strip()
    family_filter = request.args.get("family", "").strip()

    try:
        conn = get_connection()

        with conn.cursor() as cursor:
            params = []
            where_parts = []

            if search:
                where_parts.append(
                    "(sp.scientific_name LIKE %s OR sp.vernacular_name LIKE %s)"
                )
                params.extend([f"%{search}%", f"%{search}%"])

            if family_filter:
                where_parts.append("tx.family = %s")
                params.append(family_filter)

            where_clause = "WHERE " + " AND ".join(where_parts) if where_parts else ""

            cursor.execute(
                f"""
                SELECT
                    sp.species_id,
                    sp.taxonomy_id,
                    sp.scientific_name,
                    sp.vernacular_name,
                    sp.native_flag,
                    sp.endangered_status_code,
                    tx.family,
                    tx.genus
                FROM species sp
                LEFT JOIN taxonomy tx ON tx.taxonomy_id = sp.taxonomy_id
                {where_clause}
                ORDER BY sp.scientific_name
                LIMIT 500
                """,
                params,
            )
            species_list = cursor.fetchall()

            cursor.execute(
                """
                SELECT DISTINCT family
                FROM taxonomy
                WHERE family IS NOT NULL AND family != ''
                ORDER BY family
                """
            )
            family_options = [row["family"] for row in cursor.fetchall()]

            cursor.execute(
                """
                SELECT scientific_name, vernacular_name
                FROM species
                WHERE scientific_name IS NOT NULL
                ORDER BY scientific_name
                """
            )
            name_rows = cursor.fetchall()
            name_options = []
            for row in name_rows:
                if row["scientific_name"]:
                    name_options.append(row["scientific_name"])
                if row["vernacular_name"]:
                    name_options.append(row["vernacular_name"])

        conn.close()

    except Exception as exc:
        error = str(exc)
        family_options = []
        name_options = []

    return render_template(
        "species.html",
        species_list=species_list,
        family_options=family_options,
        name_options=name_options,
        search=search,
        family_filter=family_filter,
        error=error,
    )


@main.route("/species_new")
def species_new():
    """
    Show newest species by species_id desc.
    """
    species_list = []
    error = None

    search = request.args.get("q", "").strip()
    family_filter = request.args.get("family", "").strip()

    try:
        conn = get_connection()

        with conn.cursor() as cursor:
            params = []
            where_parts = []

            if search:
                where_parts.append(
                    "(sp.scientific_name LIKE %s OR sp.vernacular_name LIKE %s)"
                )
                params.extend([f"%{search}%", f"%{search}%"])

            if family_filter:
                where_parts.append("tx.family = %s")
                params.append(family_filter)

            where_clause = "WHERE " + " AND ".join(where_parts) if where_parts else ""

            cursor.execute(
                f"""
                SELECT
                    sp.species_id,
                    sp.taxonomy_id,
                    sp.scientific_name,
                    sp.vernacular_name,
                    sp.native_flag,
                    sp.endangered_status_code,
                    tx.family,
                    tx.genus
                FROM species sp
                LEFT JOIN taxonomy tx ON tx.taxonomy_id = sp.taxonomy_id
                {where_clause}
                ORDER BY sp.species_id DESC
                LIMIT 50
                """,
                params,
            )
            species_list = cursor.fetchall()

            cursor.execute(
                """
                SELECT DISTINCT family
                FROM taxonomy
                WHERE family IS NOT NULL AND family != ''
                ORDER BY family
                """
            )
            family_options = [row["family"] for row in cursor.fetchall()]

            cursor.execute(
                """
                SELECT scientific_name, vernacular_name
                FROM species
                WHERE scientific_name IS NOT NULL
                ORDER BY scientific_name
                """
            )
            name_rows = cursor.fetchall()
            name_options = []
            for row in name_rows:
                if row["scientific_name"]:
                    name_options.append(row["scientific_name"])
                if row["vernacular_name"]:
                    name_options.append(row["vernacular_name"])

        conn.close()

    except Exception as exc:
        error = str(exc)
        family_options = []
        name_options = []

    return render_template(
        "species_new.html",
        species_list=species_list,
        family_options=family_options,
        name_options=name_options,
        search=search,
        family_filter=family_filter,
        error=error,
    )


@main.route("/species_detail")
def species_detail():
    """
    Show full detail of one species.
    """

    species_id = request.args.get("species_id", "").strip()
    search = request.args.get("species", "").strip()

    species = None
    traits_list = []
    observation_count = 0
    latest_observation = None
    is_at_risk = False
    error = None
    species_options = []

    try:
        conn = get_connection()

        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    species_id,
                    scientific_name
                FROM species
                WHERE scientific_name IS NOT NULL
                ORDER BY scientific_name
                """
            )
            species_options = cursor.fetchall()

            if search and not species_id:

                cursor.execute(
                    """
                    SELECT species_id
                    FROM species
                    WHERE scientific_name = %s
                    LIMIT 1
                    """,
                    [search],
                )

                found_species = cursor.fetchone()

                if found_species:
                    species_id = found_species["species_id"]

            if not species_id:

                conn.close()

                return render_template(
                    "species_detail.html",
                    species=None,
                    traits_list=[],
                    observation_count=0,
                    latest_observation=None,
                    is_at_risk=False,
                    species_options=species_options,
                    search=search,
                    error=None,
                )

            cursor.execute(
                """
                SELECT
                    sp.species_id,
                    sp.taxonomy_id,
                    sp.scientific_name,
                    sp.vernacular_name,
                    sp.native_flag,
                    sp.endangered_status_code,
                    tx.kingdom,
                    tx.phylum,
                    tx.class_name,
                    tx.order_name,
                    tx.family,
                    tx.genus,
                    tx.species_epithet
                FROM species sp
                LEFT JOIN taxonomy tx
                    ON tx.taxonomy_id = sp.taxonomy_id
                WHERE sp.species_id = %s
                LIMIT 1
                """,
                [species_id],
            )

            species = cursor.fetchone()

            if species:

                cursor.execute(
                    """
                    SELECT
                        COUNT(*) AS obs_count,
                        MAX(event_date) AS latest_date
                    FROM occurrences
                    WHERE species_id = %s
                    """,
                    [species_id],
                )

                obs_summary = cursor.fetchone()

                observation_count = obs_summary["obs_count"] or 0
                latest_observation = obs_summary["latest_date"]

                cursor.execute(
                    """
                    SELECT
                        COUNT(*) AS obs_count,
                        COUNT(DISTINCT reserve_id) AS reserve_count,
                        MAX(YEAR(event_date)) AS latest_year
                    FROM occurrences
                    WHERE species_id = %s
                    """,
                    [species_id],
                )

                risk_data = cursor.fetchone()

                criteria_hits = 0

                if risk_data["obs_count"] > 0:

                    if risk_data["reserve_count"] == 1:
                        criteria_hits += 1

                    if risk_data["obs_count"] <= 3:
                        criteria_hits += 1

                    if (
                        risk_data["latest_year"]
                        and risk_data["latest_year"] < 2015
                    ):
                        criteria_hits += 1

                is_at_risk = criteria_hits >= 1

                cursor.execute(
                    """
                    SELECT
                        t.trait_name,
                        t.trait_label,
                        t.trait_info,
                        t.trait_unit,
                        COALESCE(
                            NULLIF(TRIM(stj.working_value), ''),
                            NULLIF(TRIM(stj.original_value), ''),
                            '(no value)'
                        ) AS trait_value,
                        stj.source_code
                    FROM species_traits_junction stj
                    JOIN traits t
                        ON t.trait_id = stj.trait_id
                    WHERE stj.species_id = %s
                    AND t.of_interest = 1
                    ORDER BY t.column_number, t.trait_name
                    """,
                    [species_id],
                )

                traits_list = cursor.fetchall()

        conn.close()

    except Exception as exc:
        error = str(exc)

    return render_template(
        "species_detail.html",
        species=species,
        traits_list=traits_list,
        observation_count=observation_count,
        latest_observation=latest_observation,
        is_at_risk=is_at_risk,
        species_options=species_options,
        search=search,
        error=error,
    )


# =========================
# Observations
# =========================

@main.route("/observations")
def observations():
    search = request.args.get("q", "").strip()

    rows = []
    observation_options = []
    error = None

    try:
        conn = get_connection()

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT scientific_name
                FROM occurrences
                WHERE scientific_name IS NOT NULL
                ORDER BY scientific_name
                LIMIT 2000
                """
            )
            observation_options = cursor.fetchall()

            params = []
            where_clause = ""

            if search:
                where_clause = """
                    WHERE (
                        o.scientific_name LIKE %s
                        OR sp.vernacular_name LIKE %s
                        OR r.asset_name LIKE %s
                        OR d.dataset_name LIKE %s
                    )
                """
                params = [
                    f"%{search}%",
                    f"%{search}%",
                    f"%{search}%",
                    f"%{search}%"
                ]

            cursor.execute(
                f"""
                SELECT
                    o.occurrence_id,
                    o.scientific_name,
                    sp.vernacular_name,
                    r.asset_name AS reserve_name,
                    o.event_date,
                    YEAR(o.event_date) AS year,
                    d.dataset_name,
                    o.decimal_latitude,
                    o.decimal_longitude
                FROM occurrences o
                LEFT JOIN species sp ON o.species_id = sp.species_id
                LEFT JOIN reserves r ON o.reserve_id = r.reserve_id
                LEFT JOIN datasets d ON o.dataset_id = d.dataset_id
                {where_clause}
                ORDER BY o.event_date DESC, o.scientific_name
                LIMIT 500
                """,
                params,
            )

            rows = cursor.fetchall()

        conn.close()

    except Exception as exc:
        error = str(exc)

    return render_template(
        "observations.html",
        observations=rows,
        observation_options=observation_options,
        search=search,
        error=error,
    )


@main.route("/observations_new")
def observations_new():
    return render_template("observations_new.html")


@main.route("/observations/export/csv")
def export_observations_csv():
    search = request.args.get("q", "").strip()

    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    params = []
    where_clause = ""

    if search:
        where_clause = """
            WHERE (
                o.scientific_name LIKE %s
                OR sp.vernacular_name LIKE %s
                OR r.asset_name LIKE %s
                OR d.dataset_name LIKE %s
            )
        """
        params = [
            f"%{search}%",
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        ]

    cursor.execute(
        f"""
        SELECT
            o.occurrence_id,
            o.scientific_name,
            sp.vernacular_name,
            r.asset_name AS reserve_name,
            o.event_date,
            YEAR(o.event_date) AS year,
            d.dataset_name,
            o.decimal_latitude,
            o.decimal_longitude
        FROM occurrences o
        LEFT JOIN species sp ON o.species_id = sp.species_id
        LEFT JOIN reserves r ON o.reserve_id = r.reserve_id
        LEFT JOIN datasets d ON o.dataset_id = d.dataset_id
        {where_clause}
        ORDER BY o.event_date DESC, o.scientific_name
        """,
        params,
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Occurrence ID",
        "Scientific Name",
        "Common Name",
        "Reserve",
        "Event Date",
        "Year",
        "Dataset",
        "Latitude",
        "Longitude"
    ])

    for row in rows:
        writer.writerow([
            row["occurrence_id"],
            row["scientific_name"],
            row["vernacular_name"],
            row["reserve_name"],
            row["event_date"],
            row["year"],
            row["dataset_name"],
            row["decimal_latitude"],
            row["decimal_longitude"],
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=observations_export.csv"
        }
    )


@main.route("/observations/export/xlsx")
def export_observations_xlsx():
    search = request.args.get("q", "").strip()

    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    params = []
    where_clause = ""

    if search:
        where_clause = """
            WHERE (
                o.scientific_name LIKE %s
                OR sp.vernacular_name LIKE %s
                OR r.asset_name LIKE %s
                OR d.dataset_name LIKE %s
            )
        """
        params = [
            f"%{search}%",
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        ]

    cursor.execute(
        f"""
        SELECT
            o.occurrence_id,
            o.scientific_name,
            sp.vernacular_name,
            r.asset_name AS reserve_name,
            o.event_date,
            YEAR(o.event_date) AS year,
            d.dataset_name,
            o.decimal_latitude,
            o.decimal_longitude
        FROM occurrences o
        LEFT JOIN species sp ON o.species_id = sp.species_id
        LEFT JOIN reserves r ON o.reserve_id = r.reserve_id
        LEFT JOIN datasets d ON o.dataset_id = d.dataset_id
        {where_clause}
        ORDER BY o.event_date DESC, o.scientific_name
        """,
        params,
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    df = pd.DataFrame(rows)

    if not df.empty:
        df.columns = [
            "Occurrence ID",
            "Scientific Name",
            "Common Name",
            "Reserve",
            "Event Date",
            "Year",
            "Dataset",
            "Latitude",
            "Longitude"
        ]

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Observations")

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="observations_export.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

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
    """
    Show species flagged as at-risk based on observation data.
    """

    at_risk_list = []
    error = None

    recent_year_cutoff = 2015

    search = request.args.get("q", "").strip()
    priority_filter = request.args.get("priority", "").strip()

    try:
        conn = get_connection()

        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    sp.species_id,
                    sp.scientific_name,
                    sp.vernacular_name,
                    COUNT(o.occurrence_id) AS obs_count,
                    COUNT(DISTINCT o.reserve_id) AS reserve_count,
                    MAX(YEAR(o.event_date)) AS latest_year
                FROM species sp
                LEFT JOIN occurrences o
                    ON o.species_id = sp.species_id
                GROUP BY
                    sp.species_id,
                    sp.scientific_name,
                    sp.vernacular_name
                HAVING
                    obs_count > 0
                    AND (
                        reserve_count = 1
                        OR obs_count <= 3
                        OR latest_year < %s
                    )
                ORDER BY sp.scientific_name
                """,
                [recent_year_cutoff],
            )

            rows = cursor.fetchall()

            cursor.execute(
                """
                SELECT scientific_name, vernacular_name
                FROM species
                WHERE scientific_name IS NOT NULL
                ORDER BY scientific_name
                """
            )

            name_rows = cursor.fetchall()

            name_options = []

            for row in name_rows:
                if row["scientific_name"]:
                    name_options.append(row["scientific_name"])

                if row["vernacular_name"]:
                    name_options.append(row["vernacular_name"])

        conn.close()

        for row in rows:

            reasons = []
            criteria_count = 0

            if row["reserve_count"] == 1:
                reasons.append("Only found in 1 reserve")
                criteria_count += 1

            if row["obs_count"] <= 3:
                reasons.append(f"Only {row['obs_count']} observation(s)")
                criteria_count += 1

            if (
                row["latest_year"] is not None
                and row["latest_year"] < recent_year_cutoff
            ):
                reasons.append(
                    f"No recent observations (since {row['latest_year']})"
                )
                criteria_count += 1

            if criteria_count >= 3:
                priority = "High"
            elif criteria_count == 2:
                priority = "Medium"
            else:
                priority = "Low"

            if search:
                combined_text = (
                    f"{row['scientific_name']} "
                    f"{row['vernacular_name'] or ''}"
                ).lower()

                if search.lower() not in combined_text:
                    continue

            if priority_filter and priority != priority_filter:
                continue

            at_risk_list.append({
                "species_id": row["species_id"],
                "scientific_name": row["scientific_name"],
                "vernacular_name": row["vernacular_name"],
                "alert_reason": "; ".join(reasons),
                "alerted_before": "No",
                "previous_alerts": 0,
                "priority": priority,
            })

        priority_order = {
            "High": 0,
            "Medium": 1,
            "Low": 2
        }

        at_risk_list.sort(
            key=lambda x: (
                priority_order[x["priority"]],
                x["scientific_name"]
            )
        )

    except Exception as exc:
        error = str(exc)
        name_options = []

    return render_template(
        "at_risk.html",
        at_risk_list=at_risk_list,
        search=search,
        priority_filter=priority_filter,
        name_options=name_options,
        error=error,
    )


# =========================
# Admin Controls
# =========================

@main.route("/admin_controls")
def admin_controls():
    return render_template("admin_controls.html")


# =========================
# Placeholder Pages
# =========================

@main.route("/flora_dashboard")
@main.route("/fauna_dashboard")
@main.route("/report")
@main.route("/settings")
def placeholder_page():
    return render_template("home.html")


# =========================
# Map
# =========================

@main.route("/map")
def map_view():
    species = request.args.get("species", "").strip()
    date = request.args.get("date", "").strip()
    data = []
    error = None

    try:
        conn = get_connection()

        with conn.cursor() as cursor:
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

        conn.close()

    except Exception as exc:
        error = str(exc)

    return render_template(
        "map.html",
        data=data,
        species=species,
        date=date,
        error=error,
    )


# =========================
# Database Test
# =========================

@main.route("/db-test")
def db_test():
    try:
        conn = get_connection()

        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 AS status")
            result = cursor.fetchone()

        conn.close()

        return f"Database connected successfully: {result}"

    except Exception as exc:
        return f"Database connection failed: {exc}"


# =========================
# Traits
# =========================

@main.route("/traits_findby")
def traits_findby():
    selected_groups = [
        value.strip()
        for value in request.args.getlist("trait_group")
        if value.strip()
    ]
    selected_traits = [
        value.strip()
        for value in request.args.getlist("trait")
        if value.strip()
    ]
    selected_values = [
        value.strip()
        for value in request.args.getlist("trait_value")
        if value.strip()
    ]
    selected_value_filters = {}
    for value in selected_values:
        if ":::" in value:
            trait_name, trait_value = value.split(":::", 1)
            selected_value_filters.setdefault(trait_name, []).append(trait_value)
        else:
            for trait_name in selected_traits:
                selected_value_filters.setdefault(trait_name, []).append(value)

    per_page_options = [10, 20, 50, 75]
    try:
        per_page = int(request.args.get("per_page", 50))
    except ValueError:
        per_page = 50
    if per_page not in per_page_options:
        per_page = 50

    try:
        page_num = int(request.args.get("page", 1))
    except ValueError:
        page_num = 1
    page_num = max(1, page_num)

    trait_groups = []
    trait_options = []
    value_options = []
    matching_species = []
    total_results = 0
    total_pages = 1
    pagination_pages = []
    result_start = 0
    result_end = 0
    error = None

    def build_findby_url(page=None, page_size=None):
        params = []
        for value in selected_groups:
            params.append(("trait_group", value))
        for value in selected_traits:
            params.append(("trait", value))
        for value in selected_values:
            params.append(("trait_value", value))
        params.append(("per_page", page_size if page_size is not None else per_page))
        params.append(("page", page if page is not None else page_num))
        return f"{url_for('main.traits_findby')}?{urlencode(params)}"

    try:
        conn = get_connection()

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT trait_type_name, COUNT(*) AS trait_count
                FROM traits
                WHERE of_interest = 1
                GROUP BY trait_type_name
                ORDER BY trait_type_name
                """
            )
            trait_groups = cursor.fetchall()

            cursor.execute(
                """
                SELECT trait_id, trait_type_name, trait_name, trait_label
                FROM traits
                WHERE of_interest = 1
                ORDER BY column_number, trait_type_name, trait_name
                """
            )
            trait_options = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    t.trait_name,
                    COALESCE(
                        NULLIF(TRIM(stj.working_value), ''),
                        NULLIF(TRIM(stj.original_value), ''),
                        '(blank)'
                    ) AS trait_value,
                    COUNT(DISTINCT stj.species_id) AS species_count
                FROM traits t
                JOIN species_traits_junction stj ON stj.trait_id = t.trait_id
                WHERE t.of_interest = 1
                GROUP BY t.trait_name, trait_value
                ORDER BY t.trait_name, species_count DESC, trait_value
                """
            )
            value_options = cursor.fetchall()

            if selected_traits:
                required_value_filters = {
                    trait_name: values
                    for trait_name, values in selected_value_filters.items()
                    if trait_name in selected_traits and values
                }
                filter_traits = list(required_value_filters.keys()) or selected_traits
                filter_trait_placeholders = ", ".join(["%s"] * len(filter_traits))
                match_where = [f"match_trait.trait_name IN ({filter_trait_placeholders})"]
                value_expression = """
                        COALESCE(
                            NULLIF(TRIM(match_stj.working_value), ''),
                            NULLIF(TRIM(match_stj.original_value), ''),
                            '(blank)'
                        )
                        """
                match_having = []
                having_params = []

                for trait_name, values in required_value_filters.items():
                    match_having.append(
                        f"""
                        SUM(
                            CASE
                                WHEN match_trait.trait_name = %s
                                AND {value_expression} IN ({', '.join(['%s'] * len(values))})
                                THEN 1
                                ELSE 0
                            END
                        ) > 0
                        """
                    )
                    having_params.append(trait_name)
                    having_params.extend(values)

                match_params = filter_traits + having_params
                having_clause = f"HAVING {' AND '.join(match_having)}" if match_having else ""

                cursor.execute(
                    f"""
                    SELECT COUNT(*) AS total
                    FROM (
                        SELECT sp.species_id
                        FROM species_traits_junction match_stj
                        JOIN traits match_trait ON match_trait.trait_id = match_stj.trait_id
                        JOIN species sp ON sp.species_id = match_stj.species_id
                        WHERE {' AND '.join(match_where)}
                        GROUP BY sp.species_id
                        {having_clause}
                    ) matched_species
                    """,
                    match_params,
                )
                total_results = cursor.fetchone()["total"]
                total_pages = max(1, -(-total_results // per_page))
                page_num = min(page_num, total_pages)
                offset = (page_num - 1) * per_page

                cursor.execute(
                    f"""
                    SELECT sp.species_id, sp.scientific_name, sp.vernacular_name
                    FROM species_traits_junction match_stj
                    JOIN traits match_trait ON match_trait.trait_id = match_stj.trait_id
                    JOIN species sp ON sp.species_id = match_stj.species_id
                    WHERE {' AND '.join(match_where)}
                    GROUP BY sp.species_id, sp.scientific_name, sp.vernacular_name
                    {having_clause}
                    ORDER BY sp.scientific_name
                    LIMIT %s OFFSET %s
                    """,
                    match_params + [per_page, offset],
                )
                species_rows = cursor.fetchall()
                matching_species = [
                    {
                        "species_id": row["species_id"],
                        "scientific_name": row["scientific_name"],
                        "vernacular_name": row["vernacular_name"],
                        "trait_values": {trait_name: [] for trait_name in selected_traits},
                    }
                    for row in species_rows
                ]

                species_ids = [row["species_id"] for row in species_rows]

                if species_ids:
                    display_value_expression = """
                        COALESCE(
                            NULLIF(TRIM(stj.working_value), ''),
                            NULLIF(TRIM(stj.original_value), ''),
                            '(blank)'
                        )
                    """
                    display_filter_clause = ""
                    display_filter_params = []

                    if required_value_filters:
                        filtered_trait_names = list(required_value_filters.keys())
                        display_filter_parts = [
                            f"t.trait_name NOT IN ({', '.join(['%s'] * len(filtered_trait_names))})"
                        ]
                        display_filter_params.extend(filtered_trait_names)

                        for trait_name, values in required_value_filters.items():
                            display_filter_parts.append(
                                f"""
                                (
                                    t.trait_name = %s
                                    AND {display_value_expression} IN ({', '.join(['%s'] * len(values))})
                                )
                                """
                            )
                            display_filter_params.append(trait_name)
                            display_filter_params.extend(values)

                        display_filter_clause = f"AND ({' OR '.join(display_filter_parts)})"

                    cursor.execute(
                        f"""
                    SELECT
                        sp.species_id,
                        sp.scientific_name,
                        sp.vernacular_name,
                        t.trait_name,
                        {display_value_expression} AS trait_value
                    FROM species_traits_junction stj
                    JOIN traits t ON t.trait_id = stj.trait_id
                    JOIN species sp ON sp.species_id = stj.species_id
                    WHERE sp.species_id IN ({', '.join(['%s'] * len(species_ids))})
                    AND t.trait_name IN ({', '.join(['%s'] * len(selected_traits))})
                    {display_filter_clause}
                    GROUP BY
                        sp.species_id,
                        sp.scientific_name,
                        sp.vernacular_name,
                        t.trait_name,
                        trait_value
                    ORDER BY sp.scientific_name, t.trait_name, trait_value
                    """,
                        species_ids + selected_traits + display_filter_params,
                    )
                    species_value_rows = cursor.fetchall()
                    species_map = {row["species_id"]: row for row in matching_species}

                    for row in species_value_rows:
                        species_map[row["species_id"]]["trait_values"].setdefault(row["trait_name"], [])
                        species_map[row["species_id"]]["trait_values"][row["trait_name"]].append(row["trait_value"])

        conn.close()
    except Exception as exc:
        error = str(exc)

    if total_results:
        result_start = ((page_num - 1) * per_page) + 1
        result_end = min(page_num * per_page, total_results)

    pagination_start = max(1, page_num - 1)
    pagination_end = min(total_pages, pagination_start + 2)
    pagination_start = max(1, pagination_end - 2)
    pagination_pages = list(range(pagination_start, pagination_end + 1))

    return render_template(
        "traits_findby.html",
        trait_groups=trait_groups,
        trait_options=trait_options,
        value_options=value_options,
        matching_species=matching_species,
        total_results=total_results,
        total_pages=total_pages,
        page_num=page_num,
        per_page=per_page,
        per_page_options=per_page_options,
        pagination_pages=pagination_pages,
        result_start=result_start,
        result_end=result_end,
        build_findby_url=build_findby_url,
        selected_groups=selected_groups,
        selected_traits=selected_traits,
        selected_values=selected_values,
        error=error,
    )


@main.route("/traits")
def traits():
    search = request.args.get("q", "").strip()
    rows = []
    trait_options = []
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

            params = []
            where_clause = ""

            if search:
                where_clause = "AND trait_name LIKE %s"
                params = [f"%{search}%"]

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

    return render_template(
        "traits.html",
        traits=rows,
        trait_options=trait_options,
        search=search,
        error=error,
    )


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

@main.route("/query_builder", methods=["GET", "POST"])
def query_builder():
    filters = {key: "" for key in QUERY_FILTERS}

    for key in filters:
        filters[key] = request.args.get(key, "").strip()

    try:
        per_page = int(request.args.get("per_page", 25))
    except ValueError:
        per_page = 25

    try:
        page_num = int(request.args.get("page", 1))
    except ValueError:
        page_num = 1

    page_num = max(1, page_num)
    offset = (page_num - 1) * per_page

    results = []
    map_points = []
    total_results = 0
    total_pages = 1
    error = None

    has_filters = any(value for value in filters.values())

    context = {
        "results": results,
        "map_points": map_points,
        "filters": filters,
        "total_results": total_results,
        "page_num": page_num,
        "total_pages": total_pages,
        "per_page": per_page,
        "username": "Development user",
        "is_admin": False,
        "error": error,
    }

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
            where.append("sp.endangered_status_code LIKE %s")
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

        where_clause = "WHERE " + " AND ".join(where) if where else ""

        # Map points should show even before searching
        cursor.execute(
            f"""
            SELECT
                o.scientific_name,
                sp.vernacular_name,
                r.asset_name AS reserve_name,
                d.dataset_name,
                o.event_date,
                o.decimal_latitude,
                o.decimal_longitude
            FROM occurrences o
            LEFT JOIN species sp ON o.species_id = sp.species_id
            LEFT JOIN reserves r ON o.reserve_id = r.reserve_id
            LEFT JOIN datasets d ON o.dataset_id = d.dataset_id
            {where_clause}
            {"AND" if where_clause else "WHERE"} o.decimal_latitude IS NOT NULL
            AND o.decimal_longitude IS NOT NULL
            LIMIT 500
            """,
            params,
        )

        map_rows = cursor.fetchall()

        for row in map_rows:
            map_points.append({
                "scientific_name": row["scientific_name"] or "Unknown species",
                "vernacular_name": row["vernacular_name"] or "",
                "reserve_name": row["reserve_name"] or "N/A",
                "dataset_name": row["dataset_name"] or "N/A",
                "event_date": str(row["event_date"] or "N/A"),
                "decimal_latitude": float(row["decimal_latitude"]),
                "decimal_longitude": float(row["decimal_longitude"]),
            })

        if has_filters:
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
            total_pages = max(1, -(-total_results // per_page))
            page_num = min(page_num, total_pages)
            offset = (page_num - 1) * per_page

            cursor.execute(
                f"""
                SELECT
                    o.occurrence_id,
                    o.scientific_name,
                    sp.vernacular_name,
                    r.asset_name AS reserve_name,
                    YEAR(o.event_date) AS year,
                    o.event_date,
                    d.dataset_name,
                    o.decimal_latitude,
                    o.decimal_longitude,
                    sp.native_flag,
                    sp.endangered_status_code
                FROM occurrences o
                LEFT JOIN species sp ON o.species_id = sp.species_id
                LEFT JOIN reserves r ON o.reserve_id = r.reserve_id
                LEFT JOIN datasets d ON o.dataset_id = d.dataset_id
                {where_clause}
                ORDER BY o.event_date DESC, o.scientific_name
                LIMIT %s OFFSET %s
                """,
                params + [per_page, offset],
            )

            results = cursor.fetchall()

        cursor.close()
        conn.close()

        context.update({
            "results": results,
            "map_points": map_points,
            "total_results": total_results,
            "page_num": page_num,
            "total_pages": total_pages,
            "per_page": per_page,
            "error": None,
        })

    except Exception as exc:
        context["error"] = str(exc)

    return render_template("query_builder.html", **context)


# =========================
# Traits Export XLSX
# =========================

@main.route("/traits/export/xlsx")
def export_traits_xlsx():

    search = request.args.get("q", "").strip()

    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    sql = """
        SELECT
            trait_type_name,
            trait_name,
            trait_label,
            trait_unit,
            trait_type
        FROM traits
        WHERE of_interest = 1
    """

    params = []

    if search:
        sql += """
            AND (
                trait_name LIKE %s
                OR trait_label LIKE %s
                OR trait_type_name LIKE %s
            )
        """

        params.extend([
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        ])

    sql += """
        ORDER BY
            column_number,
            trait_type_name,
            trait_name
    """

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    df = pd.DataFrame(rows)

    df.columns = [
        "Trait Type Name",
        "Trait Name",
        "Trait Label",
        "Trait Unit",
        "Trait Type"
    ]

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Traits"
        )

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="traits_export.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# =========================
# Traits Export CSV
# =========================

@main.route("/traits/export/csv")
def export_traits_csv():

    search = request.args.get("q", "").strip()

    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    sql = """
        SELECT
            trait_type_name,
            trait_name,
            trait_label,
            trait_unit,
            trait_type
        FROM traits
        WHERE of_interest = 1
    """

    params = []

    if search:
        sql += """
            AND (
                trait_name LIKE %s
                OR trait_label LIKE %s
                OR trait_type_name LIKE %s
            )
        """

        params.extend([
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        ])

    sql += """
        ORDER BY
            column_number,
            trait_type_name,
            trait_name
    """

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "Trait Type Name",
        "Trait Name",
        "Trait Label",
        "Trait Unit",
        "Trait Type"
    ])

    for row in rows:
        writer.writerow([
            row["trait_type_name"],
            row["trait_name"],
            row["trait_label"],
            row["trait_unit"],
            row["trait_type"]
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=traits_export.csv"
        }
    )


# =========================
# Traits FindBy Export CSV
# =========================

@main.route("/traits_findby/export/csv")
def export_traits_findby_csv():

    selected_traits = request.args.getlist("trait")
    selected_values = request.args.getlist("trait_value")

    if not selected_traits:
        return Response(
            "No traits selected",
            mimetype="text/plain"
        )

    selected_value_filters = {}

    for value in selected_values:
        if ":::" in value:
            trait_name, trait_value = value.split(":::", 1)
            selected_value_filters.setdefault(trait_name, []).append(trait_value)

    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    required_value_filters = {
        trait_name: values
        for trait_name, values in selected_value_filters.items()
        if trait_name in selected_traits and values
    }

    filter_traits = list(required_value_filters.keys()) or selected_traits

    filter_trait_placeholders = ", ".join(["%s"] * len(filter_traits))

    value_expression = """
        COALESCE(
            NULLIF(TRIM(match_stj.working_value), ''),
            NULLIF(TRIM(match_stj.original_value), ''),
            '(blank)'
        )
    """

    match_where = [
        f"match_trait.trait_name IN ({filter_trait_placeholders})"
    ]

    match_having = []
    having_params = []

    for trait_name, values in required_value_filters.items():

        match_having.append(
            f"""
            SUM(
                CASE
                    WHEN match_trait.trait_name = %s
                    AND {value_expression} IN ({', '.join(['%s'] * len(values))})
                    THEN 1
                    ELSE 0
                END
            ) > 0
            """
        )

        having_params.append(trait_name)
        having_params.extend(values)

    having_clause = (
        f"HAVING {' AND '.join(match_having)}"
        if match_having else ""
    )

    match_params = filter_traits + having_params

    cursor.execute(
        f"""
        SELECT
            sp.species_id,
            sp.scientific_name
        FROM species_traits_junction match_stj
        JOIN traits match_trait
            ON match_trait.trait_id = match_stj.trait_id
        JOIN species sp
            ON sp.species_id = match_stj.species_id
        WHERE {' AND '.join(match_where)}
        GROUP BY sp.species_id, sp.scientific_name
        {having_clause}
        ORDER BY sp.scientific_name
        """,
        match_params,
    )

    species_rows = cursor.fetchall()

    species_ids = [row["species_id"] for row in species_rows]

    if not species_ids:
        return Response(
            "No matching species",
            mimetype="text/plain"
        )

    cursor.execute(
        f"""
        SELECT
            sp.species_id,
            t.trait_name,
            COALESCE(
                NULLIF(TRIM(stj.working_value), ''),
                NULLIF(TRIM(stj.original_value), ''),
                '(blank)'
            ) AS trait_value
        FROM species_traits_junction stj
        JOIN traits t
            ON t.trait_id = stj.trait_id
        JOIN species sp
            ON sp.species_id = stj.species_id
        WHERE sp.species_id IN ({', '.join(['%s'] * len(species_ids))})
        AND t.trait_name IN ({', '.join(['%s'] * len(selected_traits))})
        ORDER BY sp.scientific_name
        """,
        species_ids + selected_traits,
    )

    value_rows = cursor.fetchall()

    species_map = {}

    for row in species_rows:
        species_map[row["species_id"]] = {
            "Species Name": row["scientific_name"]
        }

        for trait in selected_traits:
            species_map[row["species_id"]][trait] = ""

    for row in value_rows:

        current = species_map[row["species_id"]][row["trait_name"]]

        if current:
            species_map[row["species_id"]][row["trait_name"]] += ", " + row["trait_value"]
        else:
            species_map[row["species_id"]][row["trait_name"]] = row["trait_value"]

    output = io.StringIO()

    writer = csv.writer(output)

    headers = ["Species Name"] + selected_traits

    writer.writerow(headers)

    for species in species_map.values():
        writer.writerow([species.get(h, "") for h in headers])

    cursor.close()
    conn.close()

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=traits_findby_export.csv"
        }
    )


# =========================
# Traits FindBy Export XLSX
# =========================

@main.route("/traits_findby/export/xlsx")
def export_traits_findby_xlsx():

    selected_traits = request.args.getlist("trait")
    selected_values = request.args.getlist("trait_value")

    if not selected_traits:
        return Response(
            "No traits selected",
            mimetype="text/plain"
        )

    selected_value_filters = {}

    for value in selected_values:
        if ":::" in value:
            trait_name, trait_value = value.split(":::", 1)
            selected_value_filters.setdefault(trait_name, []).append(trait_value)

    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    required_value_filters = {
        trait_name: values
        for trait_name, values in selected_value_filters.items()
        if trait_name in selected_traits and values
    }

    filter_traits = list(required_value_filters.keys()) or selected_traits

    filter_trait_placeholders = ", ".join(["%s"] * len(filter_traits))

    value_expression = """
        COALESCE(
            NULLIF(TRIM(match_stj.working_value), ''),
            NULLIF(TRIM(match_stj.original_value), ''),
            '(blank)'
        )
    """

    match_where = [
        f"match_trait.trait_name IN ({filter_trait_placeholders})"
    ]

    match_having = []
    having_params = []

    for trait_name, values in required_value_filters.items():

        match_having.append(
            f"""
            SUM(
                CASE
                    WHEN match_trait.trait_name = %s
                    AND {value_expression} IN ({', '.join(['%s'] * len(values))})
                    THEN 1
                    ELSE 0
                END
            ) > 0
            """
        )

        having_params.append(trait_name)
        having_params.extend(values)

    having_clause = (
        f"HAVING {' AND '.join(match_having)}"
        if match_having else ""
    )

    match_params = filter_traits + having_params

    cursor.execute(
        f"""
        SELECT
            sp.species_id,
            sp.scientific_name
        FROM species_traits_junction match_stj
        JOIN traits match_trait
            ON match_trait.trait_id = match_stj.trait_id
        JOIN species sp
            ON sp.species_id = match_stj.species_id
        WHERE {' AND '.join(match_where)}
        GROUP BY sp.species_id, sp.scientific_name
        {having_clause}
        ORDER BY sp.scientific_name
        """,
        match_params,
    )

    species_rows = cursor.fetchall()

    species_ids = [row["species_id"] for row in species_rows]

    cursor.execute(
        f"""
        SELECT
            sp.species_id,
            t.trait_name,
            COALESCE(
                NULLIF(TRIM(stj.working_value), ''),
                NULLIF(TRIM(stj.original_value), ''),
                '(blank)'
            ) AS trait_value
        FROM species_traits_junction stj
        JOIN traits t
            ON t.trait_id = stj.trait_id
        JOIN species sp
            ON sp.species_id = stj.species_id
        WHERE sp.species_id IN ({', '.join(['%s'] * len(species_ids))})
        AND t.trait_name IN ({', '.join(['%s'] * len(selected_traits))})
        ORDER BY sp.scientific_name
        """,
        species_ids + selected_traits,
    )

    value_rows = cursor.fetchall()

    species_map = {}

    for row in species_rows:

        species_map[row["species_id"]] = {
            "Species Name": row["scientific_name"]
        }

        for trait in selected_traits:
            species_map[row["species_id"]][trait] = ""

    for row in value_rows:

        current = species_map[row["species_id"]][row["trait_name"]]

        if current:
            species_map[row["species_id"]][row["trait_name"]] += ", " + row["trait_value"]
        else:
            species_map[row["species_id"]][row["trait_name"]] = row["trait_value"]

    df = pd.DataFrame(species_map.values())

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Trait Search"
        )

    output.seek(0)

    cursor.close()
    conn.close()

    return send_file(
        output,
        as_attachment=True,
        download_name="traits_findby_export.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# Species Page Export CSV
@main.route("/species/export/csv")
def export_species_csv():

    search = request.args.get("q", "").strip()
    family_filter = request.args.get("family", "").strip()

    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    sql = """
        SELECT
            sp.taxonomy_id,
            sp.scientific_name,
            sp.vernacular_name,
            sp.native_flag,
            sp.endangered_status_code,
            tx.family
        FROM species sp
        LEFT JOIN taxonomy tx ON tx.taxonomy_id = sp.taxonomy_id
        WHERE 1=1
    """

    params = []

    if search:
        sql += """
            AND (
                sp.scientific_name LIKE %s
                OR sp.vernacular_name LIKE %s
            )
        """
        params.extend([f"%{search}%", f"%{search}%"])

    if family_filter:
        sql += " AND tx.family = %s"
        params.append(family_filter)

    sql += " ORDER BY sp.scientific_name"

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Taxonomy ID",
        "Scientific Name",
        "Vernacular Name",
        "Native Flag",
        "Endangered Status",
        "Family"
    ])

    for row in rows:
        writer.writerow([
            row["taxonomy_id"],
            row["scientific_name"],
            row["vernacular_name"],
            row["native_flag"],
            row["endangered_status_code"],
            row["family"],
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=species_export.csv"
        }
    )


# Species Page Export XLSX
@main.route("/species/export/xlsx")
def export_species_xlsx():

    search = request.args.get("q", "").strip()
    family_filter = request.args.get("family", "").strip()

    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    sql = """
        SELECT
            sp.taxonomy_id,
            sp.scientific_name,
            sp.vernacular_name,
            sp.native_flag,
            sp.endangered_status_code,
            tx.family
        FROM species sp
        LEFT JOIN taxonomy tx ON tx.taxonomy_id = sp.taxonomy_id
        WHERE 1=1
    """

    params = []

    if search:
        sql += """
            AND (
                sp.scientific_name LIKE %s
                OR sp.vernacular_name LIKE %s
            )
        """
        params.extend([f"%{search}%", f"%{search}%"])

    if family_filter:
        sql += " AND tx.family = %s"
        params.append(family_filter)

    sql += " ORDER BY sp.scientific_name"

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    df = pd.DataFrame(rows)

    df.columns = [
        "Taxonomy ID",
        "Scientific Name",
        "Vernacular Name",
        "Native Flag",
        "Endangered Status",
        "Family"
    ]

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Species")

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="species_export.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# Species New Page Export CSV
@main.route("/species_new/export/csv")
def export_species_new_csv():

    search = request.args.get("q", "").strip()
    family_filter = request.args.get("family", "").strip()

    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    sql = """
        SELECT
            sp.species_id,
            sp.taxonomy_id,
            sp.scientific_name,
            sp.vernacular_name,
            sp.native_flag,
            sp.endangered_status_code,
            tx.family
        FROM species sp
        LEFT JOIN taxonomy tx ON tx.taxonomy_id = sp.taxonomy_id
        WHERE 1=1
    """

    params = []

    if search:
        sql += """
            AND (
                sp.scientific_name LIKE %s
                OR sp.vernacular_name LIKE %s
            )
        """
        params.extend([f"%{search}%", f"%{search}%"])

    if family_filter:
        sql += " AND tx.family = %s"
        params.append(family_filter)

    sql += " ORDER BY sp.species_id DESC"

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Species ID",
        "Taxonomy ID",
        "Scientific Name",
        "Vernacular Name",
        "Native Flag",
        "Endangered Status",
        "Family"
    ])

    for row in rows:
        writer.writerow([
            row["species_id"],
            row["taxonomy_id"],
            row["scientific_name"],
            row["vernacular_name"],
            row["native_flag"],
            row["endangered_status_code"],
            row["family"],
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=species_new_export.csv"
        }
    )


# Species New Page Export XLSX
@main.route("/species_new/export/xlsx")
def export_species_new_xlsx():

    search = request.args.get("q", "").strip()
    family_filter = request.args.get("family", "").strip()

    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    sql = """
        SELECT
            sp.species_id,
            sp.taxonomy_id,
            sp.scientific_name,
            sp.vernacular_name,
            sp.native_flag,
            sp.endangered_status_code,
            tx.family
        FROM species sp
        LEFT JOIN taxonomy tx ON tx.taxonomy_id = sp.taxonomy_id
        WHERE 1=1
    """

    params = []

    if search:
        sql += """
            AND (
                sp.scientific_name LIKE %s
                OR sp.vernacular_name LIKE %s
            )
        """
        params.extend([f"%{search}%", f"%{search}%"])

    if family_filter:
        sql += " AND tx.family = %s"
        params.append(family_filter)

    sql += " ORDER BY sp.species_id DESC"

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    df = pd.DataFrame(rows)

    df.columns = [
        "Species ID",
        "Taxonomy ID",
        "Scientific Name",
        "Vernacular Name",
        "Native Flag",
        "Endangered Status",
        "Family"
    ]

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="New Species")

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="species_new_export.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# At Risk Page Export CSV
@main.route("/at_risk/export/csv")
def export_at_risk_csv():

    search = request.args.get("q", "").strip()
    priority_filter = request.args.get("priority", "").strip()

    recent_year_cutoff = 2015

    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute(
        """
        SELECT
            sp.species_id,
            sp.scientific_name,
            sp.vernacular_name,
            COUNT(o.occurrence_id) AS obs_count,
            COUNT(DISTINCT o.reserve_id) AS reserve_count,
            MAX(YEAR(o.event_date)) AS latest_year
        FROM species sp
        LEFT JOIN occurrences o
            ON o.species_id = sp.species_id
        GROUP BY sp.species_id, sp.scientific_name, sp.vernacular_name
        HAVING
            obs_count > 0
            AND (
                reserve_count = 1
                OR obs_count <= 3
                OR latest_year < %s
            )
        ORDER BY sp.scientific_name
        """,
        [recent_year_cutoff],
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Scientific Name",
        "Common Name",
        "Alert Reason",
        "Priority"
    ])

    for row in rows:

        reasons = []
        criteria = 0

        if row["reserve_count"] == 1:
            reasons.append("Only 1 reserve")
            criteria += 1

        if row["obs_count"] <= 3:
            reasons.append("Low observations")
            criteria += 1

        if row["latest_year"] and row["latest_year"] < recent_year_cutoff:
            reasons.append("No recent observations")
            criteria += 1

        if criteria >= 3:
            priority = "High"
        elif criteria == 2:
            priority = "Medium"
        else:
            priority = "Low"

        if search:
            text = f"{row['scientific_name']} {row['vernacular_name'] or ''}".lower()
            if search.lower() not in text:
                continue

        if priority_filter and priority != priority_filter:
            continue

        writer.writerow([
            row["scientific_name"],
            row["vernacular_name"],
            "; ".join(reasons),
            priority
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=at_risk_species.csv"
        }
    )


# At Risk Species Page Export XLSX
@main.route("/at_risk/export/xlsx")
def export_at_risk_xlsx():

    search = request.args.get("q", "").strip()
    priority_filter = request.args.get("priority", "").strip()

    recent_year_cutoff = 2015

    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute(
        """
        SELECT
            sp.species_id,
            sp.scientific_name,
            sp.vernacular_name,
            COUNT(o.occurrence_id) AS obs_count,
            COUNT(DISTINCT o.reserve_id) AS reserve_count,
            MAX(YEAR(o.event_date)) AS latest_year
        FROM species sp
        LEFT JOIN occurrences o
            ON o.species_id = sp.species_id
        GROUP BY sp.species_id, sp.scientific_name, sp.vernacular_name
        HAVING
            obs_count > 0
            AND (
                reserve_count = 1
                OR obs_count <= 3
                OR latest_year < %s
            )
        ORDER BY sp.scientific_name
        """,
        [recent_year_cutoff],
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    export_data = []

    for row in rows:

        reasons = []
        criteria = 0

        if row["reserve_count"] == 1:
            reasons.append("Only 1 reserve")
            criteria += 1

        if row["obs_count"] <= 3:
            reasons.append("Low observations")
            criteria += 1

        if row["latest_year"] and row["latest_year"] < recent_year_cutoff:
            reasons.append("No recent observations")
            criteria += 1

        if criteria >= 3:
            priority = "High"
        elif criteria == 2:
            priority = "Medium"
        else:
            priority = "Low"

        if search:
            text = f"{row['scientific_name']} {row['vernacular_name'] or ''}".lower()
            if search.lower() not in text:
                continue

        if priority_filter and priority != priority_filter:
            continue

        export_data.append({
            "Scientific Name": row["scientific_name"],
            "Common Name": row["vernacular_name"],
            "Alert Reason": "; ".join(reasons),
            "Priority": priority
        })

    df = pd.DataFrame(export_data)

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="At Risk Species")

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="at_risk_species.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )