import io
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from database import (
    init_db,
    get_setting,
    set_setting,
    normalize_code,
    add_employee,
    get_employee,
    list_employees,
    update_employee,
    set_employee_active,
    delete_employee,
    record_attendance,
    today_records,
    stats_today,
    absent_today,
    attendance_report,
    daily_summary_report,
    list_admin_logs,
    log_admin,
    database_backup_bytes,
)

from utils import (
    distance_meters,
    valid_coords,
    token,
    hash_password,
    verify_password,
)


# =========================================================
# إعداد الصفحة
# =========================================================

st.set_page_config(
    page_title="نظام الحضور والانصراف",
    page_icon="assets/logo.png",
    layout="centered",
    initial_sidebar_state="expanded"
)


# =========================================================
# قاعدة البيانات
# =========================================================

init_db()


# =========================================================
# إعدادات أول تشغيل
# =========================================================

if not get_setting(
    "branch_name"
):

    set_setting(
        "branch_name",
        "الأكاديمية المهنية للمعلمين - فرع الجيزة"
    )


if not get_setting(
    "branch_latitude"
):

    set_setting(
        "branch_latitude",
        "30.076183"
    )


if not get_setting(
    "branch_longitude"
):

    set_setting(
        "branch_longitude",
        "31.218751"
    )


if not get_setting(
    "radius_m"
):

    set_setting(
        "radius_m",
        "100"
    )


if not get_setting(
    "admin_password"
):

    set_setting(
        "admin_password",
        hash_password(
            "123456"
        )
    )


if not get_setting(
    "max_gps_accuracy"
):

    set_setting(
        "max_gps_accuracy",
        "100"
    )


# =========================================================
# Session
# =========================================================

if "admin" not in st.session_state:
    st.session_state.admin = False


def is_admin():
    return bool(
        st.session_state.get(
            "admin",
            False
        )
    )


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
<style>

/* ====================================
   عام
==================================== */

html,
body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"] {
    direction: rtl !important;
}

/* الخلفية الجانبية خارج البرنامج */
[data-testid="stAppViewContainer"] {
    background: #e9edf3 !important;
}

/* مساحة البرنامج نفسها — لون مستقل عن الجوانب */
.main .block-container {
    max-width: 50% !important;
    width: 50% !important;
    margin: 0 auto !important;
    padding: 1.1rem 2rem 2rem 2rem !important;
    direction: rtl !important;
    background: radial-gradient(
        circle at top,
        #13264d 0%,
        #081426 45%,
        #050c18 100%
    ) !important;
    min-height: 100vh !important;
    box-sizing: border-box !important;
}


/* ====================================
   النصوص
==================================== */

[data-testid="stMarkdownContainer"],
[data-testid="stWidgetLabel"],
.stMarkdown,
.stText,
.stCaption {

    direction: rtl !important;

    text-align: right !important;
}


h1,
h2,
h3 {

    direction: rtl !important;

}


label,
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] div {

    text-align: right !important;

    direction: rtl !important;
}


/* ====================================
   Inputs
==================================== */

input,
textarea {

    direction: rtl !important;

    text-align: right !important;
}


/* ====================================
   Sidebar
==================================== */

[data-testid="stSidebar"] {

    direction: rtl !important;

    background:
        linear-gradient(
            180deg,
            #07152a 0%,
            #0a1e3d 100%
        );
}


[data-testid="stSidebar"] * {

    direction: rtl !important;

    text-align: right !important;
}


/* ====================================
   العنوان
==================================== */

.app-title {

    text-align: center !important;

    color: #ffffff;

    font-size: 2rem;

    font-weight: 900;

    line-height: 1.5;

    margin-top: 4px;
}


.app-branch {

    text-align: center !important;

    color: #d8b35e;

    font-size: 1.15rem;

    font-weight: 800;

    margin-top: 7px;
}


.app-subtitle {

    text-align: center !important;

    color: #aebbd0;

    font-size: 0.98rem;

    margin-top: 5px;

    margin-bottom: 18px;
}


