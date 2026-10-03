import io
from datetime import date
import pandas as pd
import streamlit as st
from pathlib import Path

from database import *
from utils import distance_meters, valid_coords, token

# ==========================================
# 1. إعدادات الصفحة والتصميم العريض
# ==========================================
st.set_page_config(
    page_title="منظومة حضور وانصراف العاملين",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)
init_db()

# ==========================================
# 2. تخصيص CSS لتوسيط البرنامج بالكامل لمطابقة الصورة
# ==========================================
st.markdown("""

""", unsafe_allow_html=True)

# ==========================================
# 3. إدارة جلسة الإدارة (Admin Session)
# ==========================================
branch_name = get_setting("branch_name", "الأكاديمية المهنية للمعلمين")

def is_admin():
    return st.session_state.get("admin", False)

if "admin" not in st.session_state:
    st.session_state.admin = False

# ==========================================
# ==========================================
# 4. رأس الصفحة (الشعار والعناوين)
# ==========================================
logo_path = Path(__file__).resolve().parent / "assets" / "logo.png"
logo_col = st.columns([1, 1, 1])[1]
with logo_col:
    if logo_path.exists():
        st.image(str(logo_path), width=95)

header_html = f"""
