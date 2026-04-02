# Import necessary Flask modules and other libraries this is a test
from flask import (
    Flask, g, render_template, request, session, url_for, jsonify, send_file,
    redirect, flash
)
import io
from flask_mail import Mail, Message
from extensions import bcrypt, db, init_app
import db_management
from User import User
import pandas as pd
import query
from datetime import datetime, date
import sys
import re
from flask import request, jsonify
import pandas as pd
import os

from pathlib import Path  # Import Path for handling filenames

# Initialize the Flask application ONCE
app = Flask(__name__)

app.config.from_object("config.Config")

# Initialize Flask extensions
init_app(app)

mail = Mail(app)

# ★ Enable CORS for the application
# This is a more flexible setting for development, allowing any origin.


# Import database models
from models import (
    ClientBusiness, DataSource, Family, LocalSpeciesInfo,
    Occurrence, Reserve, Species, SpeciesTraitJunction, Traits, Fauna
)

# ... (the rest of your code from line 62 onwards) ...

# Global variables for data storage
df = None
# Load configuration from a separate file
app.config.from_object("config.Config")

# Initialize Flask extensions


# Import database models
from models import (
    ClientBusiness, DataSource, Family, LocalSpeciesInfo,
    Occurrence, Reserve, Species, SpeciesTraitJunction, Traits, Fauna
)

# Initialize Flask-Mail
mail = Mail(app)

# Function to send emails
def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=app.config["MAIL_DEFAULT_SENDER"],
    )
    mail.send(msg)

# Global variables for data storage
df = None
species_list = []
# Dictionary defining groups of traits
trait_groups = {
    "Blossoming": ["flowering_cues", "flowering_time"],
    "Botany": ["bud_bank_location", "clonal_spread_mechanism", "flower_structural_sex_type", "genome_size", "ploidy", "root_system_type", "sex_type"],
    "Descriptive": ["flower_colour", "fruit_colour", "leaf_type", "parasitic", "plant_climbing_mechanism", "plant_growth_form", "plant_growth_substrate", "plant_height", "plant_physical_defence_structures"],
    "Fire recovery": ["fire_time_from_fire_to_50_percent_flowering", "fire_time_from_fire_to_50_percent_fruiting", "fire_time_from_fire_to_flowering", "fire_time_from_fire_to_flowering_decline", "fire_time_from_fire_to_fruiting", "fire_time_from_fire_to_peak_flowering"],
    "Fire response": ["life_history_ephemeral_class", "plant_tolerance_fire", "post_fire_flowering", "post_fire_recruitment", "resprouting_capacity", "resprouting_capacity_juvenile", "resprouting_capacity_proportion_individuals", "resprouting_capacity_time_from_germination"],
    "Germination": ["establishment_light_environment_index", "recruitment_time", "reproductive_light_environment_index", "root_structure", "seed_germination", "seed_germination_time", "seedling_establishment_conditions", "seedling_germination_location"],
    "Life history": ["life_history", "lifespan"],
    "Natural Growth": ["competitive_stratum", "dispersal_syndrome", "dispersers", "nitrogen_fixing", "resprouting_capacity_non_fire_disturbance", "sprout_depth", "stem_growth_habit", "storage_organ", "vegetative_reproduction_ability"],
    "Pollination": ["pollination_syndrome", "pollination_system"],
    "Seedbank": ["seedbank_location", "seedbank_longevity", "seedbank_longevity_class"],
    "Seeds": ["dispersal_unit", "fruiting_time", "reproductive_maturity", "seed_viability", "serotiny"],
    "Propagation": ["seed_dormancy_class", "seed_germination_treatment", "germination_treatment"],
    "Soil tolerances": ["plant_tolerance_calcicole", "plant_tolerance_salt", "plant_tolerance_soil_salinity", "plant_type_by_resource_use"],
    "Water response": ["plant_flood_regime_classification", "plant_tolerance_inundation", "plant_tolerance_snow", "plant_tolerance_water_logged_soils"]
}

# Function to split trait values
def split_trait_values(val):
    if pd.isna(val):
        return []
    return [v.strip().lower() for v in re.split(r",| - |–| to | and |\+|-", str(val)) if v.strip()]

# Before each request, load trait data
@app.before_request
def before_request_load_trait_data():
    # No longer needed since we're using database directly
    pass

@app.route('/View pct Map')
def PCT_report():
    return render_template("PCT.html")

# Route for the statistics page
@app.route('/statistics')
def statistics_page():
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))

    page = {'title': 'Statistics'}
    overall_stats = query.get_overall_statistics(db.session)

    return render_template('statistics.html',
                           username=session["username"],
                           is_admin=session["is_admin"],
                           page=page,
                           stats=overall_stats)

# Route to view traits of selected species

@app.route("/insert_column")
def api_insert_column():
    src_file = request.files.get("source_file")
    tgt_file = request.files.get("target_file")
    col_name = request.form.get("column")

    if not src_file or not tgt_file or not col_name:
        return jsonify({"error": "缺少必要参数 source_file / target_file / column"}), 400

    try:
        # 读 CSV（自动识别编码可按需调整）
        df_src = pd.read_csv(src_file)
        df_tgt = pd.read_csv(tgt_file)

        if col_name not in df_src.columns:
            return jsonify({"error": f"源 CSV 不包含列：{col_name}"}), 400

        series = df_src[col_name]

        # 对齐长度：以较长为准，缺失填空
        max_len = max(len(df_tgt), len(series))
        if len(df_tgt) < max_len:
            df_tgt = df_tgt.reindex(range(max_len))
        if len(series) < max_len:
            series = series.reindex(range(max_len))

        # 作为“最后一列”追加；若同名，自动重命名避免覆盖
        final_name = col_name
        i = 1
        while final_name in df_tgt.columns:
            final_name = f"{col_name}_{i}"
            i += 1

        df_tgt[final_name] = series

        # 输出为 CSV 并返回下载
        out = io.BytesIO()
        df_tgt.to_csv(out, index=False)
        out.seek(0)

        tgt_name = Path(tgt_file.filename).stem or "target"
        download_name = f"{tgt_name}_with_{final_name}.csv"
        return send_file(
            out,
            as_attachment=True,
            download_name=download_name,
            mimetype="text/csv"
        )

    except Exception as e:
        return jsonify({"error": f"处理失败：{e}"}), 500
    
@app.route("/fliter")
def fliter_page():
    return render_template("fliter.html")

@app.route("/load_dataset")
def load_dataset():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"})

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "No selected file"})

    try:
        df = pd.read_csv(file)
        columns = list(df.columns)  
        return jsonify({"status": "ok", "columns": columns})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    

# ---- Merge selected columns ----
@app.route("/api/merge_datasets", methods=["POST"])
def merge_datasets():
    global original_df, merged_data_storage
    data = request.get_json()
    selected = data.get("selected", [])
    custom_name = data.get("custom_name", "Merged_Dataset")

    if original_df is None:
        return jsonify({"status": "error", "message": "No dataset loaded"})
    if not selected:
        return jsonify({"status": "error", "message": "No columns selected"})

    # 合并选中列
    merged_df = original_df[selected].copy()

    # 保存到内存
    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    merged_data_storage[custom_name] = {
        "data": merged_df,
        "records": len(merged_df),
        "created": created
    }

    return jsonify({
        "name": custom_name,
        "records": len(merged_df),
        "created": created
    })


# ---- Delete selected datasets ----
@app.route("/api/delete_dataset", methods=["POST"])
def delete_dataset():
    data = request.get_json()
    names = data.get("names", [])
    for n in names:
        if n in merged_data_storage:
            del merged_data_storage[n]
    return jsonify({"status": "ok"})

# ---- Clear all ----
@app.route("/api/clear_all", methods=["POST"])
def clear_all():
    merged_data_storage.clear()
    return jsonify({"status": "ok"})

@app.route("/view_traits", methods=["GET", "POST"])
def view_traits():
    selected_species = []
    species_data = {}
    
    # Get all species from database
    all_species = db.session.query(Species.scientific_name).all()
    species_list = [s.scientific_name for s in all_species]
    
    if request.method == "POST":
        selected_species = request.form.getlist("selected_species")
        if selected_species:
            for species in selected_species:
                # Get traits for this species from database
                species_trait_data = db.session.query(
                    SpeciesTraitJunction.trait_name,
                    SpeciesTraitJunction.trait_value
                ).filter(
                    SpeciesTraitJunction.scientific_name == species
                ).all()
                
                # Convert to dictionary
                species_traits_dict = {trait.trait_name: trait.trait_value for trait in species_trait_data}
                
                # Organize by trait groups
                species_traits = {}
                for group_name, traits in trait_groups.items():
                    group_data = {}
                    for trait in traits:
                        if trait in species_traits_dict:
                            group_data[trait] = species_traits_dict[trait]
                        else:
                            group_data[trait] = "nan"
                    # Always include the group, even if all values are nan
                    species_traits[group_name] = group_data
                species_data[species] = species_traits
    
    return render_template("view_traits.html", species_list=species_list, selected_species=selected_species, species_data=species_data)

