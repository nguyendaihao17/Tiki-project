import getpass
import hmac
from html import escape
import os
import re
import sqlite3
from contextlib import closing
from pathlib import Path

import bcrypt
import streamlit as st


VALID_ROLES = {"admin", "user"}
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{3,32}$")


def _database_path():
    configured_path = os.environ.get("TIKI_AUTH_DB_PATH")
    if configured_path:
        return Path(configured_path).expanduser()
    return Path(__file__).resolve().parents[1] / "data" / "users.sqlite3"


def _connect():
    path = _database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def initialize_auth_store():
    with closing(_connect()) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY COLLATE NOCASE,
                password_hash BLOB NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin', 'user')),
                display_name TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def _validate_username(username):
    normalized = username.strip()
    if not USERNAME_PATTERN.fullmatch(normalized):
        return None, "Tên đăng nhập phải dài 3-32 ký tự và chỉ gồm chữ, số, dấu chấm, gạch ngang hoặc gạch dưới."
    return normalized, None


def _validate_password(password):
    if len(password) < 12:
        return "Mật khẩu phải có ít nhất 12 ký tự."
    if len(password.encode("utf-8")) > 72:
        return "Mật khẩu không được vượt quá giới hạn 72 byte của bcrypt."
    return None


def _hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def _matches_initial_admin_setup_key(provided_key, configured_key):
    return (
        isinstance(provided_key, str)
        and isinstance(configured_key, str)
        and bool(configured_key)
        and hmac.compare_digest(provided_key, configured_key)
    )


def _initial_admin_setup_key():
    key = os.environ.get("TIKI_INITIAL_ADMIN_SETUP_KEY")
    if key:
        return key
    try:
        key = st.secrets.get("initial_admin_setup_key")
    except FileNotFoundError:
        return None
    return key if isinstance(key, str) and key else None


def _require_admin():
    if not check_permission("admin"):
        raise PermissionError("Chỉ quản trị viên mới được thực hiện thao tác này.")


def user_count():
    initialize_auth_store()
    with closing(_connect()) as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM users").fetchone()
    return row["count"]


