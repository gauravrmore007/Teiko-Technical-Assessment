import streamlit as st
import plotly.express as px
import os
import subprocess

# Auto-create DB (for cloud deployment)
if not os.path.exists("cell_counts.db"):
    subprocess.run(["python", "load_data.py"], check=True)
from analysis import (
    get_frequency_table,
    get_responder_analysis,
    run_statistics,
    get_baseline_melanoma_miraclib
)

st.set_page_config(page_title="Immune Cell Population Dashboard", layout="wide")
st.title("Immune Cell Population Dashboard")

# Part 2: Initial Analysis
st.header("Summary Table: Cell Population Frequencies by Sample")
freq_df = get_frequency_table()

st.dataframe(freq_df, use_container_width=True)

fig2 = px.bar(
    freq_df.sort_values('sample'),
    x='sample',
    y='percentage',
    color='population',
    barmode='stack',
    title='Relative Cell Population Frequency per Sample (%)',
    labels={'percentage': 'Frequency (%)', 'sample': 'Sample ID'},
    range_y=[0, 100]
)
fig2.update_xaxes(
    showticklabels=False,
    title=dict(text="Samples (n=10,500)", standoff=10)  
)
fig2.update_layout(
    yaxis_title="Frequency (%)",
    margin=dict(b=60)  
)
st.plotly_chart(fig2, use_container_width=True)

#Part 3: Statistical Analysis
st.header("Responders vs Non-Responders (Melanoma + Miraclib PBMC)")
resp_df = get_responder_analysis()

fig3 = px.box(
    resp_df, x='population', y='percentage', color='response',
    title='Cell Population Frequencies: Responders vs Non-Responders',
    labels={'percentage': 'Relative Frequency (%)', 'population': 'Cell Population'},
    color_discrete_map={'yes': '#2ecc71', 'no': '#e74c3c'}
)
st.plotly_chart(fig3, use_container_width=True)

stats_df = run_statistics(resp_df)
st.subheader("Statistical Results (Mann-Whitney U Test)")
st.dataframe(stats_df, use_container_width=True)

sig = stats_df[stats_df['significant'] == 'Yes']['population'].tolist()
if sig:
    st.success(f"Significant populations (p < 0.05): {', '.join(sig)}")
else:
    st.info("No populations showed statistically significant differences (p < 0.05).")

#Part 4: Data Subset Analysis
st.header("Baseline Melanoma Miraclib PBMC - Subset Analysis")
results = get_baseline_melanoma_miraclib()

col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("Samples per Project")
    st.dataframe(results['samples_per_project'], use_container_width=True)
with col2:
    st.subheader("Responders/Non-Responders")
    st.dataframe(results['response_counts'], use_container_width=True)
with col3:
    st.subheader("Males/Females")
    st.dataframe(results['gender_counts'], use_container_width=True)

st.metric(
    label="Avg B Cells — Melanoma Male Responders at Baseline (t=0)",
    value=f"{results['avg_bcell_male_responders']:.2f}"
)