/* ====================================
   Cards
==================================== */

.custom-card {

    border:
        1px solid
        rgba(
            216,
            179,
            94,
            0.25
        );

    background:
        rgba(
            13,
            31,
            61,
            0.7
        );

    border-radius:
        18px;

    padding:
        18px;

    margin-bottom:
        16px;

    box-shadow:
        0px 8px 24px
        rgba(
            0,
            0,
            0,
            0.12
        );
}


/* ====================================
   Metrics
==================================== */

[data-testid="stMetric"] {

    background:
        rgba(
            14,
            36,
            72,
            .75
        );

    border:
        1px solid
        rgba(
            216,
            179,
            94,
            .18
        );

    padding:
        12px;

    border-radius:
        14px;
}


[data-testid="stMetricValue"],
[data-testid="stMetricLabel"] {

    text-align:
        center !important;
}


/* ====================================
   Buttons
==================================== */

.stButton button,
.stDownloadButton button {

    border-radius:
        10px !important;

    font-weight:
        700 !important;
}


/* ====================================
   Dataframe
==================================== */

[data-testid="stDataFrame"] {

    direction:
        rtl !important;
}


/* ====================================
   Footer
==================================== */

.footer-text {

    text-align:
        center !important;

    color:
        #d8b35e;

    font-size:
        .88rem;

    padding:
        12px;
}


/* ====================================
   موبايل
==================================== */

@media (
    max-width: 768px
) {

    .app-title {

        font-size:
            1.55rem;
    }

    .app-branch {

        font-size:
            1rem;
    }

    .main .block-container {

        padding-left:
            .7rem !important;

        padding-right:
            .7rem !important;
    }
}



/* ====================================
   تخطيط البرنامج - في منتصف الشاشة بنصف العرض
==================================== */

