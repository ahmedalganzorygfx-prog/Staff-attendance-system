import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent / "data" / "attendance.db"


def normalize_code(value: str) -> str:
    value = str(value or "")
    trans = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
    return value.translate(trans).strip().upper()


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            job_title TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_code TEXT NOT NULL,
            employee_name TEXT NOT NULL,
            action TEXT NOT NULL CHECK(action IN ('حضور','انصراف')),
            work_date TEXT NOT NULL,
            work_time TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            distance_m REAL,
            accuracy_m REAL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """)
        defaults = {
            "branch_name": "الأكاديمية المهنية للمعلمين – فرع الجيزة",
            "branch_latitude": "",
            "branch_longitude": "",
            "radius_m": "100",
            "admin_password": "123456",
            "site_token": "",
        }
        for k, v in defaults.items():
            conn.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (k, v))


def get_setting(key, default=""):
    with connect() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key, value):
    with connect() as conn:
        conn.execute("""
            INSERT INTO settings(key,value) VALUES(?,?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
        """, (key, str(value)))


def get_employee(code, active_only=False):
    code = normalize_code(code)
    sql = "SELECT * FROM employees WHERE employee_code=?"
    params = [code]
    if active_only:
        sql += " AND active=1"
    with connect() as conn:
        row = conn.execute(sql, params).fetchone()
    return dict(row) if row else None


def add_employee(code, name, job_title="", phone=""):
    code = normalize_code(code)
    name = str(name or "").strip()
    job_title = str(job_title or "").strip()
    phone = str(phone or "").strip()
    if not code:
        return False, "أدخل كود الموظف."
    if not name:
        return False, "أدخل اسم الموظف."

    existing = get_employee(code)
    if existing:
        status = "نشط" if existing["active"] else "غير نشط"
        return False, f"كود الموظف {code} موجود بالفعل باسم {existing['name']} ({status})."

    try:
        with connect() as conn:
            conn.execute("""
                INSERT INTO employees(employee_code,name,job_title,phone,active,created_at)
                VALUES(?,?,?,?,1,?)
            """, (code, name, job_title, phone, datetime.now().isoformat(timespec="seconds")))
        return True, "تمت إضافة الموظف بنجاح."
    except sqlite3.IntegrityError:
        return False, f"كود الموظف {code} موجود بالفعل."


def update_employee(original_code, name, job_title, phone):
    code = normalize_code(original_code)
    with connect() as conn:
        cur = conn.execute("""
            UPDATE employees SET name=?, job_title=?, phone=? WHERE employee_code=?
        """, (str(name).strip(), str(job_title or "").strip(), str(phone or "").strip(), code))
        return cur.rowcount > 0


def set_employee_active(code, active):
    with connect() as conn:
        cur = conn.execute("UPDATE employees SET active=? WHERE employee_code=?", (1 if active else 0, normalize_code(code)))
        return cur.rowcount > 0


def delete_employee(code):
    with connect() as conn:
        cur = conn.execute("DELETE FROM employees WHERE employee_code=?", (normalize_code(code),))
        return cur.rowcount > 0


def list_employees():
    with connect() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM employees ORDER BY name COLLATE NOCASE").fetchall()]


def today_records(code):
    code = normalize_code(code)
    today = datetime.now().strftime("%Y-%m-%d")
    with connect() as conn:
        rows = conn.execute("""
            SELECT action, work_time, distance_m, accuracy_m
            FROM attendance WHERE employee_code=? AND work_date=? ORDER BY id
        """, (code, today)).fetchall()
    return [dict(r) for r in rows]


def record_attendance(employee, action, latitude, longitude, distance_m, accuracy_m):
    now = datetime.now()
    with connect() as conn:
        conn.execute("""
            INSERT INTO attendance(
                employee_code,employee_name,action,work_date,work_time,
                latitude,longitude,distance_m,accuracy_m,created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?)
        """, (
            employee["employee_code"], employee["name"], action,
            now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"),
            latitude, longitude, distance_m, accuracy_m, now.isoformat(timespec="seconds")
        ))


def attendance_report(start_date=None, end_date=None, code=None):
    sql = """
        SELECT employee_code AS 'كود الموظف', employee_name AS 'اسم الموظف',
               action AS 'العملية', work_date AS 'التاريخ', work_time AS 'الوقت',
               ROUND(distance_m,2) AS 'المسافة بالمتر', accuracy_m AS 'دقة الموقع بالمتر',
               latitude AS 'خط العرض', longitude AS 'خط الطول'
        FROM attendance WHERE 1=1
    """
    params = []
    if start_date:
        sql += " AND work_date >= ?"; params.append(str(start_date))
    if end_date:
        sql += " AND work_date <= ?"; params.append(str(end_date))
    if code:
        sql += " AND employee_code = ?"; params.append(normalize_code(code))
    sql += " ORDER BY work_date DESC, work_time DESC"
    with connect() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def stats_today():
    today = datetime.now().strftime("%Y-%m-%d")
    with connect() as conn:
        total = conn.execute("SELECT COUNT(*) c FROM employees").fetchone()["c"]
        active = conn.execute("SELECT COUNT(*) c FROM employees WHERE active=1").fetchone()["c"]
        present = conn.execute("SELECT COUNT(*) c FROM attendance WHERE work_date=? AND action='حضور'", (today,)).fetchone()["c"]
        departed = conn.execute("SELECT COUNT(*) c FROM attendance WHERE work_date=? AND action='انصراف'", (today,)).fetchone()["c"]
    return {"total": total, "active": active, "present": present, "departed": departed}
