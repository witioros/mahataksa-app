import streamlit as st
import json
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
.stTimeInput div[data-baseweb="input"] > div { background-color: #ffffff; color: #2f3640; border: 1px solid #c5e1a5; }
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
    7: "ก.ค.", 8: "ส.ค.", 9: "ก.ย.", 10: "ต.ค.", 11: "พ.ย.", 12: "ธ.ค."
}

# ==========================================
# 2. ฟังก์ชันคำนวณโหราศาสตร์
# ==========================================
def get_digit_sum(age_yang):
    while age_yang > 9:
        age_yang = sum(int(digit) for digit in str(age_yang))
    return age_yang

def generate_taksa_path(start_planet, gender):
    seq = SEQ_MALE_CW if gender == 'ชาย' else SEQ_FEMALE_CCW
    idx = seq.index(start_planet)
    rotated = seq[idx:] + seq[:idx]
    idx_1 = rotated.index(1)
    return rotated[:idx_1+1] + ['TK'] + rotated[idx_1+1:]

def get_current_dasha(natal_planet, dob, target_date):
    idx = SEQUENCE_BASE.index(natal_planet)
    ordered_planets = SEQUENCE_BASE[idx:] + SEQUENCE_BASE[:idx]
    
    current_start = dob
    for main_planet in ordered_planets:
        main_power = PLANET_POWERS[main_planet]
        main_end = current_start + relativedelta(years=main_power)
        
        if current_start <= target_date < main_end:
            sub_start = current_start
            sub_ordered = ordered_planets[ordered_planets.index(main_planet):] + ordered_planets[:ordered_planets.index(main_planet)]
            
            for sub_planet in sub_ordered:
                sub_power = PLANET_POWERS[sub_planet]
                total_years = (main_power * sub_power) / 108.0
                years = int(total_years)
                months_decimal = (total_years - years) * 12
                months = int(months_decimal)
                days = round((months_decimal - months) * 30)
                
                sub_end = sub_start + relativedelta(years=years, months=months, days=days)
                if sub_start <= target_date <= sub_end:
                    return main_planet, sub_planet, sub_start, sub_end
                sub_start = sub_end
        current_start = main_end
    return ordered_planets[0], ordered_planets[0], dob, target_date

def lookup_star_pair(p1, p2):
    key1 = f"{p1}_{p2}"
    key2 = f"{p2}_{p1}"
    raw_data = predictions_data.get("star_pairs", {}).get(key1) or predictions_data.get("star_pairs", {}).get(key2)
    
    if raw_data:
        if isinstance(raw_data, dict):
            return str(raw_data.get("type", "-")).strip(), str(raw_data.get("description", "ไม่มีคำอธิบาย")).strip()
        elif isinstance(raw_data, str):
            if ":" in raw_data:
                pair_type, desc = raw_data.split(":", 1)
                return pair_type.strip(), desc.strip()
            return "-", raw_data.strip()
    return "-", "ไม่มีเกณฑ์ดาวคู่เฉพาะกิจเด่นชัด"

def to_thai_month_year(dt):
    return f"{THAI_MONTHS[dt.month]} {dt.year + 543}"

# ==========================================
# 3. ส่วนจัดหน้าจอ (UI) หลัก
# ==========================================
st.title("🕉️ โปรแกรมคำนวณหลักมหาทักษาปกรณ์ขั้นสูง")
st.markdown("ระบบวิเคราะห์โครงสร้างพลวัตแห่งกาลเวลารายปีและเมทริกซ์ไขว้ภูมิพยากรณ์")

with st.sidebar:
    st.header("🔮 ข้อมูลดวงชะตา")
    
    # --- ปรับปรุง UI ส่วน วัน/เดือน/ปี (พ.ศ.) และ เวลาเกิด ---
    st.markdown("**วัน/เดือน/ปีเกิด (พ.ศ.)**")
    col_d, col_m, col_y = st.columns([1, 1.2, 1])
    with col_d:
        d_day = st.selectbox("วัน", range(1, 32), index=27) # ค่าเริ่มต้นวันที่ 28
    with col_m:
        d_month = st.selectbox("เดือน", list(THAI_MONTHS.values()), index=0) # ค่าเริ่มต้น ม.ค.
    with col_y:
        d_year_th = st.number_input("ปี (พ.ศ.)", min_value=2450, max_value=2600, value=2524, step=1)
        
    d_time = st.time_input("เวลาเกิด", value=time(12, 0))
    
    # ประกอบร่างเป็น Datetime อย่างปลอดภัย
    try:
        m_idx = list(THAI_MONTHS.values()).index(d_month) + 1
        y_eng = d_year_th - 543
        dob = datetime(y_eng, m_idx, d_day, d_time.hour, d_time.minute)
    except ValueError:
        st.error("⚠️ วันที่เกิดไม่ถูกต้อง (เช่น 31 ก.พ.) กรุณาเลือกวันและเดือนให้สอดคล้องกันครับ")
        st.stop()
        
    st.markdown("---")
    gender = st.radio("เพศสภาพ (มีผลต่อทิศทางการโคจร)", ["ชาย", "หญิง"])
    
    wed_night_option = st.selectbox(
        "กรณีเกิดวันพุธหลัง 18:00 น. (ดาวบริวารเดิม)", [4, 8],
        format_func=lambda x: "ดาวราหู (๘) - มติกระแสหลัก" if x == 8 else "ดาวพุธ (๔) - รักษาคุณธรรมดาวพฤหัสบดี"
    )
    base_day = st.selectbox("วันเกิดของท่าน", options=[1, 2, 3, 4, 7, 5, 8, 6], format_func=lambda x: PLANET_NAMES[x])
    natal_planet = wed_night_option if base_day in [4, 8] else base_day
    
    # --- ปรับปรุง UI ส่วนช่วงเวลาตรวจสอบ (จาก - ถึง) ---
    st.markdown("---")
    st.markdown("**ช่วงวันที่ต้องการตรวจสอบดวงชะตาจร**")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        start_target = st.date_input
