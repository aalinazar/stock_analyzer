# 📊 Stock Inventory Tracker with AI Trading Strategies

A powerful Streamlit application for tracking your stock investments with trading recommendations and persistent database storage using Yahoo Finance data.

## 🚀 New Features

### 🗄️ **Database Persistence**
- **SQLite Database**: All portfolio data is now saved in a local SQLite database
- **No Data Loss**: Your portfolio persists across application restarts
- **Automatic Migration**: Seamlessly migrates from session state to database
- **Multiple Tables**: Portfolio stocks, strategy settings, and recommendation history

### 🤖 **AI Trading Strategies**
- **5 Trading Algorithms**: Simple, Moving Average, RSI, Bollinger Bands, MACD
- **Customizable Parameters**: Fine-tune each strategy to your preferences
- **Real-time Recommendations**: Get BUY/SELL/HOLD signals with confidence scores
- **Recommendation History**: Track all past recommendations with timestamps

### 📈 **Enhanced Portfolio Management**
- **Multi-page Interface**: Organized dashboard with sidebar navigation
- **Export to CSV**: Download your portfolio data for external analysis
- **Detailed Analytics**: Enhanced charts and performance metrics
- **Strategy Configuration**: Per-stock strategy customization

## Features

### 📊 **Portfolio Overview**
- Real-time stock price updates from Yahoo Finance
- Portfolio summary cards with total value and P/L
- Color-coded profit/loss display
- Interactive portfolio distribution charts
- Export portfolio to CSV functionality

### ➕ **Add Stock**
- Add stocks with ticker validation
- Automatic company name fetching
- Real-time price verification
- Purchase date and price tracking

### 🤖 **Trading Strategy Configuration**
- **Simple Strategy**: Profit target, stop loss, and hold threshold
- **Moving Average**: Golden/Death cross detection with customizable periods
- **RSI Strategy**: Overbought/oversold signal detection
- **Bollinger Bands**: Volatility-based trading signals
- **MACD Strategy**: Momentum and trend following signals

### 💡 **AI Recommendations**
- Automated trading signals for all portfolio stocks
- Confidence scoring for each recommendation
- Detailed reasoning for each signal
- Historical recommendation tracking
- Strategy-based analysis

### ⚙️ **Settings**
- Portfolio statistics overview
- Database management tools
- CSV export functionality
- Clear data options with confirmation

## Setup Instructions

### 1. Activate Virtual Environment

```bash
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

## Database Schema

### 📋 **portfolio_stocks** Table
```sql
CREATE TABLE portfolio_stocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    shares REAL NOT NULL,
    purchase_date TEXT NOT NULL,
    purchase_price REAL NOT NULL,
    company_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### ⚙️ **strategy_settings** Table
```sql
CREATE TABLE strategy_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT UNIQUE NOT NULL,
    strategy_type TEXT NOT NULL DEFAULT 'simple',
    parameters TEXT NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 💡 **trading_recommendations** Table
```sql
CREATE TABLE trading_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    action TEXT NOT NULL, -- 'BUY', 'SELL', 'HOLD'
    reason TEXT NOT NULL,
    confidence REAL NOT NULL, -- 0-1 scale
    price_at_recommendation REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Trading Strategies Explained

### 🎯 **Simple Strategy**
- **Buy Signal**: None (HOLD by default)
- **Sell Signal**: When profit target reached or stop loss triggered
- **Parameters**: 
  - `profit_target`: Percentage gain to trigger sell (default: 20%)
  - `stop_loss`: Maximum loss before selling (default: 10%)
  - `hold_threshold`: Small price changes to ignore (default: 5%)

### 📈 **Moving Average Strategy**
- **Golden Cross**: Short MA crosses above long MA = BUY signal
- **Death Cross**: Short MA crosses below long MA = SELL signal
- **Trend Analysis**: Price position relative to moving averages
- **Parameters**:
  - `short_ma`: Short-term MA period (default: 20 days)
  - `long_ma`: Long-term MA period (default: 50 days)

### 📊 **RSI (Relative Strength Index)**
- **Oversold**: RSI below 30 = BUY signal
- **Overbought**: RSI above 70 = SELL signal
- **Momentum**: Measures speed and change of price movements
- **Parameters**:
  - `rsi_period`: RSI calculation period (default: 14)
  - `oversold_level`: RSI level for buy signals (default: 30)
  - `overbought_level`: RSI level for sell signals (default: 70)

