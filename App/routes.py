import os
import socket
from urllib.parse import urlencode

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