# Route to find flowers based on trait filters
@app.route("/find_flowers", methods=["GET", "POST"])
def find_flowers():
    matching_species = []
    selected_groups = []
    selected_traits = []
    filters_display = {}

    if request.method == "POST":
        selected_groups = request.form.getlist("selected_groups")
        available_traits = []
        for group in selected_groups:
            available_traits.extend(trait_groups[group])

        selected_traits = request.form.getlist("selected_traits")
        filters = {}
        for trait in selected_traits:
            raw_selected_vals = request.form.getlist(f"values_for_{trait}")
            selected_vals_processed = []
            for val in raw_selected_vals:
                selected_vals_processed.extend(split_trait_values(val.lower()))
            if selected_vals_processed:
                filters[trait] = list(set(selected_vals_processed))
                filters_display[trait] = raw_selected_vals

        if filters:
            # Use database query instead of CSV
            matching_species = []
            # Get all species that have the selected traits
            species_with_traits = db.session.query(SpeciesTraitJunction.scientific_name).filter(
                SpeciesTraitJunction.trait_name.in_(selected_traits)
            ).distinct().all()
            
            for species_record in species_with_traits:
                species_name = species_record.scientific_name
                species_data = {"species_name": species_name}
                match_found = True
                
                # Check if this species matches all the filter criteria
                for trait, vals in filters.items():
                    trait_values = db.session.query(SpeciesTraitJunction.trait_value).filter(
                        SpeciesTraitJunction.scientific_name == species_name,
                        SpeciesTraitJunction.trait_name == trait
                    ).all()
                    
                    if trait_values:
                        # Check if any trait value matches the filter
                        trait_match = False
                        for trait_value_record in trait_values:
                            trait_value = trait_value_record.trait_value
                            if trait_value:
                                split_vals = split_trait_values(trait_value.lower())
                                if any(v in split_vals for v in vals):
                                    trait_match = True
                                    break
                        
                        if trait_match:
                            species_data[trait] = trait_value
                        else:
                            match_found = False
                            break
                    else:
                        match_found = False
                        break
                
                if match_found:
                    matching_species.append(species_data)
        else:
            matching_species = []

    all_trait_groups = list(trait_groups.keys())
    available_traits_for_display = [trait for group in selected_groups for trait in trait_groups[group]]

    # Get trait value options from database
    trait_value_options = {}
    for trait in selected_traits:
        trait_values = db.session.query(SpeciesTraitJunction.trait_value).filter(
            SpeciesTraitJunction.trait_name == trait
        ).distinct().all()
        
        dropdown_set = set()
        for trait_value_record in trait_values:
            if trait_value_record.trait_value:
                split_vals = split_trait_values(trait_value_record.trait_value)
                dropdown_set.update(split_vals)
        
        trait_value_options[trait] = sorted(dropdown_set)

    return render_template(
        "find_flowers.html",
        all_trait_groups=all_trait_groups,
        selected_groups=selected_groups,
        available_traits_for_display=available_traits_for_display,
        selected_traits=selected_traits,
        trait_value_options=trait_value_options,
        filters_display=filters_display,
        matching_species=matching_species
    )

# Route to compare traits of multiple species
@app.route("/compare_traits", methods=["GET", "POST"])
def compare_traits():
    selected_species = []
    compare_data = None
    if request.method == "POST":
        selected_species = request.form.getlist("selected_species")
        if selected_species:
            compare_df = df[df["species_name"].isin(selected_species)].set_index("species_name")
            compare_data = compare_df.to_dict(orient='index')
    return render_template("compare_traits.html", species_list=species_list, selected_species=selected_species, compare_data=compare_data)

# Route for data update page (redirects to under construction)
@app.route('/update_data')
def update_page():
    return redirect(url_for('under_construction_page'))

# Route for the map page
@app.route('/map')
def map_page():
    return render_template('map.html')

# Route for the home page
@app.route('/home')
def home_page():
    return render_template('home.html')

# Route for the under construction page
@app.route('/under_construction')
def under_construction_page():
    return render_template('under_construction.html')

# Route for the about page (redirects to external link)
@app.route('/about')
def about_page():
    about_site_link = "https://docs.google.com/document/d/1lbjMmRwctoKtE66DqXltRtMc_ayN5u1vQrCWArIDzvc/edit?usp=sharing"
    return redirect(about_site_link)

# Route for the user guide page (redirects to external link)
@app.route('/user_guide')
def user_guide_page():
    user_guide_link = "https://drive.google.com/file/d/1YwgmjvTLvRYptbGJi_3JOybTsq-qaW0C/view?usp=sharing"
    return redirect(user_guide_link)

# Fire experiment dashboard
@app.route('/fire_experiment')
def fire_experiment_page():
    return render_template('fire_experiment.html')

# ---- sub routes for iframes (render the full-page map templates) ----
@app.route('/fire_experiment/risk')
def fire_experiment_risk():
    return render_template('fire_risk_distribution_map.html')

@app.route('/fire_experiment/recovery')
def fire_experiment_recovery():
    return render_template('fire_recovery_time_map.html')

@app.route('/fire_experiment/resprouting')
def fire_experiment_resprouting():
    return render_template('resprouting_capacity_map.html')

@app.route('/fire_experiment/recruitment')
def fire_experiment_recruitment():
    return render_template('post_fire_recruitment_map.html')

# Route for the feedback page (redirects to external link)
@app.route('/feedback')
def feedback_page():
    feedback_link = "https://docs.google.com/document/d/1qPcz25Z4GaDAbtcOG6YVc1SyVVutNPCy/edit?usp=sharing&ouid=102170301768105281260&rtpof=true&sd=true"
    return redirect(feedback_link)

# API endpoint to get map filter options
@app.route('/api/map_filters')
def get_map_filters():
    filter_options = query.get_options_occurrences(db.session)

    year_options_from_db = filter_options['yearOptions']
    full_year_range = []
    if year_options_from_db:
        min_year = min(year_options_from_db)
        max_year = max(year_options_from_db)
        full_year_range = list(range(min_year, max_year + 1))

    return jsonify({
        "species": filter_options['speciesOptions'],
        "datasets": filter_options['datasetOptions'],
        "reserves": filter_options['reserveOptions'],
        "planted_natives": filter_options['plantedNativeOptions'],
        "years": full_year_range,
        "threatened_statuses": filter_options['threatenedStatusOptions']
    })

# API endpoint to get map data based on filters
@app.route('/api/map_data')
def get_map_data():
    species = request.args.get('species')
    dataset = request.args.get('dataset')
    reserve = request.args.get('reserve')
    planted_native = request.args.get('planted_native')
    start_year = request.args.get('start_year')
    end_year = request.args.get('end_year')
    threatened_status = request.args.get('rare')

    try:
        observations = query.get_observations(
            db_session=db.session,
            species=species,
            dataset=dataset,
            reserve=reserve,
            planted_native=planted_native,
            start_year=start_year,
            end_year=end_year,
            rare=threatened_status
        )
        return jsonify(observations)
    except Exception as e:
        print(f"Error fetching map data: {e}", file=sys.stderr)
        return jsonify({"error": "Failed to fetch map data", "details": str(e)}), 500

# Default route for the application
@app.route("/")
def index():
    session['edit_mode'] = False
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))
    return redirect(url_for("flora_dashboard"))

# Route to view detailed trait information
@app.route('/traits', methods=['GET', 'POST'])
def traits_viewer():
    try:
        traits_df = pd.read_excel('TraitsCombine-helen-Dorothy.xlsx', sheet_name=0)
        values_df = pd.read_excel('Value.xlsx')
    except FileNotFoundError as e:
        print(f"ERROR: Excel file not found. Ensure 'TraitsCombine-helen-Dorothy.xlsx' and 'Value.xlsx' are in the /app directory of the container. Details: {e}", file=sys.stderr)
        return "Internal Server Error: Required data files not found.", 500

    trait_list = sorted(traits_df['trait'].unique())
    selected_trait = request.form.get('trait_select') if request.method == 'POST' else None

    trait_info = None
    value_table = None

    if selected_trait:
        trait_info = traits_df[traits_df['trait'] == selected_trait].to_dict(orient='records')[0]
        value_table = values_df[values_df['trait'] == selected_trait][[
            'allowed_values_levels', 'categorical_trait_description'
        ]].rename(columns={
            'allowed_values_levels': 'Value',
            'categorical_trait_description': 'Description'
        }).to_dict(orient='records')

    return render_template(
        'traits.html',
        trait_list=trait_list,
        selected_trait=selected_trait,
        trait_info=trait_info,
        value_table=value_table
    )

# Route for forgot password functionality
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    session['edit_mode'] = False
    if (request.method == "POST"):
        email = request.form["email"]
        user = db.session.query(User).filter_by(email=email).one_or_none()
        if user is None:
            return render_template("forgot-password.html", msg="""Invalid email address.""")

        if user.password is None or user.password == '':
            return render_template("forgot-password.html", msg="""This account has not yet set a password.
                                   Please use the 'Register New Account' option first.""")

        token = user.generate_token(app, email)
        reset_url = url_for("reset_password", token=token, _external=True)
        html = render_template("reset_password_email.html", reset_url=reset_url)
        subject = "Reset your password"
        send_email(user.email, subject, html)
        return render_template("login.html", msg="""Password reset link
                               has been sent to your email address.""")
    else:
        page = {'title': 'Forgot Password'}
        return render_template('forgot-password.html', page=page)

