import sqlite3
from datetime import datetime, date
from pathlib import Path


# =========================================================
# إعداد قاعدة البيانات
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DB_NAME = BASE_DIR / "attendance.db"


def get_connection():

    conn = sqlite3.connect(
        DB_NAME,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    conn.execute(
        "PRAGMA journal_mode = WAL"
    )

    return conn


# =========================================================
# إنشاء قاعدة البيانات
# =========================================================

def init_db():

    with get_connection() as conn:

        cursor = conn.cursor()

        # -------------------------------------------------
        # الإعدادات
        # -------------------------------------------------

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)

        # -------------------------------------------------
        # الموظفون
        # -------------------------------------------------

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (

            employee_code TEXT PRIMARY KEY,

            name TEXT NOT NULL,

            job_title TEXT,

            phone TEXT,

            active INTEGER DEFAULT 1,

            created_at TEXT
        )
        """)

        # -------------------------------------------------
        # الحضور والانصراف
        # -------------------------------------------------

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            employee_code TEXT NOT NULL,

            name TEXT NOT NULL,

            action TEXT NOT NULL,

            timestamp TEXT NOT NULL,

            latitude REAL,

            longitude REAL,

            distance_m REAL,

            accuracy_m REAL,

            FOREIGN KEY (employee_code)
            REFERENCES employees(employee_code)
        )
        """)

        # -------------------------------------------------
        # سجل الإدارة
        # -------------------------------------------------

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_logs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            action TEXT NOT NULL,

            details TEXT,

            created_at TEXT NOT NULL
        )
        """)

        # -------------------------------------------------
        # تحديث قواعد البيانات القديمة
        # -------------------------------------------------

        cursor.execute(
            "PRAGMA table_info(employees)"
        )

        columns = [
            row["name"]
            for row in cursor.fetchall()
        ]

        if "created_at" not in columns:

            cursor.execute("""
            ALTER TABLE employees
            ADD COLUMN created_at TEXT
            """)

        # -------------------------------------------------
        # Indexes
        # -------------------------------------------------

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_attendance_employee
        ON attendance(employee_code)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_attendance_timestamp
        ON attendance(timestamp)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_attendance_employee_time
        ON attendance(employee_code, timestamp)
        """)

        conn.commit()


# =========================================================
# الإعدادات
# =========================================================

def get_setting(key, default=""):

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT value
            FROM settings
            WHERE key = ?
            """,
            (key,)
        )

        row = cursor.fetchone()

        if row:
            return row["value"]

        return default


def set_setting(key, value):

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO settings (
                key,
                value
            )
            VALUES (?, ?)

            ON CONFLICT(key)
            DO UPDATE SET value = excluded.value
            """,
            (
                key,
                str(value)
            )
        )

        conn.commit()


# =========================================================
# سجل الإدارة
# =========================================================