def create_initial_admin(username, display_name, password):
    """Tạo admin đầu tiên đúng một lần, an toàn khi có nhiều phiên khởi tạo."""
    normalized, error = _validate_username(username)
    if error:
        return False, error
    if not display_name.strip():
        return False, "Vui lòng nhập tên hiển thị."
    error = _validate_password(password)
    if error:
        return False, error

    initialize_auth_store()
    try:
        with closing(_connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            count = connection.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
            if count:
                connection.rollback()
                return False, "Tài khoản quản trị đầu tiên đã được tạo."
            connection.execute(
                "INSERT INTO users (username, password_hash, role, display_name) VALUES (?, ?, 'admin', ?)",
                (normalized, _hash_password(password), display_name.strip()),
            )
            connection.commit()
    except sqlite3.IntegrityError:
        return False, "Tên đăng nhập đã tồn tại."
    return True, "Đã tạo tài khoản quản trị. Vui lòng đăng nhập."


def authenticate(username, password):
    normalized, error = _validate_username(username)
    if error:
        return None
    initialize_auth_store()
    with closing(_connect()) as connection:
        row = connection.execute(
            "SELECT username, password_hash, role, display_name, is_active FROM users WHERE username = ?",
            (normalized,),
        ).fetchone()

    if row is None or not row["is_active"]:
        return None
    try:
        verified = bcrypt.checkpw(password.encode("utf-8"), row["password_hash"])
    except (ValueError, TypeError):
        verified = False
    if not verified:
        return None
    return {
        "username": row["username"],
        "role": row["role"],
        "name": row["display_name"],
    }


def get_active_user(username):
    if not username:
        return None
    initialize_auth_store()
    with closing(_connect()) as connection:
        row = connection.execute(
            "SELECT username, role, display_name FROM users WHERE username = ? AND is_active = 1",
            (username,),
        ).fetchone()
    if row is None:
        return None
    return {"username": row["username"], "role": row["role"], "name": row["display_name"]}


def list_users():
    _require_admin()
    initialize_auth_store()
    with closing(_connect()) as connection:
        rows = connection.execute(
            "SELECT username, display_name, role, is_active, created_at FROM users ORDER BY username"
        ).fetchall()
    return [dict(row) for row in rows]


def _create_user_record(username, display_name, password, role):
    normalized, error = _validate_username(username)
    if error:
        return False, error
    if not display_name.strip():
        return False, "Vui lòng nhập tên hiển thị."
    if role not in VALID_ROLES:
        return False, "Vai trò không hợp lệ."
    error = _validate_password(password)
    if error:
        return False, error

    initialize_auth_store()
    try:
        with closing(_connect()) as connection:
            connection.execute(
                "INSERT INTO users (username, password_hash, role, display_name) VALUES (?, ?, ?, ?)",
                (normalized, _hash_password(password), role, display_name.strip()),
            )
            connection.commit()
    except sqlite3.IntegrityError:
        return False, "Tên đăng nhập đã tồn tại."
    return True, "Đã tạo tài khoản."


def create_user(username, display_name, password, role):
    _require_admin()
    return _create_user_record(username, display_name, password, role)


def register_user(username, display_name, password):
    return _create_user_record(username, display_name, password, "user")


def _active_admin_count(connection):
    return connection.execute(
        "SELECT COUNT(*) AS count FROM users WHERE role = 'admin' AND is_active = 1"
    ).fetchone()["count"]


def set_user_role(username, role):
    _require_admin()
    if role not in VALID_ROLES:
        return False, "Vai trò không hợp lệ."
    if username.casefold() == str(st.session_state.get("username", "")).casefold() and role != "admin":
        return False, "Không thể hạ quyền tài khoản quản trị đang đăng nhập."

    initialize_auth_store()
    with closing(_connect()) as connection:
        connection.execute("BEGIN IMMEDIATE")
        user = connection.execute(
            "SELECT role, is_active FROM users WHERE username = ?", (username,)
        ).fetchone()
        if user is None:
            connection.rollback()
            return False, "Không tìm thấy tài khoản."
        if user["role"] == "admin" and user["is_active"] and role != "admin":
            if _active_admin_count(connection) <= 1:
                connection.rollback()
                return False, "Không thể hạ quyền quản trị viên hoạt động cuối cùng."
        connection.execute("UPDATE users SET role = ? WHERE username = ?", (role, username))
        connection.commit()
    return True, "Đã cập nhật vai trò."


def set_user_active(username, is_active):
    _require_admin()
    if username.casefold() == str(st.session_state.get("username", "")).casefold() and not is_active:
        return False, "Không thể vô hiệu hóa tài khoản quản trị đang đăng nhập."

    initialize_auth_store()
    with closing(_connect()) as connection:
        connection.execute("BEGIN IMMEDIATE")
        user = connection.execute(
            "SELECT role, is_active FROM users WHERE username = ?", (username,)
        ).fetchone()
        if user is None:
            connection.rollback()
            return False, "Không tìm thấy tài khoản."
        if user["role"] == "admin" and user["is_active"] and not is_active:
            if _active_admin_count(connection) <= 1:
                connection.rollback()
                return False, "Không thể vô hiệu hóa quản trị viên hoạt động cuối cùng."
        connection.execute(
            "UPDATE users SET is_active = ? WHERE username = ?", (int(is_active), username)
        )
        connection.commit()
    return True, "Đã cập nhật trạng thái tài khoản."


def reset_user_password(username, new_password):
    _require_admin()
    error = _validate_password(new_password)
    if error:
        return False, error
    initialize_auth_store()
    with closing(_connect()) as connection:
        result = connection.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (_hash_password(new_password), username),
        )
        connection.commit()
    if result.rowcount == 0:
        return False, "Không tìm thấy tài khoản."
    return True, "Đã đặt lại mật khẩu."


