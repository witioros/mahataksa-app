import streamlit as st
import json
import re
from datetime import datetime, time
from dateutil.relativedelta import relativedelta

# ==========================================
# 0. ตั้งค่าหน้าเพจและตกแต่ง CSS
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
    1: "ม.ค.", 2: "ก.พ.", 3: "มี.ค.", 4: "เม.ย.", 
    5: "พ.ค.", 6: "มิ.ย.", 7: "ก.ค.", 8: "ส.ค.", 
    9: "ก.ย.", 10: "ต.ค.", 11: "พ.ย.", 12: "ธ.ค."
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

# ดึงค่าปัจจุบันสำหรับเป็นค่าเริ่มต้น
today = datetime.now()
current_thai_year = today.year + 543

# ==========================================
# 3. ส่วนจัดหน้าจอ (UI) หลัก
# ==========================================
st.title("🕉️ โปรแกรมคำนวณหลักมหาทักษาปกรณ์ขั้นสูง")
st.markdown("ระบบวิเคราะห์โครงสร้างพลวัตแห่งกาลเวลารายปีและเมทริกซ์ไขว้ภูมิพยากรณ์")

error_message = None
dob = None

with st.sidebar:
    st.header("🔮 ข้อมูลดวงชะตา")
    
    st.markdown("**วัน/เดือน/ปีเกิด (พ.ศ.)**")
    col_d, col_m, col_y = st.columns([1, 1.2, 1])
    with col_d:
        d_day = st.selectbox("วัน", range(1, 32), index=today.day - 1)
    with col_m:
        d_month = st.selectbox("เดือน", list(THAI_MONTHS.values()), index=today.month - 1)
    with col_y:
        d_year_th = st.number_input("ปี (พ.ศ.)", min_value=2400, max_value=2600, value=current_thai_year, step=1)
        
    d_time_str = st.text_input("เวลาเกิด (พิมพ์ตัวเลข เช่น 13:45)", value=today.strftime("%H:%M"))
    
    time_val = d_time_str.strip().replace(".", ":")
    hour, minute = 0, 0
    if not re.match(r"^\d{1,2}:\d{2}$", time_val):
        error_message = "⚠️ รูปแบบเวลาเกิดไม่ถูกต้อง กรุณาพิมพ์ตัวเลข เช่น 09:30 หรือ 13:45"
    else:
        try:
            hour, minute = map(int, time_val.split(":"))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                error_message = "⚠️ ตัวเลขเวลาเกินขอบเขต (ชั่วโมงต้องอยู่ระหว่าง 0-23, นาที 0-59)"
        except:
            error_message = "⚠️ รูปแบบเวลาเกิดไม่ถูกต้อง"
    
    if not error_message:
        try:
            m_idx = list(THAI_MONTHS.values()).index(d_month) + 1
            y_eng = d_year_th - 543
            dob = datetime(y_eng, m_idx, d_day, hour, minute)
        except ValueError:
            error_message = f"⚠️ วันที่ {d_day} {d_month} {d_year_th} ไม่มีอยู่จริงบนปฏิทิน (เช่น 31 ก.พ.) กรุณาเลือกใหม่ครับ"
        
    st.markdown("---")
    gender = st.radio("เพศสภาพ (มีผลต่อทิศทางการโคจร)", ["ชาย", "หญิง"])
    
    wed_night_option = st.selectbox(
        "กรณีเกิดวันพุธหลัง 18:00 น. (ดาวบริวารเดิม)", [4, 8],
        format_func=lambda x: "ดาวราหู (๘) - มติกระแสหลัก" if x == 8 else "ดาวพุธ (๔) - รักษาคุณธรรมดาวพฤหัสบดี"
    )
    base_day = st.selectbox("วันเกิดของท่าน", options=[1, 2, 3, 4, 7, 5, 8, 6], format_func=lambda x: PLANET_NAMES[x])
    natal_planet = wed_night_option if base_day in [4, 8] else base_day
    
    st.markdown("---")
    st.markdown("**ช่วงวันที่ต้องการตรวจสอบดวงชะตาจร**")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        start_target = st.date_input("เริ่มจากวันที่", value=today)
    with col_t2:
        end_target = st.date_input("ถึงวันที่", value=today + relativedelta(years=1))
        
    if not error_message:
        if start_target > end_target:
            error_message = "⚠️ วันที่เริ่มต้น ต้องไม่มากกว่าวันที่สิ้นสุดครับ"
        elif datetime.combine(start_target, datetime.min.time()) < dob:
            error_message = "⚠️ วันที่ตรวจสอบดวงชะตา ต้องเป็นวันที่หลังจากเจ้าชะตาเกิดแล้วครับ"
        
    center_eye_config = st.selectbox("ตั้งค่าดาวประธานช่วงตกตากลาง", ["พฤหัสบดี (๕)", "พระเกตุ (๙)"])