# Route to reset password using a token
@app.route("/reset_password/<token>", methods = ['POST', 'GET'])
def reset_password(token):
    session['edit_mode'] = False

    email = User.confirm_token(app, token)
    user = db.session.query(User).filter_by(email=email).one_or_none()
    if not email or not user:
        return render_template("login.html", msg="""The password reset
                               link is invalid or has expired.""")

    if request.method == 'POST':
        password = request.form["password"]
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return render_template("login.html", msg="""Password has been reset.""")
    else:
        return render_template('reset_password.html')

# Route for user login
@app.route('/login', methods = ['POST', 'GET'])
def login():
    session['edit_mode'] = False
    page = {'title' : 'login'}
    if (request.method == 'POST'):
        email = request.form["username"]
        password = request.form["password"]
        user = db.session.query(User).filter_by(email=email).one_or_none()

        if user is None:
            return render_template('login.html', msg = """Username or password is incorrect.""")

        if user.password is None or user.password == '':
            return render_template('login.html', msg = """Your account requires initial setup. Please use the 'Register New Account' button.""")

        if user.verify_password(password) == False:
            return render_template('login.html', msg = """Username or password is incorrect.""")

        session['logged_in'] = True
        session['username'] = email
        session['is_admin'] = user.is_admin()
        return redirect(url_for('home_page'))

    else:
        if ('logged_in' in session and session['logged_in'] == True):
            return redirect(url_for('index'))
        return render_template('login.html', page = page)

# Route for user settings
@app.route('/settings')
def settings():
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))
    session['edit_mode'] = False
    return render_template('settings.html', username = session["username"], is_admin = session["is_admin"])

# Route for new user registration (sign-up)
@app.route('/signup', methods = ['POST', 'GET'])
def sign_up():
    if ('logged_in' in session and session['logged_in'] == True):
        return redirect(url_for('index'))

    session['edit_mode'] = False
    page = {'title' : 'Register New Account'}
    error_msg = ""

    if (request.method == 'POST'):
        username = request.form['username']
        secret_password_attempt = request.form['secret_password'].lower()
        new_password = request.form['new_password']
        confirm_new_password = request.form['confirm_new_password']

        user = db.session.query(User).filter_by(email=username).one_or_none()

        if user is None:
            error_msg = "Account not found for initial setup. Please check your email."
        elif user.password is not None and user.password != '':
            error_msg = "This account has already been set up. Please use the login page."
        elif secret_password_attempt != app.config['SECRET_INITIAL_PASSWORD']:
            error_msg = "Incorrect secret password."
        elif new_password != confirm_new_password:
            error_msg = "New passwords do not match."
        else:
            user.set_password(new_password)
            db.session.add(user)
            db.session.commit()
            return render_template("login.html", msg="""Your account has been successfully set up. You can now log in with your new password.""")

    return render_template('signup.html', page = page, error_msg = error_msg)

# Route to manage users
@app.route('/manage_users', methods=['GET'])
def manage_users():
    # Check if user is logged in
    if 'logged_in' not in session or not session['logged_in']:
        flash("Please log in to access this page.")
        return redirect(url_for('login'))
    # Check if user is an administrator
    if not session.get('is_admin'):
        flash("You do not have administrative privileges to access this page.", "error")
        return redirect(url_for('home_page'))

    # Get all users from the database
    all_users = db.session.query(User).all()

    # Render the manage users page
    return render_template('manage_users.html',
                           username=session["username"],
                           is_admin=session["is_admin"],
                           users=all_users)

# Route to create a new user
@app.route('/create_user', methods=['POST'])
def create_user():
    # Check if user is logged in
    if 'logged_in' not in session or not session['logged_in']:
        flash("Please log in to perform this action.")
        return redirect(url_for('login'))
    # Check if user is an administrator
    if not session.get('is_admin'):
        flash("You do not have administrative privileges to perform this action.", "error")
        return redirect(url_for('home_page'))

    # Get email from form data
    email = request.form.get('email')

    # Validate email input
    if not email:
        flash("Email address is required to create a user.", "error")
        return redirect(url_for('manage_users'))

    # Validate email format
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        flash("Invalid email format.", "error")
        return redirect(url_for('manage_users'))

    # Check if user already exists
    existing_user = db.session.query(User).filter_by(email=email).one_or_none()
    if existing_user:
        flash(f"User with email '{email}' already exists.", "error")
    else:
        try:
            # Create new user and add to database
            new_user = User(email=email, password=None, write_permission=False, role='user')
            db.session.add(new_user)
            db.session.commit()
            flash(f"User '{email}' created successfully. They can now set their password via 'Register New Account'.", "success")
        except Exception as e:
            # Rollback on error
            db.session.rollback()
            flash(f"Error creating user: {e}", "error")
            print(f"Error creating user: {e}", file=sys.stderr)

    # Redirect back to manage users page
    return redirect(url_for('manage_users'))

# Route to toggle user role (admin/regular user)
@app.route('/toggle_user_role/<int:user_id>', methods=['POST'])
def toggle_user_role(user_id):
    # Check if user is logged in
    if 'logged_in' not in session or not session['logged_in']:
        flash("Please log in to perform this action.")
        return redirect(url_for('login'))
    # Check if user is an administrator
    if not session.get('is_admin'):
        flash("You do not have administrative privileges to perform this action.", "error")
        return redirect(url_for('home_page'))

    # Get the user to toggle by ID
    user_to_toggle = db.session.query(User).get(user_id)

    if user_to_toggle:
        try:
            # Prevent demoting own admin account
            current_user_email = session.get("username")
            if user_to_toggle.email == current_user_email and user_to_toggle.role == 'Administrator':
                flash("Cannot demote your own administrator account.", "error")
            else:
                # Toggle the user's role
                if user_to_toggle.role == 'user':
                    user_to_toggle.role = 'Administrator'
                    flash(f"User '{user_to_toggle.email}' is now an Administrator.", "success")
                else:
                    user_to_toggle.role = 'user'
                    flash(f"User '{user_to_toggle.email}' is now a regular user.", "success")
                db.session.add(user_to_toggle)
                db.session.commit()
        except Exception as e:
            # Rollback on error
            db.session.rollback()
            flash(f"Error toggling role for user '{user_to_toggle.email}': {e}", "error")
            print(f"Error toggling role: {e}", file=sys.stderr)
    else:
        flash(f"User with ID {user_id} not found.", "error")

    # Redirect back to manage users page
    return redirect(url_for('manage_users'))

# Route to delete a user
@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    # Check if user is logged in
    if 'logged_in' not in session or not session['logged_in']:
        flash("Please log in to perform this action.")
        return redirect(url_for('login'))
    # Check if user is an administrator
    if not session.get('is_admin'):
        flash("You do not have administrative privileges to perform this action.", "error")
        return redirect(url_for('home_page'))

    # Get the user to delete by ID
    user_to_delete = db.session.query(User).get(user_id)

    if user_to_delete:
        try:
            # Prevent deleting own account
            current_user_email = session.get("username")
            if user_to_delete.email == current_user_email:
                flash("Cannot delete your own account.", "error")
            else:
                # Delete the user from the database
                db.session.delete(user_to_delete)
                db.session.commit()
                flash(f"User '{user_to_delete.email}' deleted successfully.", "success")
        except Exception as e:
            # Rollback on error
            db.session.rollback()
            flash(f"Error deleting user '{user_to_delete.email}': {e}", "error")
            print(f"Error deleting user: {e}", file=sys.stderr)
    else:
        flash(f"User with ID {user_id} not found.", "error")

    # Redirect back to manage users page
    return redirect(url_for('manage_users'))

