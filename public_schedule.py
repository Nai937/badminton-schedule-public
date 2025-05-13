import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import pytz

# ====== SETTINGS ======
DB_PATH = "badminton_courts.db"

st.set_page_config(page_title="ตารางคอร์ดแบดมินตัน", layout="wide")


# ====== FUNCTIONS ======
def connect_db():
    return sqlite3.connect(DB_PATH)


def get_reserves(date=""):
    conn = connect_db()
    query = "SELECT * FROM reserve_bookings"
    params = []
    if date:
        query += " WHERE DATE(created_at) = DATE(?)"
        params.append(date)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def format_thai_date(date_obj):
    if not date_obj:
        return "-"
    days_th = ["วันจันทร์", "วันอังคาร", "วันพุธ", "วันพฤหัสบดี", "วันศุกร์", "วันเสาร์", "วันอาทิตย์"]
    months_th = [
        "มกราคม",
        "กุมภาพันธ์",
        "มีนาคม",
        "เมษายน",
        "พฤษภาคม",
        "มิถุนายน",
        "กรกฎาคม",
        "สิงหาคม",
        "กันยายน",
        "ตุลาคม",
        "พฤศจิกายน",
        "ธันวาคม",
    ]
    weekday = date_obj.weekday()
    return f"{days_th[weekday]}ที่ {date_obj.day} {months_th[date_obj.month - 1]} {date_obj.year + 543} เวลา {date_obj.strftime('%H:%M:%S')}"


def slot_range_overlap(slot, booking_range):
    def to_min(t):
        return int(t[:2]) * 60 + int(t[3:5])

    s1, e1 = [x.strip() for x in slot.split("-")]
    s2, e2 = [x.strip() for x in booking_range.split("-")]
    return to_min(s1) < to_min(e2) and to_min(e1) > to_min(s2)


def generate_slots(start_hour=15, end_hour=23):
    return [f"{h:02d}:00 - {h+1:02d}:00" for h in range(start_hour, end_hour)]


# ====== UI ======
st.title("📋 ตารางแสดงสถานะคอร์ด (Reserve)")
selected_date = st.date_input("📅 เลือกวันที่แสดงตาราง", value=datetime.now().date())
date_str = selected_date.strftime("%Y-%m-%d")
thai_date_str = format_thai_date(selected_date)

df_r = get_reserves(date=date_str).copy()
df_r["note"] = df_r["note"].fillna("")

time_slots = generate_slots()
courts = [1, 2, 3, 4]
court_schedule = {f"Court {i}": {slot: "ว่าง" for slot in time_slots} for i in courts}

for _, row in df_r.iterrows():
    court_key = f"Court {row['court']}"
    booking_range = row["time_range"]
    name = row["name"]
    note = row["note"]

    if "รอ" in note:
        status = "<span style='background-color:#fff176; color:black; padding:4px 6px; border-radius:6px;'>รอชำระ</span>"
    else:
        status = f"<span style='background-color:#ef5350; color:white; padding:4px 6px; border-radius:6px;'>{name}</span>"

    for slot in time_slots:
        if slot_range_overlap(slot, booking_range):
            court_schedule[court_key][slot] = status

# ====== RENDER TABLE ======
table_html = f"""
<style>
table {{ width: 100%; border-collapse: collapse; font-size: 15px; text-align: center; }}
th {{ background-color: #4caf50; color: white; padding: 10px; border: 1px solid #888; }}
td {{ padding: 8px; border: 1px solid #ccc; background-color: #e3f2fd; }}
.court-col {{ background-color: #c8e6c9; font-weight: bold; }}
</style>

<h4 style="text-align:center; font-size:24px;">LANGSUAN BADMINTON HALL</h4>
<p style="text-align:center; font-size:16px;">{thai_date_str}</p>

<table>
    <tr><th>Court / เวลา</th>
"""
for slot in time_slots:
    table_html += f"<th>{slot}</th>"
table_html += "</tr>"

for court in courts:
    court_key = f"Court {court}"
    table_html += f"<tr><td class='court-col'>{court_key}</td>"
    for slot in time_slots:
        value = court_schedule[court_key].get(slot, "ว่าง")
        if value == "ว่าง":
            value = "<span style='color:gray;'>ว่าง</span>"
        table_html += f"<td>{value}</td>"
    table_html += "</tr>"

table_html += "</table>"
st.markdown(table_html, unsafe_allow_html=True)

thai_time = datetime.now(pytz.timezone("Asia/Bangkok"))
st.caption(f"🕒 ตารางอัปเดตล่าสุด: {thai_time.strftime('%d/%m/%Y %H:%M:%S')}")
