import streamlit as st
import json
import re
from datetime import datetime, time
from dateutil.relativedelta import relativedelta

# ==========================================
# 0. ตั้งค่าหน้าเพจและตกแต่ง CSS (ธีมสีเขียวพาสเทล)
# ==========================================
st.set_page_config(page_title="โปรแกรมมหาทักษาปกรณ์ขั้นสูง", layout="wide")

st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #f1f8e9 0%, #e8f5e9 100%); color: #2f3640; }
[data-testid="stSidebar"] { background: #dcedc8; border-right: 1px solid #c5e1a5; }
div.stAlert { background-color: rgba(255, 255, 255, 0.9) !important; border: 1px solid #a5d6a7; border-radius: 10px; color: #2f3640 !important; }
h1, h2, h3, h4 { color: #2e7d32 !important; text-shadow: none; font-weight: 600; }
p, span, label, div { color: #2f3640; }
table { background-color: #ffffff; border-radius: 8px; overflow: hidden; width: 100%; border-collapse: collapse; }
th { background-color: #a5d6a7 !important; color: #1b5e20 !important; font-size: 16px; padding: 12px; text-align: left; }
td { color: #2f3640 !important; padding: 10px; border-bottom: 1px solid #e0e0e0; }
tbody tr:nth-child(even) { background-color: #f9fbe7; }
tbody tr:hover { background-color: #f1f8e9; }
.stSelectbox div[data-baseweb="select"] > div { background-color: #ffffff; color: #2f3640; border: 1px solid #c5e1a5; }
.stDateInput div[data-baseweb="input"] > div { background-color: #ffffff; color: #2f3640; border: 1px solid #c5e1a5; }
.stNumberInput div[data-baseweb="input"] > div { background-color: #ffffff; color: #2f3640; border: 1px solid #c5e1a5; }
.stTextInput div[data-baseweb="input"] > div { background-color: #ffffff; color: #2f3640; border: 1px solid #c5e1a5; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. โหลดข้อมูลคลังคำทำนาย
# ==========================================
@st.cache_data
def load_predictions():
    try:
        with open('predictions.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"matrix_64": {}, "star_pairs": {}, "anatomical_astrology": {}}

predictions_data = load_predictions()

PLANET_POWERS = {1: 6, 2: 15, 3: 8, 4: 17, 7: 10, 5: 19, 8: 12, 6: 21}
SEQUENCE_BASE = [1, 2, 3, 4, 7, 5, 8, 6]
SEQ_MALE_CW = [1, 2, 3, 4, 7, 5, 8, 6]
SEQ_FEMALE_CCW = [1, 6, 8, 5, 7, 4, 3, 2]
BHUM_NAMES = ["บริวาร", "อายุ", "เดช", "ศรี", "มูละ", "อุตสาหะ", "มนตรี", "กาลกิณี"]
PLANET_NAMES = {
    1: "อาทิตย์ (๑)", 2: "จันทร์ (๒)", 3: "อังคาร (๓)", 4: "พุธ (๔)",
    7: "เสาร์ (๗)", 5: "พฤหัสบดี (๕)", 8: "ราหู (๘)", 6: "ศุกร์ (๖)", 'TK': "ตากลาง (๕/๙)"
}
THAI_MONTHS = {
    1: "ม.ค.", 2: "ก.พ.", 3: "มี.ค.", 4: "เม.ย.", 5: "พ.ค.", 6: "มิ.ย.",
    7: "ก.ค.", 8: "ส.ค.", 9: "ก.ย.", 10: "ต.ค
