
import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
import plotly.express as px
from fpdf import FPDF

st.set_page_config(layout="wide")
st.title("🏗️ Architect Fee Calculator with Schedule, Consultants & PDF Export")

# --- Project Info ---
st.header("1. Project Info")
construction_cost = st.number_input("Estimated Construction Cost ($)", min_value=0, value=1_000_000)
base_fee_percent = st.number_input("Base Fee % of Construction Cost", min_value=0.0, value=0.08)
complexity_factor = st.number_input("Complexity Factor", min_value=0.5, value=1.1)
location_factor = st.number_input("Location Factor", min_value=0.5, value=1.0)
risk_factor = st.number_input("Risk Factor", min_value=0.5, value=1.05)
firm_multiplier = st.number_input("Firm Multiplier (Overhead + Profit)", min_value=1.0, value=3.0)

# --- Hourly Rates ---
st.header("2. Hourly Rates ($)")
roles = ["Principal", "Project Manager", "Architect", "Drafter"]
rates = {role: st.number_input(f"{role}", value=rate) for role, rate in zip(roles, [200, 150, 100, 75])}

# --- Hours per Phase ---
st.header("3. Estimated Hours per Phase")
phases = ['Pre-Design', 'Schematic Design', 'Design Development',
          'Construction Documents', 'Bidding/Negotiation', 'Construction Administration']
hours_data = {}
for phase in phases:
    with st.expander(phase, expanded=False):
        hours_data[phase] = {role: st.number_input(f"{phase} - {role}", min_value=0, value=10) for role in roles}

# --- Consultant Fees ---
st.header("4. Consultants")
st.markdown("*(as a % of construction cost)*")
consultants = {
    "Structural Engineer": st.number_input("Structural Engineer (%)", value=1.5),
    "MEP Engineer": st.number_input("MEP Engineer (%)", value=2.0),
    "Civil Engineer": st.number_input("Civil Engineer (%)", value=1.0),
    "Landscape Architect": st.number_input("Landscape Architect (%)", value=0.5),
}
consultant_fees = {k: construction_cost * (v / 100) for k, v in consultants.items()}

# --- Schedule Tracking ---
st.header("5. Schedule Tracker")
schedule_data = []
for phase in phases:
    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input(f"{phase} Start", value=date.today(), key=f"{phase}_start")
    with col2:
        end = st.date_input(f"{phase} End", value=date.today(), key=f"{phase}_end")
    duration = (end - start).days
    schedule_data.append({"Phase": phase, "Start": start, "End": end, "Duration (days)": duration})

df_schedule = pd.DataFrame(schedule_data)

# --- Fee Calculations ---
total_raw_labor_cost = sum(hours_data[phase][role] * rates[role] for phase in phases for role in roles)
workplan_fee = total_raw_labor_cost * firm_multiplier
adjusted_fee_percent = base_fee_percent * complexity_factor * location_factor * risk_factor
construction_fee = construction_cost * adjusted_fee_percent

# --- Fee Summary ---
st.header("6. Fee Summary")
st.write(f"**Total Raw Labor Cost:** ${total_raw_labor_cost:,.2f}")
st.write(f"**Workplan Method Fee:** ${workplan_fee:,.2f}")
st.write(f"**Construction Cost % Method Fee:** ${construction_fee:,.2f}")
st.write("### Consultant Cost Estimates")
for k, v in consultant_fees.items():
    st.write(f"{k}: ${v:,.2f}")

# --- Gantt-style Chart ---
st.subheader("📊 Project Schedule Timeline")
fig = px.timeline(df_schedule, x_start="Start", x_end="End", y="Phase")
fig.update_yaxes(autorange="reversed")
st.plotly_chart(fig, use_container_width=True)

# --- Download CSVs ---
st.header("7. Download Reports")

summary_data = {
    "Workplan Method Fee": [workplan_fee],
    "Construction % Method Fee": [construction_fee],
    "Total Labor Cost": [total_raw_labor_cost],
}
summary_data.update({f"{k} (Consultant)": [v] for k, v in consultant_fees.items()})
df_summary = pd.DataFrame(summary_data)

def convert_df_to_csv(df):
    return df.to_csv(index=False).encode("utf-8")

st.download_button(
    "📥 Download Fee Summary (CSV)",
    data=convert_df_to_csv(df_summary),
    file_name='architect_fee_summary.csv',
    mime='text/csv',
)

st.download_button(
    "📥 Download Project Schedule (CSV)",
    data=convert_df_to_csv(df_schedule),
    file_name='project_schedule.csv',
    mime='text/csv',
)

# --- PDF Report Generator ---
st.subheader("🧾 Export Fee Report as PDF")
def create_pdf(summary_df, schedule_df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, "Architect Fee Summary Report", ln=True, align="C")

    pdf.set_font("Arial", "", 10)
    pdf.ln(5)
    for col in summary_df.columns:
        pdf.cell(60, 8, f"{col}:", 0)
        pdf.cell(60, 8, f"${summary_df[col][0]:,.2f}", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(200, 10, "Project Schedule", ln=True)

    pdf.set_font("Arial", "", 9)
    for _, row in schedule_df.iterrows():
        pdf.cell(60, 7, f"{row['Phase']}", 0)
        pdf.cell(60, 7, f"{row['Start']} to {row['End']}", 0)
        pdf.cell(40, 7, f"{row['Duration (days)']} days", ln=True)
    
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    return pdf_output

pdf_bytes = create_pdf(df_summary, df_schedule)

st.download_button(
    label="📄 Download PDF Report",
    data=pdf_bytes,
    file_name="architect_fee_report.pdf",
    mime="application/pdf",
)
