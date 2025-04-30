
import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from pathlib import Path
import plotly.express as px
from fpdf import FPDF
from PIL import Image

# -------------------------------------------------
# CONFIG & LOGO
# -------------------------------------------------
st.set_page_config(page_title="Architect Fee Tool – aperioddesign",
                   page_icon="🅰️", layout="wide")

LOGO_PATH = Path(__file__).with_name("logo.png")
if LOGO_PATH.exists():
    st.image(Image.open(LOGO_PATH), width=140)

st.title("🏗️ Architect Fee Calculator | aperioddesign.com")

# -------------------------------------------------
# 1. Project Info
# -------------------------------------------------
st.header("1 · Project Info")
construction_cost = st.number_input("Estimated Construction Cost ($)",
                                    min_value=0.0, value=1_000_000.0, step=10000.0, format="%.0f")
base_fee_percent = st.number_input("Base Fee % of Construction Cost",
                                   min_value=0.0, max_value=1.0, value=0.08, step=0.01, format="%.2f")
complexity_factor = st.number_input("Complexity Factor", min_value=0.5, value=1.10, step=0.05)
location_factor   = st.number_input("Location Factor",   min_value=0.5, value=1.00, step=0.05)
risk_factor       = st.number_input("Risk Factor",       min_value=0.5, value=1.05, step=0.05)
firm_multiplier   = st.number_input("Firm Multiplier (OH + Profit)", min_value=1.0, value=3.0, step=0.1)

# -------------------------------------------------
# 2. Hourly Rates
# -------------------------------------------------
st.header("2 · Hourly Rates ($)")
roles = ["Principal", "Project Manager", "Architect", "Drafter"]
role_defaults = [200, 150, 100, 75]
rates = {r: st.number_input(r, value=d, step=10) for r, d in zip(roles, role_defaults)}

# -------------------------------------------------
# 3. Hours per Phase
# -------------------------------------------------
st.header("3 · Estimated Hours per Phase")
phases = ['Pre-Design', 'Schematic Design', 'Design Development',
          'Construction Documents', 'Bidding/Negotiation', 'Construction Administration']
hours_data = {}
for p in phases:
    with st.expander(p, expanded=False):
        hours_data[p] = {r: st.number_input(f"{p} – {r}", min_value=0, value=10, step=1) for r in roles}

# -------------------------------------------------
# 4. Consultant Percentages
# -------------------------------------------------
st.header("4 · Consultant Percentages")
consultant_pct = {
    "Structural Engineer": st.number_input("Structural Engineer (%)", value=1.5, step=0.1),
    "MEP Engineer":        st.number_input("MEP Engineer (%)",        value=2.0, step=0.1),
    "Civil Engineer":      st.number_input("Civil Engineer (%)",      value=1.0, step=0.1),
    "Landscape Architect": st.number_input("Landscape Architect (%)", value=0.5, step=0.1),
}
consultant_fees = {k: construction_cost * v / 100 for k, v in consultant_pct.items()}

# -------------------------------------------------
# 5. Schedule Tracker
# -------------------------------------------------
st.header("5 · Schedule Tracker")
schedule_rows = []
for p in phases:
    col1, col2 = st.columns(2)
    start = col1.date_input(f"{p} Start", value=date.today(), key=f"{p}_start")
    end   = col2.date_input(f"{p} End",   value=date.today(), key=f"{p}_end")
    schedule_rows.append({"Phase": p, "Start": start, "End": end, "Duration (days)": (end - start).days})
df_schedule = pd.DataFrame(schedule_rows)

# -------------------------------------------------
# Fee Calculations
# -------------------------------------------------
total_raw = sum(hours_data[p][r] * rates[r] for p in phases for r in roles)
workplan_fee = total_raw * firm_multiplier
adjusted_pct = base_fee_percent * complexity_factor * location_factor * risk_factor
percentage_fee = construction_cost * adjusted_pct

df_summary = pd.DataFrame({
    "Metric": ["Total Raw Labor", "Workplan Fee", "%‑of‑Cost Fee"],
    "Amount ($)": [total_raw, workplan_fee, percentage_fee]
})

df_consultants = pd.DataFrame(list(consultant_fees.items()), columns=["Consultant", "Fee ($)"])

# -------------------------------------------------
# 6. On‑screen Summary
# -------------------------------------------------
st.header("6 · Fee Summary")
st.dataframe(df_summary.style.format({"Amount ($)": "${:,.2f}"}), use_container_width=True)

