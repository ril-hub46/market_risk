from datetime import date
from io import BytesIO

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from web.api_client import (
    compute_historical_var,
    compute_options_var,
    compute_stocks_var,
)


def _preview(uploaded_file):
    """Aperçu brut (non nettoyé) d'un fichier Excel uploadé, pour affichage seulement."""
    try:
        return pd.read_excel(uploaded_file)
    except Exception:
        return None


def run_dashboard():
    st.set_page_config(page_title="Assets Pricing and VaR", page_icon="📊", layout="wide")

    if "options_file" not in st.session_state:
        st.session_state.options_file = None
    if "stocks_file" not in st.session_state:
        st.session_state.stocks_file = None
    if "funds_file" not in st.session_state:
        st.session_state.funds_file = None
    if "qty_file" not in st.session_state:
        st.session_state.qty_file = None
    if "curve_files" not in st.session_state:
        st.session_state.curve_files = {}
    if "last_calc_type" not in st.session_state:
        st.session_state.last_calc_type = None
    if "last_var_results" not in st.session_state:
        st.session_state.last_var_results = None

    st.title("Assets Pricing and Monte Carlo VaR")

    st.sidebar.header("Parameters")

    pricing_date = st.sidebar.date_input("Valuation Date", value=date(2024, 12, 31))

    n_simulations = st.sidebar.number_input(
        "Number of Simulations", min_value=100, max_value=100000, value=1000, step=100
    )

    confidence_level = st.sidebar.slider(
        "Confidence Level (%)", min_value=90.0, max_value=99.9, value=99.0, step=0.1
    )

    nb_returns = st.sidebar.number_input(
        "Number of Returns", min_value=50, max_value=5000, value=500, step=50
    )

    tab1, tab2, tab3, tab4 = st.tabs(["Import Data", "Yield Curves", "VaR Computation", "Export"])

    with tab1:
        st.header("Import Portofolio Data")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Options")
            uploaded_options = st.file_uploader(
                "Import options file", type=["xlsx", "xls"], key="options"
            )

            if uploaded_options:
                st.session_state.options_file = uploaded_options
                st.success("✅ Options imported successfully!")
                with st.expander("Data Preview"):
                    st.dataframe(_preview(uploaded_options), use_container_width=True)

            st.subheader("Stocks")
            uploaded_stocks = st.file_uploader(
                "Import stock portfolio", type=["xlsx", "xls"], key="stocks"
            )

            if uploaded_stocks:
                st.session_state.stocks_file = uploaded_stocks
                st.session_state.last_calc_type = "stocks"
                st.success("✅ Stocks imported successfully!")
                with st.expander("Data Preview"):
                    st.dataframe(_preview(uploaded_stocks), use_container_width=True)

        with col2:
            st.subheader("OPCVM")
            uploaded_funds = st.file_uploader(
                "Import OPCVM portfolio", type=["xlsx", "xls"], key="funds"
            )

            if uploaded_funds:
                st.session_state.funds_file = uploaded_funds
                st.session_state.last_calc_type = "funds"
                st.success("✅ OPCVM imported successfully!")
                with st.expander("Data Preview"):
                    st.dataframe(_preview(uploaded_funds), use_container_width=True)

            st.subheader("Quantities")
            uploaded_qty = st.file_uploader(
                "Import quantities", type=["xlsx", "xls"], key="quantities"
            )

            if uploaded_qty:
                st.session_state.qty_file = uploaded_qty
                st.success("✅ Quantities imported successfully!")
                with st.expander("Data Preview"):
                    st.dataframe(_preview(uploaded_qty), use_container_width=True)

    with tab2:
        st.header("Interest Rate Curves")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("USD")
            uploaded_usd = st.file_uploader(
                "Import USD curve", type=["xlsx", "xls"], key="usd_curve"
            )

            if uploaded_usd:
                st.session_state.curve_files["USD"] = uploaded_usd
                st.success("✅ USD curve imported!")
                with st.expander("Preview"):
                    st.dataframe(_preview(uploaded_usd), use_container_width=True)

        with col2:
            st.subheader("EUR")
            uploaded_eur = st.file_uploader(
                "Import EUR curve", type=["xlsx", "xls"], key="eur_curve"
            )

            if uploaded_eur:
                st.session_state.curve_files["EUR"] = uploaded_eur
                st.success("✅ EUR curve imported!")
                with st.expander("Preview"):
                    st.dataframe(_preview(uploaded_eur), use_container_width=True)

        with col3:
            st.subheader("MAD")
            uploaded_mad = st.file_uploader(
                "Import MAD curve", type=["xlsx", "xls"], key="mad_curve"
            )

            if uploaded_mad:
                st.session_state.curve_files["MAD"] = uploaded_mad
                st.success("✅ MAD curve imported!")
                with st.expander("Preview"):
                    st.dataframe(_preview(uploaded_mad), use_container_width=True)

    with tab3:
        st.header("Value at Risk Computation")

        calc_type = st.radio(
            "Calculation Type",
            ["Options VaR", "Stocks VaR", "Historical VaR"],
            horizontal=True,
        )

        if calc_type == "Options VaR":
            st.subheader(" Monte Carlo VaR for Options")

            if st.button(" Run Calculation", type="primary", use_container_width=True):
                if st.session_state.options_file is None:
                    st.error("⚠️ Please import an options file first")
                elif not {"USD", "EUR", "MAD"} <= st.session_state.curve_files.keys():
                    st.error("⚠️ Please import USD, EUR and MAD yield curves first")
                else:
                    try:
                        with st.spinner("Computing..."):
                            result = compute_options_var(
                                st.session_state.options_file,
                                st.session_state.curve_files["USD"],
                                st.session_state.curve_files["EUR"],
                                st.session_state.curve_files["MAD"],
                                pricing_date,
                                confidence_level,
                                n_simulations,
                            )
                            var_value = result["var_value"]
                            pnl_total = result["pnl_total"]

                            st.session_state.last_calc_type = "options"
                            st.session_state.last_var_results = result

                            st.success("Calculation completed!")
                            col1, col2 = st.columns([1, 2])

                            with col1:
                                st.metric(
                                    label=f"VaR {int(confidence_level)}%",
                                    value=f"{abs(var_value):,.2f} MAD",
                                )

                                st.dataframe(
                                    pd.DataFrame(
                                        {
                                            "Scenario": range(1, min(31, len(pnl_total) + 1)),
                                            "P&L (MAD)": pnl_total[:30],
                                        }
                                    ),
                                    use_container_width=True,
                                    height=400,
                                )

                            with col2:
                                fig = go.Figure()

                                fig.add_trace(
                                    go.Histogram(
                                        x=pnl_total,
                                        nbinsx=40,
                                        name="P&L Distribution",
                                        marker_color="skyblue",
                                        marker_line_color="black",
                                        marker_line_width=1,
                                    )
                                )

                                fig.add_vline(
                                    x=-var_value,
                                    line_dash="dash",
                                    line_color="red",
                                    line_width=2,
                                    annotation_text=f"VaR {int(confidence_level)}%",
                                    annotation_position="top",
                                )

                                fig.update_layout(
                                    title="Simulated P&L Distribution",
                                    xaxis_title="P&L (MAD)",
                                    yaxis_title="Frequency",
                                    showlegend=True,
                                    template="plotly_white",
                                    height=500,
                                )

                                st.plotly_chart(fig, use_container_width=True)

                    except Exception as e:
                        st.error(f"Calculation error: {e}")

        elif calc_type == "Stocks VaR":
            st.subheader(" Stocks VaR - Monte Carlo & Cornish-Fisher")

            if st.button(" Run Calculation", type="primary", use_container_width=True):
                if st.session_state.stocks_file is None:
                    st.error(" Please import a stock portfolio first")
                else:
                    try:
                        with st.spinner("Computing..."):
                            result = compute_stocks_var(
                                st.session_state.stocks_file,
                                confidence_level,
                                n_simulations,
                            )
                            var_cf = result["var_cf"]
                            var_gbm = result["var_gbm"]
                            real_returns = result["real_returns"]
                            sim_porto = result["sim_porto"]

                            st.session_state.last_calc_type = "stocks"
                            st.session_state.last_var_results = result

                            st.success("Calculation completed!")

                            col1, col2 = st.columns(2)
                            col1.metric("VaR Cornish-Fisher", f"{var_cf * 100:.2f}%")
                            col2.metric("VaR GBM", f"{var_gbm * 100:.2f}%")

                            fig = make_subplots(
                                rows=1,
                                cols=2,
                                subplot_titles=("Actual Returns", "Simulated Returns"),
                            )

                            fig.add_trace(
                                go.Histogram(
                                    x=real_returns,
                                    nbinsx=30,
                                    name="Actual",
                                    marker_color="steelblue",
                                    marker_line_color="black",
                                    marker_line_width=1,
                                    showlegend=False,
                                ),
                                row=1,
                                col=1,
                            )

                            fig.add_vline(
                                x=-var_cf,
                                line_dash="dash",
                                line_color="red",
                                line_width=2,
                                annotation_text=f"VaR CF ({var_cf * 100:.2f}%)",
                                annotation_position="top left",
                                row=1,
                                col=1,
                            )

                            fig.add_trace(
                                go.Histogram(
                                    x=sim_porto,
                                    nbinsx=30,
                                    name="Simulated",
                                    marker_color="darkorange",
                                    marker_line_color="black",
                                    marker_line_width=1,
                                    showlegend=False,
                                ),
                                row=1,
                                col=2,
                            )

                            fig.add_vline(
                                x=-var_gbm,
                                line_dash="dash",
                                line_color="red",
                                line_width=2,
                                annotation_text=f"VaR GBM ({var_gbm * 100:.2f}%)",
                                annotation_position="top left",
                                row=1,
                                col=2,
                            )

                            fig.update_xaxes(title_text="Return", row=1, col=1)
                            fig.update_xaxes(title_text="Return", row=1, col=2)
                            fig.update_yaxes(title_text="Frequency", row=1, col=1)
                            fig.update_yaxes(title_text="Frequency", row=1, col=2)

                            fig.update_layout(height=500, showlegend=False, template="plotly_white")

                            st.plotly_chart(fig, use_container_width=True)

                    except Exception as e:
                        st.error(f"Calculation error: {e}")

        else:
            st.subheader("Historical VaR")

            if st.button("Run Calculation", type="primary", use_container_width=True):
                if st.session_state.qty_file is None:
                    st.warning(" Please import quantities")
                elif st.session_state.last_calc_type not in ["funds", "stocks"]:
                    st.error("Please import a portfolio first (Mutual Funds or Stocks)")
                else:
                    try:
                        with st.spinner("Computing..."):
                            portfolio_file = (
                                st.session_state.funds_file
                                if st.session_state.last_calc_type == "funds"
                                else st.session_state.stocks_file
                            )

                            result = compute_historical_var(
                                portfolio_file,
                                st.session_state.qty_file,
                                confidence_level,
                                nb_returns,
                            )
                            var = result["var_histo"]
                            dates = result["dates"]
                            pnl = result["pnl"]

                            st.session_state.last_var_results = result

                            st.success("Calculation completed!")

                            st.metric(
                                f"Historical VaR {int(confidence_level)}%",
                                f"{var:,.4f} MAD",
                            )

                            fig = go.Figure()

                            fig.add_trace(
                                go.Scatter(
                                    x=dates,
                                    y=pnl,
                                    mode="lines",
                                    name="Weighted P&L",
                                    line=dict(color="steelblue", width=2),
                                )
                            )

                            fig.add_hline(
                                y=-var,
                                line_dash="dash",
                                line_color="red",
                                line_width=2,
                                annotation_text=f"VaR {int(confidence_level)}% = {var:} MAD",
                                annotation_position="right",
                            )

                            fig.update_layout(
                                title="P&L Distribution and Historical VaR",
                                xaxis_title="Date",
                                yaxis_title="P&L (MAD)",
                                template="plotly_white",
                                height=500,
                                showlegend=True,
                            )

                            st.plotly_chart(fig, use_container_width=True)

                    except Exception as e:
                        st.error(f"Calculation error: {e}")

    with tab4:
        st.header("Export Results")

        if st.session_state.last_var_results is None:
            st.info("No results to export. Please run a calculation first.")
        else:
            st.success("Results available for export")

            if st.button("Download Results", type="primary", use_container_width=True):
                try:
                    output = BytesIO()

                    with pd.ExcelWriter(output, engine="openpyxl") as writer:
                        if st.session_state.last_calc_type == "options":
                            pd.DataFrame(
                                {"VaR": [st.session_state.last_var_results["var_value"]]}
                            ).to_excel(writer, index=False, sheet_name="Summary")

                            pd.DataFrame(
                                {
                                    "Scenario": range(
                                        1,
                                        len(st.session_state.last_var_results["pnl_total"]) + 1,
                                    ),
                                    "Simulated P&L": st.session_state.last_var_results["pnl_total"],
                                }
                            ).to_excel(writer, index=False, sheet_name="Simulated P&L")

                        elif st.session_state.last_calc_type == "stocks":
                            pd.DataFrame(
                                {
                                    "VaR Cornish-Fisher": [
                                        st.session_state.last_var_results["var_cf"]
                                    ],
                                    "VaR GBM": [st.session_state.last_var_results["var_gbm"]],
                                }
                            ).to_excel(writer, index=False, sheet_name="Summary")

                            pd.DataFrame(
                                {
                                    "Date": st.session_state.last_var_results["real_returns_dates"],
                                    "Actual Returns": st.session_state.last_var_results[
                                        "real_returns"
                                    ],
                                }
                            ).to_excel(writer, index=False, sheet_name="Actual Returns")

                            pd.DataFrame(
                                {
                                    "Simulated Returns GBM": st.session_state.last_var_results[
                                        "sim_porto"
                                    ]
                                }
                            ).to_excel(writer, index=True, sheet_name="Simulated Returns")

                        else:  # funds
                            pd.DataFrame(
                                {"Historical VaR": [st.session_state.last_var_results["var_histo"]]}
                            ).to_excel(writer, index=False, sheet_name="Summary")

                            pd.DataFrame(
                                {
                                    "Date": st.session_state.last_var_results["dates"],
                                    "P&L": st.session_state.last_var_results["pnl"],
                                }
                            ).to_excel(writer, index=False, sheet_name="Historical P&L")

                    output.seek(0)

                    st.download_button(
                        label="Download Excel",
                        data=output,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

                except Exception as e:
                    st.error(f"Export error: {e}")

    st.markdown("---")
    st.markdown(
        "<div style='text-align: center;'>VaR Calculator - Streamlit Version</div>",
        unsafe_allow_html=True,
    )
