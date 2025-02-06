import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import numpy as np
import plotly.express as px
from MarketAnalysis import generate_growth_forecast

# 📌 **Backend API URL**
FLASK_API_URL = "http://127.0.0.1:5000"


# Page styling
st.markdown("""
    <style>
    @media print {
        /* Force new page before every heading (H1 to H6) */
        h1, h2, h3, h4, h5, h6 {
            page-break-before: always !important;
            display: block !important; /* Ensure they behave like block elements */
            margin-top: 35px !important;  /* Adds space before a new page section */
            margin-bottom: 5px !important; /* Adds space below headings */
        }
        
        .page-break {
            page-break-before: always;
        }
        
        /* Hide Streamlit UI elements that shouldn't appear in print */
        [data-testid="stToolbar"], /* Hide Streamlit toolbar */
        [data-testid="stSidebar"], /* Hide Sidebar */
        .stButton, /* Hide buttons */
        .download-button { display: none !important; } /* Hide download buttons */

        /* Prevent tables and charts from being cut between pages */
        .stPlotlyChart, div[data-testid="stDataFrame"] {
            page-break-inside: avoid !important;
            max-width: 100% !important;
            overflow: visible !important;
        }

        /* Remove shadows to keep a clean print layout */
        .stPlotlyChart, .stCard, .header-container {
            box-shadow: none !important;
        }

        /* Improve text readability */
        h1 { font-size: 24px !important; font-weight: bold !important; }
        h2 { font-size: 22px !important; font-weight: bold !important; }
        h3 { font-size: 20px !important; font-weight: bold !important; }
        h4 { font-size: 18px !important; font-weight: bold !important; }
        h5 { font-size: 16px !important; font-weight: bold !important; }
        h6 { font-size: 14px !important; font-weight: bold !important; }
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <style>
    .header-container {
        background-color: #005A9C;
        color: white;
        text-align: center;
        padding: 15px;
        border-radius: 10px;
        font-size: 32px;
        font-weight: bold;
        margin-bottom: 20px;
        box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.2), 
                    -4px -4px 10px rgba(0, 0, 0, 0.2), 
                    4px -4px 10px rgba(0, 0, 0, 0.2), 
                    -4px 4px 10px rgba(0, 0, 0, 0.2); /* Shadow effect on all sides */
    }
    </style>
    <div class="header-container">MarketTrend AI: Strategy & Analysis</div>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
        /* Background Styling */
        .main {
            background-color: #f7f7f7; /* Light gray background */
            padding: 10px;
            border-radius: 5px;
        }

        /* Section Headers */
        h2, h3 {
            color: #005A9C; /* Dark Blue Headers */
            text-align: center;
            font-weight: bold;
        }

        /* Buttons Styling */
        .stButton>button {
            border-radius: 10px;
            background-color: #005A9C;
            color: white;
            padding: 8px 16px;
            font-size: 16px;
            font-weight: bold;
        }
        .stButton>button:hover {
            background-color: #003f7f; /* Darker Blue Hover */
        }

        /* Tables Styling */
        div[data-testid="stDataFrame"] table {
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            border-radius: 10px;
        }
        th {
            text-align: center !important;
            background-color: #005A9C !important;
            color: white !important;
            font-size: 14px;
            padding: 10px;
        }
        td {
            text-align: left !important;
            padding: 8px;
        }

        /* Charts & Cards */
        .stPlotlyChart {
            border-radius: 10px;
            background-color: white;
            padding: 15px;
            margin: 10px;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.15), 
                        4px 0px 10px rgba(0,0,0,0.15), 
                        -4px 0px 10px rgba(0,0,0,0.15), 
                        0px -4px 10px rgba(0,0,0,0.15); /* Shadow on all sides */
            
        }
        
    @media print {
        /* Hide all download buttons when printing */
        .stDownloadButton {
            display: none !important;
        }
    }

    </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <style>
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #E8F1FA; /* Light Blue Sidebar */
            border-radius: 10px;
        }
        [data-testid="stSidebar"] h1 {
            color: #003f7f !important; /* Dark Blue Text */
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)


# ---- Download the Data --- #
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')


# Set period for stock-analysis
period = '18mo'


@st.cache_data
def fetch_top_companies_stock(tickers):
    stock_data = {ticker: yf.Ticker(ticker).history(period=period) for ticker in tickers}
    return stock_data


def calculate_risk_metrics(stock_data):
    risk_data = {}
    for ticker, data in stock_data.items():
        returns = data["Close"].pct_change().dropna()
        volatility = np.std(returns) * np.sqrt(252)
        var_95 = np.percentile(returns, 5)
        risk_data[ticker] = {"Volatility": round(volatility * 100, 2), "VaR": round(var_95 * 100, 2)}
    return pd.DataFrame(risk_data).T


st.subheader("Enter Stock Tickers (Comma Separated)")
user_input = st.text_area("Enter tickers:", "AAPL,MSFT,GOOGL")
selected_tickers = [ticker.strip().upper() for ticker in user_input.split(",") if ticker.strip()]

if st.button("Fetch Data"):
    all_risk_data = {}
    stock_data = {}
    try:
        response = requests.post("http://127.0.0.1:5000/market-data", json={"tickers": selected_tickers})
        if response.status_code != 200:
            st.error(f"Error fetching data: {response.json().get('error', 'Unknown error')}")
        else:
            all_risk_data = response.json()
            stock_data = fetch_top_companies_stock(selected_tickers)
    except requests.exceptions.RequestException as e:
        st.error(f"Network error fetching data: {e}")
    except ValueError:
        st.error("Invalid response received from server.")

    if not all_risk_data:
        st.warning("No valid data available for selected tickers.")
    else:
        # Stock Performance & Risk Metrics Graph
        st.subheader("Stock Performance")
        st.line_chart({ticker: data["Close"] for ticker, data in stock_data.items()})
        # st.table(calculate_risk_metrics(stock_data))

        # 📈 **Growth Potential Graph for Selected Companies**
        st.subheader("Growth Rate")

        # Computing growth over the last {period} months
        growth_data = {}
        for ticker, data in stock_data.items():
            if not data.empty:
                start_price = data["Close"].iloc[0]  # First available price
                end_price = data["Close"].iloc[-1]  # Latest price
                growth_rate = ((end_price - start_price) / start_price) * 100  # Percentage change
                growth_data[ticker] = round(growth_rate, 2)

        # Converting to DataFrame for better visualization
        growth_df = pd.DataFrame.from_dict(growth_data, orient='index', columns=["Growth (%)"])
        growth_df.reset_index(inplace=True)
        growth_df.rename(columns={"index": "Company"}, inplace=True)

        # Plotting growth potential as a bar chart
        fig_growth = go.Figure()
        heading_color = "#005A9C"
        fig_growth.add_trace(go.Bar(x=growth_df["Company"], y=growth_df["Growth (%)"], text=growth_df["Growth (%)"],
                                    textposition='auto', marker=dict(color=heading_color)))

        fig_growth.update_layout(title=f'Growth Potential Over Last {period[:2]} Months',
                                 xaxis_title="Company",
                                 yaxis_title="Growth (%)",
                                 barmode='group',
                                 template="plotly_white",
                                 margin=dict(l=40, r=40, t=50, b=50),  # Proper margins to prevent overflow
                                 width=650,  # Ensures responsiveness
                                 height=425,  # Optional: Adjust height
                                 xaxis=dict(tickangle=-45, automargin=True)
                                 )

        st.plotly_chart(fig_growth)
        st.markdown('</div>', unsafe_allow_html=True)

        # Display Risk Metrics
        st.subheader("Risk Metrics")

        fig = go.Figure()
        for ticker, data in all_risk_data.items():
            if "error" in data:
                st.warning(f"{ticker}: {data['error']}")
                continue
            fig.add_trace(go.Bar(x=["Annual Volatility", "Value at Risk (95%)"], y=[data['volatility'], data['VaR_95']],
                                 name=ticker))
        fig.update_layout(title='Comparison', xaxis_title='Metric', yaxis_title='Value', barmode='group',
                          margin=dict(l=40, r=40, t=50, b=50),  # Proper margins to prevent overflow
                          width=650,  # Ensures responsiveness
                          height=410,  # Optional: Adjust height
                          xaxis=dict(tickangle=-45, automargin=True)
                          )
        st.plotly_chart(fig)
        risk_table = pd.DataFrame.from_dict(all_risk_data, orient='index').reset_index()

        risk_table = risk_table.rename(
            columns={"index": "Company", "current_price": "Current Price ($)", "VaR_95": "Value at Risk (95%)",
                     "volatility": "Annual Volatility"})[
            ["Company", "Current Price ($)", "Value at Risk (95%)", "Annual Volatility"]]

        # Applying CSS Styling for Centering Headers in DataFrame
        st.markdown("""
            <style>
            div[data-testid="stDataFrame"] table {
                width: 100%;
            }
            th {
                text-align: center !important;
                font-weight: bold !important;
            }
            td {
                text-align: left !important;
            }
            </style>
            """, unsafe_allow_html=True)

        st.dataframe(
            risk_table.set_index("Company").style.format({
                "Current Price ($)": "${:,.2f}",
                "Value at Risk (95%)": "{:.4f}",
                "Annual Volatility": "{:.4f}"
            }).set_table_styles(
                [{"selector": "th",
                  "props": [("font-size", "16px"), ("text-align", "center"), ("background-color", "#005A9C"),
                            ("color", "white")]}]
            ),
            use_container_width=True,
            height=400
        )

        # Download Risk Table
        csv = convert_df_to_csv(risk_table)
        st.download_button(
            "📥 Download Risk Analysis Data",
            csv,
            "Risk_Data.csv",
            "text/csv",
            help="Download the risk data as a CSV file",
        )

        # -- Market Trend Analysis Section --- #
        st.subheader("Market Trend Analysis")

        if selected_tickers:
            for ticker in selected_tickers:
                try:
                    # Fetch insights from Flask API
                    insight_response = requests.get(f"{FLASK_API_URL}/sentiment-insights?keyword={ticker}")

                    # Debugging: Print API response
                    print(f"DEBUG: API response for {ticker}:", insight_response.text)

                    # Checking if the response is valid
                    if insight_response.status_code != 200 or not insight_response.text.strip():
                        st.warning(f"⚠️ No detailed insights available for {ticker}. API returned no data.")
                    else:
                        # Convert response to JSON
                        insight_data = insight_response.json()

                        if "error" in insight_data:
                            st.warning(f"⚠️ No insights available for {ticker}: {insight_data['error']}")
                        else:
                            insight_text = insight_data.get("insight_text", "No detailed insight provided.")
                            # key_sentence = insight_data.get("key_sentence", "No key sentence extracted.")

                            st.markdown(f"<h5>📌 Key-Insights for {ticker}</h5>", unsafe_allow_html=True)
                            st.info(f"{insight_text}")
                            # st.write(f"**Key Sentence:** \"{key_sentence}\"")

                except Exception as e:
                    st.error(f"❌ Error fetching sentiment insights for {ticker}: {str(e)}")

        # Part-2

        if selected_tickers:
            all_insights = []  # Store insights for all companies

            for ticker in selected_tickers:
                try:
                    insight_response = requests.get(f"{FLASK_API_URL}/sentiment-insights?keyword={ticker}").json()

                    if "error" in insight_response:
                        st.warning(f"⚠️ No AI insights available for {ticker}.")
                    else:
                        insight_text = insight_response.get("insight_text", "No detailed insight provided.")
                        all_insights.append({"Company": ticker, "Insights": insight_text})
                        # {"Company": ticker, "AI Insight": insight_text, "Key Takeaway": key_sentence}

                except Exception as e:
                    st.error(f"❌ Error fetching AI insights for {ticker}: {str(e)}")

            if all_insights:
                # df_insights = pd.DataFrame(all_insights)
                df_insights = pd.DataFrame(all_insights)[["Company", "Insights"]]
                # st.dataframe(df_insights, use_container_width=True)

                # Download insights
                csv_insights = convert_df_to_csv(df_insights)

                st.download_button(
                    "📥 Download Insights Data",
                    csv_insights,
                    "Market_Trend_Analysis.csv",
                    "text/csv",
                    help="Download the market trend analysis as a CSV file",
                )

        # ----- FORECAST DISPLAY AND DOWNLOAD ----- #
        st.subheader("Growth Forecast")

        if selected_tickers:
            growth_forecasts = {"Company": [], "6-Month Growth (%)": [], "12-Month Growth (%)": []}

            for ticker in selected_tickers:
                forecast_text = generate_growth_forecast(ticker)

                # Extract numeric values from AI response
                try:
                    six_month_growth = float(forecast_text.split("6-Month Growth Estimate:")[1].split("%")[0].strip())
                    twelve_month_growth = float(
                        forecast_text.split("12-Month Growth Estimate:")[1].split("%")[0].strip())
                except:
                    six_month_growth, twelve_month_growth = None, None  # Handle AI output issues

                # Store results
                growth_forecasts["Company"].append(ticker)
                growth_forecasts["6-Month Growth (%)"].append(six_month_growth)
                growth_forecasts["12-Month Growth (%)"].append(twelve_month_growth)

            # Convert to DataFrame
            df_forecast = pd.DataFrame(growth_forecasts)

            # Plotting Graph (Bar Chart)
            fig = px.bar(
                df_forecast,
                x="Company",
                y=["6-Month Growth (%)", "12-Month Growth (%)"],
                barmode="group",
                title="Stock Growth Forecast (6M vs 12M)",
                labels={"value": "Growth (%)", "variable": "Forecast Period"},
                # Proper margins to prevent overflow
                width=650,  # Ensures responsiveness
                height=425,  # Optional: Adjust height
            )
            st.plotly_chart(fig)

            csv_forecast = convert_df_to_csv(df_forecast)

            st.download_button(
                label="📥 Download Growth Forecast data",
                data=csv_forecast,
                file_name="Growth_Forecasts.csv",
                mime="text/csv",
                help="Download the growth forecast as a CSV file",
            )