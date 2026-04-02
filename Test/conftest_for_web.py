# tests/conftest.py
import sys, types, importlib.util, pathlib, io
import pytest
from sqlalchemy.pool import StaticPool

# === 路径按你的实际项目来 ===
ROOT = pathlib.Path(__file__).resolve().parents[1]
APP_DIR = ROOT  # 如果你的文件在包 app/ 里，就改成 ROOT / "app"
ENTRY = APP_DIR / "__init__.py"  # 就是你贴的那份大文件；若名为 app.py 就改

# === 注入测试 config ===
config_mod = types.ModuleType("config")
class Config:
    TESTING = True
    SECRET_KEY = "testkey"
    SECRET_INITIAL_PASSWORD = "init-secret"
    MAIL_DEFAULT_SENDER = "noreply@example.com"
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_ENGINE_OPTIONS = {"poolclass": StaticPool}
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_CONNECT_ARGS = {"check_same_thread": False}
config_mod.Config = Config
sys.modules["config"] = config_mod

# === 动态加载应用 ===
spec = importlib.util.spec_from_file_location("plant_site_app", str(ENTRY))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

try:
    flask_app = mod.app
except AttributeError as e:
    raise RuntimeError("没找到 app = Flask(__name__)") from e

# === 有两个全局在你的代码中会用到（否则 NameError）===
# 建议你在源代码里加： original_df = None; merged_data_storage = {}
# 这里兜底一下
if not hasattr(mod, "original_df"):
    mod.original_df = None
if not hasattr(mod, "merged_data_storage"):
    mod.merged_data_storage = {}