with st.expander("Consultant Fee Breakdown", expanded=False):
    st.dataframe(df_consultants.style.format({"Fee ($)": "${:,.2f}"}), use_container_width=True)

# -------------------------------------------------
# 7. CSV Downloads
# -------------------------------------------------
st.header("7 · Download Data (CSV)")
csv_summary = df_summary.to_csv(index=False).encode("utf-8")
csv_schedule = df_schedule.to_csv(index=False).encode("utf-8")
st.download_button("📥 Fee Summary CSV", data=csv_summary,
                   file_name="fee_summary.csv", mime="text/csv")
st.download_button("📥 Schedule CSV", data=csv_schedule,
                   file_name="project_schedule.csv", mime="text/csv")

# -------------------------------------------------
# 8. PDF Report
# -------------------------------------------------
def build_pdf() -> BytesIO:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Logo
    if LOGO_PATH.exists():
        try:
            pdf.image(str(LOGO_PATH), x=10, y=8, w=40)
        except RuntimeError:
            pass
    pdf.ln(22)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Architect Fee Calculator Report", ln=True, align="C")
    pdf.ln(2)

    # Project info
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Project Information", ln=True)
    pdf.set_font("Arial", "", 10)
    for label, val in [
        ("Construction Cost", f"${construction_cost:,.0f}"),
        ("Base Fee %", f"{base_fee_percent*100:.2f}%"),
        ("Complexity Factor", complexity_factor),
        ("Location Factor", location_factor),
        ("Risk Factor", risk_factor),
        ("Firm Multiplier", firm_multiplier),
    ]:
        pdf.cell(60, 6, f"{label}:", 0)
        pdf.cell(40, 6, str(val), ln=True)

    # Rates
    pdf.ln(3)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Hourly Rates", ln=True)
    pdf.set_font("Arial", "", 10)
    for r in roles:
        pdf.cell(60, 6, f"{r}:", 0)
        pdf.cell(40, 6, f"${rates[r]:,.2f}", ln=True)

    # Hours table
    pdf.ln(3)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Hours per Phase", ln=True)
    pdf.set_font("Arial", "", 8)
    pdf.cell(35, 6, "Phase", 1)
    for r in roles:
        pdf.cell(25, 6, r.split()[0], 1)
    pdf.ln()
    for p in phases:
        pdf.cell(35, 6, p, 1)
        for r in roles:
            pdf.cell(25, 6, str(hours_data[p][r]), 1)
        pdf.ln()

    # Fee summary
    pdf.ln(3)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Fee Summary", ln=True)
    pdf.set_font("Arial", "", 10)
    for _, row in df_summary.iterrows():
        pdf.cell(60, 6, f"{row['Metric']}:", 0)
        pdf.cell(40, 6, f"${row['Amount ($)']:,.2f}", ln=True)

    # Consultant fees
    pdf.ln(3)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Consultant Fees", ln=True)
    pdf.set_font("Arial", "", 10)
    for _, row in df_consultants.iterrows():
        pdf.cell(70, 6, f"{row['Consultant']}:", 0)
        pdf.cell(40, 6, f"${row['Fee ($)']:,.2f}", ln=True)

    # Schedule page
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Project Schedule", ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.cell(60, 6, "Phase", 1)
    pdf.cell(35, 6, "Start", 1)
    pdf.cell(35, 6, "End", 1)
    pdf.cell(25, 6, "Days", 1)
    pdf.ln()
    for _, row in df_schedule.iterrows():
        pdf.cell(60, 6, row["Phase"], 1)
        pdf.cell(35, 6, row["Start"].strftime("%Y-%m-%d"), 1)
        pdf.cell(35, 6, row["End"].strftime("%Y-%m-%d"), 1)
        pdf.cell(25, 6, str(row["Duration (days)"]), 1)
        pdf.ln()

    # Footer
    pdf.set_y(-15)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 8, "aperioddesign.com", 0, 0, "C")

    return BytesIO(pdf.output(dest="S").encode("latin1"))

st.header("8 · Download Branded PDF")
st.download_button("📄 Download PDF Report",
                   data=build_pdf(),
                   file_name="aperioddesign_fee_report.pdf",
                   mime="application/pdf")

# -------------------------------------------------
# 9. Timeline
# -------------------------------------------------
st.header("9 · Schedule Timeline")
fig = px.timeline(df_schedule, x_start="Start", x_end="End", y="Phase")
fig.update_yaxes(autorange="reversed")
st.plotly_chart(fig, use_container_width=True)
