import os
import yfinance as yf
import numpy as np
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
import cohere

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.DEBUG)

# ---- FOR COHERE-API -----
COHERE_API_KEY = os.getenv("your_API_key_here")  # Ensure API key is stored safely
co = cohere.Client(COHERE_API_KEY)


# Implementing the AI Model
def generate_insight(prompt):
    response = co.generate(
        model="command-r-plus",
        prompt=prompt,
        max_tokens=300,
        temperature=0.7
    )

    return response.generations[0].text.strip()


# Using "sentiment-insights" for AI prompt generation
@app.route("/sentiment-insights", methods=["GET"])
def sentiment_insights():
    keyword = request.args.get("keyword", "").strip()

    if not keyword:
        return jsonify({"error": "No key provided!"}), 400

    print(f"🔍 DEBUG: Received request for sentiment insights: {keyword}")

    prompt = f"Analyze the market sentiment for {keyword}. Provide only 3 key insights based on financial trends. " \
             f"Do not include any kind of summary."

    try:
        insight = generate_insight(prompt)
        return jsonify({"insight_text": insight, "key_sentence": insight.split(' ')[0]})
        #return jsonify({"company": keyword, "insights": insight})
    except Exception as e:
        print(f"❌ DEBUG: AI Generation Failed: {str(e)}")
        return jsonify({"error": f"AI generation failed: {str(e)}"}), 500


# Generate Future forecasts for chosen stocks
def generate_growth_forecast(ticker):

    # Constructing AI prompt
    prompt = f"""
            Predict the future stock performance of {ticker} based on its historical trends and market conditions.
            Provide an estimated percentage growth for the next 6 months and 12 months.
            Format the response as:
            - 6-Month Growth Estimate: X%
            - 12-Month Growth Estimate: Y%
            """

    try:
        response = co.generate(
            model="command-r-plus",
            prompt=prompt,
            max_tokens=100,
            temperature=0.7
        )

        forecast_text = response.generations[0].text.strip()
        return forecast_text

    except Exception as e:
        return f"❌ AI Forecasting Failed: {str(e)}"


# For Market Trend Analysis
@app.route("/market-data", methods=["POST"])
def market_data():
    try:
        tickers = request.json.get("tickers", [])
        logging.info(f"Received request for tickers: {tickers}")
        if not tickers:
            return jsonify({"error": "No tickers provided"}), 400

        response_data = {}
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1y")

                if hist.empty:
                    logging.warning(f"No data available for ticker: {ticker}")
                    response_data[ticker] = {"error": "Invalid ticker or no data available"}
                    continue

                hist["Returns"] = hist["Close"].pct_change()
                volatility = np.std(hist["Returns"]) * np.sqrt(252)
                VaR_95 = np.percentile(hist["Returns"].dropna(), 5)

                response_data[ticker] = {
                    "current_price": round(stock.history(period="1d")["Close"].iloc[-1], 2),
                    "volatility": round(volatility, 4),
                    "VaR_95": round(VaR_95, 4)
                }
            except Exception as e:
                logging.error(f"Error fetching data for {ticker}: {str(e)}")
                response_data[ticker] = {"error": "Error retrieving market data"}

        logging.info(f"Returning response: {response_data}")
        return jsonify(response_data)
    except Exception as e:
        logging.error(f"Internal Server Error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)