def log_admin(action, details=""):

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO admin_logs (
                action,
                details,
                created_at
            )
            VALUES (?, ?, ?)
            """,
            (
                action,
                details,
                now
            )
        )

        conn.commit()


def list_admin_logs(limit=200):

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                action,
                details,
                created_at
            FROM admin_logs
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(limit),)
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]


# =========================================================
# أكواد الموظفين
# =========================================================

def normalize_code(code):

    if code is None:
        return ""

    code = str(code).strip()

    if not code:
        return ""

    # إزالة .0 الناتجة من Excel أحيانًا
    if code.endswith(".0"):

        try:
            code = str(
                int(float(code))
            )

        except Exception:
            pass

    # إذا كان الكود رقميًا نجعله 3 خانات على الأقل
    if code.isdigit():

        return code.zfill(3)

    return code


# =========================================================
# الموظفون
# =========================================================

def add_employee(
    code,
    name,
    job_title="",
    phone=""
):

    code = normalize_code(code)

    name = str(name).strip()

    job_title = str(
        job_title or ""
    ).strip()

    phone = str(
        phone or ""
    ).strip()

    if not code:

        return (
            False,
            "يرجى إدخال كود الموظف."
        )

    if not name:

        return (
            False,
            "يرجى إدخال اسم الموظف."
        )

    if phone:

        phone_check = (
            phone.replace("+", "")
            .replace("-", "")
            .replace(" ", "")
        )

        if not phone_check.isdigit():

            return (
                False,
                "رقم الهاتف غير صحيح."
            )

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT employee_code
            FROM employees
            WHERE employee_code = ?
            """,
            (code,)
        )

        if cursor.fetchone():

            return (
                False,
                "كود الموظف مستخدم بالفعل."
            )

        cursor.execute(
            """
            INSERT INTO employees (

                employee_code,
                name,
                job_title,
                phone,
                active,
                created_at

            )
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            (
                code,
                name,
                job_title,
                phone,
                now
            )
        )

        conn.commit()

    log_admin(
        "إضافة موظف",
        f"{code} - {name}"
    )

    return (
        True,
        "تم إضافة الموظف بنجاح."
    )


def get_employee(
    code,
    active_only=True
):

    code = normalize_code(code)

    if not code:
        return None

    with get_connection() as conn:

        cursor = conn.cursor()

        query = """
        SELECT *
        FROM employees
        WHERE employee_code = ?
        """

        params = [code]

        if active_only:

            query += """
            AND active = 1
            """

        cursor.execute(
            query,
            params
        )

        row = cursor.fetchone()

        return (
            dict(row)
            if row
            else None
        )


def list_employees():

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM employees
        ORDER BY employee_code ASC
        """)

        return [
            dict(row)
            for row in cursor.fetchall()
        ]


def update_employee(
    code,
    name,
    job_title,
    phone
):

    code = normalize_code(code)

    name = str(name).strip()

    if not name:
        return False

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE employees

            SET
                name = ?,
                job_title = ?,
                phone = ?

            WHERE employee_code = ?
            """,
            (
                name,
                str(job_title or "").strip(),
                str(phone or "").strip(),
                code
            )
        )

        changed = cursor.rowcount > 0

        conn.commit()

    if changed:

        log_admin(
            "تعديل موظف",
            f"{code} - {name}"
        )

    return changed


def set_employee_active(
    code,
    active_status
):

    code = normalize_code(code)

    status = (
        1
        if active_status
        else 0
    )

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE employees
            SET active = ?
            WHERE employee_code = ?
            """,
            (
                status,
                code
            )
        )

        conn.commit()

    status_text = (
        "نشط"
        if status
        else "غير نشط"
    )

    log_admin(
        "تغيير حالة موظف",
        f"{code} -> {status_text}"
    )


def delete_employee(code):

    code = normalize_code(code)

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT name
            FROM employees
            WHERE employee_code = ?
            """,
            (code,)
        )

        employee = cursor.fetchone()

        if not employee:

            return (
                False,
                "الموظف غير موجود."
            )

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM attendance
            WHERE employee_code = ?
            """,
            (code,)
        )

        count = cursor.fetchone()["total"]

        if count > 0:

            return (
                False,
                "لا يمكن حذف الموظف لوجود سجلات حضور وانصراف مرتبطة به. يمكنك تعطيله بدلًا من حذفه."
            )

        cursor.execute(
            """
            DELETE FROM employees
            WHERE employee_code = ?
            """,
            (code,)
        )

        conn.commit()

    log_admin(
        "حذف موظف",
        f"{code} - {employee['name']}"
    )

    return (
        True,
        "تم حذف الموظف بنجاح."
    )


# =========================================================
# الحضور والانصراف
# =========================================================

