import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import date


from src.VaR.model import compute_var, CF_var, GBM, compute_historical_var

st.set_page_config(
    page_title="FX Option Pricer & VaR Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🛡️ Financial Risk Management Dashboard")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ Global Settings")
    pricing_date = st.date_input("Valuation Date", date(2024, 12, 31))
    
    st.subheader("Model Parameters")
    n_sims = st.number_input("Monte Carlo Simulations", min_value=100, max_value=100000, value=1000)
    conf_level = st.slider("Confidence Level (%)", 90.0, 99.9, 99.0, step=0.5) / 100
    n_returns = st.number_input("Number of Historical Returns", value=500)
    
    st.info("These settings apply to all calculation engines below.")

col_files, col_results = st.columns([1, 2])

with col_files:
    st.subheader("📥 Data Intake")
    opt_file = st.file_uploader("Options Portfolio", type=["xlsx"])
    asset_file = st.file_uploader("Stock/Assets Portfolio", type=["xlsx"])
    opcvm_file = st.file_uploader("OPCVM Portfolio", type=["xlsx"])
    
    st.divider()
    st.subheader("💱 Yield Curves")
    curves = {
        "USD": st.file_uploader("USD Curve", type=["xlsx"]),
        "EUR": st.file_uploader("EUR Curve", type=["xlsx"]),
        "MAD": st.file_uploader("MAD Curve", type=["xlsx"])
    }

with col_results:
    tab_data, tab_calc, tab_viz = st.tabs(["Data Preview", "VaR Engines", "Risk Visualization"])

    with tab_data:
        if opt_file:
            st.write("**Options Portfolio Preview:**")
            df_opt = pd.read_excel(opt_file)
            st.dataframe(df_opt, use_container_width=True)
        else:
            st.warning("Please upload a file to see the preview.")

    with tab_calc:
        st.write("### Compute Value at Risk")
        
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        
        if btn_col1.button("Run Options MC VaR"):
            if opt_file and curves["MAD"]:
                with st.spinner("Simulating Scenarios..."):
                    var_val, pnl_total = compute_var(df_opt, pricing_date, conf_level, n_sims, curves)
                    st.session_state['last_var'] = (var_val, pnl_total)
                    st.success(f"Options VaR: {var_val:,.2f} MAD")
            else:
                st.error("Missing Options file or MAD Yield Curve.")

        if btn_col2.button("Run MC & CF VaR"):
            st.info("Calculating Cornish-Fisher and GBM VaR...")

        if btn_col3.button("Run Historical VaR"):
            st.info("Calculating Historical Scenarios...")

    with tab_viz:
        if 'last_var' in st.session_state:
            var_val, pnl_total = st.session_state['last_var']
            
            fig = px.histogram(
                pnl_total, 
                nbins=50, 
                title="Simulated P&L Distribution",
                labels={'value': 'P&L (MAD)'},
                color_discrete_sequence=['#3366CC']
            )
            
            fig.add_vline(
                x=-var_val, 
                line_dash="dash", 
                line_color="red",
                annotation_text=f"VaR {conf_level*100:.1f}%",
                annotation_position="top left"
            )
            
            fig.update_layout(template="plotly_white", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
            st.download_button(
                label="💾 Export Results to CSV",
                data=pd.DataFrame(pnl_total).to_csv(),
                file_name="var_results.csv",
                mime="text/csv"
            )
        else:
            st.info("No results to visualize. Run a calculation first.")