# Route for the flora dashboard
@app.route('/flora_dashboard', methods = ['GET', 'POST'])
def flora_dashboard():
    # Check if user is logged in
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))

    # Set page title and get filter options
    page = {'title' : 'Flora Dashboard'}
    filterOptions = query.get_options_occurrences(db.session)

    # Get pagination parameters
    page_num = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Get filter parameters from request arguments
    species_param = request.args.get('species')
    dataset_param = request.args.get('dataset')
    reserve_param = request.args.get('reserve')
    locality_param = request.args.get('locality')
    habitat_param = request.args.get('habitat')
    basis_of_record_param = request.args.get('basis')
    native_param = request.args.get('native')
    rare_param = request.args.get('rare')

    start_year_param = request.args.get('start_year')
    end_year_param = request.args.get('end_year')

    selected_reserves_param = request.args.get('selected_reserves_input')
    selected_reserves_list = selected_reserves_param.split(',') if selected_reserves_param else []

    # Determine effective reserve filter
    effective_reserve_filter = selected_reserves_list if selected_reserves_list else (reserve_param.split(',') if reserve_param else None)

    # Get paginated data
    paginated_data_query = query.get_observations_query(
        db.session,
        species=species_param,
        dataset=dataset_param,
        reserve=effective_reserve_filter,
        locality=locality_param,
        habitat=habitat_param,
        basis_of_record=basis_of_record_param,
        planted_native=native_param,
        rare=rare_param,

        start_year=start_year_param,
        end_year=end_year_param
    )

    paginated_results = paginated_data_query.paginate(page=page_num, per_page=per_page, error_out=False)
    result = [obs.to_dict() for obs in paginated_results.items]
    total_results = paginated_results.total

    # Get full filtered data for download/export
    full_filtered_data_query = query.get_observations_query(
        db.session,
        species=species_param,
        dataset=dataset_param,
        reserve=effective_reserve_filter,
        locality=locality_param,
        habitat=habitat_param,
        basis_of_record=basis_of_record_param,
        planted_native=native_param,
        rare=rare_param,

        start_year=start_year_param,
        end_year=end_year_param
    )

    full_filtered_result = [obs.to_dict() for obs in full_filtered_data_query.all()]

    # Determine which template to render based on edit mode
    template_name = 'editable_dashboard.html' if session.get('edit_mode') else 'flora_dashboard.html'

    # Render the flora dashboard template
    return render_template(template_name,
                           username=session["username"],
                           is_admin=session["is_admin"],
                           page=page,
                           speciesOptions=filterOptions["speciesOptions"],
                           datasetOptions=filterOptions["datasetOptions"],
                           localityOptions=filterOptions["localityOptions"],
                           habitatOptions=filterOptions["habitatOptions"],
                           basisOptions=filterOptions["basisOptions"],
                           reserveOptions=filterOptions["reserveOptions"],
                           filtered_result=result,
                           full_filtered_result=full_filtered_result,
                           species=species_param or '',
                           dataset=dataset_param or '',
                           locality=locality_param or '',
                           habitat=habitat_param or '',
                           basis=basis_of_record_param or '',
                           reserve='',
                           selected_reserves=selected_reserves_list,
                           native=native_param or '',
                           rare=rare_param or '',
                           start_year=start_year_param or '',
                           end_year=end_year_param or '',
                           is_flora=True,
                           page_num=page_num,
                           per_page=per_page,
                           total_results=total_results,
                           has_next=paginated_results.has_next,
                           has_prev=paginated_results.prev_num,
                           next_num=paginated_results.next_num,
                           prev_num=paginated_results.prev_num
                           )

# Route to filter flora data
@app.route('/filter_flora', methods = ['POST', 'GET'])
def filter_flora():
    # Check if user is logged in
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))

    # Get form data
    form_data = request.form.to_dict()

    # Get selected reserves from form
    selected_reserves_input = request.form.getlist('selected_reserves')

    # Convert selected reserves to a comma-separated string
    if selected_reserves_input:
        selected_reserves_str = ','.join(selected_reserves_input)
    else:
        selected_reserves_str = ''

    # Prepare arguments for redirect
    redirect_args = {
        'species': form_data.get('species', ''),
        'dataset': form_data.get('dataset', ''),
        'reserve': form_data.get('reserve', ''),
        'locality': form_data.get('locality', ''),
        'habitat': form_data.get('habitat', ''),
        'basis': form_data.get('basis', ''),
        'native': form_data.get('native', ''),
        'rare': form_data.get('rare', ''),
        'start_year': form_data.get('start_year', ''),
        'end_year': form_data.get('end_year', ''),
        'selected_reserves_input': selected_reserves_str,
        'page': request.args.get('page', 1, type=int),
        'per_page': request.args.get('per_page', 20, type=int)
    }

    # Redirect to flora dashboard with filter arguments
    return redirect(url_for('flora_dashboard', **redirect_args))

@app.route('/species_survey_map')
def species_survey_map():
    return render_template('mapping_dashboard.html')





# Route for the fauna dashboard
@app.route('/fauna_dashboard', methods = ['GET', 'POST'])
def fauna_dashboard():
    # Check if user is logged in
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))

    # Set page title
    page = {'title' : 'Fauna Dashboard'}

    # Helper function to clean parameters
    def clean_param(param):
        return param.strip() if param and str(param).strip() else None

    # Get filter options for fauna
    filterOptions = query.get_options_fauna(db.session)

    # Get pagination parameters
    page_num = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Get filter parameters from request arguments and clean them
    genus_param = clean_param(request.args.get('genus'))
    species_param = clean_param(request.args.get('species'))
    family_param = clean_param(request.args.get('family'))
    vernacular_name_param = clean_param(request.args.get('vernacular_name'))
    class_name_param = clean_param(request.args.get('class_name'))
    rare_endangered_param = clean_param(request.args.get('rare_endangered'))
    local_rare_endangered_param = clean_param(request.args.get('local_rare_endangered'))
    exotic_param = clean_param(request.args.get('exotic'))
    year_param = clean_param(request.args.get('year'))
    reserve_name_param = clean_param(request.args.get('reserve_name'))

    # Debug print statement for parameters
    print(f"DEBUG: Params to query in fauna_dashboard: genus={repr(genus_param)}, species={repr(species_param)}, class_name={repr(class_name_param)}, year={repr(year_param)}, reserve_name={repr(reserve_name_param)}")

    # Get paginated fauna data
    paginated_data_query = query.get_fauna_query(
        db.session,
        genus=genus_param,
        species=species_param,
        family=family_param,
        vernacular_name=vernacular_name_param,
        class_name=class_name_param,
        rare_endangered=rare_endangered_param,
        local_rare_endangered=local_rare_endangered_param,
        exotic=exotic_param,
        year=year_param,
        reserve_name=reserve_name_param
    )

    paginated_results = paginated_data_query.paginate(page=page_num, per_page=per_page, error_out=False)

    # Process paginated results
    result = []
    for fauna_obj in paginated_results.items:
        fauna_dict = fauna_obj.to_dict()
        fauna_dict.pop('old_location_name', None)
        fauna_dict.pop('fauna_id', None)
        result.append(fauna_dict)

    total_results = paginated_results.total

    # Get full filtered fauna data for download/export
    full_filtered_fauna_query = query.get_fauna_query(
        db.session,
        genus=genus_param,
        species=species_param,
        family=family_param,
        vernacular_name=vernacular_name_param,
        class_name=class_name_param,
        rare_endangered=rare_endangered_param,
        local_rare_endangered=local_rare_endangered_param,
        exotic=exotic_param,
        year=year_param,
        reserve_name=reserve_name_param
    )

    full_filtered_fauna_result = []
    for fauna_obj in full_filtered_fauna_query.all():
        fauna_dict = fauna_obj.to_dict()
        fauna_dict.pop('old_location_name', None)
        fauna_dict.pop('fauna_id', None)
        full_filtered_fauna_result.append(fauna_dict)

    # Set template name
    template_name = 'fauna_dashboard.html'

    # Render the fauna dashboard template
    return render_template(template_name,
                           username=session["username"],
                           is_admin=session["is_admin"],
                           page=page,
                           genusOptions=filterOptions["genusOptions"],
                           speciesOptions=filterOptions["speciesOptions"],
                           familyOptions=filterOptions["familyOptions"],
                           vernacularNameOptions=filterOptions["vernacularNameOptions"],
                           classNameOptions=filterOptions["classNameOptions"],
                           rareEndangeredOptions=filterOptions["rareEndangeredOptions"],
                           localRareEndangeredOptions=filterOptions["localRareEndangeredOptions"],
                           exoticOptions=filterOptions["exoticOptions"],
                           yearOptions=filterOptions["yearOptions"],
                           reserveNameOptions=filterOptions["reserveNameOptions"],
                           filtered_result=result,
                           full_filtered_fauna_result=full_filtered_fauna_result,

                           genus=genus_param or '',
                           species=species_param or '',
                           family=family_param or '',
                           vernacular_name=vernacular_name_param or '',
                           class_name=class_name_param or '',
                           rare_endangered=rare_endangered_param or '',
                           local_rare_endangered=local_rare_endangered_param or '',
                           exotic=exotic_param or '',
                           year=year_param or '',
                           reserve_name=reserve_name_param or '',
                           is_flora=False,
                           page_num=page_num,
                           per_page=per_page,
                           total_results=total_results,
                           has_next=paginated_results.has_next,
                           has_prev=paginated_results.prev_num,
                           next_num=paginated_results.next_num,
                           prev_num=paginated_results.prev_num
                           )

# Route to filter fauna data
@app.route('/filter_fauna', methods = ['POST', 'GET'])
def filter_fauna():
    # Check if user is logged in
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))

    # Get form data
    form_data = request.form.to_dict()

    # Prepare arguments for redirect
    redirect_args = {
        'genus': form_data.get('genus', ''),
        'species': form_data.get('species', ''),
        'family': form_data.get('family', ''),
        'vernacular_name': form_data.get('vernacular_name', ''),
        'class_name': form_data.get('class_name', ''),
        'rare_endangered': form_data.get('rare_endangered', ''),
        'local_rare_endangered': form_data.get('local_rare_endangered', ''),
        'exotic': form_data.get('exotic', ''),
        'year': form_data.get('year', ''),
        'reserve_name': form_data.get('reserve_name', ''),
        'page': request.args.get('page', 1, type=int),
        'per_page': request.args.get('per_page', 20, type=int)
    }

    # Redirect to fauna dashboard with filter arguments
    return redirect(url_for('fauna_dashboard', **redirect_args))

