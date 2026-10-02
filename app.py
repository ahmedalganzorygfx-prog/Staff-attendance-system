import io
import base64
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from database import *
from utils import distance_meters, valid_coords, token


# =========================================================
# إعداد الصفحة
# =========================================================

st.set_page_config(
    page_title="نظام حضور وانصراف الموظفين",
    page_icon="assets/logo.png",
    layout="centered",
    initial_sidebar_state="expanded"
)

init_db()


# =========================================================
# CSS - RTL + توسيط البرنامج + ضبط القائمة الجانبية
# =========================================================

st.markdown("""
<style>

/* =========================================================
   الاتجاه العام
   ========================================================= */

html,
body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"] {

    direction: rtl !important;

}


/* =========================================================
   الحاوية الرئيسية
   ========================================================= */

.main .block-container {

    max-width: 760px !important;

    width: 100% !important;

    margin-left: auto !important;

    margin-right: auto !important;

    padding-top: 1rem !important;

    padding-bottom: 2rem !important;

    direction: rtl !important;

}


/* =========================================================
   جميع العناصر الداخلية
   ========================================================= */

[data-testid="stVerticalBlock"] {

    direction: rtl !important;

}


/* =========================================================
   القائمة الجانبية
   ========================================================= */

section[data-testid="stSidebar"] {

    direction: rtl !important;

    text-align: right !important;

}

section[data-testid="stSidebar"] * {

    direction: rtl !important;

    text-align: right !important;

}


/* =========================================================
   عند إخفاء / طي القائمة الجانبية
   ========================================================= */

section[data-testid="stSidebar"][aria-expanded="false"] {

    width: 0 !important;

    min-width: 0 !important;

    max-width: 0 !important;

    padding: 0 !important;

    margin: 0 !important;

    overflow: hidden !important;

}

section[data-testid="stSidebar"][aria-expanded="false"] > div {

    width: 0 !important;

    min-width: 0 !important;

    max-width: 0 !important;

    padding: 0 !important;

    margin: 0 !important;

    overflow: hidden !important;

}

section[data-testid="stSidebar"][aria-expanded="false"] * {

    visibility: hidden !important;

}


/* =========================================================
   رأس البرنامج بالكامل
   محور مركزي واحد فعليًا
   ========================================================= */

.app-header {

    width: 100% !important;

    max-width: 760px !important;

    margin: 0 auto 24px auto !important;

    padding: 0 !important;

    display: flex !important;

    flex-direction: column !important;

    align-items: center !important;

    justify-content: flex-start !important;

    text-align: center !important;

    direction: rtl !important;

}


/* =========================================================
   حاوية اللوجو
   ========================================================= */

.app-logo-wrap {

    width: 100% !important;

    display: flex !important;

    align-items: center !important;

    justify-content: center !important;

    margin: 0 auto 12px auto !important;

    padding: 0 !important;

    text-align: center !important;

}


/* =========================================================
   اللوجو
   ========================================================= */

.app-logo {

    display: block !important;

    width: 150px !important;

    height: 150px !important;

    min-width: 150px !important;

    max-width: 150px !important;

    min-height: 150px !important;

    max-height: 150px !important;

    object-fit: contain !important;

    margin: 0 auto !important;

    padding: 0 !important;

}


/* =========================================================
   اسم البرنامج
   ========================================================= */

.app-title {

    width: 100% !important;

    display: block !important;

    margin: 0 auto !important;

    padding: 0 !important;

    text-align: center !important;

    direction: rtl !important;

    font-size: 1.85rem !important;

    font-weight: 800 !important;

    line-height: 1.5 !important;

}


/* =========================================================
   اسم الفرع
   ========================================================= */

.app-branch {

    width: 100% !important;

    display: block !important;

    margin: 5px auto 0 auto !important;

    padding: 0 !important;

    text-align: center !important;

    direction: rtl !important;

    font-size: 1.12rem !important;

    font-weight: 700 !important;

    line-height: 1.5 !important;

    color: #d9b35f !important;

}


/* =========================================================
   وصف البرنامج
   ========================================================= */

.app-subtitle {

    width: 100% !important;

    display: block !important;

    margin: 5px auto 0 auto !important;

    padding: 0 !important;

    text-align: center !important;

    direction: rtl !important;

    color: #aeb6c8 !important;

    font-size: .98rem !important;

    line-height: 1.5 !important;

}


/* =========================================================
   النصوص والعناوين
   ========================================================= */

.stMarkdown,
.stText,
.stCaption,
.stAlert,
.stRadio,
.stSelectbox,
.stTextInput,
.stNumberInput,
.stDateInput,
.stButton,
.stDownloadButton,
.stForm,
.stFormSubmitButton,
.stDataFrame {

    direction: rtl !important;

    text-align: right !important;

}


/* =========================================================
   عناوين الحقول
   ========================================================= */

label,
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] div {

    direction: rtl !important;

    text-align: right !important;

}


/* =========================================================
   حقول الإدخال
   ========================================================= */

input,
textarea,
select {

    direction: rtl !important;

    text-align: right !important;

}


/* =========================================================
   الأزرار
   ========================================================= */

button {

    direction: rtl !important;

}


/* =========================================================
   البطاقات
   ========================================================= */

.card {

    border: 1px solid rgba(128,128,128,.25);

    border-radius: 14px;

    padding: 18px;

    margin-bottom: 14px;

}


/* =========================================================
   المؤشرات
   ========================================================= */

[data-testid="stMetricValue"],
[data-testid="stMetricLabel"] {

    text-align: center !important;

}

</style>
""", unsafe_allow_html=True)


