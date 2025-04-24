# Sentiment AI - Earnings Call Sentiment Analysis

A tool for analyzing earnings call sentiment and its correlation with stock price movements. The application provides backtesting capabilities to evaluate trading strategies based on sentiment analysis.

## Prerequisites

- Python 3.9+ 
- Node.js 16+ and npm
- Git

## Installation and Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd sentiment_ai
```

### 2. Setup API Keys

Create a `.env` file in the root directory with the following content:

```
# Financial Modeling Prep API Key
FMP_API_KEY=your_fmp_api_key_here

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Add other API keys and configuration below
```

You'll need to obtain API keys from:
- [Financial Modeling Prep](https://financialmodelingprep.com/developer/docs/) for earnings call transcripts
- [OpenAI](https://platform.openai.com/api-keys) for sentiment analysis

### 3. Backend Setup

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Frontend Setup

```bash
cd frontend
npm install
```

Also create a `.env` file in the `frontend` directory:

```
VITE_API_URL=http://localhost:8000
```

## Running the Application

### 1. Start the Backend

From the root directory with the virtual environment activated:

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The API will be accessible at http://localhost:8000

### 2. Start the Frontend

In a separate terminal:

```bash
cd frontend
npm run dev
```

The frontend will be accessible at http://localhost:5173

## API Endpoints

- Health Check: `GET /health`
- Root Info: `GET /`
- Analyze Ticker: `GET /analyze/{ticker}?from_year={year}`
- Price Forecast: `GET /api/forecast/{ticker}?start_date={date}&forecast_days={days}`
- Backtest: `GET /api/backtest/{ticker}?{params}`

## Troubleshooting

### Common Issues

1. **API Key Issues**: Ensure your API keys are correctly set in the `.env` file.
2. **Module Not Found Errors**: Make sure you're running from the correct directory and the virtual environment is activated.
3. **Port Already in Use**: Change the port in the command if 8000 or 5173 are already being used.

### Logs

- Backend logs: Check the terminal running the uvicorn server.
- Detailed logs in: `acn_sentiment_analysis.log` and `backtest_debug.log`

## Running Tests

```bash
# From the root directory
pytest

# For specific test files
pytest backend/tests/
```