# Route to save flora table data
@app.route('/save_table_flora', methods = ['POST'])
def save_table_flora():
    # Get data from the JSON request
    data = request.json
    original_data = data['originalData']
    new_data = data['newData']
    replace_all = data['replaceAll']

    # SQL query to update a single occurrence record
    query_str_1 = """
    UPDATE Occurrence
    SET scientificName = :scientificName, eventDate = :eventDate, datasetName = :datasetName,
        reserveName = :reserveName, decimalLatitude = :decimalLatitude, decimalLongitude = :decimalLongitude,
        individualCount = :individualCount, reproductiveCondition = :reproductiveCondition,
        establishmentMeans = :establishmentMeans, occurrenceRemarks = :occurrenceRemarks,
        year = :year, month = :month, day = :day, habitat = :habitat,
        samplingProtocol = :samplingProtocol, locality = :locality, locationRemarks = :locationRemarks,
        identifiedBy = :identifiedBy, dateIdentified = :dateIdentified,
        ownerInstitutionCode = :ownerInstitutionCode, basisOfRecord = :basisOfRecord,
        dataGeneralizations = :dataGeneralizations, recordedBy = :recordedBy,
        clientBusinessName = :clientBusinessName
    WHERE occurrenceId = :occurrenceId
    """
    try:
        # Parameters for the first update query
        params_1 = {
            'scientificName': new_data.get('scientificName'),
            'eventDate': new_data.get('eventDate'),
            'datasetName': new_data.get('datasetName'),
            'reserveName': new_data.get('reserveName'),
            'decimalLatitude': new_data.get('decimalLatitude'),
            'decimalLongitude': new_data.get('decimalLongitude'),
            'individualCount': new_data.get('individualCount'),
            'reproductiveCondition': new_data.get('reproductiveCondition'),
            'establishmentMeans': new_data.get('establishmentMeans'),
            'occurrenceRemarks': new_data.get('occurrenceRemarks'),
            'year': new_data.get('year'),
            'month': new_data.get('month'),
            'day': new_data.get('day'),
            'habitat': new_data.get('habitat'),
            'samplingProtocol': new_data.get('samplingProtocol'),
            'locality': new_data.get('locality'),
            'locationRemarks': new_data.get('locationRemarks'),
            'identifiedBy': new_data.get('identifiedBy'),
            'dateIdentified': new_data.get('dateIdentified'),
            'ownerInstitutionCode': new_data.get('ownerInstitutionCode'),
            'basisOfRecord': new_data.get('basisOfRecord'),
            'dataGeneralizations': new_data.get('dataGeneralizations'),
            'recordedBy': new_data.get('recordedBy'),
            'clientBusinessName': new_data.get('clientBusinessName'),
            'occurrenceId': original_data['occurrenceId']
        }

        # Execute the first update
        db_management.update_db(db, query_str_1, params_1)

        # If 'replace_all' is true, perform a bulk update
        if replace_all:
            set_str_ls = []
            where_str_ls = ["scientificName = :original_scientificName"]
            params_2 = {'original_scientificName': original_data['scientificName']}

            for column in replace_all:
                # Map display column names to database column names
                db_column = {
                    'Scientific Name': 'scientificName',
                    'Event Date': 'eventDate',
                    'Dataset Name': 'datasetName',
                    'Reserve Name': 'reserveName',
                    'Decimal Latitude': 'decimalLatitude',
                    'Decimal Longitude': 'decimalLongitude',
                    'Individual Count': 'individualCount',
                    'Reproductive Condition': 'reproductiveCondition',
                    'Establishment Means': 'establishmentMeans',
                    'Occurrence Remarks': 'occurrenceRemarks',
                    'Year': 'year',
                    'Month': 'month',
                    'Day': 'day',
                    'Habitat': 'habitat',
                    'Sampling Protocol': 'samplingProtocol',
                    'Locality': 'locality',
                    'Location Remarks': 'locationRemarks',
                    'Identified By': 'identifiedBy',
                    'Date Identified': 'dateIdentified',
                    'Owner Institution Code': 'ownerInstitutionCode',
                    'Basis of Record': 'basisOfRecord',
                    'Data Generalizations': 'dataGeneralizations',
                    'Recorded By': 'recordedBy',
                    'Client Business Name': 'clientBusinessName'
                }.get(column, column)

                set_str_ls.append(f'"{db_column}" = :new_{db_column}')
                params_2[f'new_{db_column}'] = new_data.get(column)

                if db_column != 'scientificName':
                    where_str_ls.append(f'"{db_column}" = :original_{db_column}')
                    params_2[f'original_{db_column}'] = original_data.get(column)

            # Construct and execute the second update query
            query_str_2 = 'UPDATE Occurrence SET ' + ', '.join(set_str_ls) + ' WHERE ' + ' AND '.join(where_str_ls)

            db_management.update_db(db, query_str_2, params_2)

        # Return success message
        return jsonify({"message": "Update successful"}), 200
    except Exception as e:
        # Handle errors during update
        print(f"Exception occurred in save_table_flora: {type(e).__name__}, {e}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500

# Route to generate reports
@app.route('/report', methods=['GET', 'POST'])
def generate_report():
    # Check if user is logged in
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))

    # Get report type and name from form or set defaults
    report_type = request.form.get('report_type', "Flora")
    report_name = request.form.get('report_name', "All Species")

    result = []

    # Debug print statements
    print(f"DEBUG: Request Method: {request.method}")
    print(f"DEBUG: Form Data: {request.form}")
    print(f"DEBUG: Initial Report Type: {report_type}, Report Name: {report_name}")

    if request.method == 'POST':
        print(f"DEBUG: Processing POST - Report Type={report_type}, Name={report_name}")

        # Handle Flora reports
        if report_type == "Flora":
            if report_name == "All Species":
                result = query.get_flora_all_species_report(db.session)
            elif report_name == "Summary Report":
                result = query.get_summary_report(db.session, "Flora")
            elif report_name == "Report by Reserve":
                result = query.get_flora_report_by_reserve(db.session)
            elif report_name == "Native Flora = 1 Site":
                try:
                    result = query.get_native_flora_equal_1_1_site(db.session)
                except AttributeError:
                    flash("Native Flora = 1 Site report is not implemented or has issues.", "error")
                    result = []
            else:
                flash("Invalid Flora report type selected.", "error")

        # Handle Fauna reports
        elif report_type == "Fauna":
            if report_name == "All Species":
                result = query.get_fauna_all_species_report(db.session)
            elif report_name == "Summary Report":
                result = query.get_summary_report(db.session, "Fauna")
            else:
                flash("Invalid Fauna report type selected.", "error")
        else:
            flash("Invalid report type selected.", "error")

        # Display warning if no results found
        if not result:
            print(f"DEBUG: No results found for report Type={report_type}, Name={report_name}")
            flash(f"No data available for '{report_name}' for {report_type}.", "warning")

    # Initial GET request for default report
    if not result and request.method == 'GET':
        report_type = "Flora"
        report_name = "All Species"
        result = query.get_flora_all_species_report(db.session)
        print(f"DEBUG: Initial GET load - Report Type={report_type}, Name={report_name}, Result Count: {len(result)}")

    # Render the report page
    return render_template('report.html',
                           username = session["username"],
                           is_admin = session["is_admin"],
                           result=result,
                           report=report_name,
                           report_type=report_type,
                           is_flora=(report_type == "Flora"))

# Experiment routes
@app.route('/exp0')
def experiment_0():
    """Experiment 0 - Data Analysis and Visualization"""
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))
    
    # Get list of output files for experiment 0
    exp0_files = []
    output_dir = Path("static/report/experiment0/experiment0_outputs")
    if output_dir.exists():
        for file_path in output_dir.glob("*"):
            if file_path.is_file():
                # Determine icon based on file extension
                if file_path.suffix == '.html':
                    icon = "🌐"
                elif file_path.suffix == '.png':
                    icon = "📊"
                elif file_path.suffix == '.csv':
                    icon = "📄"
                else:
                    icon = "📁"
                
                exp0_files.append({
                    'name': file_path.name,
                    'icon': icon
                })
    
    return render_template("experiment0.html", exp0_files=exp0_files)

