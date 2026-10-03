import math
import secrets
import hashlib
import hmac
import os


# =========================================================
# حساب المسافة بين نقطتين جغرافيتين
# =========================================================
def distance_meters(lat1, lon1, lat2, lon2):
    """
    حساب المسافة بين نقطتين جغرافيتين بالمتر
    باستخدام معادلة Haversine.
    """

    R = 6371000.0

    lat1 = float(lat1)
    lon1 = float(lon1)
    lat2 = float(lat2)
    lon2 = float(lon2)

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(delta_lambda / 2.0) ** 2
    )

    a = min(1.0, max(0.0, a))

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return R * c


# =========================================================
# التحقق من الإحداثيات
# =========================================================
def valid_coords(lat, lon):
    """
    التحقق من صحة خط العرض وخط الطول.
    """

    try:
        lat = float(lat)
        lon = float(lon)

        return (
            -90 <= lat <= 90
            and -180 <= lon <= 180
        )

    except (ValueError, TypeError):
        return False


# =========================================================
# توليد Token آمن للـ QR
# =========================================================
def token():
    """
    إنشاء رمز أمان عشوائي لاستخدامه داخل QR Code.
    """

    return secrets.token_urlsafe(32)


# =========================================================
# تشفير كلمة المرور
# =========================================================
def hash_password(password):
    """
    تشفير كلمة المرور باستخدام PBKDF2-SHA256.
    """

    if not password:
        return ""

    iterations = 260000

    salt = os.urandom(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations
    )

    return (
        f"pbkdf2_sha256"
        f"${iterations}"
        f"${salt.hex()}"
        f"${password_hash.hex()}"
    )


# =========================================================
# التحقق من كلمة المرور
# =========================================================
def verify_password(password, stored_password):
    """
    التحقق من كلمة المرور المشفرة.

    يدعم أيضًا كلمات المرور القديمة النصية
    بهدف الانتقال للنسخة الجديدة دون فقد البيانات.
    """

    if not password or not stored_password:
        return False

    try:
        if stored_password.startswith("pbkdf2_sha256$"):

            algorithm, iterations, salt_hex, hash_hex = (
                stored_password.split("$", 3)
            )

            iterations = int(iterations)

            salt = bytes.fromhex(salt_hex)

            saved_hash = bytes.fromhex(hash_hex)

            current_hash = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt,
                iterations
            )

            return hmac.compare_digest(
                current_hash,
                saved_hash
            )

        # دعم النسخة القديمة إذا كانت كلمة المرور نصًا عاديًا
        return hmac.compare_digest(
            password,
            stored_password
        )

    except Exception:
        return False
