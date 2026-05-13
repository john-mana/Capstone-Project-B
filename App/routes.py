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


@main.route("/logout")
def logout():
    return redirect(url_for("main.login"))


# =========================
# Species
# =========================

@main.route("/species")
def species():
    species_list = []
    error = None

    search = request.args.get("q", "").strip()
    family_filter = request.args.get("family", "").strip()
    
    # pagination params
    per_page_options = [50, 100, 200]
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
    
    offset = (page_num - 1) * per_page
    total_count = 0

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

            # count total for pagination
            cursor.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM species sp
                LEFT JOIN taxonomy tx ON tx.taxonomy_id = sp.taxonomy_id
                {where_clause}
                """,
                params,
            )
            total_count = cursor.fetchone()["total"]

            # get paginated results
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
                LIMIT %s OFFSET %s
                """,
                params + [per_page, offset],
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

    total_pages = max(1, -(-total_count // per_page))
    page_num = min(page_num, total_pages)

    return render_template(
        "species.html",
        species_list=species_list,
        family_options=family_options,
        name_options=name_options,
        search=search,
        family_filter=family_filter,
        error=error,
        per_page=per_page,
        per_page_options=per_page_options,
        page_num=page_num,
        total_pages=total_pages,
        total_count=total_count,
    )


@main.route("/species_new")
def species_new():
    species_list = []
    error = None

    search = request.args.get("q", "").strip()
    family_filter = request.args.get("family", "").strip()

    # pagination
    per_page_options = [50, 100, 200]
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

    offset = (page_num - 1) * per_page
    total_count = 0

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
                SELECT COUNT(*) AS total
                FROM species sp
                LEFT JOIN taxonomy tx ON tx.taxonomy_id = sp.taxonomy_id
                {where_clause}
                """,
                params,
            )
            total_count = cursor.fetchone()["total"]

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
                LIMIT %s OFFSET %s
                """,
                params + [per_page, offset],
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

    total_pages = max(1, -(-total_count // per_page))
    page_num = min(page_num, total_pages)

    return render_template(
        "species_new.html",
        species_list=species_list,
        family_options=family_options,
        name_options=name_options,
        search=search,
        family_filter=family_filter,
        error=error,
        per_page=per_page,
        per_page_options=per_page_options,
        page_num=page_num,
        total_pages=total_pages,
        total_count=total_count,
    )



@main.route("/species_detail")
def species_detail():
    """
    Show full detail of one species:
      - taxonomy
      - native/vulnerable/at-risk status tags
      - traits with values
      - observation count and latest date
      - searchable species dropdown
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

            # dropdown search options
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

            # if searching by species name
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

            # if still no species selected
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

            # main species info with taxonomy
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

                # observation count and latest date
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

                # at-risk calculation
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

                # traits
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
    """
    Show species flagged as at-risk based on observation data.

    Criteria used:
      1. Few reserves: species in only 1 reserve
      2. Few observations: 3 or less total observations
      3. No recent records: no observations since 2015

    Priority is based on how many criteria a species hits:
      3 criteria = High, 2 = Medium, 1 = Low

    Filters:
      - native_filter: 'native', 'exotic', '' (all)
      - priority_filter: 'High', 'Medium', 'Low', '' (all)
    """
    at_risk_list = []
    error = None
    total_count = 0
    total_pages = 1

    native_filter = request.args.get("native", "").strip()
    priority_filter = request.args.get("priority", "").strip()

    # pagination
    per_page_options = [50, 100, 200]
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

    recent_year_cutoff = 2015

    try:
        conn = get_connection()

        with conn.cursor() as cursor:
            native_where = ""
            params = []

            if native_filter == "native":
                native_where = "WHERE sp.native_flag = 1"
            elif native_filter == "exotic":
                native_where = "WHERE sp.native_flag = 0"

            params.append(recent_year_cutoff)

            cursor.execute(
                f"""
                SELECT
                    sp.species_id,
                    sp.scientific_name,
                    sp.vernacular_name,
                    sp.native_flag,
                    sp.endangered_status_code,
                    COUNT(o.occurrence_id) AS obs_count,
                    COUNT(DISTINCT o.reserve_id) AS reserve_count,
                    MAX(YEAR(o.event_date)) AS latest_year
                FROM species sp
                LEFT JOIN occurrences o ON o.species_id = sp.species_id
                {native_where}
                GROUP BY sp.species_id, sp.scientific_name, sp.vernacular_name,
                         sp.native_flag, sp.endangered_status_code
                HAVING
                    obs_count > 0
                    AND (
                        reserve_count = 1
                        OR obs_count <= 3
                        OR latest_year < %s
                    )
                ORDER BY sp.scientific_name
                """,
                params,
            )
            rows = cursor.fetchall()

        conn.close()

        # process rows into full list
        full_list = []
        for row in rows:
            reasons = []
            criteria_count = 0

            if row["reserve_count"] == 1:
                reasons.append("Only found in 1 reserve")
                criteria_count += 1

            if row["obs_count"] <= 3:
                reasons.append(f"Only {row['obs_count']} observation(s)")
                criteria_count += 1

            if row["latest_year"] is not None and row["latest_year"] < recent_year_cutoff:
                reasons.append(f"No recent observations (since {row['latest_year']})")
                criteria_count += 1

            if criteria_count >= 3:
                priority = "High"
            elif criteria_count == 2:
                priority = "Medium"
            else:
                priority = "Low"

            # apply priority filter
            if priority_filter and priority != priority_filter:
                continue

            if row["native_flag"] == 1:
                native_label = "Native"
            elif row["native_flag"] == 0:
                native_label = "Exotic"
            else:
                native_label = "Unknown"

            full_list.append({
                "species_id": row["species_id"],
                "scientific_name": row["scientific_name"],
                "vernacular_name": row["vernacular_name"],
                "native_label": native_label,
                "endangered_status_code": row["endangered_status_code"],
                "alert_reason": "; ".join(reasons),
                "priority": priority,
            })

        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        full_list.sort(
            key=lambda x: (priority_order[x["priority"]], x["scientific_name"])
        )

        # paginate the full list
        total_count = len(full_list)
        total_pages = max(1, -(-total_count // per_page))
        page_num = min(page_num, total_pages)
        offset = (page_num - 1) * per_page
        at_risk_list = full_list[offset:offset + per_page]

    except Exception as exc:
        error = str(exc)

    return render_template(
        "at_risk.html",
        at_risk_list=at_risk_list,
        error=error,
        native_filter=native_filter,
        priority_filter=priority_filter,
        per_page=per_page,
        per_page_options=per_page_options,
        page_num=page_num,
        total_pages=total_pages,
        total_count=total_count,
    )


# =========================
# Taxonomy
# =========================

@main.route("/taxonomy_detail")
def taxonomy_detail():
    """
    Show taxonomy hierarchy and all species sharing this taxonomy_id.
    """
    taxonomy_id = request.args.get("taxonomy_id", "").strip()
    taxonomy = None
    species_in_taxonomy = []
    error = None

    if not taxonomy_id:
        return render_template(
            "taxonomy_detail.html",
            taxonomy=None,
            species_in_taxonomy=[],
            error="No taxonomy selected. Click a taxonomy ID from species pages.",
        )

    try:
        conn = get_connection()

        with conn.cursor() as cursor:
            # main taxonomy info
            cursor.execute(
                """
                SELECT
                    taxonomy_id,
                    kingdom,
                    phylum,
                    class_name,
                    order_name,
                    family,
                    genus,
                    species_epithet
                FROM taxonomy
                WHERE taxonomy_id = %s
                LIMIT 1
                """,
                [taxonomy_id],
            )
            taxonomy = cursor.fetchone()

            if taxonomy:
                # species linked to this taxonomy
                cursor.execute(
                    """
                    SELECT
                        species_id,
                        scientific_name,
                        vernacular_name,
                        native_flag,
                        endangered_status_code
                    FROM species
                    WHERE taxonomy_id = %s
                    ORDER BY scientific_name
                    """,
                    [taxonomy_id],
                )
                species_in_taxonomy = cursor.fetchall()

        conn.close()

    except Exception as exc:
        error = str(exc)

    return render_template(
        "taxonomy_detail.html",
        taxonomy=taxonomy,
        species_in_taxonomy=species_in_taxonomy,
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
                            '(blank)'
                        ) AS trait_value,
                        COALESCE(
                           NULLIF(TRIM(stj.original_value), ''),
                            '(blank)'
                        ) AS original_value,
                        COALESCE(
                            NULLIF(TRIM(stj.source_code), ''),
                            '-'
                        ) AS source_code,
                        COUNT(DISTINCT stj.species_id) AS species_count,
                        MAX(o.event_date) AS latest_observation_date
                    FROM species_traits_junction stj
                    LEFT JOIN occurrences o ON o.species_id = stj.species_id
                    WHERE stj.trait_id = %s
                    GROUP BY trait_value, original_value, source_code
                    ORDER BY species_count DESC, trait_value, original_value
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
            """
            SELECT DISTINCT scientific_name
            FROM occurrences
            WHERE scientific_name IS NOT NULL
            ORDER BY scientific_name
            LIMIT 2000
            """
        )
        species_options = [row["scientific_name"] for row in cursor.fetchall()]

        cursor.execute(
            """
            SELECT DISTINCT asset_name
            FROM reserves
            WHERE asset_name IS NOT NULL
            ORDER BY asset_name
            """
        )
        reserve_options = [row["asset_name"] for row in cursor.fetchall()]

        cursor.execute(
            """
            SELECT DISTINCT dataset_name
            FROM datasets
            WHERE dataset_name IS NOT NULL
            ORDER BY dataset_name
            """
        )
        dataset_options = [row["dataset_name"] for row in cursor.fetchall()]

        cursor.execute(
            """
            SELECT DISTINCT vernacular_name
            FROM species
            WHERE vernacular_name IS NOT NULL
            ORDER BY vernacular_name
            LIMIT 2000
            """
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