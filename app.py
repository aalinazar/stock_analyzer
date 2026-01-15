import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from database import db
from trading_strategy import strategy

# Set page config
st.set_page_config(
    page_title="Stock Inventory Tracker",
    page_icon="📊",
    layout="wide"
)

# Title and description
st.title("📊 Stock Inventory Tracker")
st.markdown("---")
st.write("Track your stock investments, purchase details, and get AI-powered trading recommendations.")

# Sidebar for navigation
st.sidebar.title("📈 Portfolio Management")
page = st.sidebar.selectbox("Choose a page", [
    "Portfolio Overview", 
    "Add Stock", 
    "Trading Strategy", 
    "Recommendations",
    "Settings"
])

def load_portfolio():
    """Load portfolio from database and enrich with current data"""
    portfolio = db.get_portfolio()
    enriched_portfolio = []
    
    for stock in portfolio:
        try:
            # Get current stock data
            stock_ticker = yf.Ticker(stock['ticker'])
            info = stock_ticker.info
            
            # Get current price
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            if current_price is None:
                hist = stock_ticker.history(period="1d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                else:
                    current_price = stock['purchase_price']  # Fallback to purchase price
            
            # Calculate values
            current_total_value = current_price * stock['shares']
            purchase_total_value = stock['purchase_price'] * stock['shares']
            profit_loss = current_total_value - purchase_total_value
            profit_loss_percent = (profit_loss / purchase_total_value) * 100 if purchase_total_value > 0 else 0
            
            enriched_stock = {
                'id': stock['id'],
                'ticker': stock['ticker'],
                'shares': stock['shares'],
                'purchase_date': stock['purchase_date'],
                'purchase_price': stock['purchase_price'],
                'current_price': current_price,
                'purchase_total': purchase_total_value,
                'current_total': current_total_value,
                'profit_loss': profit_loss,
                'profit_loss_percent': profit_loss_percent,
                'company_name': stock['company_name'] or info.get('shortName', stock['ticker']),
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'created_at': stock['created_at']
            }
            
            enriched_portfolio.append(enriched_stock)
            
        except Exception as e:
            st.error(f"Error fetching data for {stock['ticker']}: {str(e)}")
            continue
    
    return enriched_portfolio

def format_portfolio_for_display(portfolio_df):
    """Format portfolio dataframe for display"""
    display_df = portfolio_df[[
        'id', 'ticker', 'company_name', 'shares', 'purchase_date', 
        'purchase_price', 'current_price', 'purchase_total', 
        'current_total', 'profit_loss', 'profit_loss_percent'
    ]].copy()
    
    # Format columns
    display_df['purchase_price'] = display_df['purchase_price'].apply(lambda x: f"${x:.2f}")
    display_df['current_price'] = display_df['current_price'].apply(lambda x: f"${x:.2f}")
    display_df['purchase_total'] = display_df['purchase_total'].apply(lambda x: f"${x:,.2f}")
    display_df['current_total'] = display_df['current_total'].apply(lambda x: f"${x:,.2f}")
    display_df['profit_loss'] = display_df['profit_loss'].apply(lambda x: f"${x:,.2f}")
    display_df['profit_loss_percent'] = display_df['profit_loss_percent'].apply(lambda x: f"{x:+.2f}%")
    display_df['shares'] = display_df['shares'].apply(lambda x: f"{x:,.0f}")
    
    display_df.columns = [
        'ID', 'Ticker', 'Company', 'Shares', 'Purchase Date',
        'Purchase Price', 'Current Price', 'Purchase Total',
        'Current Total', 'Profit/Loss', 'P/L %'
    ]
    
    return display_df

# Portfolio Overview Page
if page == "Portfolio Overview":
    portfolio = load_portfolio()
    
    if portfolio:
        portfolio_df = pd.DataFrame(portfolio)
        
        # Calculate summary metrics
        total_purchase_value = portfolio_df['purchase_total'].sum()
        total_current_value = portfolio_df['current_total'].sum()
        total_profit_loss = portfolio_df['profit_loss'].sum()
        total_shares = portfolio_df['shares'].sum()
        total_profit_loss_percent = (total_profit_loss / total_purchase_value) * 100 if total_purchase_value > 0 else 0
        
        # Display summary cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Stocks", len(portfolio))
        with col2:
            st.metric("Total Shares", f"{total_shares:,.0f}")
        with col3:
            st.metric("Current Value", f"${total_current_value:,.2f}")
        with col4:
            profit_color = "normal" if total_profit_loss >= 0 else "inverse"
            st.metric(
                "Total P/L", 
                f"${total_profit_loss:,.2f}",
                f"{total_profit_loss_percent:+.2f}%",
                delta_color=profit_color
            )
        
        # Portfolio details table
        st.header("📈 Portfolio Details & Performance")
        display_df = format_portfolio_for_display(portfolio_df)
        
        # Color code the profit/loss columns
        def color_profit_loss(val):
            if isinstance(val, str) and '$' in val:
                try:
                    num_val = float(val.replace('$', '').replace(',', ''))
                    if num_val > 0:
                        return 'color: green'
                    elif num_val < 0:
                        return 'color: red'
                except:
                    pass
            return ''
        
        def color_percent(val):
            if isinstance(val, str) and '%' in val:
                if val.startswith('+'):
                    return 'color: green'
                elif val.startswith('-'):
                    return 'color: red'
            return ''
        
        styled_df = display_df.style.map(color_profit_loss, subset=['Profit/Loss'])
        styled_df = styled_df.map(color_percent, subset=['P/L %'])
        
        st.dataframe(styled_df, use_container_width=True)
        
        # Portfolio distribution chart
        st.subheader("Portfolio Distribution by Current Value")
        chart_data = portfolio_df.set_index('ticker')['current_total']
        st.bar_chart(chart_data)
        
        # Export to CSV
        csv_data = db.export_portfolio_to_csv()
        if csv_data:
            st.download_button(
                label="📄 Export Portfolio to CSV",
                data=csv_data,
                file_name=f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        # Clear portfolio button
        if st.button("Clear Entire Portfolio", type="secondary"):
            if st.session_state.get('confirm_clear', False):
                db.clear_portfolio()
                st.success("Portfolio cleared successfully!")
                st.session_state.confirm_clear = False
                st.rerun()
            else:
                st.session_state.confirm_clear = True
                st.warning("⚠️ Are you sure? Click again to confirm clearing the entire portfolio.")
        
    else:
        st.info("📝 No stocks in your portfolio yet. Go to 'Add Stock' to get started!")

# Add Stock Page
elif page == "Add Stock":
    st.header("➕ Add Stock to Portfolio")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        ticker = st.text_input(
            "Stock Ticker",
            placeholder="e.g., AAPL, GOOGL, MSFT",
            help="Enter the stock ticker symbol"
        ).upper()
    
    with col2:
        shares = st.number_input(
            "Number of Shares",
            min_value=0.0,
            step=1.0,
            value=0.0,
            help="Enter the number of shares you own"
        )
    
    # Purchase details
    col1, col2 = st.columns([2, 1])
    
    with col1:
        purchase_date = st.date_input(
            "Purchase Date",
            value=datetime.now().date() - timedelta(days=30),
            max_value=datetime.now().date(),
            help="When did you purchase these shares?"
        )
    
    with col2:
        purchase_price = st.number_input(
            "Purchase Price per Share ($)",
            min_value=0.0,
            step=0.01,
            value=0.0,
            help="Price you paid per share"
        )
    
    # Add stock button
    if st.button("Add Stock", type="primary"):
        if ticker and shares > 0 and purchase_price > 0:
            try:
                # Get stock info
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Add to database
                stock_id = db.add_stock(
                    ticker=ticker,
                    shares=shares,
                    purchase_date=purchase_date.strftime("%Y-%m-%d"),
                    purchase_price=purchase_price,
                    company_name=info.get('shortName')
                )
                
                # Get current price for success message
                current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                if current_price is None:
                    hist = stock.history(period="1d")
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                    else:
                        current_price = purchase_price
                
                # Calculate values
                current_total_value = current_price * shares
                purchase_total_value = purchase_price * shares
                profit_loss = current_total_value - purchase_total_value
                profit_loss_percent = (profit_loss / purchase_total_value) * 100 if purchase_total_value > 0 else 0
                
                # Show success message
                profit_emoji = "🟢" if profit_loss >= 0 else "🔴"
                st.success(f"{profit_emoji} Successfully added {shares} shares of {ticker} ({info.get('shortName', ticker)}) to your portfolio!")
                st.info(f"Current P/L: ${profit_loss:,.2f} ({profit_loss_percent:+.2f}%)")
                
            except Exception as e:
                st.error(f"Error fetching data for {ticker}: {str(e)}")
                st.info("Please check if the ticker symbol is correct and try again.")
        else:
            st.warning("Please enter all required fields: ticker, shares, and purchase price.")

# Trading Strategy Page
elif page == "Trading Strategy":
    st.header("🤖 Trading Strategy Configuration")
    
    portfolio = db.get_portfolio()
    if not portfolio:
        st.warning("⚠️ No stocks in portfolio. Add stocks first to configure trading strategies.")
        st.stop()
    
    # Select stock to configure
    stock_options = [(stock['ticker'], stock['id']) for stock in portfolio]
    selected_stock_id = st.selectbox("Select Stock", [sid for _, sid in stock_options], 
                                    format_func=lambda x: next(t for t, sid in stock_options if sid == x))
    
    selected_stock = next(stock for stock in portfolio if stock['id'] == selected_stock_id)
    
    # Get current strategy settings
    current_settings = db.get_strategy_settings(selected_stock['ticker'])
    
    col1, col2 = st.columns(2)
    
    with col1:
        strategy_type = st.selectbox(
            "Trading Strategy",
            ["simple", "moving_average", "rsi", "bollinger_bands", "macd"],
            index=["simple", "moving_average", "rsi", "bollinger_bands", "macd"].index(current_settings['strategy_type'] if current_settings else 'simple'),
            help="Choose the trading strategy to apply to this stock"
        )
    
    with col2:
        st.write("**Strategy Description:**")
        strategy_descriptions = {
            "simple": "Simple profit/loss based strategy with configurable targets",
            "moving_average": "Moving average crossover strategy for trend following",
            "rsi": "RSI (Relative Strength Index) for overbought/oversold signals",
            "bollinger_bands": "Bollinger Bands for volatility-based trading",
            "macd": "MACD (Moving Average Convergence Divergence) for momentum signals"
        }
        st.info(strategy_descriptions.get(strategy_type, "No description available"))
    
    # Strategy parameters
    st.subheader(f"📊 {strategy_type.title()} Parameters")
    
    parameters = {}
    
    if strategy_type == "simple":
        col1, col2, col3 = st.columns(3)
        with col1:
            parameters['profit_target'] = st.slider("Profit Target (%)", 5, 100, 20) / 100
        with col2:
            parameters['stop_loss'] = st.slider("Stop Loss (%)", 5, 50, 10) / 100
        with col3:
            parameters['hold_threshold'] = st.slider("Hold Threshold (%)", 1, 20, 5) / 100
    
    elif strategy_type == "moving_average":
        col1, col2 = st.columns(2)
        with col1:
            parameters['short_ma'] = st.slider("Short MA Period", 5, 50, 20)
        with col2:
            parameters['long_ma'] = st.slider("Long MA Period", 20, 200, 50)
    
    elif strategy_type == "rsi":
        col1, col2, col3 = st.columns(3)
        with col1:
            parameters['rsi_period'] = st.slider("RSI Period", 10, 30, 14)
        with col2:
            parameters['oversold_level'] = st.slider("Oversold Level", 20, 40, 30)
        with col3:
            parameters['overbought_level'] = st.slider("Overbought Level", 60, 80, 70)
    
    elif strategy_type == "bollinger_bands":
        col1, col2 = st.columns(2)
        with col1:
            parameters['bb_period'] = st.slider("Bollinger Band Period", 10, 50, 20)
        with col2:
            parameters['bb_std'] = st.slider("Standard Deviations", 1, 3, 2)
    
    elif strategy_type == "macd":
        col1, col2, col3 = st.columns(3)
        with col1:
            parameters['macd_fast'] = st.slider("Fast EMA Period", 8, 20, 12)
        with col2:
            parameters['macd_slow'] = st.slider("Slow EMA Period", 20, 40, 26)
        with col3:
            parameters['macd_signal'] = st.slider("Signal Line Period", 5, 15, 9)
    
    # Save strategy button
    if st.button("Save Strategy Settings", type="primary"):
        db.save_strategy_settings(selected_stock['ticker'], strategy_type, parameters)
        st.success(f"✅ Strategy settings saved for {selected_stock['ticker']}!")

# Recommendations Page
elif page == "Recommendations":
    st.header("💡 AI Trading Recommendations")
    
    portfolio = db.get_portfolio()
    if not portfolio:
        st.warning("⚠️ No stocks in portfolio. Add stocks first to get recommendations.")
        st.stop()
    
    # Get all recommendations
    with st.spinner("🔄 Analyzing portfolio and generating recommendations..."):
        recommendations = strategy.get_all_portfolio_recommendations(portfolio)
    
    if recommendations:
        # Summary dashboard
        buy_count = sum(1 for r in recommendations if r['action'] == 'BUY')
        sell_count = sum(1 for r in recommendations if r['action'] == 'SELL')
        hold_count = sum(1 for r in recommendations if r['action'] == 'HOLD')
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📈 Buy Signals", buy_count, delta=f"{buy_count} stocks")
        with col2:
            st.metric("📉 Sell Signals", sell_count, delta=f"{sell_count} stocks")
        with col3:
            st.metric("⏸️ Hold", hold_count, delta=f"{hold_count} stocks")
        with col4:
            avg_confidence = sum(r['confidence'] for r in recommendations) / len(recommendations)
            st.metric("🎯 Avg Confidence", f"{avg_confidence:.1%}")
        
        # Detailed recommendations
        st.subheader("📋 Detailed Recommendations")
        
        for rec in recommendations:
            stock = rec['stock_data']
            
            # Color coding for action
            action_color = {
                'BUY': '🟢',
                'SELL': '🔴', 
                'HOLD': '🟡'
            }.get(rec['action'], '⚪')
            
            with st.expander(f"{action_color} {stock['ticker']} - {rec['action']} (Confidence: {rec['confidence']:.1%})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Company:** {stock['company_name'] or stock['ticker']}")
                    st.write(f"**Current Price:** ${rec['current_price']:.2f}")
                    st.write(f"**Purchase Price:** ${stock['purchase_price']:.2f}")
                    st.write(f"**Shares:** {stock['shares']:,.0f}")
                    profit_loss = ((rec['current_price'] - stock['purchase_price']) / stock['purchase_price']) * 100
                    st.write(f"**P/L:** {profit_loss:+.2f}%")
                
                with col2:
                    st.write(f"**Strategy:** {rec['strategy'].title()}")
                    st.write(f"**Reason:** {rec['reason']}")
                
                # Strategy settings badge
                settings = db.get_strategy_settings(stock['ticker'])
                if settings:
                    st.info(f"⚙️ Strategy: {settings['strategy_type'].title()}")
        
        # Recent recommendations history
        st.subheader("📜 Recent Recommendation History")
        recent_recs = db.get_recent_recommendations(20)
        
        if recent_recs:
            rec_df = pd.DataFrame(recent_recs)
            rec_df['created_at'] = pd.to_datetime(rec_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
            
            def color_action(val):
                if val == 'BUY':
                    return 'color: green'
                elif val == 'SELL':
                    return 'color: red'
                else:
                    return 'color: orange'
            
            styled_recs = rec_df.style.map(color_action, subset=['action'])
            st.dataframe(styled_recs, use_container_width=True)
        else:
            st.info("No previous recommendations found.")
    
    else:
        st.info("No recommendations available at this time.")

# Settings Page
elif page == "Settings":
    st.header("⚙️ Portfolio Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Portfolio Statistics")
        portfolio = db.get_portfolio()
        st.metric("Total Stocks", len(portfolio))
        
        if portfolio:
            total_shares = sum(stock['shares'] for stock in portfolio)
            total_investment = sum(stock['shares'] * stock['purchase_price'] for stock in portfolio)
            st.metric("Total Shares", f"{total_shares:,.0f}")
            st.metric("Total Investment", f"${total_investment:,.2f}")
    
    with col2:
        st.subheader("🗄️ Database Operations")
        
        if st.button("📄 Export Portfolio to CSV", type="secondary"):
            csv_data = db.export_portfolio_to_csv()
            if csv_data:
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        if st.button("🗑️ Clear All Data", type="secondary"):
            if st.session_state.get('confirm_clear_all', False):
                db.clear_portfolio()
                st.success("All portfolio data cleared!")
                st.session_state.confirm_clear_all = False
                st.rerun()
            else:
                st.session_state.confirm_clear_all = True
                st.warning("⚠️ Are you sure? Click again to confirm clearing all data.")

# Footer
st.markdown("---")
st.markdown("*Data provided by Yahoo Finance. Prices are delayed and may not reflect real-time market data.*")
st.markdown("*Trading recommendations are for educational purposes only. Always consult with a financial advisor before making investment decisions.*")
