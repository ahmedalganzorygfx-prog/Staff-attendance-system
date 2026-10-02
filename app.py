import io
from datetime import date
import pandas as pd
import streamlit as st
from pathlib import Path

from database import *
from utils import distance_meters, valid_coords, token

st.set_page_config(
    page_title="نظام حضور وانصراف الموظفين",
    page_icon="assets/logo.png",
    layout="centered",
    initial_sidebar_state="expanded"
)
init_db()

# ---------- Style ----------
st.markdown("""

""", unsafe_allow_html=True)

branch_name = get_setting("branch_name", "الأكاديمية المهنية للمعلمين – فرع الجيزة")

def is_admin():
    return st.session_state.get("admin", False)

if "admin" not in st.session_state:
    st.session_state.admin = False

# ---------- Header & Logo ----------
logo_path = Path(__file__).resolve().parent / "assets" / "logo.png"

# توسيط اللوجو وتكبيره
_, logo_col, _ = st.columns([1, 1.5, 1])
with logo_col:
    st.image(str(logo_path), width=170)

st.markdown('