def record_attendance(
    employee,
    action,
    lat,
    lon,
    dist,
    accuracy=None
):

    if action not in (
        "حضور",
        "انصراف"
    ):

        return (
            False,
            "نوع العملية غير صحيح."
        )

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    code = employee[
        "employee_code"
    ]

    # فحص إضافي داخل قاعدة البيانات
    today = today_records(code)

    if action == "حضور":

        if any(
            item["action"] == "حضور"
            for item in today
        ):

            return (
                False,
                "تم تسجيل الحضور اليوم بالفعل."
            )

    if action == "انصراف":

        has_attendance = any(
            item["action"] == "حضور"
            for item in today
        )

        has_departure = any(
            item["action"] == "انصراف"
            for item in today
        )

        if not has_attendance:

            return (
                False,
                "لا يمكن تسجيل الانصراف قبل الحضور."
            )

        if has_departure:

            return (
                False,
                "تم تسجيل الانصراف اليوم بالفعل."
            )

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO attendance (

                employee_code,
                name,
                action,
                timestamp,
                latitude,
                longitude,
                distance_m,
                accuracy_m

            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                employee["employee_code"],
                employee["name"],
                action,
                now,
                float(lat),
                float(lon),
                float(dist),
                float(accuracy)
                if accuracy is not None
                else None
            )
        )

        conn.commit()

    return (
        True,
        f"تم تسجيل {action} بنجاح."
    )


def today_records(code):

    code = normalize_code(code)

    today_str = date.today().strftime(
        "%Y-%m-%d"
    )

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT

                action,
                timestamp,
                distance_m,
                accuracy_m

            FROM attendance

            WHERE
                employee_code = ?
                AND date(timestamp) = ?

            ORDER BY timestamp ASC
            """,
            (
                code,
                today_str
            )
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]


# =========================================================
# إحصائيات اليوم
# =========================================================

def stats_today():

    today_str = date.today().strftime(
        "%Y-%m-%d"
    )

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute("""
        SELECT COUNT(*) AS total
        FROM employees
        """)

        total = cursor.fetchone()["total"]

        cursor.execute("""
        SELECT COUNT(*) AS active
        FROM employees
        WHERE active = 1
        """)

        active = cursor.fetchone()["active"]

        cursor.execute(
            """
            SELECT
                COUNT(DISTINCT employee_code)
                AS present

            FROM attendance

            WHERE
                date(timestamp) = ?
                AND action = 'حضور'
            """,
            (today_str,)
        )

        present = cursor.fetchone()[
            "present"
        ]

        cursor.execute(
            """
            SELECT
                COUNT(DISTINCT employee_code)
                AS departed

            FROM attendance

            WHERE
                date(timestamp) = ?
                AND action = 'انصراف'
            """,
            (today_str,)
        )

        departed = cursor.fetchone()[
            "departed"
        ]

        absent = max(
            active - present,
            0
        )

        return {
            "total": total,
            "active": active,
            "present": present,
            "departed": departed,
            "absent": absent
        }


# =========================================================
# كشف الغياب
# =========================================================

def absent_today():

    today_str = date.today().strftime(
        "%Y-%m-%d"
    )

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT

                employee_code,
                name,
                job_title,
                phone

            FROM employees

            WHERE

                active = 1

                AND employee_code NOT IN (

                    SELECT DISTINCT employee_code

                    FROM attendance

                    WHERE
                        date(timestamp) = ?
                        AND action = 'حضور'
                )

            ORDER BY employee_code ASC
            """,
            (today_str,)
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]


# =========================================================
# ساعات العمل
# =========================================================

