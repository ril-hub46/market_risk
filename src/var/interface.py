from datetime import date
from io import BytesIO

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from var.model import (
    GBM,
    CF_var,
    compute_historical_var,
    compute_var,
)


def run_dashboard():
    st.set_page_config(
        page_title="Assets Pricing and VaR", page_icon="📊", layout="wide"
    )

    if "df_options" not in st.session_state:
        st.session_state.df_options = None
    if "df_stocks" not in st.session_state:
        st.session_state.df_stocks = None
    if "df_funds" not in st.session_state:
        st.session_state.df_funds = None
    if "df_qty" not in st.session_state:
        st.session_state.df_qty = None
    if "curve_map" not in st.session_state:
        st.session_state.curve_map = {}
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

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Import Data", "Yield Curves", "VaR Computation", "Export"]
    )

    with tab1:
        st.header("Import Portofolio Data")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Options")
            uploaded_options = st.file_uploader(
                "Import options file", type=["xlsx", "xls"], key="options"
            )

            if uploaded_options:
                try:
                    st.session_state.df_options = pd.read_excel(uploaded_options)
                    st.success("✅ Options imported successfully!")
                    with st.expander("Data Preview"):
                        st.dataframe(
                            st.session_state.df_options, use_container_width=True
                        )
                except Exception as e:
                    st.error(f"Import error: {e}")

            st.subheader("Stocks")
            uploaded_stocks = st.file_uploader(
                "Import stock portfolio", type=["xlsx", "xls"], key="stocks"
            )

            if uploaded_stocks:
                try:
                    df = pd.read_excel(uploaded_stocks)
                    df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors="coerce")
                    df = df.dropna(subset=[df.columns[0]])
                    df = df.sort_values(by=df.columns[0])
                    df = df.set_index(df.columns[0])
                    df = df.apply(pd.to_numeric, errors="coerce")

                    st.session_state.df_stocks = df
                    st.session_state.last_calc_type = "stocks"
                    st.success("✅ Stocks imported successfully!")
                    with st.expander("Data Preview"):
                        st.dataframe(df, use_container_width=True)
                except Exception as e:
                    st.error(f"Import error: {e}")

        with col2:
            st.subheader("OPCVM")
            uploaded_funds = st.file_uploader(
                "Import OPCVM portfolio", type=["xlsx", "xls"], key="funds"
            )

            if uploaded_funds:
                try:
                    df = pd.read_excel(uploaded_funds)
                    df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors="coerce")
                    df = df.dropna(subset=[df.columns[0]])
                    df = df.sort_values(by=df.columns[0], ascending=False)
                    df.set_index(df.columns[0], inplace=True)
                    df = df.apply(pd.to_numeric, errors="coerce")

                    st.session_state.df_funds = df
                    st.session_state.last_calc_type = "funds"
                    st.success("✅ OPCVM imported successfully!")
                    with st.expander("Data Preview"):
                        st.dataframe(df, use_container_width=True)
                except Exception as e:
                    st.error(f"Import error: {e}")

            st.subheader("Quantities")
            uploaded_qty = st.file_uploader(
                "Import quantities", type=["xlsx", "xls"], key="quantities"
            )

            if uploaded_qty:
                try:
                    df_qty = pd.read_excel(uploaded_qty, header=0)
                    qty_series = df_qty.iloc[0]
                    qty_series = pd.to_numeric(qty_series, errors="coerce")

                    st.session_state.df_qty = qty_series
                    st.success("✅ Quantities imported successfully!")
                    with st.expander("Data Preview"):
                        st.dataframe(qty_series, use_container_width=True)
                except Exception as e:
                    st.error(f"Import error: {e}")

    with tab2:
        st.header("Interest Rate Curves")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("USD")
            uploaded_usd = st.file_uploader(
                "Import USD curve", type=["xlsx", "xls"], key="usd_curve"
            )

            if uploaded_usd:
                try:
                    df = pd.read_excel(uploaded_usd)
                    df["Date"] = pd.to_datetime(df["Date"])
                    st.session_state.curve_map["USD"] = df
                    st.success("✅ USD curve imported!")
                    with st.expander("Preview"):
                        st.dataframe(df, use_container_width=True)
                except Exception as e:
                    st.error(f"Error: {e}")

        with col2:
            st.subheader("EUR")
            uploaded_eur = st.file_uploader(
                "Import EUR curve", type=["xlsx", "xls"], key="eur_curve"
            )

            if uploaded_eur:
                try:
                    df = pd.read_excel(uploaded_eur)
                    df["Date"] = pd.to_datetime(df["Date"])
                    st.session_state.curve_map["EUR"] = df
                    st.success("✅ EUR curve imported!")
                    with st.expander("Preview"):
                        st.dataframe(df, use_container_width=True)
                except Exception as e:
                    st.error(f"Error: {e}")

        with col3:
            st.subheader("MAD")
            uploaded_mad = st.file_uploader(
                "Import MAD curve", type=["xlsx", "xls"], key="mad_curve"
            )

            if uploaded_mad:
                try:
                    df = pd.read_excel(uploaded_mad)
                    df["Date"] = pd.to_datetime(df["Date"])
                    st.session_state.curve_map["MAD"] = df
                    st.success("✅ MAD curve imported!")
                    with st.expander("Preview"):
                        st.dataframe(df, use_container_width=True)
                except Exception as e:
                    st.error(f"Error: {e}")

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
                if st.session_state.df_options is None:
                    st.error("⚠️ Please import an options file first")
                else:
                    try:
                        with st.spinner("Computing..."):
                            var_value, pnl_total = compute_var(
                                st.session_state.df_options,
                                pricing_date,
                                confidence_level / 100,
                                n_simulations,
                                st.session_state.curve_map,
                            )

                            st.session_state.last_calc_type = "options"
                            st.session_state.last_var_results = {
                                "var_value": var_value,
                                "pnl_total": pnl_total,
                            }

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
                                            "Scenario": range(
                                                1, min(31, len(pnl_total) + 1)
                                            ),
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
                if st.session_state.df_stocks is None:
                    st.error(" Please import a stock portfolio first")
                else:
                    try:
                        with st.spinner("Computing..."):
                            df = st.session_state.df_stocks.copy()
                            returns = np.log(df / df.shift(1)).dropna()
                            n_assets = returns.shape[1]
                            weights = np.ones(n_assets) / n_assets
                            real_returns = returns.dot(weights)

                            var_cf = CF_var(returns, 100 - confidence_level, weights)
                            var_gbm, sim_porto = GBM(
                                n_simulations, returns, weights, confidence_level
                            )

                            st.session_state.last_calc_type = "stocks"
                            st.session_state.last_var_results = {
                                "var_cf": var_cf,
                                "var_gbm": var_gbm,
                                "real_returns": real_returns,
                                "sim_porto": sim_porto,
                            }

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

                            fig.update_layout(
                                height=500, showlegend=False, template="plotly_white"
                            )

                            st.plotly_chart(fig, use_container_width=True)

                    except Exception as e:
                        st.error(f"Calculation error: {e}")

        else:
            st.subheader("Historical VaR")

            if st.button("Run Calculation", type="primary", use_container_width=True):
                if st.session_state.df_qty is None:
                    st.warning(" Please import quantities")
                elif st.session_state.last_calc_type not in ["funds", "stocks"]:
                    st.error("Please import a portfolio first (Mutual Funds or Stocks)")
                else:
                    try:
                        with st.spinner("Computing..."):
                            if st.session_state.last_calc_type == "funds":
                                df = st.session_state.df_funds.copy()
                            else:
                                df = st.session_state.df_stocks.copy()

                            qty = st.session_state.df_qty.copy()

                            var, port_returns = compute_historical_var(
                                df, qty, confidence_level / 100, nb_returns
                            )
                            returns = (
                                (df.pct_change().dropna() * qty)
                                .sum(axis=1)
                                .tail(nb_returns)
                            )
                            var = abs(
                                np.percentile(
                                    returns, (1 - confidence_level / 100) * 100
                                )
                            )

                            st.session_state.last_var_results = {
                                "var_histo": var,
                                "pnl": returns.values,
                                "dates": returns.index,
                            }

                            st.success("Calculation completed!")

                            st.metric(
                                f"Historical VaR {int(confidence_level)}%",
                                f"{var:,.4f} MAD",
                            )

                            fig = go.Figure()

                            fig.add_trace(
                                go.Scatter(
                                    x=returns.index,
                                    y=returns.values,
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
                                {
                                    "VaR": [
                                        st.session_state.last_var_results["var_value"]
                                    ]
                                }
                            ).to_excel(writer, index=False, sheet_name="Summary")

                            pd.DataFrame(
                                {
                                    "Scenario": range(
                                        1,
                                        len(
                                            st.session_state.last_var_results[
                                                "pnl_total"
                                            ]
                                        )
                                        + 1,
                                    ),
                                    "Simulated P&L": st.session_state.last_var_results[
                                        "pnl_total"
                                    ],
                                }
                            ).to_excel(writer, index=False, sheet_name="Simulated P&L")

                        elif st.session_state.last_calc_type == "stocks":
                            pd.DataFrame(
                                {
                                    "VaR Cornish-Fisher": [
                                        st.session_state.last_var_results["var_cf"]
                                    ],
                                    "VaR GBM": [
                                        st.session_state.last_var_results["var_gbm"]
                                    ],
                                }
                            ).to_excel(writer, index=False, sheet_name="Summary")

                            pd.DataFrame(
                                {
                                    "Actual Returns": st.session_state.last_var_results[
                                        "real_returns"
                                    ]
                                }
                            ).to_excel(writer, index=True, sheet_name="Actual Returns")

                            pd.DataFrame(
                                {
                                    "Simulated Returns GBM": st.session_state.last_var_results[
                                        "sim_porto"
                                    ]
                                }
                            ).to_excel(
                                writer, index=True, sheet_name="Simulated Returns"
                            )

                        else:  # funds
                            pd.DataFrame(
                                {
                                    "Historical VaR": [
                                        st.session_state.last_var_results["var_histo"]
                                    ]
                                }
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