@app.route('/run_experiment_0')
def run_experiment_0():
    """Run Experiment 0 analysis"""
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))
    
    try:
        # Import the experiment script
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'Remade experiment', 'experiment0', 'exp_coding'))
        
        # Copy the experiment files to the static directory
        import shutil
        from pathlib import Path
        
        # Use absolute paths to avoid path issues
        base_dir = Path(__file__).parent
        source_dir = base_dir / "Remade experiment" / "experiment0" / "exp_coding"
        target_dir = base_dir / "static" / "report" / "experiment0"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Source directory: {source_dir}")
        print(f"Target directory: {target_dir}")
        print(f"Source exists: {source_dir.exists()}")
        
        # Copy CSV files
        for csv_file in ["ALA.csv", "iNaturalist.csv", "Prototype.csv"]:
            source_file = source_dir / csv_file
            if source_file.exists():
                shutil.copy2(source_file, target_dir / csv_file)
                print(f"Copied {csv_file}")
            else:
                print(f"CSV file not found: {source_file}")
        
        # Copy and run the Python script
        script_path = source_dir / "exp0_pyformat.py"
        if script_path.exists():
            target_script = target_dir / "exp0_pyformat.py"
            shutil.copy2(script_path, target_script)
            print(f"Copied script to: {target_script}")
            
            # Run the script
            import subprocess
            result = subprocess.run([
                sys.executable, str(target_script)
            ], capture_output=True, text=True, cwd=str(target_dir))
            
            print(f"Script output: {result.stdout}")
            print(f"Script error: {result.stderr}")
            
            if result.returncode == 0:
                flash("Experiment 0 analysis completed successfully!", "success")
            else:
                flash(f"Experiment 0 analysis failed: {result.stderr}", "error")
        else:
            flash("Experiment 0 script not found!", "error")
            
    except Exception as e:
        flash(f"Error running experiment: {str(e)}", "error")
    
    return redirect(url_for('experiment_0'))


@app.route('/exp1')
def experiment_1():
    """Experiment 1 - Species Survey Mapping"""
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))
    return redirect(url_for('species_survey_map'))

@app.route('/exp2')
def experiment_2():
    """Experiment 2 - Advanced Mapping Analysis"""
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))
    return redirect(url_for('species_survey_map'))


@app.route('/exp4')
def experiment_4():
    """Experiment 4 - Fire Tolerant Plants Analysis"""
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))
    
    # Get list of output files for experiment 4 (only HTML and PDF files)
    exp4_files = []
    output_dir = Path("static/report/experiment4/experiment4_outputs")
    if output_dir.exists():
        for file_path in output_dir.glob("*"):
            if file_path.is_file():
                # Only include HTML and PDF files
                if file_path.suffix == '.html':
                    icon = "🌐"
                    exp4_files.append({
                        'name': file_path.name,
                        'icon': icon
                    })
                elif file_path.suffix == '.pdf':
                    icon = "📋"
                    exp4_files.append({
                        'name': file_path.name,
                        'icon': icon
                    })
    
    return render_template("experiment4.html", exp4_files=exp4_files)


@app.route('/exp9')
def experiment_9():
    """Experiment 9 - Time Frame Analysis"""
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))

    exp9_files = []
    output_dir = Path("static/report/experiment9/experiment9_outputs")
    if output_dir.exists():
        for p in output_dir.glob("*"):
            if not p.is_file():
                continue
            suffix = p.suffix.lower()
            if suffix == ".html":
                icon = "🌐"
            elif suffix == ".pdf":
                icon = "📋"
            elif suffix == ".png":
                icon = "🖼️"
            elif suffix == ".csv":
                icon = "📄"
            else:
                continue
            exp9_files.append({"name": p.name, "icon": icon, "suffix": suffix})

    return render_template("experiment9.html", exp9_files=exp9_files)

@app.route('/run_experiment_9')
def run_experiment_9():
    """Run Experiment 9 - Time Frame Analysis"""
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))

    try:
        import sys, shutil, subprocess
        from pathlib import Path

        base_dir   = Path(__file__).parent
        source_dir = base_dir / "Remade experiment" / "experiment9"
        target_dir = base_dir / "static" / "report" / "experiment9"
        outputs_dir = target_dir / "experiment9_outputs"

        target_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)

        # Remove stale outputs before running the script
        for old_file in outputs_dir.glob("*"):
            if old_file.is_file():
                try:
                    old_file.unlink()
                except Exception:
                    pass


        # 需要的文件（按你的目录可增减）
        files_to_copy = [
            "time_frame.py",
            "ALA_e9.csv",
            "iNaturalist_e9.csv",
            "new_flora_e9.csv",
            "Prototype_e9.csv",
            "WithoutPrototype_e9.csv",
        ]
        missing = []
        for f in files_to_copy:
            src = source_dir / f
            if src.exists():
                shutil.copy2(src, target_dir / f)
            else:
                missing.append(str(src))
        if missing:
            print("[EXP9] Missing:", missing)

        # 在 target_dir 下运行（time_frame.py 会把图存到 target_dir/experiment9_outputs）
        script_path = target_dir / "time_frame.py"
        if not script_path.exists():
            flash("Experiment 9 script not found (time_frame.py)!", "error")
            return redirect(url_for('experiment_9'))

        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True, text=True, cwd=str(target_dir)
        )
        print("[EXP9] STDOUT:\n", result.stdout)
        print("[EXP9] STDERR:\n", result.stderr)

        if result.returncode != 0:
            flash(f"Experiment 9 failed: {result.stderr[:500]}", "error")
        else:
            flash("Experiment 9 analysis completed successfully!", "success")

    except Exception as e:
        flash(f"Error running experiment 9: {e}", "error")

    return redirect(url_for('experiment_9'))

@app.route('/outputs/<filename>')
def serve_output_file(filename):
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))

    from flask import send_from_directory
    from pathlib import Path

    # exp9
    d = Path("static/report/experiment9/experiment9_outputs")
    if d.exists() and (d / filename).exists():
        return send_from_directory(str(d), filename)

    # exp0
    d = Path("static/report/experiment0/experiment0_outputs")
    if d.exists() and (d / filename).exists():
        return send_from_directory(str(d), filename)
    # exp6
    d = Path("static/report/experiment6/experiment6_outputs")
    if d.exists() and (d / filename).exists():
        return send_from_directory(str(d), filename)
    
    # exp3
    d = Path("static/report/experiment3/experiment3_outputs")
    if d.exists() and (d / filename).exists():
        return send_from_directory(str(d), filename)
    # Try experiment8
    output_dir = Path("static/report/experiment8/experiment8_outputs")
    if output_dir.exists() and (output_dir / filename).exists():
        return send_from_directory(str(output_dir), filename)

    # exp4
    d = Path("static/report/experiment4/experiment4_outputs")
    if d.exists() and (d / filename).exists():
        return send_from_directory(str(d), filename)

    # exp5
    d = Path("static/report/experiment5/experiment5_outputs")
    if d.exists() and (d / filename).exists():
        return send_from_directory(str(d), filename)

    flash(f"File {filename} not found!", "error")
    return redirect(url_for('experiment_6'))


@app.route('/exp3')
def experiment_3():
    """Experiment 3 - Species Form Analysis"""
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))

    exp3_files = []
    output_dir = Path("Remade experiment/experiment3")
    if output_dir.exists():
        for file_path in output_dir.glob("*"):
            if file_path.is_file():
                if file_path.suffix.lower() == '.pdf':
                    icon = "📋"
                    exp3_files.append({'name': file_path.name, 'icon': icon})
                elif file_path.suffix.lower() == '.html':
                    icon = "🌐"
                    exp3_files.append({'name': file_path.name, 'icon': icon})
              

    return render_template("experiment3.html", exp3_files=exp3_files)

@app.route('/run_experiment_3')
def run_experiment_3():
    """Run Experiment 3 (Species Form Analysis) and copy outputs to static dir."""
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))

    try:
        import sys, os, shutil, subprocess
        from pathlib import Path

        base_dir = Path(__file__).parent
        src_dir  = base_dir  / "static" / "report" / "experiment3"
        out_dir  = base_dir / "static" / "report" / "experiment3" / "experiment3_outputs"
        out_dir.mkdir(parents=True, exist_ok=True)

        # Keep runtime script in sync with remade version
        source_script = base_dir / "Remade experiment" / "experiment3" / "species_form_analysis.py"
        target_script = src_dir / "species_form_analysis.py"
        if source_script.exists():
            shutil.copy2(source_script, target_script)
            print(f"Synchronized Experiment 3 script: {source_script} -> {target_script}")

        dataset_files = [
            "ALA_e9.csv",
            "iNaturalist_e9.csv",
            "Prototype_e9.csv",
        ]
        dataset_search_dirs = [
            base_dir / "Remade experiment" / "experiment9",
            base_dir / "static" / "report" / "experiment9",
            base_dir / "report" / "experiment9",
        ]

        for filename in dataset_files:
            target_path = base_dir / filename
            if target_path.exists():
                continue

            copied = False
            for search_dir in dataset_search_dirs:
                candidate = search_dir / filename
                if candidate.exists():
                    shutil.copy2(candidate, target_path)
                    print(f"Copied dataset for experiment 3: {candidate} -> {target_path}")
                    copied = True
                    break

            if not copied:
                flash(f"Experiment 3 dataset missing: {filename}", "error")
                return redirect(url_for('experiment_3'))

     
        script_path = src_dir / "species_form_analysis.py"

        if script_path.exists():
          
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(src_dir),
                capture_output=True, text=True
            )
            print("EXP3 STDOUT:", result.stdout)
            print("EXP3 STDERR:", result.stderr)

            if result.returncode != 0:
                flash(f"Experiment 3 failed: {result.stderr}", "error")
                return redirect(url_for('experiment_3'))
        else:
            print(f"[WARN] Script not found: {script_path}")

      
        pdf_src = src_dir / "species_form_analysis_report.pdf"
        if pdf_src.exists():
            pdf_dst = out_dir / pdf_src.name  
            shutil.copy2(pdf_src, pdf_dst)
            flash("Experiment 3 completed! Report copied to outputs.", "success")
        else:
            flash("Experiment 3 finished but PDF was not found.", "error")

    except Exception as e:
        flash(f"Error running Experiment 3: {e}", "error")

    return redirect(url_for('experiment_3'))


