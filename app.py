%%writefile app.py
import streamlit as st
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

# โหลดข้อมูลคำทำนายจาก JSON
@st.cache_data
def load_predictions():
    try:
        with open('predictions.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"matrix_64": {}}

predictions_data = load_predictions()

# ข้อมูลพื้นฐาน
PLANET_POWERS = {1: 6, 2: 15, 3: 8, 4: 17, 7: 10, 5: 19, 8: 12, 6: 21}
SEQ_MALE_CW = [1, 2, 3, 4, 7, 5, 8, 6]
SEQ_FEMALE_CCW = [1, 6, 8, 5, 7, 4, 3, 2]
BHUM_NAMES = ["บริวาร", "อายุ", "เดช", "ศรี", "มูละ", "อุตสาหะ", "มนตรี", "กาลกิณี"]
PLANET_NAMES = {1: "อาทิตย์ (๑)", 2: "จันทร์ (๒)", 3: "อังคาร (๓)", 4: "พุธ (๔)", 7: "เสาร์ (๗)", 5: "พฤหัสบดี (๕)", 8: "ราหู (๘)", 6: "ศุกร์ (๖)", 'TK': "ตากลาง (๕/๙)"}

def get_digit_sum(age_yang):
    while age_yang > 9:
        age_yang = sum(int(digit) for digit in str(age_yang))
    return age_yang

def generate_taksa_path(start_planet, gender):
    seq = SEQ_MALE_CW if gender == 'ชาย' else SEQ_FEMALE_CCW
    idx = seq.index(start_planet)
    if start_planet == 1:
        return seq + ['TK']
    else:
        rotated = seq[idx:] + seq[:idx]
        idx_1 = rotated.index(1)
        return rotated[:idx_1+1] + ['TK'] + rotated[idx_1+1:]

def calculate_sub_periods(main_planet, start_date):
    main_power = PLANET_POWERS[main_planet]
    sub_periods = []
    current_date = start_date
    seq_keys = list(PLANET_POWERS.keys())
    start_idx = seq_keys.index(main_planet)
    ordered_subs = seq_keys[start_idx:] + seq_keys[:start_idx]

    for sub_planet in ordered_subs:
        sub_power = PLANET_POWERS[sub_planet]
        total_years = (main_power * sub_power) / 108.0
        years = int(total_years)
        months_decimal = (total_years - years) * 12
        months = int(months_decimal)
        days = round((months_decimal - months) * 30)
        end_date = current_date + relativedelta(years=years, months=months, days=days)
        sub_periods.append({
            "ดาวแทรก": PLANET_NAMES[sub_planet], "กำลัง": sub_power,
            "ระยะเวลา": f"{years} ปี {months} เดือน {days} วัน",
            "เริ่ม": current_date.strftime("%d/%m/%Y"), "สิ้นสุด": end_date.strftime("%d/%m/%Y")
        })
        current_date = end_date
    return sub_periods

# หน้าตาเว็บ
st.set_page_config(page_title="มหาทักษา", layout="wide")
st.title("🕉️ โปรแกรมคำนวณหลักมหาทักษาปกรณ์ขั้นสูง")

with st.sidebar:
    dob = st.date_input("วัน/เดือน/ปีเกิด", datetime(1995, 1, 15))
    gender = st.radio("เพศสภาพ", ["ชาย", "หญิง"])
    natal_planet = st.selectbox("ทักษากำเนิด (บริวารเดิม)", options=list(PLANET_NAMES.keys())[:-1], format_func=lambda x: PLANET_NAMES[x])
    target_date = st.date_input("วันที่ต้องการตรวจสอบ", datetime(2026, 6, 2))

age_full = relativedelta(target_date, dob).years
age_yang = age_full + 1
digit_sum = get_digit_sum(age_yang)
path = generate_taksa_path(natal_planet, gender)
transit_bariwan_planet = path[(digit_sum - 1) % len(path)] 

st.header(f"📊 ผลการคำนวณทักษาจร (อายุย่าง {age_yang} ปี)")
cols = st.columns(2)
with cols[0]: st.success(f"🌟 **บริวารเดิม:** {PLANET_NAMES[natal_planet]}")
with cols[1]: 
    if transit_bariwan_planet == 'TK': st.error("🎯 **ตากลาง** ใช้ พฤหัสบดี (๕) หรือ เกตุ (๙)")
    else: st.warning(f"🚀 **บริวารจรปีนี้:** {PLANET_NAMES[transit_bariwan_planet]}")

if transit_bariwan_planet != 'TK':
    seq_logic = SEQ_MALE_CW if gender == 'ชาย' else SEQ_FEMALE_CCW
    idx_natal = seq_logic.index(natal_planet)
    natal_bhum_map = {seq_logic[(idx_natal + i) % 8]: BHUM_NAMES[i] for i in range(8)}
    idx_transit = seq_logic.index(transit_bariwan_planet)
    transit_bhum_map = {seq_logic[(idx_transit + i) % 8]: BHUM_NAMES[i] for i in range(8)}

    matrix_data = []
    for p in seq_logic:
        b_orig = natal_bhum_map[p]
        b_trans = transit_bhum_map[p]
        prediction = predictions_data["matrix_64"].get(f"{b_orig}_{b_trans}", "🔮 รออัปเดตคำทำนาย...")
        matrix_data.append({"ดาว": PLANET_NAMES[p], "การไขว้ภูมิ": f"{b_orig} -> {b_trans}", "คำทำนาย": prediction})
    st.table(matrix_data)

st.subheader(f"⏳ ตารางดาวแทรกเสวยอายุ")
st.table(calculate_sub_periods(natal_planet, dob))