def _set_session_user(user):
    st.session_state.authenticated = user is not None
    st.session_state.username = user["username"] if user else None
    st.session_state.role = user["role"] if user else None
    st.session_state.name = user["name"] if user else None


def init_session_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "role" not in st.session_state:
        st.session_state.role = None
    if "name" not in st.session_state:
        st.session_state.name = None


def login_sidebar():
    init_session_state()
    try:
        initialize_auth_store()
        if st.session_state.authenticated:
            user = get_active_user(st.session_state.username)
            if user is None:
                _set_session_user(None)
            else:
                _set_session_user(user)
        account_count = user_count()
    except sqlite3.Error:
        st.error("Không thể mở kho tài khoản. Kiểm tra quyền truy cập tệp dữ liệu người dùng.")
        return False

    if account_count == 0:
        st.title("Thiết lập TikiLens")
        setup_key = _initial_admin_setup_key()
        if not setup_key or len(setup_key) < 16:
            st.error("Ứng dụng chưa có khóa thiết lập quản trị viên hợp lệ.")
            st.caption("Trong Streamlit Cloud, mở Settings → Secrets và thêm khóa riêng tối thiểu 16 ký tự.")
            st.code('initial_admin_setup_key = "một-khóa-riêng-dài-và-khó-đoán"', language="toml")
            return False

        st.info("Tạo tài khoản quản trị viên đầu tiên. Khóa thiết lập chỉ dùng để bảo vệ bước này.")
        with st.form("initial_admin_setup"):
            provided_key = st.text_input("Khóa thiết lập", type="password")
            username = st.text_input("Tên đăng nhập", placeholder="VD: admin")
            display_name = st.text_input("Tên hiển thị", placeholder="VD: Quản trị viên")
            password = st.text_input("Mật khẩu", type="password", help="Ít nhất 12 ký tự, tối đa 72 byte.")
            confirmation = st.text_input("Nhập lại mật khẩu", type="password")
            submitted = st.form_submit_button("Tạo tài khoản quản trị", type="primary")
        if submitted:
            if not _matches_initial_admin_setup_key(provided_key, setup_key):
                st.error("Khóa thiết lập không đúng.")
            elif password != confirmation:
                st.error("Hai mật khẩu chưa khớp.")
            else:
                try:
                    success, message = create_initial_admin(username, display_name, password)
                except sqlite3.Error:
                    st.error("Không thể tạo tài khoản lúc này. Vui lòng thử lại sau.")
                else:
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        return False

    if not st.session_state.authenticated:
        login_form_version = st.session_state.get("login_form_version", 0)
        left, center, right = st.columns([1, 1.8, 1])
        with center:
            st.markdown('<div class="login-eyebrow">TIKILENS · ANALYTICS WORKSPACE</div>', unsafe_allow_html=True)
            st.title("Chào mừng đến TikiLens")
            st.caption("Đăng nhập hoặc tạo tài khoản để khám phá dữ liệu và báo cáo phân tích Tiki.")
            with st.container(border=True):
                login_tab, register_tab = st.tabs(["Đăng nhập", "Đăng ký"])
                with login_tab:
                    with st.form("login_form"):
                        username = st.text_input("Tên đăng nhập", placeholder="Nhập tên đăng nhập", autocomplete="username", key=f"login_username_{login_form_version}")
                        password = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu", autocomplete="current-password", key=f"login_password_{login_form_version}")
                        submitted = st.form_submit_button("Vào hệ thống", type="primary", width="stretch")
                    if submitted:
                        try:
                            user = authenticate(username, password)
                        except sqlite3.Error:
                            st.error("Không thể kiểm tra tài khoản lúc này. Vui lòng thử lại sau.")
                            return False
                        if user is None:
                            st.error("Tên đăng nhập hoặc mật khẩu không đúng, hoặc tài khoản đã bị vô hiệu hóa.")
                        else:
                            _set_session_user(user)
                            st.rerun()
                    st.caption("Quên mật khẩu? Liên hệ quản trị viên để được đặt lại.")
                with register_tab:
                    st.caption("Tài khoản mới có quyền Người dùng. Quản trị viên có thể thay đổi quyền sau.")
                    with st.form(f"register_form_{login_form_version}"):
                        new_username = st.text_input("Tên đăng nhập", placeholder="VD: nguyenvana", help="3–32 ký tự: chữ, số, dấu . _ -", key=f"register_username_{login_form_version}")
                        display_name = st.text_input("Tên hiển thị", placeholder="Tên bạn muốn hiển thị", key=f"register_name_{login_form_version}")
                        new_password = st.text_input("Mật khẩu", type="password", autocomplete="new-password", help="Ít nhất 12 ký tự, tối đa 72 byte.", key=f"register_password_{login_form_version}")
                        confirmation = st.text_input("Nhập lại mật khẩu", type="password", autocomplete="new-password", key=f"register_confirmation_{login_form_version}")
                        registered = st.form_submit_button("Tạo tài khoản", type="primary", width="stretch")
                    if registered:
                        if new_password != confirmation:
                            st.error("Hai mật khẩu chưa khớp.")
                        else:
                            try:
                                success, message = register_user(new_username, display_name, new_password)
                                user = get_active_user(new_username.strip()) if success else None
                            except sqlite3.Error:
                                st.error("Không thể tạo tài khoản lúc này. Vui lòng thử lại sau.")
                                return False
                            if not success:
                                st.error(message)
                            elif user is None:
                                st.success("Đã tạo tài khoản. Hãy chuyển sang Đăng nhập.")
                            else:
                                _set_session_user(user)
                                st.rerun()
        return False

    st.sidebar.markdown("### TikiLens")
    st.sidebar.caption("Không gian phân tích thương mại điện tử")
    st.sidebar.markdown(f"<div class='user-name'>{escape(st.session_state.name)}</div>",
                        unsafe_allow_html=True)
    st.sidebar.caption(access_role_badge(st.session_state.role))
    if st.sidebar.button("Đăng xuất", width="stretch"):
        _set_session_user(None)
        login_form_version = st.session_state.get("login_form_version", 0)
        st.session_state.login_form_version = login_form_version + 1
        st.session_state.pop(f"login_username_{login_form_version}", None)
        st.session_state.pop(f"login_password_{login_form_version}", None)
        st.session_state.pop(f"register_password_{login_form_version}", None)
        st.session_state.pop(f"register_confirmation_{login_form_version}", None)
        st.rerun()
    return True


def access_role_badge(role):
    return "Vai trò: Quản trị viên" if role == "admin" else "Vai trò: Người dùng"


def check_permission(required_role):
    if required_role not in VALID_ROLES:
        return False
    username = st.session_state.get("username")
    if not st.session_state.get("authenticated") or not username:
        return False

    user = get_active_user(username)
    if user is None:
        _set_session_user(None)
        return False
    _set_session_user(user)
    return user["role"] == "admin" or user["role"] == required_role


def _bootstrap_admin_from_terminal():
    if user_count():
        print("Kho tài khoản đã có người dùng; không thể tạo Admin đầu tiên.")
        return 1

    print("Tạo tài khoản Admin đầu tiên. Mật khẩu tối thiểu 12 ký tự.")
    username = input("Tên đăng nhập: ")
    display_name = input("Tên hiển thị: ")
    password = getpass.getpass("Mật khẩu: ")
    confirmation = getpass.getpass("Nhập lại mật khẩu: ")
    if password != confirmation:
        print("Hai mật khẩu không khớp.")
        return 1

    success, message = create_initial_admin(username, display_name, password)
    print(message)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(_bootstrap_admin_from_terminal())