@app.route('/run_experiment_4')
def run_experiment_4():
    """Run Experiment 4 analysis"""
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))
    
    try:
        # Import the experiment script
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'Remade experiment', 'experiment4', 'exp4_code'))
        
        # Copy the experiment files to the static directory
        import shutil
        from pathlib import Path
        
        # Use absolute paths to avoid path issues
        base_dir = Path(__file__).parent
        source_dir = base_dir / "Remade experiment" / "experiment4" / "exp4_code"
        target_dir = base_dir / "static" / "report" / "experiment4"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Source directory: {source_dir}")
        print(f"Target directory: {target_dir}")
        print(f"Source exists: {source_dir.exists()}")
        
        # Copy Python scripts
        for script_file in ["fire_traits_analysis.py", "fire_plant_location_maps.py"]:
            source_file = source_dir / script_file
            if source_file.exists():
                shutil.copy2(source_file, target_dir / script_file)
                print(f"Copied {script_file}")
            else:
                print(f"Script file not found: {source_file}")
        
        # Run the fire traits analysis script
        script_path = target_dir / "fire_traits_analysis.py"
        if script_path.exists():
            print(f"Running script: {script_path}")
            
            # Run the script
            import subprocess
            result = subprocess.run([
                sys.executable, str(script_path)
            ], capture_output=True, text=True, cwd=str(target_dir))
            
            print(f"Script output: {result.stdout}")
            print(f"Script error: {result.stderr}")
            
            if result.returncode == 0:
                flash("Experiment 4 analysis completed successfully!", "success")
            else:
                flash(f"Experiment 4 analysis failed: {result.stderr}", "error")
        else:
            flash("Experiment 4 script not found!", "error")
            
    except Exception as e:
        flash(f"Error running experiment: {str(e)}", "error")
    
    return redirect(url_for('experiment_4'))

@app.route('/exp5')
def experiment_5():
    """Experiment 5 - Environmental Impact Study"""
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))
    
    # Get list of output files for experiment 5
    exp5_files = []
    output_dir = Path("static/report/experiment5/experiment5_outputs")
    if output_dir.exists():
        for file_path in output_dir.glob("*"):
            if file_path.is_file():
                # Determine icon based on file extension
                if file_path.suffix == '.html':
                    icon = "🌐"
                elif file_path.suffix == '.pdf':
                    icon = "📋"
                elif file_path.suffix == '.png':
                    icon = "📊"
                elif file_path.suffix == '.csv':
                    icon = "📄"
                else:
                    icon = "📁"
                
                exp5_files.append({
                    'name': file_path.name,
                    'icon': icon
                })
    
    return render_template("experiment5.html", exp5_files=exp5_files, username=session.get("username"))

@app.route('/run_experiment_5')
def run_experiment_5():
    """Run Experiment 5 - Environmental Impact Study"""
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))
    
    try:
        import sys, shutil, subprocess
        from pathlib import Path

        base_dir = Path(__file__).parent
        source_dir = base_dir / "Remade experiment" / "experiment5"
        target_dir = base_dir / "static" / "report" / "experiment5"
        outputs_dir = target_dir / "experiment5_outputs"

        # Ensure target directories exist
        target_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)
        
        # Remove stale outputs before running the script
        for old_file in outputs_dir.glob("*"):
            if old_file.is_file():
                try:
                    old_file.unlink()
                except Exception:
                    pass

        # Copy only the Python script
        script_src = source_dir / "exp5_coding.py"
        if not script_src.exists():
            flash("Experiment 5 script not found in source directory", "error")
            return redirect(url_for('experiment_5'))
        
        shutil.copy2(script_src, target_dir / "exp5_coding.py")

        # Run the script
        script_path = target_dir / "exp5_coding.py"
        if not script_path.exists():
            flash(f"Experiment 5 script not found: {script_path}", "error")
            return redirect(url_for('experiment_5'))

        # Run the script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(target_dir),
            capture_output=True,
            text=True
        )

        # Print to server logs for debugging
        print("[EXP5] STDOUT:\n", result.stdout)
        print("[EXP5] STDERR:\n", result.stderr)

        if result.returncode != 0:
            err_snippet = (result.stderr or "")[:600]
            flash(f"Experiment 5 failed: {err_snippet}", "error")
            return redirect(url_for('experiment_5'))

        # Check for produced outputs (script outputs directly to experiment5_outputs)
        produced_any = False
        for p in outputs_dir.glob("*"):
            if p.is_file():
                produced_any = True
                break

        if produced_any:
            flash("Experiment 5 analysis completed successfully!", "success")
        else:
            flash("Experiment 5 finished but no outputs were found.", "error")

    except Exception as e:
        flash(f"Error running experiment 5: {e}", "error")

    return redirect(url_for('experiment_5'))

@app.route('/exp6')
def experiment_6():
    """Experiment 6 - Biodiversity Assessment (outputs listing)"""
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))

    exp6_files = []
    from pathlib import Path
    output_dir = Path("static/report/experiment6/experiment6_outputs")
    if output_dir.exists():
        for p in output_dir.glob("*"):
            if not p.is_file():
                continue
            if p.name.lower().startswith("species_form_analysis_report"):
                continue
            suffix = p.suffix.lower()
            if suffix == '.html':
                icon = "🌐"
            elif suffix == '.pdf':
                icon = "📋"
            elif suffix == '.png':
                icon = "🖼️"
            elif suffix == '.csv':
                icon = "📄"
            else:
                icon = "📁"
            exp6_files.append({'name': p.name, 'icon': icon})

    return render_template("experiment6.html", exp6_files=exp6_files, username=session.get("username"))



@app.post("/tools/native_traits_export")
def native_traits_export():
    # 需要登录
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))

    try:
        # 直接用 SQLAlchemy 引擎读取三张表
        traits_df  = pd.read_sql("SELECT * FROM traits", db.engine)
        species_df = pd.read_sql("SELECT * FROM species", db.engine)
        stj_df     = pd.read_sql("SELECT * FROM species_trait_junction", db.engine)

        # 仅保留本地种（exotic = 'f'）
        native_species = (
            species_df[species_df['exotic'] == 'f']['scientific_name']
            .dropna().unique()
        )
        stj_df = stj_df[stj_df['scientific_name'].isin(native_species)]

        # 合并 trait 元信息（用于排序）
        stj_df = stj_df.merge(traits_df, on='trait_name', how='left')

        # 映射 trait_value -> 'I' | 'Y' | ''（空）
        def map_value(val):
            if pd.isnull(val) or str(val).strip() == '':
                return ''
            elif str(val).strip().upper() == 'I':
                return 'I'
            else:
                return 'Y'

        stj_df['YI'] = stj_df['trait_value'].apply(map_value)

        # 透视：物种为行、trait 为列；同一物种-性状多条时优先 'I'，否则 'Y'
        pivot_df = stj_df.pivot_table(
            index='scientific_name',
            columns='trait_name',
            values='YI',
            aggfunc=lambda x: 'I' if 'I' in set(x) else ('Y' if 'Y' in set(x) else '')
        )

        # 根据 traits 表中的 trait_info 对列做个排序（可选）
        if not pivot_df.empty:
            trait_order = traits_df.set_index('trait_name').loc[pivot_df.columns]['trait_info']
            pivot_df = pivot_df[trait_order.sort_values().index]

        # 写入内存中的 Excel 并返回下载
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            pivot_df.to_excel(writer, sheet_name='Native_Species_Traits_YI')
        output.seek(0)

        fname = f"Native_Species_Traits_YI_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return send_file(
            output,
            as_attachment=True,
            download_name=fname,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        # 出错就返回 JSON，方便你调试
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/exp7')
def experiment_7():
    """Experiment 7 - Ecosystem Analysis"""
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))
    return redirect(url_for('species_survey_map'))


@app.route('/exp8')
def experiment_8():
    """Experiment 8 - Historical Species Analysis"""
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))
    
    # Get list of output files for experiment 8 (only specific output files)
    exp8_files = []
    output_dir = Path("static/report/experiment8/experiment8_outputs")
    if output_dir.exists():
        # Only show the two specific output files
        expected_files = ["Historical_Species_Analysis_Report.pdf", "species_survey_map.html"]
        for filename in expected_files:
            file_path = output_dir / filename
            if file_path.exists():
                # Determine icon based on file extension
                if file_path.suffix == '.html':
                    icon = "🌐"
                elif file_path.suffix == '.pdf':
                    icon = "📋"
                else:
                    icon = "📁"
                
                exp8_files.append({
                    'name': file_path.name,
                    'icon': icon
                })
    
    return render_template("experiment8.html", exp8_files=exp8_files)