# =========================================================
# اسم الفرع
# =========================================================

branch_name = get_setting(
    "branch_name",
    "الأكاديمية المهنية للمعلمين – فرع الجيزة"
)


# =========================================================
# حالة الإدارة
# =========================================================

def is_admin():

    return st.session_state.get(
        "admin",
        False
    )


if "admin" not in st.session_state:

    st.session_state.admin = False


# =========================================================
# شعار الفرع + اسم البرنامج + اسم الفرع + الوصف
# محور مركزي واحد تمامًا
# =========================================================

logo_path = (
    Path(__file__).resolve().parent
    / "assets"
    / "logo.png"
)


# =========================================================
# التحقق من وجود اللوجو
# =========================================================

if logo_path.exists():

    logo_data = base64.b64encode(
        logo_path.read_bytes()
    ).decode("utf-8")

else:

    logo_data = ""


# =========================================================
# بداية رأس البرنامج
# =========================================================

st.markdown(
    '<div class="app-header">',
    unsafe_allow_html=True
)


# =========================================================
# اللوجو
# =========================================================

if logo_data:

    st.markdown(
        f"""
        <div class="app-logo-wrap">

            <img
                src="data:image/png;base64,{logo_data}"
                class="app-logo"
                alt="شعار الأكاديمية"
            >

        </div>
        """,
        unsafe_allow_html=True
    )

else:

    st.warning(
        "لم يتم العثور على ملف الشعار: assets/logo.png"
    )


# =========================================================
# اسم البرنامج
# =========================================================