# === 统一打桩（模板/邮件/文件IO/查询层/DB更新）===
@pytest.fixture(autouse=True)
def _patch_common(monkeypatch):
    # 1) 模板：返回占位文本避免缺模板
    def fake_render_template(name, **ctx):
        # 也能顺便覆盖 context 反序列化场景
        return f"[[TEMPLATE:{name}]]", 200
    monkeypatch.setattr(mod, "render_template", fake_render_template, raising=True)

    # 2) 邮件：不实际发送
    class DummyMail:
        def send(self, *a, **kw): pass
    if hasattr(mod, "mail") and mod.mail:
        monkeypatch.setattr(mod.mail, "send", DummyMail().send, raising=True)

    # 3) pandas：给 CSV/Excel 提供最小数据，避免依赖外部文件
    import pandas as pd

    def fake_read_csv(file, *a, **kw):
        # insert_column 用到 request.files，所以 file 可能是 FileStorage
        if hasattr(file, "read"):
            file.stream.seek(0)
            return pd.read_csv(io.BytesIO(file.read()))
        # 懒加载 traits 的 CSV
        return pd.DataFrame({
            "species_name": ["Aaa", "Bbb"],
            "flower_colour": ["red, white", "blue"],
            "plant_height": ["1-2 m", "3-4 m"]
        })
    def fake_read_excel(file, *a, **kw):
        fn = str(file)
        if "Value" in fn:
            return pd.DataFrame({
                "trait": ["flower_colour"],
                "allowed_values_levels": ["red;blue"],
                "categorical_trait_description": ["color values"]
            })
        return pd.DataFrame({
            "trait": ["flower_colour"],
            "whatever": ["meta"]
        })

    monkeypatch.setattr(mod.pd, "read_csv", fake_read_csv, raising=True)
    monkeypatch.setattr(mod.pd, "read_excel", fake_read_excel, raising=True)

    # 4) query 层：flora/fauna/dashboard/map/report 用到的函数打桩
    class Obj:
        def __init__(self, d): self._d = dict(d)
        def to_dict(self): return dict(self._d)

    class Pager:
        def __init__(self, items):
            self._items = items
            self.total = len(items)
            self.has_next = False
            self.prev_num = None
            self.next_num = None
        @property
        def items(self): return self._items
        def paginate(self, page=1, per_page=20, error_out=False): return self
        def all(self): return self._items

    def q_get_options_occurrences(_s):
        return {
            "speciesOptions": ["Sp1"],
            "datasetOptions": ["DS1"],
            "reserveOptions": ["R1"],
            "localityOptions": ["Loc1"],
            "habitatOptions": ["Hab1"],
            "basisOptions": ["Specimen"],
            "plantedNativeOptions": [0,1],
            "threatenedStatusOptions": ["Rare"],
            "yearOptions": [2019, 2020, 2021]
        }
    def q_get_observations_query(*a, **kw):
        return Pager([Obj({"occurrenceId": 1, "scientificName": "AAA"})])
    def q_get_observations(*a, **kw):
        return [{"id": 1, "lat": -33.8, "lng": 151.2}]
    def q_get_options_fauna(_s):
        return {
            "genusOptions": ["Gen1"],
            "speciesOptions": ["Sp1"],
            "familyOptions": ["Fam1"],
            "vernacularNameOptions": ["Name1"],
            "classNameOptions": ["Aves"],
            "rareEndangeredOptions": ["Yes","No"],
            "localRareEndangeredOptions": ["Yes","No"],
            "exoticOptions": ["Yes","No"],
            "yearOptions": [2018, 2020],
            "reserveNameOptions": ["R1"]
        }
    def q_get_fauna_query(*a, **kw):
        return Pager([Obj({"genus": "Gen1", "species": "Sp1", "vernacular_name": "Bird"})])
    def q_get_flora_all_species_report(_s): return [{"name":"X"}]
    def q_get_summary_report(_s, typ): return [{"summary":"ok","type":typ}]
    def q_get_flora_report_by_reserve(_s): return [{"reserve":"R1"}]

    monkeypatch.setattr(mod.query, "get_options_occurrences", q_get_options_occurrences, raising=True)
    monkeypatch.setattr(mod.query, "get_observations_query", q_get_observations_query, raising=True)
    monkeypatch.setattr(mod.query, "get_observations", q_get_observations, raising=True)
    monkeypatch.setattr(mod.query, "get_options_fauna", q_get_options_fauna, raising=True)
    monkeypatch.setattr(mod.query, "get_fauna_query", q_get_fauna_query, raising=True)
    monkeypatch.setattr(mod.query, "get_flora_all_species_report", q_get_flora_all_species_report, raising=True)
    monkeypatch.setattr(mod.query, "get_summary_report", q_get_summary_report, raising=True)
    monkeypatch.setattr(mod.query, "get_flora_report_by_reserve", q_get_flora_report_by_reserve, raising=True)

    # 5) db_management.update_db：直接返回 1（成功）
    def fake_update_db(db, sql, params): return 1
    monkeypatch.setattr(mod.db_management, "update_db", fake_update_db, raising=True)

    # 6) 伪造 db.session.query(User...) 能用
    #    - manage_users: .all()
    #    - login/forgot/reset/signup: .filter_by(...).one_or_none()
    #    - get_current_user: .filter_by(...).one_or_none()
    class FakeUser:
        def __init__(self, email, password="hashed", role="user", write_permission=False):
            self.email = email
            self.password = password
            self.role = role
            self.write_permission = write_permission
        def set_password(self, pw): self.password = f"hashed:{pw}"
        def verify_password(self, pw): return pw == "ok"
        def is_admin(self): return self.role == "Administrator"

    USERS = {
        "admin@example.com": FakeUser("admin@example.com", "hashed", role="Administrator"),
        "tester@example.com": FakeUser("tester@example.com", "hashed", role="user"),
        "nouser@example.com": None,
    }

    class FakeUserQuery:
        def __init__(self, users): self._users = users
        def all(self): return [u for u in self._users.values() if u]
        def filter_by(self, **kw):
            email = kw.get("email")
            res = USERS.get(email)
            return types.SimpleNamespace(one_or_none=lambda: res)

    class FakeSession:
        def query(self, model):
            # 仅对 User 生效，其他模型测试里不碰就行
            if model.__name__ == "User":
                return FakeUserQuery(USERS)
            # 对其他 ORM 查询（例如 view_traits）你可以再补充
            # 这里返回一个空对象避免误用
            return types.SimpleNamespace(all=lambda: [], count=lambda: 0)

    monkeypatch.setattr(mod.db, "session", FakeSession(), raising=False)

    # 7) User.confirm_token / generate_token 打桩
    def fake_confirm_token(app, token):
        return "tester@example.com" if token == "goodtoken" else None
    def fake_generate_token(app, email): return "goodtoken"

    monkeypatch.setattr(mod.User, "confirm_token", staticmethod(fake_confirm_token), raising=True)
    monkeypatch.setattr(mod.User, "generate_token", staticmethod(fake_generate_token), raising=True)

    yield

# === Flask 测试客户端 ===
@pytest.fixture
def app():
    flask_app.config.update(TESTING=True)
    return flask_app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def logged_in_client(client):
    with client.session_transaction() as s:
        s["logged_in"] = True
        s["username"] = "admin@example.com"
        s["is_admin"] = True
        s["edit_mode"] = False
    return client
