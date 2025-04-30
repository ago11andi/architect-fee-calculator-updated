
import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
import plotly.express as px
from fpdf import FPDF
from PIL import Image
import os

st.set_page_config(page_title="Architect Fee Tool – aperioddesign",
                   page_icon="🅰️", layout="wide")

# Load logo
LOGO_PATH = "logo.png"
if os.path.exists(LOGO_PATH):
    st.image(Image.open(LOGO_PATH), width=140)

st.title("🏗️ Architect Fee Calculator  |  aperioddesign.com")

# --- Project Info
st.header("1. Project Info")
construction_cost = st.number_input("Estimated Construction Cost ($)", min_value=0.0, value=1_000_000.0, step=10000.0)
base_fee_percent = st.number_input("Base Fee % of Construction Cost", min_value=0.0, max_value=1.0, value=0.08, step=0.01)
complexity_factor = st.number_input("Complexity Factor", min_value=0.5, value=1.1, step=0.05)
location_factor   = st.number_input("Location Factor",   min_value=0.5, value=1.0, step=0.05)
risk_factor       = st.number_input("Risk Factor",       min_value=0.5, value=1.05, step=0.05)
firm_multiplier   = st.number_input("Firm Multiplier (OH + Profit)", min_value=1.0, value=3.0, step=0.1)

# --- Hourly Rates
st.header("2. Hourly Rates ($)")
roles = ["Principal", "Project Manager", "Architect", "Drafter"]
defaults = [200, 150, 100, 75]
rates = {r: st.number_input(r, value=d, step=10) for r, d in zip(roles, defaults)}

# --- Hours per Phase
st.header("3. Estimated Hours per Phase")
phases = ['Pre-Design', 'Schematic Design', 'Design Development',
          'Construction Documents', 'Bidding/Negotiation', 'Construction Administration']
hours_data = {}
for p in phases:
    with st.expander(p, expanded=False):
        hours_data[p] = {r: st.number_input(f"{p} – {r}", min_value=0, value=10, step=1) for r in roles}

# --- Consultants
st.header("4. Consultant Percentages")
consultant_percent = {
    "Structural Engineer": st.number_input("Structural Engineer (%)", value=1.5, step=0.1),
    "MEP Engineer": st.number_input("MEP Engineer (%)", value=2.0, step=0.1),
    "Civil Engineer": st.number_input("Civil Engineer (%)", value=1.0, step=0.1),
    "Landscape Architect": st.number_input("Landscape Architect (%)", value=0.5, step=0.1)
}
consultant_fees = {k: construction_cost * v/100 for k, v in consultant_percent.items()}

# --- Schedule
st.header("5. Schedule Tracker")
schedule_rows = []
for p in phases:
    c1, c2 = st.columns(2)
    start = c1.date_input(f"{p} Start", date.today(), key=f"{p}_start")
    end   = c2.date_input(f"{p} End", date.today(), key=f"{p}_end")
    schedule_rows.append({"Phase": p, "Start": start, "End": end, "Duration (days)": (end-start).days})
df_schedule = pd.DataFrame(schedule_rows)

# --- Calculations
total_raw = sum(hours_data[p][r]*rates[r] for p in phases for r in roles)
workplan_fee = total_raw * firm_multiplier
pct_adj = base_fee_percent*complexity_factor*location_factor*risk_factor
pct_fee = construction_cost * pct_adj

df_summary = pd.DataFrame({
    "Metric": ["Total Raw Labor", "Workplan Fee", "%-of-Cost Fee"],
    "Amount ($)": [total_raw, workplan_fee, pct_fee]
})

# --- PDF creation
def build_pdf():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    # logo
    if os.path.exists(LOGO_PATH):
        try:
            pdf.image(LOGO_PATH, x=10, y=8, w=40)
        except RuntimeError:
            pass
    pdf.ln(22)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Architect Fee Calculator Report", ln=True, align="C")
    pdf.ln(3)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0,8,"Project Information",ln=True)
    pdf.set_font("Arial","",10)
    for label, val in [
        ("Construction Cost", f"${construction_cost:,.0f}"),
        ("Base Fee %", f"{base_fee_percent*100:.2f}%"),
        ("Complexity Factor", complexity_factor),
        ("Location Factor", location_factor),
        ("Risk Factor", risk_factor),
        ("Firm Multiplier", firm_multiplier)
    ]:
        pdf.cell(60,6,f"{label}:",0)
        pdf.cell(40,6,str(val),ln=True)

    pdf.ln(3)
    pdf.set_font("Arial","B",12)
    pdf.cell(0,8,"Hourly Rates",ln=True)
    pdf.set_font("Arial","",10)
    for r in roles:
        pdf.cell(60,6,f"{r}:",0)
        pdf.cell(40,6,f"${rates[r]:,.2f}",ln=True)

    pdf.ln(3)
    pdf.set_font("Arial","B",12)
    pdf.cell(0,8,"Hours per Phase",ln=True)
    pdf.set_font("Arial","",8)
    pdf.cell(35,6,"Phase",1)
    for r in roles:
        pdf.cell(25,6,r.split()[0],1)
    pdf.ln()
    for p in phases:
        pdf.cell(35,6,p,1)
        for r in roles:
            pdf.cell(25,6,str(hours_data[p][r]),1)
        pdf.ln()

    pdf.ln(3)
    pdf.set_font("Arial","B",12)
    pdf.cell(0,8,"Fee Summary",ln=True)
    pdf.set_font("Arial","",10)
    for _,row in df_summary.iterrows():
        pdf.cell(60,6,f"{row['Metric']}:",0)
        pdf.cell(40,6,f"${row['Amount ($)']:,.2f}",ln=True)

    pdf.ln(3)
    pdf.set_font("Arial","B",12)
    pdf.cell(0,8,"Consultant Fees",ln=True)
    pdf.set_font("Arial","",10)
    for k,v in consultant_fees.items():
        pdf.cell(70,6,f"{k}:",0)
        pdf.cell(40,6,f"${v:,.2f}",ln=True)

    pdf.add_page()
    pdf.set_font("Arial","B",12)
    pdf.cell(0,8,"Project Schedule",ln=True)
    pdf.set_font("Arial","",9)
    pdf.cell(60,6,"Phase",1)
    pdf.cell(35,6,"Start",1)
    pdf.cell(35,6,"End",1)
    pdf.cell(25,6,"Days",1)
    pdf.ln()
    for _,row in df_schedule.iterrows():
        pdf.cell(60,6,row["Phase"],1)
        pdf.cell(35,6,row["Start"].strftime("%Y-%m-%d"),1)
        pdf.cell(35,6,row["End"].strftime("%Y-%m-%d"),1)
        pdf.cell(25,6,str(row["Duration (days)"]),1)
        pdf.ln()

    pdf.set_y(-15)
    pdf.set_font("Arial","I",8)
    pdf.cell(0,8,"aperioddesign.com",0,0,"C")
    return BytesIO(pdf.output(dest="S").encode("latin1"))

pdf_bytes = build_pdf()
st.download_button("📄 Download Branded PDF", data=pdf_bytes,
                   file_name="aperioddesign_fee_report.pdf",
                   mime="application/pdf")

# timeline
st.header("6. Schedule Timeline")
fig = px.timeline(df_schedule, x_start="Start", x_end="End", y="Phase")
fig.update_yaxes(autorange="reversed")
st.plotly_chart(fig, use_container_width=True)