.main .block-container {
    width: 50% !important;
    max-width: 50% !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

/* توسيط اللوجو بشكل صريح */
[data-testid="stImage"] {
    display: flex !important;
    justify-content: center !important;
    width: 100% !important;
}

[data-testid="stImage"] img {
    display: block !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

@media (max-width: 768px) {
    .main .block-container {
        width: 94% !important;
        max-width: 94% !important;
        padding-left: .9rem !important;
        padding-right: .9rem !important;
        border-radius: 0 !important;
    }
}

/* ====================================
   Navigation - بدون Sidebar
==================================== */

[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}

.top-nav-title {
    text-align: right;
    direction: rtl;
    color: #d8b35e;
    font-size: 1rem;
    font-weight: 800;
    margin: 8px 0 6px;
}

[data-testid="stSelectbox"] {
    width: 100% !important;
}

[data-testid="stSelectbox"] > div {
    width: 100% !important;
}

[data-testid="stSelectbox"] [role="combobox"] {
    direction: rtl !important;
    text-align: right !important;
    min-height: 46px !important;
    border-radius: 12px !important;
}

[data-testid="stSelectbox"] [role="option"] {
    direction: rtl !important;
    text-align: right !important;
    white-space: normal !important;
}
</style>
""",
    unsafe_allow_html=True
)


# =========================================================
# Logo
# =========================================================

BASE_DIR = Path(
    __file__
).resolve().parent

logo_path = (
    BASE_DIR
    / "assets"
    / "logo.png"
)


if logo_path.exists():

    logo_col = st.columns(
        [1, 1.4, 1]
    )[1]

    with logo_col:

        st.image(
            str(logo_path),
            width=160
        )


# =========================================================
# Header
# =========================================================

branch_name = get_setting(
    "branch_name",
    "الأكاديمية المهنية للمعلمين - فرع الجيزة"
)


st.markdown(
    """
    <div class="app-title">
    منظومة الحضور والانصراف الإلكترونية
    </div>
    """,
    unsafe_allow_html=True
)


st.markdown(
    f"""
    <div class="app-branch">
    {branch_name}
    </div>
    """,
    unsafe_allow_html=True
)


st.markdown(
    """
    <div class="app-subtitle">
    نظام متكامل لإدارة حضور وانصراف العاملين ومتابعة الدوام
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# Navigation
# =========================================================

pages = [
    "تسجيل الحضور والانصراف",
    "QR Code"
]

if is_admin():
    pages += [
        "لوحة الإدارة",
        "الموظفون",
        "التقارير",
        "سجل الإدارة",
        "إعدادات الفرع"
    ]
else:
    pages += ["دخول الإدارة"]

# قائمة التنقل الرئيسية داخل الصفحة — بدون Sidebar
st.markdown(
    "<div class=\"top-nav-title\">🧭 القائمة الرئيسية</div>",
    unsafe_allow_html=True
)

page = st.selectbox(
    "الانتقال إلى",
    pages,
    label_visibility="collapsed",
    key="top_navigation"
)

if is_admin():
    if st.button("🚪 تسجيل خروج الإدارة", use_container_width=True):
        log_admin(
            "تسجيل خروج",
            "تسجيل خروج الإدارة من النظام."
        )
        st.session_state.admin = False
        st.rerun()


# =========================================================
# تسجيل الحضور والانصراف
# =========================================================

if page == "تسجيل الحضور والانصراف":

    st.subheader(
        "📍 تسجيل الحضور والانصراف"
    )

    token_from_url = str(
        st.query_params.get(
            "site",
            ""
        )
    ).strip()

    configured_token = get_setting(
        "site_token",
        ""
    )

    if not token_from_url:

        st.warning(
            "يجب فتح صفحة التسجيل من خلال QR Code الخاص بالفرع."
        )

        st.stop()

    if (
        not configured_token
        or token_from_url
        != configured_token
    ):

        st.error(
            "رمز QR غير صالح أو تم استبداله."
        )

        st.stop()


    action_from_url = str(
        st.query_params.get(
            "action",
            ""
        )
    ).strip()


    actions = [
        "حضور",
        "انصراف"
    ]


    default_action_index = 0

    if action_from_url in actions:

        default_action_index = (
            actions.index(
                action_from_url
            )
        )


    action = st.radio(
        "نوع العملية",
        actions,
        index=default_action_index,
        horizontal=True
    )


    code = st.text_input(
        "كود الموظف",
        placeholder="مثال: 001"
    )


    if st.button(
        "📍 التحقق من الموقع وتسجيل العملية",
        type="primary",
        use_container_width=True
    ):

        code = normalize_code(
            code
        )

        if not code:

            st.error(
                "أدخل كود الموظف."
            )

            st.stop()


        employee = get_employee(
            code,
            active_only=True
        )


        if not employee:

            st.error(
                "كود الموظف غير صحيح أو الموظف غير نشط."
            )

            st.stop()


        branch_lat = get_setting(
            "branch_latitude",
            ""
        )

        branch_lon = get_setting(
            "branch_longitude",
            ""
        )


        try:

            radius = float(
                get_setting(
                    "radius_m",
                    "100"
                )
                or 100
            )

        except ValueError:

            radius = 100


        try:

            max_accuracy = float(
                get_setting(
                    "max_gps_accuracy",
                    "100"
                )
                or 100
            )

        except ValueError:

            max_accuracy = 100


        if not valid_coords(
            branch_lat,
            branch_lon
        ):

            st.error(
                "لم يتم ضبط إحداثيات الفرع بطريقة صحيحة."
            )

            st.stop()


        try:

            from streamlit_js_eval import (
                get_geolocation
            )

            location = get_geolocation(
                component_key=(
                    "attendance_location"
                )
            )

        except Exception as error:

            st.error(
                f"تعذر تشغيل GPS: {error}"
            )

            st.stop()


        if not location:

            st.info(
                "اسمح للمتصفح باستخدام الموقع ثم اضغط زر التسجيل مرة أخرى."
            )

            st.stop()


        if (
            isinstance(
                location,
                dict
            )
            and "error" in location
        ):

            error_data = location.get(
                "error",
                {}
            )

            if isinstance(
                error_data,
                dict
            ):

                message = error_data.get(
                    "message",
                    "تعذر الحصول على الموقع."
                )

            else:

                message = str(
                    error_data
                )

            st.error(
                message
            )

            st.stop()


        coords = location.get(
            "coords",
            {}
        )


        user_lat = coords.get(
            "latitude"
        )

        user_lon = coords.get(
            "longitude"
        )

        accuracy = coords.get(
            "accuracy"
        )


        if (
            user_lat is None
            or user_lon is None
        ):

            st.error(
                "بيانات الموقع غير مكتملة."
            )

            st.stop()


        if not valid_coords(
            user_lat,
            user_lon
        ):

            st.error(
                "إحداثيات الجهاز غير صحيحة."
            )

            st.stop()


        # التحقق من دقة GPS
        if accuracy is not None:

            try:

                accuracy_value = float(
                    accuracy
                )

                if (
                    accuracy_value
                    > max_accuracy
                ):

                    st.error(
                        f"""
                        دقة تحديد الموقع ضعيفة:
                        {accuracy_value:.0f} متر.

                        الحد المسموح:
                        {max_accuracy:.0f} متر.

                        فعّل GPS وانتقل إلى مكان يسمح باستقبال إشارة أفضل ثم حاول مرة أخرى.
                        """
                    )

                    st.stop()

            except (
                ValueError,
                TypeError
            ):

                accuracy_value = None

        else:

            accuracy_value = None


        dist = distance_meters(
            user_lat,
            user_lon,
            branch_lat,
            branch_lon
        )


        if accuracy_value is not None:

            st.info(
                f"""
                المسافة عن الفرع:
                {dist:.1f} متر

                | دقة GPS:
                {accuracy_value:.1f} متر
                """
            )

        else:

            st.info(
                f"""
                المسافة عن الفرع:
                {dist:.1f} متر
                """
            )


        if dist > radius:

            st.error(
                f"""
                لم يتم التسجيل.

                الجهاز خارج نطاق الفرع المحدد.

                النطاق المسموح:
                {radius:.0f} متر.

                المسافة الحالية:
                {dist:.1f} متر.
                """
            )

            st.stop()


        rows_today = today_records(
            code
        )


        if (
            action == "حضور"
            and any(
                row["action"] == "حضور"
                for row in rows_today
            )
        ):

            st.warning(
                "تم تسجيل حضور هذا الموظف اليوم بالفعل."
            )

            st.stop()


        if action == "انصراف":

            has_attendance = any(
                row["action"] == "حضور"
                for row in rows_today
            )

            has_departure = any(
                row["action"] == "انصراف"
                for row in rows_today
            )


            if not has_attendance:

                st.warning(
                    "لا يمكن تسجيل الانصراف قبل تسجيل الحضور."
                )

                st.stop()


            if has_departure:

                st.warning(
                    "تم تسجيل الانصراف لهذا الموظف اليوم بالفعل."
                )

                st.stop()


        ok, message = record_attendance(

            employee,

            action,

            user_lat,

            user_lon,

            dist,

            accuracy_value
        )


        if ok:

            st.success(
                f"""
                ✅ {message}

                الموظف:
                {employee['name']}
                """
            )

        else:

            st.warning(
                message
            )


    # عرض سجل اليوم
    if code:

        rows = today_records(
            code
        )

        if rows:

            st.markdown(
                "### 🕒 سجل اليوم"
            )

            df_today = pd.DataFrame(
                rows
            )

            df_today = df_today.rename(
                columns={
                    "action":
                        "العملية",

                    "timestamp":
                        "التاريخ والوقت",

                    "distance_m":
                        "المسافة",

                    "accuracy_m":
                        "دقة GPS"
                }
            )

            st.dataframe(
                df_today,
                use_container_width=True,
                hide_index=True
            )


# =========================================================
# QR Code
# =========================================================

elif page == "QR Code":

    st.subheader(
        "🔳 QR Code الخاص بالفرع"
    )


    site_token = get_setting(
        "site_token",
        ""
    )

    app_url = get_setting(
        "app_url",
        ""
    ).strip()


    if not site_token:

        st.info(
            "يجب على الإدارة إنشاء QR Code أولًا من إعدادات الفرع."
        )

    elif not app_url:

        st.warning(
            """
            لم يتم تحديد رابط النظام.

            ادخل إلى:
            إعدادات الفرع ← رابط النظام

            ثم أدخل رابط تطبيق Streamlit المنشور.
            """
        )

    else:

        try:

            import qrcode


            base_url = (
                app_url.rstrip(
                    "/"
                )
            )


            attendance_url = (
                f"{base_url}"
                f"?site={site_token}"
            )


            qr_img = qrcode.make(
                attendance_url
            )


            buffer = io.BytesIO()

            qr_img.save(
                buffer,
                format="PNG"
            )

            qr_data = (
                buffer.getvalue()
            )


            st.image(
                qr_data,
                width=320
            )


            st.success(
                "يمكن طباعة هذا الرمز وتعليقه داخل مقر الفرع."
            )


            st.code(
                attendance_url,
                language=None
            )


            st.download_button(
                "📥 تحميل QR Code",
                data=qr_data,
                file_name=(
                    "giza_attendance_qr.png"
                ),
                mime="image/png",
                use_container_width=True
            )


        except Exception as error:

            st.error(
                f"تعذر إنشاء QR Code: {error}"
            )


# =========================================================
# تسجيل دخول الإدارة
# =========================================================

elif page == "دخول الإدارة":

    st.subheader(
        "🔐 دخول الإدارة"
    )


    password = st.text_input(
        "كلمة مرور الإدارة",
        type="password"
    )


    st.caption(
        "كلمة المرور الافتراضية عند أول تشغيل: 123456"
    )


    if st.button(
        "🔐 دخول",
        type="primary",
        use_container_width=True
    ):

        stored_password = get_setting(
            "admin_password",
            ""
        )


        if verify_password(
            password,
            stored_password
        ):

            # ترقية كلمة المرور القديمة تلقائيًا
            if not stored_password.startswith(
                "pbkdf2_sha256$"
            ):

                set_setting(
                    "admin_password",
                    hash_password(
                        password
                    )
                )


            st.session_state.admin = True


            log_admin(
                "تسجيل دخول",
                "تم تسجيل دخول الإدارة بنجاح."
            )


            st.success(
                "تم تسجيل الدخول بنجاح."
            )


            st.rerun()

        else:

            st.error(
                "كلمة مرور الإدارة غير صحيحة."
            )


# =========================================================
# Dashboard
# =========================================================

elif page == "لوحة الإدارة":

    if not is_admin():
        st.stop()


    st.subheader(
        "📊 لوحة الإدارة"
    )


    stats = stats_today()


    col1, col2, col3 = (
        st.columns(3)
    )


    col1.metric(
        "إجمالي الموظفين",
        stats["total"]
    )


    col2.metric(
        "الموظفون النشطون",
        stats["active"]
    )


    col3.metric(
        "الحضور اليوم",
        stats["present"]
    )


    col4, col5 = (
        st.columns(2)
    )


    col4.metric(
        "الانصراف اليوم",
        stats["departed"]
    )


    col5.metric(
        "الغياب حتى الآن",
        stats["absent"]
    )


    st.divider()


    st.markdown(
        "### 🚫 الغائبون حتى الآن"
    )


    absent_rows = absent_today()


    if absent_rows:

        absent_df = pd.DataFrame(
            absent_rows
        )


        absent_df = absent_df.rename(
            columns={
                "employee_code":
                    "كود الموظف",

                "name":
                    "اسم الموظف",

                "job_title":
                    "الوظيفة",

                "phone":
                    "الهاتف"
            }
        )


        st.dataframe(
            absent_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.success(
            "لا يوجد موظفون غائبون في الوقت الحالي."
        )


# =========================================================
# الموظفون
# =========================================================

elif page == "الموظفون":

    if not is_admin():
        st.stop()


    st.subheader(
        "👥 إدارة الموظفين"
    )


    with st.expander(
        "➕ إضافة موظف جديد",
        expanded=True
    ):

        with st.form(
            "add_employee_form"
        ):

            c1, c2 = (
                st.columns(2)
            )


            code = c1.text_input(
                "كود الموظف *",
                placeholder="001"
            )


            name = c2.text_input(
                "اسم الموظف *"
            )


            job = c1.text_input(
                "الوظيفة"
            )


            phone = c2.text_input(
                "رقم الهاتف"
            )


            submit = (
                st.form_submit_button(
                    "💾 إضافة الموظف",
                    type="primary",
                    use_container_width=True
                )
            )


        if submit:

            ok, message = add_employee(
                code,
                name,
                job,
                phone
            )


            if ok:

                st.success(
                    message
                )

                st.rerun()

            else:

                st.error(
                    message
                )


    employees = list_employees()


    if not employees:

        st.info(
            "لا يوجد موظفون حتى الآن."
        )

    else:

        df = pd.DataFrame(
            employees
        )


        df["الحالة"] = (
            df["active"].map(
                {
                    1: "نشط",
                    0: "غير نشط"
                }
            )
        )


        display_columns = [
            "employee_code",
            "name",
            "job_title",
            "phone",
            "الحالة"
        ]


        employee_df = df[
            display_columns
        ].rename(
            columns={
                "employee_code":
                    "كود الموظف",

                "name":
                    "اسم الموظف",

                "job_title":
                    "الوظيفة",

                "phone":
                    "الهاتف"
            }
        )


        st.dataframe(
            employee_df,
            use_container_width=True,
            hide_index=True
        )


        st.divider()


        st.markdown(
            "### ✏️ تعديل بيانات الموظف"
        )


        options = [

            f"{employee['employee_code']} — {employee['name']}"

            for employee in employees
        ]


        selected = st.selectbox(
            "اختر الموظف",
            options
        )


        selected_code = (
            selected.split(
                " — ",
                1
            )[0]
        )


        employee = get_employee(
            selected_code,
            active_only=False
        )


        if employee:

            c1, c2 = (
                st.columns(2)
            )


            with c1:

                new_name = st.text_input(
                    "الاسم",
                    value=(
                        employee["name"]
                        or ""
                    ),
                    key=(
                        f"edit_name_{selected_code}"
                    )
                )


                new_job = st.text_input(
                    "الوظيفة",
                    value=(
                        employee["job_title"]
                        or ""
                    ),
                    key=(
                        f"edit_job_{selected_code}"
                    )
                )


            with c2:

                new_phone = st.text_input(
                    "الهاتف",
                    value=(
                        employee["phone"]
                        or ""
                    ),
                    key=(
                        f"edit_phone_{selected_code}"
                    )
                )


                status_text = (
                    "نشط"
                    if employee["active"]
                    else "غير نشط"
                )


                st.write(
                    f"""
                    **الكود:** {employee['employee_code']}

                    **الحالة:** {status_text}
                    """
                )


            x1, x2, x3 = (
                st.columns(3)
            )


            if x1.button(
                "💾 حفظ التعديل",
                use_container_width=True
            ):

                if update_employee(
                    selected_code,
                    new_name,
                    new_job,
                    new_phone
                ):

                    st.success(
                        "تم حفظ التعديل."
                    )

                    st.rerun()

                else:

                    st.error(
                        "تعذر حفظ التعديل."
                    )


            toggle_label = (
                "⛔ تعطيل"
                if employee["active"]
                else "✅ تفعيل"
            )


            if x2.button(
                toggle_label,
                use_container_width=True
            ):

                set_employee_active(
                    selected_code,
                    not bool(
                        employee["active"]
                    )
                )

                st.success(
                    "تم تغيير حالة الموظف."
                )

                st.rerun()


            if x3.button(
                "🗑️ حذف",
                use_container_width=True
            ):

                ok, message = delete_employee(
                    selected_code
                )


                if ok:

                    st.success(
                        message
                    )

                    st.rerun()

                else:

                    st.warning(
                        message
                    )


# =========================================================
# التقارير
# =========================================================

elif page == "التقارير":

    if not is_admin():
        st.stop()


    st.subheader(
        "📑 التقارير"
    )


    c1, c2 = (
        st.columns(2)
    )


    start_date = c1.date_input(
        "من تاريخ",
        value=date.today()
    )


    end_date = c2.date_input(
        "إلى تاريخ",
        value=date.today()
    )


    if start_date > end_date:

        st.error(
            "تاريخ البداية يجب أن يكون قبل تاريخ النهاية."
        )

        st.stop()


    code_filter = st.text_input(
        "كود الموظف - اختياري"
    )


    report_type = st.radio(
        "نوع التقرير",
        [
            "سجل الحركات",
            "ملخص الحضور وساعات العمل"
        ],
        horizontal=True
    )


    if (
        report_type
        == "سجل الحركات"
    ):

        rows = attendance_report(
            start_date,
            end_date,
            code_filter or None
        )

    else:

        rows = daily_summary_report(
            start_date,
            end_date,
            code_filter or None
        )


    if not rows:

        st.info(
            "لا توجد بيانات للفترة المحددة."
        )

    else:

        report_df = pd.DataFrame(
            rows
        )


        st.dataframe(
            report_df,
            use_container_width=True,
            hide_index=True
        )


        excel_buffer = io.BytesIO()


        with pd.ExcelWriter(
            excel_buffer,
            engine="openpyxl"
        ) as writer:

            report_df.to_excel(
                writer,
                index=False,
                sheet_name=(
                    "الحضور والانصراف"
                )
            )


        st.download_button(
            "📥 تنزيل التقرير Excel",
            data=excel_buffer.getvalue(),
            file_name=(
                f"attendance_report_"
                f"{start_date}_"
                f"{end_date}.xlsx"
            ),
            mime=(
                "application/"
                "vnd.openxmlformats-"
                "officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True
        )


# =========================================================
# سجل الإدارة
# =========================================================

elif page == "سجل الإدارة":

    if not is_admin():
        st.stop()


    st.subheader(
        "🧾 سجل عمليات الإدارة"
    )


    logs = list_admin_logs(
        500
    )


    if not logs:

        st.info(
            "لا توجد عمليات مسجلة."
        )

    else:

        logs_df = pd.DataFrame(
            logs
        )


        logs_df = logs_df.rename(
            columns={
                "id":
                    "م",

                "action":
                    "العملية",

                "details":
                    "التفاصيل",

                "created_at":
                    "التاريخ والوقت"
            }
        )


        st.dataframe(
            logs_df,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# الإعدادات
# =========================================================

elif page == "إعدادات الفرع":

    if not is_admin():
        st.stop()


    st.subheader(
        "⚙️ إعدادات الفرع"
    )


    branch_name_input = st.text_input(
        "اسم الفرع",
        value=get_setting(
            "branch_name",
            ""
        )
    )


    app_url = st.text_input(
        "رابط النظام المنشور",
        value=get_setting(
            "app_url",
            ""
        ),
        placeholder=(
            "https://your-app.streamlit.app"
        )
    )


    st.caption(
        "اكتب الرابط الرئيسي للتطبيق بدون معاملات ?site="
    )


    c1, c2 = (
        st.columns(2)
    )


    latitude = c1.text_input(
        "خط العرض Latitude",
        value=get_setting(
            "branch_latitude",
            "30.076183"
        )
    )


    longitude = c2.text_input(
        "خط الطول Longitude",
        value=get_setting(
            "branch_longitude",
            "31.218751"
        )
    )


    try:

        radius_default = int(
            float(
                get_setting(
                    "radius_m",
                    "100"
                )
                or 100
            )
        )

    except ValueError:

        radius_default = 100


    radius = st.number_input(
        "نطاق الحضور بالمتر",
        min_value=10,
        max_value=5000,
        value=radius_default,
        step=10
    )


    try:

        accuracy_default = int(
            float(
                get_setting(
                    "max_gps_accuracy",
                    "100"
                )
                or 100
            )
        )

    except ValueError:

        accuracy_default = 100


    max_accuracy = st.number_input(
        "أقصى دقة GPS مسموح بها بالمتر",
        min_value=10,
        max_value=1000,
        value=accuracy_default,
        step=10
    )


    st.markdown(
        "### 🔐 كلمة مرور الإدارة"
    )


    new_password = st.text_input(
        "كلمة مرور الإدارة الجديدة",
        type="password"
    )


    confirm_password = st.text_input(
        "تأكيد كلمة المرور",
        type="password"
    )


    if st.button(
        "💾 حفظ الإعدادات",
        type="primary",
        use_container_width=True
    ):

        if not valid_coords(
            latitude,
            longitude
        ):

            st.error(
                "أدخل إحداثيات صحيحة للفرع."
            )

        elif (
            new_password
            and new_password
            != confirm_password
        ):

            st.error(
                "كلمتا المرور غير متطابقتين."
            )

        elif (
            new_password
            and len(
                new_password
            ) < 6
        ):

            st.error(
                "كلمة المرور يجب ألا تقل عن 6 أحرف أو أرقام."
            )

        else:

            set_setting(
                "branch_name",
                branch_name_input.strip()
            )


            set_setting(
                "app_url",
                app_url.strip()
            )


            set_setting(
                "branch_latitude",
                latitude.strip()
            )


            set_setting(
                "branch_longitude",
                longitude.strip()
            )


            set_setting(
                "radius_m",
                radius
            )


            set_setting(
                "max_gps_accuracy",
                max_accuracy
            )


            if new_password:

                set_setting(
                    "admin_password",
                    hash_password(
                        new_password
                    )
                )


                log_admin(
                    "تغيير كلمة المرور",
                    "تم تغيير كلمة مرور الإدارة."
                )


            log_admin(
                "تعديل الإعدادات",
                "تم تحديث إعدادات الفرع."
            )


            st.success(
                "تم حفظ الإعدادات بنجاح."
            )


            st.rerun()


    # -----------------------------------------------------
    # QR
    # -----------------------------------------------------

    st.divider()


    st.subheader(
        "🔑 إعداد QR Code"
    )


    site_token = get_setting(
        "site_token",
        ""
    )


    if site_token:

        st.success(
            "يوجد QR Code فعال حاليًا."
        )

    else:

        st.warning(
            "لم يتم إنشاء QR Code بعد."
        )


    if st.button(
        "🔄 إنشاء / تغيير QR Code",
        use_container_width=True
    ):

        new_token = token()


        set_setting(
            "site_token",
            new_token
        )


        log_admin(
            "تغيير QR Code",
            "تم إنشاء رمز QR جديد."
        )


        st.success(
            "تم إنشاء QR Code جديد. الرمز السابق أصبح غير صالح."
        )


        st.rerun()


    st.caption(
        "عند تغيير QR Code يصبح أي رمز قديم غير صالح."
    )


    # -----------------------------------------------------
    # Backup
    # -----------------------------------------------------

    st.divider()


    st.subheader(
        "💾 النسخ الاحتياطي"
    )


    backup_data = (
        database_backup_bytes()
    )


    if backup_data:

        timestamp = (
            datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )
        )


        st.download_button(
            "📥 تنزيل نسخة احتياطية من قاعدة البيانات",
            data=backup_data,
            file_name=(
                f"attendance_backup_"
                f"{timestamp}.db"
            ),
            mime=(
                "application/"
                "octet-stream"
            ),
            use_container_width=True
        )


# =========================================================
# Footer
# =========================================================

st.divider()


st.markdown(
    """
    <div class="footer-text">
    ✦ تصميم وتنفيذ: أحمد الجنزوري - مدير فرع الجيزة ✦
    <br>
    الإصدار 2.0.0
    </div>
    """,
    unsafe_allow_html=True
)