def working_hours(
    code,
    target_date
):

    code = normalize_code(code)

    if isinstance(
        target_date,
        date
    ):

        target_date = (
            target_date.strftime(
                "%Y-%m-%d"
            )
        )

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                action,
                timestamp

            FROM attendance

            WHERE
                employee_code = ?
                AND date(timestamp) = ?

            ORDER BY timestamp ASC
            """,
            (
                code,
                target_date
            )
        )

        rows = cursor.fetchall()

    attendance_time = None
    departure_time = None

    for row in rows:

        if (
            row["action"] == "حضور"
            and attendance_time is None
        ):
            attendance_time = row[
                "timestamp"
            ]

        elif row["action"] == "انصراف":
            departure_time = row[
                "timestamp"
            ]

    if (
        attendance_time
        and departure_time
    ):

        start = datetime.strptime(
            attendance_time,
            "%Y-%m-%d %H:%M:%S"
        )

        end = datetime.strptime(
            departure_time,
            "%Y-%m-%d %H:%M:%S"
        )

        seconds = (
            end - start
        ).total_seconds()

        if seconds >= 0:

            return round(
                seconds / 3600,
                2
            )

    return 0.0


# =========================================================
# تقرير تفصيلي
# =========================================================

def attendance_report(
    start_date,
    end_date,
    code_filter=None
):

    if hasattr(
        start_date,
        "strftime"
    ):
        start_date = start_date.strftime(
            "%Y-%m-%d"
        )

    if hasattr(
        end_date,
        "strftime"
    ):
        end_date = end_date.strftime(
            "%Y-%m-%d"
        )

    with get_connection() as conn:

        cursor = conn.cursor()

        query = """
        SELECT

            employee_code AS "كود الموظف",

            name AS "اسم الموظف",

            action AS "العملية",

            timestamp AS "التاريخ والوقت",

            ROUND(distance_m, 2)
            AS "المسافة (متر)",

            ROUND(accuracy_m, 2)
            AS "دقة GPS (متر)"

        FROM attendance

        WHERE
            date(timestamp)
            BETWEEN ? AND ?
        """

        params = [
            start_date,
            end_date
        ]

        if code_filter:

            query += """
            AND employee_code = ?
            """

            params.append(
                normalize_code(
                    code_filter
                )
            )

        query += """
        ORDER BY timestamp DESC
        """

        cursor.execute(
            query,
            params
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]


# =========================================================
# تقرير يومي مجمع
# =========================================================

def daily_summary_report(
    start_date,
    end_date,
    code_filter=None
):

    if hasattr(
        start_date,
        "strftime"
    ):
        start_date = start_date.strftime(
            "%Y-%m-%d"
        )

    if hasattr(
        end_date,
        "strftime"
    ):
        end_date = end_date.strftime(
            "%Y-%m-%d"
        )

    with get_connection() as conn:

        cursor = conn.cursor()

        query = """
        SELECT

            employee_code,
            name,
            date(timestamp) AS work_date,

            MIN(
                CASE
                WHEN action = 'حضور'
                THEN timestamp
                END
            ) AS attendance_time,

            MAX(
                CASE
                WHEN action = 'انصراف'
                THEN timestamp
                END
            ) AS departure_time

        FROM attendance

        WHERE
            date(timestamp)
            BETWEEN ? AND ?
        """

        params = [
            start_date,
            end_date
        ]

        if code_filter:

            query += """
            AND employee_code = ?
            """

            params.append(
                normalize_code(
                    code_filter
                )
            )

        query += """
        GROUP BY
            employee_code,
            name,
            date(timestamp)

        ORDER BY
            work_date DESC,
            employee_code ASC
        """

        cursor.execute(
            query,
            params
        )

        rows = cursor.fetchall()

    result = []

    for row in rows:

        hours = 0.0

        if (
            row["attendance_time"]
            and row["departure_time"]
        ):

            start = datetime.strptime(
                row["attendance_time"],
                "%Y-%m-%d %H:%M:%S"
            )

            end = datetime.strptime(
                row["departure_time"],
                "%Y-%m-%d %H:%M:%S"
            )

            seconds = (
                end - start
            ).total_seconds()

            if seconds >= 0:

                hours = round(
                    seconds / 3600,
                    2
                )

        result.append({

            "كود الموظف":
                row["employee_code"],

            "اسم الموظف":
                row["name"],

            "التاريخ":
                row["work_date"],

            "وقت الحضور":
                row["attendance_time"] or "",

            "وقت الانصراف":
                row["departure_time"] or "",

            "ساعات العمل":
                hours
        })

    return result


# =========================================================
# قاعدة البيانات كملف للنسخ الاحتياطي
# =========================================================

def database_backup_bytes():

    if not DB_NAME.exists():
        return None

    with open(
        DB_NAME,
        "rb"
    ) as file:

        return file.read()
