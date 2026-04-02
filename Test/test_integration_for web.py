# tests/test_integration.py
import io
from urllib.parse import urlparse

# --- basic loddingz ---
def test_ping_ok(client):
    r = client.get("/ping")
    assert r.status_code == 200
    assert b"pong" in r.data

def test_index_redirects_to_login_when_not_logged_in(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 303)
    assert "/login" in r.headers.get("Location", "")

def test_login_page_get(client):
    r = client.get("/login")
    assert r.status_code == 200
    assert b"[[TEMPLATE:login.html]]" in r.data

def test_login_post_success(client):
    r = client.post("/login", data={"username": "tester@example.com", "password": "ok"}, follow_redirects=False)
    assert r.status_code in (302, 303)
    assert "/home" in r.headers.get("Location","")

def test_login_post_fail(client):
    r = client.post("/login", data={"username": "nouser@example.com", "password": "ok"})
    assert r.status_code == 200
    assert b"Username or password is incorrect" in r.data or b"[[TEMPLATE:login.html]]" in r.data

def test_logout_redirects_to_login(logged_in_client):
    r = logged_in_client.get("/logout", follow_redirects=False)
    assert r.status_code in (302, 303)
    assert "/login" in r.headers.get("Location","")

# --- webpage protect ---
def test_home_page(logged_in_client):
    r = logged_in_client.get("/home")
    assert r.status_code == 200
    assert b"[[TEMPLATE:home.html]]" in r.data

def test_flora_dashboard_basic(logged_in_client):
    r = logged_in_client.get("/flora_dashboard")
    assert r.status_code == 200
    assert b"[[TEMPLATE:flora_dashboard.html]]" in r.data

def test_fauna_dashboard_basic(logged_in_client):
    r = logged_in_client.get("/fauna_dashboard")
    assert r.status_code == 200
    assert b"[[TEMPLATE:fauna_dashboard.html]]" in r.data

def test_flora_dashboard_with_filters_and_pagination(logged_in_client):
    r = logged_in_client.get("/flora_dashboard?species=Sp1&reserve=R1&basis=Specimen&page=2&per_page=10&start_year=2019&end_year=2021")
    assert r.status_code == 200

def test_fauna_dashboard_with_filters(logged_in_client):
    r = logged_in_client.get("/fauna_dashboard?genus=Gen1&species=Sp1&class_name=Aves&year=2020&reserve_name=R1")
    assert r.status_code == 200

def test_filter_flora_redirects(logged_in_client):
    r = logged_in_client.post("/filter_flora", data={"species":"Sp1","reserve":"R1"}, follow_redirects=False)
    assert r.status_code in (302,303)
    assert urlparse(r.headers["Location"]).path == "/flora_dashboard"

def test_filter_fauna_redirects(logged_in_client):
    r = logged_in_client.post("/filter_fauna", data={"genus":"Gen1"}, follow_redirects=False)
    assert r.status_code in (302,303)
    assert urlparse(r.headers["Location"]).path == "/fauna_dashboard"

# --- map api ---
def test_api_map_filters(logged_in_client):
    r = logged_in_client.get("/api/map_filters")
    assert r.status_code == 200
    js = r.get_json()
    assert "species" in js and "years" in js

def test_api_map_data(logged_in_client):
    r = logged_in_client.get("/api/map_data?species=Sp1")
    assert r.status_code == 200
    js = r.get_json()
    assert isinstance(js, list) and js

# --- CSV insertion ---
def test_insert_column_returns_csv(logged_in_client):
    src_csv = b"colA,colB\n1,2\n3,4\n"
    tgt_csv = b"x,y\n9,8\n7,6\n"
    data = {
        "source_file": (io.BytesIO(src_csv), "src.csv"),
        "target_file": (io.BytesIO(tgt_csv), "tgt.csv"),
        "column": "colA",
    }
    r = logged_in_client.get("/insert_column", data=data, content_type="multipart/form-data")
    assert r.status_code == 200
    assert r.mimetype == "text/csv"
    body = r.data.decode()
    assert "colA" in body


# --- download ---
def test_report_get_default(logged_in_client):
    r = logged_in_client.get("/report")
    assert r.status_code == 200
    assert b"[[TEMPLATE:report.html]]" in r.data

def test_report_post_flora_all_species(logged_in_client):
    r = logged_in_client.post("/report", data={"report_type":"Flora", "report_name":"All Species"})
    assert r.status_code == 200

def test_download_report_without_form_redirects(logged_in_client):
    r = logged_in_client.get("/download", follow_redirects=False)

    assert r.status_code in (302,303)

# --- user maneger ---
def test_manage_users_page(logged_in_client):
    r = logged_in_client.get("/manage_users")
    assert r.status_code == 200
    assert b"[[TEMPLATE:manage_users.html]]" in r.data

def test_create_user_missing_email(logged_in_client):
    r = logged_in_client.post("/create_user", data={}, follow_redirects=False)
    assert r.status_code in (302,303) 

def test_create_user_success(logged_in_client):
    r = logged_in_client.post("/create_user", data={"email":"new@example.com"}, follow_redirects=False)
  
    assert r.status_code in (302,303)

def test_toggle_user_role(logged_in_client):

    r = logged_in_client.post("/toggle_user_role/123", follow_redirects=False)
    assert r.status_code in (302,303)

def test_delete_user(logged_in_client):
    r = logged_in_client.post("/delete_user/123", follow_redirects=False)
    assert r.status_code in (302,303)

# --- login test ---
def test_forgot_password_get(client):
    r = client.get("/forgot-password")
    assert r.status_code == 200
    assert b"[[TEMPLATE:forgot-password.html]]" in r.data

def test_forgot_password_post_unknown_user(client):
    r = client.post("/forgot-password", data={"email":"unknown@example.com"})
    assert r.status_code == 200


def test_reset_password_token_bad(client):
    r = client.get("/reset_password/badtoken")
    assert r.status_code == 200
    assert b"[[TEMPLATE:login.html]]" in r.data  
def test_reset_password_token_good_get(client):
    r = client.get("/reset_password/goodtoken")
    assert r.status_code == 200
    assert b"[[TEMPLATE:reset_password.html]]" in r.data

def test_reset_password_token_good_post(client):
    r = client.post("/reset_password/goodtoken", data={"password":"newpass"})
    assert r.status_code == 200
    assert b"[[TEMPLATE:login.html]]" in r.data

def test_signup_get(client):
    r = client.get("/signup")
    assert r.status_code == 200
    assert b"[[TEMPLATE:signup.html]]" in r.data

def test_settings_requires_login(client):
    r = client.get("/settings", follow_redirects=False)
    assert r.status_code in (302,303)
    assert "/login" in r.headers.get("Location","")
