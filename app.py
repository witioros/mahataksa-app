import streamlit as st
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

# ==========================================
# 1. โหลดข้อมูลคลังคำทำนายจากไฟล์ JSON
# ==========================================
@st.cache_data
def load_predictions():
    try:
        with open('predictions.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"matrix_64": {}, "star_pairs": {}, "anatomical_astrology": {}}

predictions_data = load_predictions()

# กำลังพระเคราะห์ตามคัมภีร์เฉลิมไตรภพ
PLANET_POWERS = {1: 6, 2: 15, 3: 8, 4: 17, 7: 10, 5: 19, 8: 12, 6: 21}
# ลำดับดาวเสวยอายุมาตรฐาน
SEQUENCE_BASE = [1, 2, 3, 4, 7, 5, 8, 6]

# ลำดับการโคจรทักษาจรจรรายปีแยกเพศสภาพ
SEQ_MALE_CW = [1, 2, 3, 4, 7, 5, 8, 6]
SEQ_FEMALE_CCW = [1, 6, 8, 5, 7, 4, 3, 2]

BHUM_NAMES = ["บริวาร", "อายุ", "เดช", "ศรี", "มูละ", "อุตสาหะ", "มนตรี", "กาลกิณี"]
PLANET_NAMES = {
    1: "อาทิตย์ (๑)", 2: "จันทร์ (๒)", 3: "อังคาร (๓)", 4: "พุธ (๔)",
    7: "เสาร์ (๗)", 5: "พฤหัสบดี (๕)", 8: "ราหู (๘)", 6: "ศุกร์ (๖)", 'TK': "ตากลาง (๕/๙)"
}

# ==========================================
# 2. ฟังก์ชันคำนวณตามหลักคณิตศาสตร์โหราศาสตร์
# ==========================================
def get_digit_sum(age_yang):
    """กระบวนการยุบตัวเลข (Digit Summation) จนเหลือหลักเดียว"""
    while age_yang > 9:
        age_yang = sum(int(digit) for digit in str(age_yang))
    return age_yang

def generate_taksa_path(start_planet, gender):
    """คำนวณเส้นทางการเดินทักษาจรพร้อมกฎแห่งตากลาง"""
    seq = SEQ_MALE_CW if gender == 'ชาย' else SEQ_FEMALE_CCW
    idx = seq.index(start_planet)
    
    # หมุนวงรอบให้เริ่มที่ดาวบริวารกำเนิด
    rotated = seq[idx:] + seq[:idx]
    # แทรก 'ตากลาง' (TK) เข้าไปในตำแหน่งหลังจากก้าวผ่านดาวอาทิตย์ (๑) เสมอ
    idx_1 = rotated.index(1)
    return rotated[:idx_1+1] + ['TK'] + rotated[idx_1+1:]

def get_current_dasha(natal_planet, dob, target_date):
    """คำนวณหาดาวเสวยอายุหลักและดาวแทรก ณ วันที่ตรวจสอบ"""
    idx = SEQUENCE_BASE.index(natal_planet)
    ordered_planets = SEQUENCE_BASE[idx:] + SEQUENCE_BASE[:idx]
    
    current_start = dob
    for main_planet in ordered_planets:
        main_power = PLANET_POWERS[main_planet]
        main_end = current_start + relativedelta(years=main_power)
        
        # ตรวจสอบว่าช่วงเวลาเป้าหมายตกอยู่ในดาวเสวยอายุนี้หรือไม่
        if current_start <= target_date < main_end:
            # คำนวณดาวแทรกข้างใน
            sub_start = current_start
            sub_ordered = ordered_planets[ordered_planets.index(main_planet):] + ordered_planets[:ordered_planets.index(main_planet)]
            
            for sub_planet in sub_ordered:
                sub_power = PLANET_POWERS[sub_planet]
                # สมการสัดส่วนกำลังพระเคราะห์รวม 108 ปี
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

# ==========================================
# 3. ส่วนการจัดหน้าจอ Web Application (UI)
# ==========================================
st.set_page_config(page_title="โปรแกรมมหาทักษาปกรณ์ขั้นสูง", layout="wide")
st.title("🕉️ โปรแกรมคำนวณหลักมหาทักษาปกรณ์และดาวเสวยอายุขั้นสูง")
st.markdown("ระบบคำนวณโครงสร้างพลวัตแห่งกาลเวลารายปีและเมทริกซ์ไขว้ภูมิพยากรณ์")

# ส่วนรับข้อมูลอินพุต
with st.sidebar:
    st.header("🔮 ข้อมูลดวงชะตา")
    
    # 🛠️ [จุดแก้ไข] เพิ่มระบบล็อกช่วงเวลาปฏิทินให้ย้อนหลังได้มากกว่า 70 ปี ถึงปีปัจจุบัน 2026
    dob = st.date_input(
        "วันเกิด (ค.ศ.)", 
        value=datetime(1985, 1, 1),              # ตั้งค่าเริ่มต้นให้อยู่ในช่วงกลางๆ
        min_value=datetime(1950, 1, 1),          # ย้อนหลังได้สูงสุดถึงปี 1950 (ครอบคลุม 76 ปี)
        max_value=datetime(2026, 12, 31)         # สิ้นสุดที่ปีปัจจุบัน 2026
    )
    
    gender = st.radio("เพศสภาพ (มีผลต่อทิศทางการโคจร)", ["ชาย", "หญิง"])
    
    wed_night_option = st.selectbox(
        "กรณีเกิดวันพุธหลัง 18:00 น. (ดาวบริวารเดิม)",
        options=[4, 8],
        format_func=lambda x: "ดาวราหู (๘) - มติกระแสหลัก" if x == 8 else "ดาวพุธ (๔) - รักษาคุณธรรมดาวพฤหัสบดี"
    )
    
    base_day = st.selectbox(
        "วันเกิดของท่าน",
        options=[1, 2, 3, 4, 7, 5, 8, 6],
        format_func=lambda x: PLANET_NAMES[x]
    )
    
    # หากเลือกวันเกิดอื่นๆ ที่ไม่ใช่พุธ ให้ยึดตามนั้น แต่ถ้าเป็นพุธให้เลือกตาม Option พิเศษได้
    natal_planet = wed_night_option if base_day in [4, 8] else base_day
    
    # 🛠️ [จุดแก้ไข] เพิ่มการล็อกช่วงเวลาของวันจรที่ต้องการตรวจสอบด้วยเช่นกัน
    target_date = st.date_input(
        "วันที่ต้องการตรวจสอบดวงชะตาจร", 
        value=datetime(2026, 6, 2),
        min_value=datetime(1950, 1, 1),
        max_value=datetime(2050, 12, 31)
    )
    
    center_eye_config = st.selectbox("ตั้งค่าดาวประธานช่วงตกตากลาง", ["พฤหัสบดี (๕)", "พระเกตุ (๙)"])

# คำนวณอายุและทักษาจรรายปี
age_full = relativedelta(target_date, dob).years
age_yang = age_full + 1
digit_sum = get_digit_sum(age_yang)

path = generate_taksa_path(natal_planet, gender)
transit_bariwan_planet = path[(digit_sum - 1) % len(path)]

# แสดงผลการคำนวณหลัก
st.header(f"📊 ผลการประมวลผลทักษาจร (อายุย่าง {age_yang} ปี)")
st.info(f"**สมการยุบตัวเลข (Digit Sum):** อายุย่าง {age_yang} ปี ➡️ รวมได้ = **{digit_sum} ก้าวดำเนิน** | **ทิศทางวิถี:** เพศ{gender} {'เวียนขวา (ตามเข็ม)' if gender == 'ชาย' else 'เวียนซ้าย (ทวนเข็ม)'}")

col1, col2 = st.columns(2)
with col1:
    st.success(f"🌟 **ภูมิบริวารเดิม (กำเนิด):** {PLANET_NAMES[natal_planet]}")
with col2:
    if transit_bariwan_planet == 'TK':
        st.error(f"🎯 **ทักษาจรตกภูมิ 'ตากลาง' (ปีแห่งจุดพักสมดุล)** ➡️ ใช้ {center_eye_config} ทำหน้าที่บริวารจรประธานปี")
    else:
        st.warning(f"🚀 **ภูมิบริวารจรประจำปีนี้:** {PLANET_NAMES[transit_bariwan_planet]}")

# ==========================================
# 4. การแสดงผลตารางเมทริกซ์ไขว้ภูมิ 64 รูปแบบ
# ==========================================
st.markdown("---")
st.subheader("🧬 เมทริกซ์แห่งการไขว้ภูมิและการโรคาพยากรณ์ (Matrix Interpretation)")

if transit_bariwan_planet == 'TK':
    st.write("🔍 เนื่องจากปีนี้ดวงชะตาตกอยู่ในภูมิ **'ตากลาง'** พลังงานดาวเข้าสู่ช่วงปรับสมดุลพิกัดศูนย์กลาง จึงงดการไขว้ภูมิปะทะชั่วคราวตามกฎคัมภีร์ดั้งเดิม")
else:
    seq_logic = SEQ_MALE_CW if gender == 'ชาย' else SEQ_FEMALE_CCW
    idx_natal = seq_logic.index(natal_planet)
    natal_bhum_map = {seq_logic[(idx_natal + i) % 8]: BHUM_NAMES[i] for i in range(8)}
    
    idx_transit = seq_logic.index(transit_bariwan_planet)
    transit_bhum_map = {seq_logic[(idx_transit + i) % 8]: BHUM_NAMES[i] for i in range(8)}

    matrix_rows = []
    for p in seq_logic:
        b_orig = natal_bhum_map[p]
        b_trans = transit_bhum_map[p]
        
        # ดึงคำทำนายจากคลังข้อความใน JSON
        lookup_key = f"{b_orig}_{b_trans}"
        prediction_text = predictions_data.get("matrix_64", {}).get(lookup_key, "🔮 (ระบบกำลังรออัปเดตคำทำนายภูมิคู่พยากรณ์นี้...)")
        
        # ตรวจสอบจุดเปราะบางทางกายวิภาคศาสตร์ (เมื่อตกภูมิกาลกิณี หรือ อายุจร)
        health_alert = "-"
        if b_trans in ["กาลกิณี", "อายุ"]:
            organ = predictions_data.get("anatomical_astrology", {}).get(str(p), "ระบบอวัยวะภายใน")
            health_alert = f"⚠️ ระวังจุดเปราะบาง: {organ}"
            
        matrix_rows.append({
            "ดาวพระเคราะห์": PLANET_NAMES[p],
            "ภูมิเดิม": b_orig,
            "ภูมิจรปีนี้": b_trans,
            "การปะทะไขว้ภูมิ": f"{b_orig}เดิม -> {b_trans}จร",
            "🔮 คำทำนายตามคัมภีร์": prediction_text,
            "🩺 โรคาพยากรณ์": health_alert
        })
    st.table(matrix_rows)

# ==========================================
# 5. การคำนวณดาวเสวยอายุและดาวแทรกปัจจุบัน
# ==========================================
st.markdown("---")
st.subheader("⏳ ไทม์ไลน์ระบบดาวเสวยอายุและดาวแทรกปัจจุบัน")

main_p, sub_p, start_d, end_d = get_current_dasha(natal_planet, dob, target_date)
pair_key = f"{main_p}_{sub_p}"
pair_relation = predictions_data.get("star_pairs", {}).get(pair_key, "ไม่มีเกณฑ์ดาวคู่เฉพาะกิจเด่นชัด (ให้คุณโทษตามมาตรฐานดาว)")

st.write(f"📌 ณ วันที่ตรวจสอบ ดวงชะตากำลังตกอยู่ในช่วง: **ดาวหลักเสวยอายุ: {PLANET_NAMES[main_p]}** และมี **ดาวแทรก: {PLANET_NAMES[sub_p]}**")
st.warning(f"💬 **วิเคราะห์ปฏิสัมพันธ์คู่ดาวปะทะช่วงเวลานี้:** {pair_relation}")

# แสดงตารางดาวแทรกทั้งหมดภายใต้ดาวเสวยอายุหลักปัจจุบัน
st.markdown("#### 📅 ตารางไทม์ไลน์ดาวแทรกในรอบเสวยปัจจุบัน")
main_power = PLANET_POWERS[main_p]
idx_m = SEQUENCE_BASE.index(main_p)
ordered_subs = SEQUENCE_BASE[idx_m:] + SEQUENCE_BASE[:idx_m]

sub_timeline_data = []
current_runner = dob # คำนวณสะสมจากวันเกิดเพื่อหาลูปดาวเสวยปัจจุบัน
# วิ่งหาจุดเริ่มต้นของรอบเสวยอายุหลักนี้ก่อน
for p in SEQUENCE_BASE:
    if p == main_p:
        break
    current_runner += relativedelta(years=PLANET_POWERS[p])

for sub_planet in ordered_subs:
    sub_power = PLANET_POWERS[sub_planet]
    total_years = (main_power * sub_power) / 108.0
    years = int(total_years)
    months_decimal = (total_years - years) * 12
    months = int(months_decimal)
    days = round((months_decimal - months) * 30)
    
    next_runner = current_runner + relativedelta(years=years, months=months, days=days)
    
    # ตรวจสอบว่าเป็นช่วงปัจจุบันเพื่อทำการไฮไลท์
    is_current = "🟢 กำลังมีอิทธิพลอยู่ตอนนี้" if sub_planet == sub_p else "-"
    
    sub_timeline_data.append({
        "ลำดับดาวแทรก": PLANET_NAMES[sub_planet],
        "กำลังดาว": sub_power,
        "ระยะเวลาเสวยแทรก": f"{years} ปี {months} เดือน {days} วัน",
        "เริ่มวันที่": current_runner.strftime("%d/%m/%Y"),
        "สิ้นสุดวันที่": next_runner.strftime("%d/%m/%Y"),
        "สถานะ": is_current
    })
    current_runner = next_runner

st.table(sub_timeline_data)