# ==========================================
# 🛑 จุดตรวจสอบ Error บนหน้าจอหลัก
# ==========================================
if error_message:
    st.error(error_message)
    st.info("💡 โปรดตรวจสอบและแก้ไขข้อมูลในเมนูด้านซ้ายมือให้ถูกต้อง เพื่อให้ระบบเริ่มประมวลผลการคำนวณครับ")
    st.stop()

target_date = datetime.combine(start_target, datetime.min.time())
dt_end_target = datetime.combine(end_target, datetime.max.time())

age_full = relativedelta(target_date, dob).years
age_yang = age_full + 1
digit_sum = get_digit_sum(age_yang)

path = generate_taksa_path(natal_planet, gender)
transit_bariwan_planet = path[(digit_sum - 1) % len(path)]

st.header(f"📊 ผลการประมวลผลทักษาจร (อายุย่าง {age_yang} ปี ณ วันที่เริ่มต้นตรวจสอบ)")
st.info(f"**สมการยุบตัวเลข (Digit Sum):** อายุย่าง {age_yang} ปี ➡️ รวมได้ = **{digit_sum} ก้าวดำเนิน** | **ทิศทางวิถี:** เพศ{gender} {'เวียนขวา (ตามเข็ม)' if gender == 'ชาย' else 'เวียนซ้าย (ทวนเข็ม)'}")

col1, col2 = st.columns(2)
with col1: st.success(f"🌟 **ภูมิบริวารเดิม (กำเนิด):** {PLANET_NAMES[natal_planet]}")
with col2:
    if transit_bariwan_planet == 'TK': st.error(f"🎯 **ทักษาจรตกภูมิ 'ตากลาง'** ➡️ ใช้ {center_eye_config} ทำหน้าที่บริวารจรประธานปี")
    else: st.warning(f"🚀 **ภูมิบริวารจรประจำปีนี้:** {PLANET_NAMES[transit_bariwan_planet]}")

# ==========================================
# 4. เมทริกซ์ไขว้ภูมิ
# ==========================================
st.markdown("---")
st.subheader("🧬 เมทริกซ์แห่งการไขว้ภูมิและการโรคาพยากรณ์ (อ้างอิง ณ วันเริ่มต้นตรวจสอบ)")

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
        prediction_text = predictions_data.get("matrix_64", {}).get(f"{b_orig}_{b_trans}", "🔮 รออัปเดตคำทำนาย...")
        
        health_alert = "-"
        if b_trans in ["กาลกิณี", "อายุ"]:
            organ = predictions_data.get("anatomical_astrology", {}).get(str(p), "ระบบอวัยวะภายใน")
            health_alert = f"⚠️ ระวังจุดเปราะบาง: {organ}"
            
        matrix_rows.append({
            "ดาวพระเคราะห์": PLANET_NAMES[p], "ภูมิเดิม": b_orig, "ภูมิจรปีนี้": b_trans,
            "การปะทะไขว้ภูมิ": f"{b_orig}เดิม ➡️ {b_trans}จร", "🔮 คำทำนายตามคัมภีร์": prediction_text, "🩺 โรคาพยากรณ์": health_alert
        })
    st.table(matrix_rows)

# ==========================================
# 5. ระบบไทม์ไลน์ดาวเสวยอายุและดาวแทรก (ประมวลผลเฉพาะช่วงเวลาที่เลือก)
# ==========================================
st.markdown("---")
st.subheader(f"⏳ รายงานพยากรณ์ดาวแทรกแบบเจาะลึก (เฉพาะช่วงเวลาที่คุณระบุ)")
st.info(f"📌 แสดงผลเฉพาะดาวแทรกที่โคจรพาดผ่านช่วงวันที่: **{start_target.strftime('%d/%m/%Y')}** ถึง **{end_target.strftime('%d/%m/%Y')}**")

idx_natal = SEQUENCE_BASE.index(natal_planet)
natal_ordered_planets = SEQUENCE_BASE[idx_natal:] + SEQUENCE_BASE[:idx_natal]

expanded_timeline = []
counter = 1
current_runner = dob
cycle_count = 0