st.markdown(
    """
    <div class="app-title">
        نظام الحضور والانصراف
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# اسم الفرع
# =========================================================

st.markdown(
    f"""
    <div class="app-branch">
        {branch_name}
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# وصف البرنامج
# =========================================================

st.markdown(
    """
    <div class="app-subtitle">
        نظام رقمي لإدارة حضور وانصراف موظفي الفرع
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# نهاية رأس البرنامج
# =========================================================

st.markdown(
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# القائمة الجانبية
# =========================================================

with st.sidebar:

    st.markdown("## القائمة")


    pages = [
        "تسجيل الحضور والانصراف",
        "QR Code"
    ]


    if is_admin():

        pages += [
            "لوحة الإدارة",
            "الموظفون",
            "التقارير",
            "إعدادات الفرع"
        ]


        if st.button(
            "تسجيل خروج الإدارة",
            use_container_width=True
        ):

            st.session_state.admin = False

            st.rerun()


    else:

        pages += [
            "دخول الإدارة"
        ]


    page = st.radio(
        "",
        pages
    )


# =========================================================
# تسجيل الحضور والانصراف
# =========================================================

if page == "تسجيل الحضور والانصراف":

    st.subheader(
        "📍 تسجيل الحضور والانصراف"
    )


    token_from_url = st.query_params.get(
        "site",
        ""
    )


    configured_token = get_setting(
        "site_token",
        ""
    )


    if not token_from_url:

        st.warning(
            "يجب فتح هذه الصفحة من خلال QR Code الخاص بالفرع."
        )


    elif not configured_token or token_from_url != configured_token:

        st.error(
            "رمز QR غير صالح."
        )

        st.stop()


    action = st.radio(
        "العملية",
        ["حضور", "انصراف"],
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

        code = normalize_code(code)


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


        lat = get_setting(
            "branch_latitude",
            ""
        )


        lon = get_setting(
            "branch_longitude",
            ""
        )


        radius = float(
            get_setting(
                "radius_m",
                "100"
            ) or 100
        )


        if not valid_coords(
            lat,
            lon
        ):

            st.error(
                "لم يتم ضبط إحداثيات الفرع بعد. ادخل إلى إعدادات الفرع من الإدارة."
            )

            st.stop()


        try:

            from streamlit_js_eval import get_geolocation

            loc = get_geolocation(
                component_key="attendance_location"
            )


        except Exception as e:

            st.error(
                f"تعذر تشغيل GPS: {e}"
            )

            st.stop()


        if not loc:

            st.info(
                "اسمح للمتصفح باستخدام الموقع ثم اضغط الزر مرة أخرى."
            )

            st.stop()


        if "error" in loc:

            st.error(
                loc["error"].get(
                    "message",
                    "تعذر الحصول على الموقع."
                )
            )

            st.stop()


        coords = loc.get(
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


        if user_lat is None or user_lon is None:

            st.error(
                "بيانات الموقع غير مكتملة."
            )

            st.stop()


        dist = distance_meters(
            float(user_lat),
            float(user_lon),
            float(lat),
            float(lon)
        )


        if accuracy is not None:

            st.info(
                f"المسافة عن الفرع: {dist:.1f} متر | "
                f"دقة GPS: {float(accuracy):.1f} متر"
            )

        else:

            st.info(
                f"المسافة عن الفرع: {dist:.1f} متر"
            )


        if dist > radius:

            st.error(
                f"لم يتم التسجيل: الجهاز خارج نطاق الفرع المحدد "
                f"({radius:.0f} متر)."
            )

            st.stop()


        today = today_records(
            code
        )


        if action == "حضور":

            if any(
                x["action"] == "حضور"
                for x in today
            ):

                st.warning(
                    "تم تسجيل حضور هذا الموظف اليوم بالفعل."
                )

                st.stop()


        if action == "انصراف":

            if not any(
                x["action"] == "حضور"
                for x in today
            ):

                st.warning(
                    "لا يمكن تسجيل الانصراف قبل تسجيل الحضور."
                )

                st.stop()


            if any(
                x["action"] == "انصراف"
                for x in today
            ):

                st.warning(
                    "تم تسجيل الانصراف لهذا الموظف اليوم بالفعل."
                )

                st.stop()


        record_attendance(
            employee,
            action,
            user_lat,
            user_lon,
            dist,
            accuracy
        )


        st.success(
            f"تم تسجيل {action} بنجاح للموظف: "
            f"{employee['name']}"
        )


    if code:

        rows = today_records(
            code
        )


        if rows:

            st.markdown(
                "### سجل اليوم"
            )


            st.dataframe(
                pd.DataFrame(rows),
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


    if not site_token:

        st.info(
            "يجب على الإدارة إنشاء QR أولًا من إعدادات الفرع."
        )


    else:

        try:

            import qrcode

            base = st.context.url.split(
                "?"
            )[0]


            url = (
                f"{base}?site={site_token}&action=حضور"
            )


            img = qrcode.make(
                url
            )


            buf = io.BytesIO()


            img.save(
                buf,
                format="PNG"
            )


            data = buf.getvalue()


            st.image(
                data,
                width=320
            )


            st.download_button(
                "📥 تحميل QR",
                data,
                "giza_attendance_qr.png",
                "image/png",
                use_container_width=True
            )


        except Exception as e:

            st.error(
                f"تعذر إنشاء QR: {e}"
            )


# =========================================================
# دخول الإدارة
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
        "كلمة المرور الافتراضية في النسخة الجديدة: "
        "123456 — غيّرها من إعدادات الفرع."
    )


    if st.button(
        "دخول",
        type="primary",
        use_container_width=True
    ):

        if password == get_setting(
            "admin_password",
            "123456"
        ):

            st.session_state.admin = True

            st.rerun()


        else:

            st.error(
                "كلمة مرور الإدارة غير صحيحة."
            )


# =========================================================
# لوحة الإدارة
# =========================================================

elif page == "لوحة الإدارة":

    st.subheader(
        "📊 لوحة الإدارة"
    )


    s = stats_today()


    a, b, c, d = st.columns(4)


    a.metric(
        "إجمالي الموظفين",
        s["total"]
    )


    b.metric(
        "الموظفون النشطون",
        s["active"]
    )


    c.metric(
        "حضور اليوم",
        s["present"]
    )


    d.metric(
        "انصراف اليوم",
        s["departed"]
    )


# =========================================================
# الموظفون
# =========================================================

elif page == "الموظفون":

    st.subheader(
        "👥 إدارة الموظفين"
    )


    with st.expander(
        "➕ إضافة موظف جديد",
        expanded=True
    ):

        with st.form(
            "add_employee"
        ):

            c1, c2 = st.columns(2)


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
                "الهاتف"
            )


            submit = st.form_submit_button(
                "💾 إضافة الموظف",
                type="primary",
                use_container_width=True
            )


        if submit:

            ok, msg = add_employee(
                code,
                name,
                job,
                phone
            )


            if ok:

                st.success(
                    msg
                )

                st.rerun()


            else:

                st.error(
                    msg
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


        df["الحالة"] = df["active"].map(
            {
                1: "نشط",
                0: "غير نشط"
            }
        )


        st.dataframe(
            df[
                [
                    "employee_code",
                    "name",
                    "job_title",
                    "phone",
                    "الحالة"
                ]
            ].rename(
                columns={
                    "employee_code": "كود الموظف",
                    "name": "اسم الموظف",
                    "job_title": "الوظيفة",
                    "phone": "الهاتف"
                }
            ),
            use_container_width=True,
            hide_index=True
        )


        st.markdown(
            "### ✏️ تعديل / تفعيل / تعطيل / حذف"
        )


        selected = st.selectbox(
            "اختر الموظف",
            [
                f"{e['employee_code']} — {e['name']}"
                for e in employees
            ]
        )


        selected_code = selected.split(
            " — ",
            1
        )[0]


        emp = get_employee(
            selected_code
        )


        if not emp:

            emp = get_employee(
                selected_code,
                active_only=False
            )


        c1, c2 = st.columns(2)


        with c1:

            new_name = st.text_input(
                "الاسم",
                value=emp["name"],
                key="edit_name"
            )


            new_job = st.text_input(
                "الوظيفة",
                value=emp["job_title"],
                key="edit_job"
            )


        with c2:

            new_phone = st.text_input(
                "الهاتف",
                value=emp["phone"],
                key="edit_phone"
            )


            st.write(
                f"الكود: **{emp['employee_code']}**"
            )


        x1, x2, x3 = st.columns(3)


        if x1.button(
            "حفظ التعديل",
            use_container_width=True
        ):

            if update_employee(
                selected_code,
                new_name,
                new_job,
                new_phone
            ):

                st.success(
                    "تم الحفظ."
                )

                st.rerun()


        if x2.button(
            "تفعيل/تعطيل",
            use_container_width=True
        ):

            set_employee_active(
                selected_code,
                not bool(emp["active"])
            )


            st.success(
                "تم تغيير حالة الموظف."
            )


            st.rerun()


        if x3.button(
            "حذف الموظف",
            use_container_width=True
        ):

            delete_employee(
                selected_code
            )


            st.success(
                "تم حذف الموظف."
            )


            st.rerun()


# =========================================================
# التقارير
# =========================================================

elif page == "التقارير":

    st.subheader(
        "📑 التقارير"
    )


    c1, c2 = st.columns(2)


    start = c1.date_input(
        "من",
        value=date.today()
    )


    end = c2.date_input(
        "إلى",
        value=date.today()
    )


    code_filter = st.text_input(
        "كود موظف (اختياري)"
    )


    rows = attendance_report(
        start,
        end,
        code_filter or None
    )


    if not rows:

        st.info(
            "لا توجد بيانات للفترة المحددة."
        )


    else:

        df = pd.DataFrame(
            rows
        )


        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


        x = io.BytesIO()


        with pd.ExcelWriter(
            x,
            engine="openpyxl"
        ) as writer:

            df.to_excel(
                writer,
                index=False,
                sheet_name="الحضور والانصراف"
            )


        st.download_button(
            "📥 تنزيل Excel",
            x.getvalue(),
            "attendance_report.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )


# =========================================================
# إعدادات الفرع
# =========================================================

elif page == "إعدادات الفرع":

    st.subheader(
        "⚙️ إعدادات الفرع"
    )


    name = st.text_input(
        "اسم الفرع",
        value=get_setting(
            "branch_name"
        )
    )


    lat = st.text_input(
        "خط العرض",
        value=get_setting(
            "branch_latitude"
        )
    )


    lon = st.text_input(
        "خط الطول",
        value=get_setting(
            "branch_longitude"
        )
    )


    radius = st.number_input(
        "نطاق الحضور بالمتر",
        10,
        1000,
        int(
            float(
                get_setting(
                    "radius_m",
                    "100"
                ) or 100
            )
        )
    )


    new_password = st.text_input(
        "كلمة مرور الإدارة الجديدة",
        type="password"
    )


    if st.button(
        "💾 حفظ الإعدادات",
        type="primary",
        use_container_width=True
    ):

        if not valid_coords(
            lat,
            lon
        ):

            st.error(
                "أدخل إحداثيات صحيحة."
            )


        else:

            set_setting(
                "branch_name",
                name
            )


            set_setting(
                "branch_latitude",
                lat
            )


            set_setting(
                "branch_longitude",
                lon
            )


            set_setting(
                "radius_m",
                radius
            )


            if new_password:

                set_setting(
                    "admin_password",
                    new_password
                )


            st.success(
                "تم حفظ الإعدادات."
            )


            st.rerun()


    st.divider()


    st.subheader(
        "🔑 QR Code"
    )


    if st.button(
        "إنشاء / تغيير QR",
        use_container_width=True
    ):

        set_setting(
            "site_token",
            token()
        )


        st.success(
            "تم إنشاء QR جديد."
        )


        st.rerun()


    st.caption(
        "تغيير QR يجعل الرمز السابق غير صالح."
    )


# =========================================================
# Footer
# =========================================================

st.divider()


st.caption(
    "✦ تصميم وتنفيذ أحمد الجنزوري ✦"
)