### 📊 **Bollinger Bands**
- **Upper Band**: Price above = Overbought = SELL signal
- **Lower Band**: Price below = Oversold = BUY signal
- **Volatility**: Dynamic bands based on price volatility
- **Parameters**:
  - `bb_period`: Moving average period (default: 20)
  - `bb_std`: Standard deviations for bands (default: 2)

### 📈 **MACD (Moving Average Convergence Divergence)**
- **Bullish Cross**: MACD crosses above signal line = BUY
- **Bearish Cross**: MACD crosses below signal line = SELL
- **Momentum**: Trend strength and direction analysis
- **Parameters**:
  - `macd_fast`: Fast EMA period (default: 12)
  - `macd_slow`: Slow EMA period (default: 26)
  - `macd_signal`: Signal line period (default: 9)

## Usage Guide

### Navigating the Application

1. **Portfolio Overview**: Main dashboard showing all your stocks
2. **Add Stock**: Add new stocks to your portfolio
3. **Trading Strategy**: Configure strategies for individual stocks
4. **Recommendations**: View trading signals
5. **Settings**: Manage data and export options

### Adding Stocks to Your Portfolio

1. Navigate to **Add Stock** page
2. Enter stock ticker (e.g., AAPL, GOOGL, MSFT)
3. Specify number of shares and purchase details
4. Click **Add Stock** to save to database

### Configuring Trading Strategies

1. Go to **Trading Strategy** page
2. Select a stock from your portfolio
3. Choose a strategy type and adjust parameters
4. Save settings to apply the strategy

### Viewing Recommendations

1. Visit **Recommendations** page
2. View real-time BUY/SELL/HOLD signals
3. Check confidence scores and reasoning
4. Review recommendation history

## Requirements

- Python 3.10+
- Streamlit 1.52.2
- yfinance 1.0
- pandas 2.3.3
- numpy 1.24.3
- SQLite (built into Python)

## Project Structure

```
stock_analyzer/
├── venv/                      # Python virtual environment
├── app.py                     # Main Streamlit application
├── database.py                # Database operations module
├── trading_strategy.py        # Trading algorithms module
├── portfolio.db              # SQLite database (auto-created)
├── requirements.txt          # Python dependencies
└── README.md                # This documentation
```

## Data Persistence

### 🗄️ **Automatic Database Creation**
- Database file `portfolio.db` is created automatically on first run
- Three tables are initialized with proper schema
- No manual database setup required

### 💾 **Data Storage**
- All portfolio data is persisted in SQLite
- Strategy settings saved per ticker
- Complete recommendation history logged
- Data survives application restarts

### 📤 **Data Export**
- CSV export available from multiple pages
- Includes all portfolio data with timestamps
- Format compatible with Excel and other tools

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure write permissions in project directory
   - Database file created automatically on first run

2. **"Could not fetch current price" Error**
   - Check if the ticker symbol is correct
   - Ensure you have an internet connection
   - Try refreshing the page

3. **Strategy Recommendations Not Working**
   - Verify ticker has sufficient historical data
   - Check strategy parameters are valid
   - Some strategies require minimum data periods

4. **Application Won't Start**
   - Make sure the virtual environment is activated
   - Verify all dependencies are installed
   - Check Python version compatibility

### Technical Notes

- **Database Backup**: Regularly backup `portfolio.db` file
- **Data Migration**: No manual migration needed from old session state
- **Performance**: SQLite optimized for single-user applications
- **Security**: Local database, no external data exposure

## Future Enhancements

- [ ] Technical analysis charts with indicators
- [ ] Portfolio performance analytics over time
- [ ] Multiple portfolio support
- [ ] Price alerts and notifications
- [ ] Backtesting strategy performance
- [ ] Risk management tools
- [ ] Dividend tracking and reinvestment
- [ ] Currency conversion for international stocks

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the application.

## Disclaimer

**⚠️ Important Disclaimer**: This application is for educational and informational purposes only. Stock market data is provided by Yahoo Finance and may be delayed. Trading recommendations are generated by algorithms and should not be considered financial advice. Always consult with a qualified financial advisor before making investment decisions. Past performance does not guarantee future results.

---

**Version**: 2.0 - Database & AI Trading Integration
**Last Updated**: January 2026