@app.route('/run_experiment_6')
def run_experiment_6():
    """Run Experiment 6 - Biodiversity Assessment"""
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))

    try:
        import sys, shutil, subprocess
        from pathlib import Path

        base_dir    = Path(__file__).parent
        source_dir  = base_dir / "Remade experiment" / "experiment6"
        target_dir  = base_dir / "static" / "report" / "experiment6"
        outputs_dir = target_dir / "experiment6_outputs"

        # 确保目标目录存在
        target_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)
        # Remove stale outputs before running the script
        for old_file in outputs_dir.glob("*"):
            if old_file.is_file():
                try:
                    old_file.unlink()
                except Exception:
                    pass


        # === 1) 复制脚本和数据 ===
        # 根据你自己的文件命名改这里：
        script_name = "exp6.py"   # 你的主脚本文件名
        files_to_copy = [
            script_name,
            # 下面按需添加你的数据文件名（示例）
            # "ALA_e6.csv",
            # "iNaturalist_e6.csv",
            # "Prototype_e6.csv",
        ]

        missing = []
        for fname in files_to_copy:
            src = source_dir / fname
            if src.exists():
                shutil.copy2(src, target_dir / fname)
            else:
                missing.append(str(src))

        if missing:
            flash("Experiment 6 missing files: " + "; ".join(missing), "error")
            return redirect(url_for('experiment_6'))

        # === 2) 运行脚本 ===
        script_path = target_dir / script_name
        if not script_path.exists():
            flash(f"Experiment 6 script not found: {script_path}", "error")
            return redirect(url_for('experiment_6'))

        # 在 target_dir 下运行脚本；建议你的脚本把产出写到 outputs_dir
        env = dict(**os.environ)
        # 如需给脚本传入输出目录，可通过环境变量或命令行参数；
        # 这里示例用环境变量，脚本里用 os.environ.get("E6_OUTPUT_DIR")
        env["E6_OUTPUT_DIR"] = str(outputs_dir)

        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(target_dir),
            capture_output=True,
            text=True,
            env=env
        )

        # 打印到服务器日志，方便调试
        print("[EXP6] STDOUT:\n", result.stdout)
        print("[EXP6] STDERR:\n", result.stderr)

        if result.returncode != 0:
            # 失败就提示一段错误
            err_snippet = (result.stderr or "")[:600]
            flash(f"Experiment 6 failed: {err_snippet}", "error")
            return redirect(url_for('experiment_6'))

        # === 3) 收集产出 ===
        # 规范：脚本应把结果直接写入 outputs_dir。
        # 若脚本写在 target_dir，下方也会把新文件迁到 outputs_dir（可选）。
        produced_any = False

        # Scan for new files produced under target_dir and copy into outputs_dir
        for p in target_dir.glob("*"):
            if p.is_file() and p.suffix.lower() in {".html", ".pdf", ".png", ".csv"}:
                if p.parent == outputs_dir:
                    produced_any = True
                    continue
                try:
                    shutil.copy2(p, outputs_dir / p.name)
                    produced_any = True
                except Exception as _:
                    pass

        if not produced_any:
            produced_any = any(child.is_file() for child in outputs_dir.glob("*"))

        if produced_any:
            flash("Experiment 6 analysis completed successfully!", "success")
        else:
            flash("Experiment 6 finished but no outputs were found. Check your script to write files into experiment6_outputs.", "error")

    except Exception as e:
        flash(f"Error running experiment 6: {e}", "error")

    return redirect(url_for('experiment_6'))


@app.route('/run_experiment_8')
def run_experiment_8():
    """Run Experiment 8 analysis"""
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))
    
    try:
        # Import the experiment script
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'Remade experiment', 'experiment8'))
        
        # Copy the experiment files to the static directory
        import shutil
        from pathlib import Path
        
        # Use absolute paths to avoid path issues
        base_dir = Path(__file__).parent
        source_dir = base_dir / "Remade experiment" / "experiment8"
        target_dir = base_dir / "static" / "report" / "experiment8"
        output_dir = target_dir / "experiment8_outputs"
        target_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Source directory: {source_dir}")
        print(f"Target directory: {target_dir}")
        print(f"Output directory: {output_dir}")
        print(f"Source exists: {source_dir.exists()}")
        print(f"Target exists: {target_dir.exists()}")
        print(f"Output exists: {output_dir.exists()}")
        
        # Copy Python scripts to target directory
        script_file = "historical_species_analysis.py"
        source_script = source_dir / script_file
        if source_script.exists():
            shutil.copy2(source_script, target_dir / script_file)
            print(f"Copied {script_file}")
        else:
            print(f"Script file not found: {source_script}")
        
        # Copy data file if it exists
        data_file = "all_species_complete_data.csv"
        source_data = source_dir / data_file
        if source_data.exists():
            shutil.copy2(source_data, output_dir / data_file)
            print(f"Copied {data_file}")
        else:
            print(f"Data file not found: {source_data}")
        
        # Copy output files from output directory after script runs
        # This will be done after the script execution
        
        # Run the historical species analysis script
        script_path = target_dir / "historical_species_analysis.py"
        if script_path.exists():
            print(f"Running script: {script_path}")
            
            # Run the script with output directory as working directory
            import subprocess
            result = subprocess.run([
                sys.executable, str(script_path)
            ], capture_output=True, text=True, cwd=str(output_dir))
            
            print(f"Script output: {result.stdout}")
            print(f"Script error: {result.stderr}")
            print(f"Script return code: {result.returncode}")
            
            if result.returncode == 0:
                # Copy output files from output directory to experiment8_outputs
                output_source_dir = output_dir / "output"
                if output_source_dir.exists():
                    for output_file in ["Historical_Species_Analysis_Report.pdf", "species_survey_map.html"]:
                        source_file = output_source_dir / output_file
                        if source_file.exists():
                            shutil.copy2(source_file, output_dir / output_file)
                            print(f"Copied output file: {output_file}")
                        else:
                            print(f"Output file not found: {source_file}")
                
                flash("Experiment 8 analysis completed successfully!", "success")
            else:
                flash(f"Experiment 8 analysis failed: {result.stderr}", "error")
                print(f"Full error details: stdout={result.stdout}, stderr={result.stderr}")
        else:
            flash("Experiment 8 script not found!", "error")
            
    except Exception as e:
        flash(f"Error running experiment: {str(e)}", "error")
    
    return redirect(url_for('experiment_8'))

@app.route('/exp10')
def experiment_10():
    """Experiment 10 - Advanced Research Tools"""
    if ('logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))
    return redirect(url_for('species_survey_map'))

# Route to download reports
@app.route('/download')
def download_report():
    # Get report type and name from form
    report_type = request.form.get('report_type')
    report_name = request.form.get('report_name')
    print("Report Type:", report_type)
    print("Report Name:", report_name)

    # Validate report type and name
    if not report_type or not report_name:
        flash("Missing report_type or report_name for download.", "error")
        return redirect(url_for('generate_report'))

    result = None

    # Retrieve data based on report type and name
    if report_type == "Flora":
        if report_name == "All Species":
            result = query.get_flora_all_species_report(db.session)
        elif report_name == "Summary Report":
            result = query.get_summary_report(db.session, "Flora")
        elif report_name == "Report by Reserve":
            result = query.get_flora_report_by_reserve(db.session)
        elif report_name == "Native Flora = 1 Site":
            try:
                result = query.get_native_flora_equal_1_site(db.session)
            except AttributeError:
                flash("Native Flora = 1 Site report is not implemented or has issues, cannot download.", "error")
                return redirect(url_for('generate_report'))
        else:
            flash("Invalid Flora report type for download.", "error")
            return redirect(url_for('generate_report'))

    elif report_type == "Fauna":
        if report_name == "All Species":
            result = query.get_fauna_all_species_report(db.session)
        elif report_name == "Summary Report":
            result = query.get_summary_report(db.session, "Fauna")
        else:
            flash("Invalid Fauna report type for download.", "error")
            return redirect(url_for('generate_report'))
    else:
        flash("Invalid report type for download.", "error")
        return redirect(url_for('generate_report'))

    # If no data, display warning
    if not result:
        flash(f"No data to download for '{report_name}' for {report_type}.", "warning")
        return redirect(url_for('generate_report'))

    try:
        # Create a Pandas DataFrame from the result
        df_to_download = pd.DataFrame(result)
    except Exception as e:
        flash(f"Error creating DataFrame for download: {e}", "error")
        print(f"Error creating DataFrame for download: {e}", file=sys.stderr)
        return redirect(url_for('generate_report'))

    # Create an in-memory Excel file
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df_to_download.to_excel(writer, index=False, sheet_name='Report')
    writer.close()
    output.seek(0)

    # Send the Excel file as an attachment
    return send_file(output, as_attachment=True, download_name=f'{report_type}_{report_name}.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# Route to log out a user
@app.route('/logout')
def logout():
    session.clear() # Clear the session
    return redirect(url_for('login')) # Redirect to login page

# Add headers to responses to control caching
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Function to get the current logged-in user
def get_current_user():
    if "username" in session:
        return db.session.query(User).filter_by(email=session["username"]).one_or_none()
    return None

# Run the Flask application


# Duplicate definition of PCT_report removed to fix function redefinition error.
    
@app.get("/ping")
def ping():
    return "pong", 200


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    app.run(debug=True, host='0.0.0.0', port=port)