# ลูปหาดาวแทรกเฉพาะที่ทับซ้อนกับช่วงเวลาที่ผู้ใช้ระบุเท่านั้น (ข้ามรอบอายุได้ไม่จำกัด)
while current_runner <= dt_end_target and cycle_count < 200:
    for main_p in natal_ordered_planets:
        main_power = PLANET_POWERS[main_p]
        main_end = current_runner + relativedelta(years=main_power)
        
        if main_end >= target_date and current_runner <= dt_end_target:
            idx_m = SEQUENCE_BASE.index(main_p)
            ordered_subs = SEQUENCE_BASE[idx_m:] + SEQUENCE_BASE[:idx_m]
            
            sub_start = current_runner
            for sub_p in ordered_subs:
                sub_power = PLANET_POWERS[sub_p]
                total_years = (main_power * sub_power) / 108.0
                years = int(total_years)
                months_decimal = (total_years - years) * 12
                months = int(months_decimal)
                days = round((months_decimal - months) * 30)
                
                sub_end = sub_start + relativedelta(years=years, months=months, days=days)
                
                # เช็คว่าดาวแทรกช่วงนี้ ทับซ้อนกับช่วงเวลาที่ขอตรวจสอบหรือไม่
                if sub_end >= target_date and sub_start <= dt_end_target:
                    p_type, p_essence = lookup_star_pair(main_p, sub_p)
                    analysis_text = f"**เนื้อแท้:** {p_essence}\n\n"
                    
                    seg_date = sub_start
                    while seg_date < sub_end:
                        a_full = relativedelta(seg_date, dob).years
                        a_yang = a_full + 1
                        
                        next_birthday = dob + relativedelta(years=a_full + 1)
                        seg_end = min(next_birthday, sub_end)
                        
                        d_sum = get_digit_sum(a_yang)
                        p_path = generate_taksa_path(natal_planet, gender)
                        t_bariwan = p_path[(d_sum - 1) % len(p_path)]
                        
                        if t_bariwan == 'TK':
                            analysis_text += f"🔹 **ปี พ.ศ. {seg_date.year + 543} (อายุย่าง {a_yang} ปี):** ทักษาจรตกภูมิ **'ตากลาง'** พลังดาวเข้าสู่จุดปรับสมดุลพิกัดศูนย์กลาง\n\n"
                        else:
                            s_logic = SEQ_MALE_CW if gender == 'ชาย' else SEQ_FEMALE_CCW
                            idx_n = s_logic.index(natal_planet)
                            n_map = {s_logic[(idx_n + i) % 8]: BHUM_NAMES[i] for i in range(8)}
                            b_orig = n_map[sub_p]
                            
                            idx_t = s_logic.index(t_bariwan)
                            t_map = {s_logic[(idx_t + i) % 8]: BHUM_NAMES[i] for i in range(8)}
                            b_trans = t_map[sub_p]
                            
                            matrix_desc = predictions_data.get("matrix_64", {}).get(f"{b_orig}_{b_trans}", "รออัปเดตคำพยากรณ์...")
                            
                            prefix = "⚠️ **ปีวิกฤต!** " if b_trans == "กาลกิณี" else "🔹 "
                            analysis_text += f"{prefix}**ปี พ.ศ. {seg_date.year + 543} (อายุย่าง {a_yang} ปี):** บริวารจรตกดาว {PLANET_NAMES[t_bariwan]} ส่งผลให้ดาว {PLANET_NAMES[sub_p]} แปรสภาพเป็น **'{b_trans}จร'** ({b_orig}เดิม ➡️ {b_trans}จร) : {matrix_desc}\n\n"
                        
                        seg_date = seg_end
                        
                    age_y_start = relativedelta(sub_start, dob).years + 1
                    age_y_end = relativedelta(sub_end, dob).years + 1
                    age_range_str = f"อายุย่าง {age_y_start} ปี" if age_y_start == age_y_end else f"อายุย่าง {age_y_start} - {age_y_end} ปี"
                    
                    expanded_timeline.append({
                        "ลำดับ": counter,
                        "ช่วงเวลาโดยประมาณ\n(ระบุตามอายุย่าง)": f"{to_thai_month_year(sub_start)} - {to_thai_month_year(sub_end)}\n({age_range_str})",
                        "เสวย - แทรก\n(คู่ดาว)": f"{PLANET_NAMES[main_p]} - {PLANET_NAMES[sub_p]}",
                        "ประเภท\n(เนื้อแท้)": p_type,
                        "ความหมายพื้นฐาน และ ผลลัพธ์เมื่อมหาทักษาจรแทรกแซงในแต่ละปี": analysis_text
                    })
                    counter += 1
                sub_start = sub_end
        current_runner = main_end
        if current_runner > dt_end_target:
            break
    cycle_count += 1

if not expanded_timeline:
    st.warning("ไม่พบช่วงดาวแทรกในระยะเวลาที่คุณระบุครับ")
else:
    for row in expanded_timeline:
        with st.container():
            st.markdown(f"### โครงสร้างลูปดาวแทรกที่ {row['ลำดับ']} 🟢")
            col_t1, col_t2, col_t3 = st.columns([1, 1, 3])
            with col_t1:
                st.metric(label="ช่วงเวลา (พ.ศ.)", value=row["ช่วงเวลาโดยประมาณ\n(ระบุตามอายุย่าง)"].split("\n")[0])
                st.caption(row["ช่วงเวลาโดยประมาณ\n(ระบุตามอายุย่าง)"].split("\n")[1])
            with col_t2:
                st.write(f"**คู่ดาวเสวย-แทรก:**\n{row['เสวย - แทรก\n(คู่ดาว)']}")
                st.write(f"**ประเภท:** {row['ประเภท\n(เนื้อแท้)']}")
            with col_t3:
                st.markdown(row["ความหมายพื้นฐาน และ ผลลัพธ์เมื่อมหาทักษาจรแทรกแซงในแต่ละปี"])
            st.markdown("---")
