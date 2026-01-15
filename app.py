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
    "Edit Portfolio",
    "Sell Stock",
    "Sales History",
    "Trading Strategy", 
    "Watchlist",
    "Add to Watchlist",
    "Edit Watchlist",
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
    display_df['purchase_price'] = display_df['purchase_price'].apply(lambda x: f"{x:.2f}")
    display_df['current_price'] = display_df['current_price'].apply(lambda x: f"{x:.2f}")
    display_df['purchase_total'] = display_df['purchase_total'].apply(lambda x: f"{x:,.2f}")
    display_df['current_total'] = display_df['current_total'].apply(lambda x: f"{x:,.2f}")
    display_df['profit_loss'] = display_df['profit_loss'].apply(lambda x: f"{x:,.2f}")
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
        
        # Get realized profits
        total_realized_profits = db.get_total_realized_profits()
        
        # Display summary cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Stocks", len(portfolio))
        with col2:
            st.metric("Total Shares", f"{total_shares:,.0f}")
        with col3:
            st.metric("Current Value", f"{total_current_value:,.2f}")
        with col4:
            profit_color = "normal" if total_profit_loss >= 0 else "inverse"
            st.metric(
                "Total P/L", 
                f"{total_profit_loss:,.2f}",
                f"{total_profit_loss_percent:+.2f}%",
                delta_color=profit_color
            )
        
        # Additional summary row with realized profits
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Investment", f"{total_purchase_value:,.2f}")
        with col2:
            total_gain_loss = total_current_value - total_purchase_value
            total_gain_loss_percent = (total_gain_loss / total_purchase_value) * 100 if total_purchase_value > 0 else 0
            gain_loss_color = "normal" if total_gain_loss >= 0 else "inverse"
            st.metric(
                "Unrealized P/L",
                f"{total_gain_loss:,.2f}",
                f"{total_gain_loss_percent:+.2f}%",
                delta_color=gain_loss_color
            )
        with col3:
            realized_color = "normal" if total_realized_profits >= 0 else "inverse"
            st.metric(
                "Realized P/L",
                f"{total_realized_profits:,.2f}",
                delta_color=realized_color
            )
        with col4:
            overall_total = total_gain_loss + total_realized_profits
            overall_investment = total_purchase_value
            overall_percent = (overall_total / overall_investment) * 100 if overall_investment > 0 else 0
            overall_color = "normal" if overall_total >= 0 else "inverse"
            st.metric(
                "Overall P/L",
                f"{overall_total:,.2f}",
                f"{overall_percent:+.2f}%",
                delta_color=overall_color
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
        
        st.dataframe(styled_df, width='stretch')
        
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
            "Purchase Price per Share",
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
                st.info(f"Current P/L: {profit_loss:,.2f} ({profit_loss_percent:+.2f}%)")
                
            except Exception as e:
                st.error(f"Error fetching data for {ticker}: {str(e)}")
                st.info("Please check if the ticker symbol is correct and try again.")
        else:
            st.warning("Please enter all required fields: ticker, shares, and purchase price.")

# Edit Portfolio Page
elif page == "Edit Portfolio":
    st.header("✏️ Edit Portfolio Stocks")
    
    portfolio = db.get_portfolio()
    if not portfolio:
        st.warning("⚠️ No stocks in portfolio to edit. Add stocks first.")
        st.stop()
    
    # Select stock to edit
    stock_options = [(f"{stock['ticker']} - {stock['shares']} shares @ {stock['purchase_price']:.2f}", stock['id']) for stock in portfolio]
    selected_stock_id = st.selectbox("Select Stock to Edit", [sid for _, sid in stock_options], 
                                    format_func=lambda x: next(t for t, sid in stock_options if sid == x))
    
    selected_stock = next(stock for stock in portfolio if stock['id'] == selected_stock_id)
    
    # Display current stock info
    st.subheader(f"📊 Current Information for {selected_stock['ticker']}")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Ticker", selected_stock['ticker'])
    with col2:
        st.metric("Shares", f"{selected_stock['shares']:,.0f}")
    with col3:
        st.metric("Purchase Price", f"{selected_stock['purchase_price']:.2f}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Purchase Date", selected_stock['purchase_date'])
    with col2:
        st.metric("Company", selected_stock['company_name'] or 'N/A')
    
    st.markdown("---")
    
    # Edit form
    st.subheader("📝 Edit Stock Details")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        new_ticker = st.text_input(
            "Stock Ticker",
            value=selected_stock['ticker'],
            placeholder="e.g., AAPL, GOOGL, MSFT",
            help="Update the stock ticker symbol"
        ).upper()
    
    with col2:
        new_shares = st.number_input(
            "Number of Shares",
            min_value=0.0,
            step=1.0,
            value=float(selected_stock['shares']),
            help="Update the number of shares"
        )
    
    # Purchase details
    col1, col2 = st.columns([2, 1])
    
    with col1:
        new_purchase_date = st.date_input(
            "Purchase Date",
            value=datetime.strptime(selected_stock['purchase_date'], "%Y-%m-%d").date(),
            max_value=datetime.now().date(),
            help="Update the purchase date"
        )
    
    with col2:
        new_purchase_price = st.number_input(
            "Purchase Price per Share",
            min_value=0.0,
            step=0.01,
            value=float(selected_stock['purchase_price']),
            help="Update the purchase price per share"
        )
    
    # Optional: Company name
    new_company_name = st.text_input(
        "Company Name (Optional)",
        value=selected_stock['company_name'] or '',
        placeholder="Company name",
        help="Update the company name"
    )
    
    # Update button
    if st.button("Update Stock", type="primary"):
        if new_ticker and new_shares > 0 and new_purchase_price > 0:
            try:
                # Update in database
                success = db.update_stock(
                    stock_id=selected_stock_id,
                    ticker=new_ticker,
                    shares=new_shares,
                    purchase_price=new_purchase_price,
                    purchase_date=new_purchase_date.strftime("%Y-%m-%d"),
                    company_name=new_company_name if new_company_name else None
                )
                
                if success:
                    st.success(f"✅ Successfully updated {new_ticker}!")
                    
                    # Show changes summary
                    changes = []
                    if new_ticker != selected_stock['ticker']:
                        changes.append(f"Ticker: {selected_stock['ticker']} → {new_ticker}")
                    if new_shares != selected_stock['shares']:
                        changes.append(f"Shares: {selected_stock['shares']} → {new_shares}")
                    if new_purchase_price != selected_stock['purchase_price']:
                        changes.append(f"Price: {selected_stock['purchase_price']:.2f} → {new_purchase_price:.2f}")
                    if new_purchase_date.strftime("%Y-%m-%d") != selected_stock['purchase_date']:
                        changes.append(f"Date: {selected_stock['purchase_date']} → {new_purchase_date.strftime('%Y-%m-%d')}")
                    if new_company_name != selected_stock['company_name']:
                        changes.append(f"Company: {selected_stock['company_name'] or 'None'} → {new_company_name or 'None'}")
                    
                    if changes:
                        st.info("Changes made:")
                        for change in changes:
                            st.write(f"• {change}")
                    
                    # Get current stock info for updated P/L
                    try:
                        stock_ticker = yf.Ticker(new_ticker)
                        info = stock_ticker.info
                        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                        if current_price is None:
                            hist = stock_ticker.history(period="1d")
                            if not hist.empty:
                                current_price = hist['Close'].iloc[-1]
                            else:
                                current_price = new_purchase_price
                        
                        current_total_value = current_price * new_shares
                        purchase_total_value = new_purchase_price * new_shares
                        profit_loss = current_total_value - purchase_total_value
                        profit_loss_percent = (profit_loss / purchase_total_value) * 100 if purchase_total_value > 0 else 0
                        
                        profit_emoji = "🟢" if profit_loss >= 0 else "🔴"
                        st.info(f"{profit_emoji} Updated P/L: {profit_loss:,.2f} ({profit_loss_percent:+.2f}%)")
                        
                    except Exception as e:
                        st.warning(f"Could not fetch current price for {new_ticker}: {str(e)}")
                else:
                    st.error("❌ Failed to update stock. Please try again.")
                    
            except Exception as e:
                st.error(f"Error updating stock: {str(e)}")
        else:
            st.warning("Please enter valid ticker, shares, and purchase price.")
    
    # Delete option (already available in Sell Stock page, but adding here for convenience)
    st.markdown("---")
    st.subheader("🗑️ Delete Stock")
    
    if st.checkbox("Show delete option"):
        st.warning("⚠️ This will completely remove this stock from your portfolio without recording a sale.")
        if st.button(f"Delete {selected_stock['ticker']} from Portfolio", type="secondary"):
            if st.session_state.get('confirm_delete_edit', False):
                if db.delete_stock(selected_stock_id):
                    st.success(f"✅ Successfully deleted {selected_stock['ticker']} from portfolio!")
                    st.session_state.confirm_delete_edit = False
                    st.rerun()
                else:
                    st.error("❌ Failed to delete stock from portfolio.")
            else:
                st.session_state.confirm_delete_edit = True
                st.warning("⚠️ Are you sure? Click again to confirm deleting this stock.")

# Sell Stock Page
elif page == "Sell Stock":
    st.header("💰 Sell Stock from Portfolio")
    
    portfolio = db.get_portfolio()
    if not portfolio:
        st.warning("⚠️ No stocks in portfolio to sell. Add stocks first.")
        st.stop()
    
    # Select stock to sell
    stock_options = [(f"{stock['ticker']} - {stock['shares']} shares @ {stock['purchase_price']:.2f}", stock['id']) for stock in portfolio]
    selected_stock_id = st.selectbox("Select Stock to Sell", [sid for _, sid in stock_options], 
                                    format_func=lambda x: next(t for t, sid in stock_options if sid == x))
    
    selected_stock = next(stock for stock in portfolio if stock['id'] == selected_stock_id)
    
    # Display stock details
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Available Shares", f"{selected_stock['shares']:,.0f}")
    with col2:
        st.metric("Purchase Price", f"{selected_stock['purchase_price']:.2f}")
    with col3:
        # Get current price
        try:
            stock_ticker = yf.Ticker(selected_stock['ticker'])
            info = stock_ticker.info
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            if current_price is None:
                hist = stock_ticker.history(period="1d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                else:
                    current_price = selected_stock['purchase_price']
            st.metric("Current Price", f"{current_price:.2f}")
        except:
            st.metric("Current Price", f"{selected_stock['purchase_price']:.2f}")
    
    st.markdown("---")
    
    # Sale details
    col1, col2 = st.columns([2, 1])
    
    with col1:
        shares_to_sell = st.number_input(
            "Shares to Sell",
            min_value=0.0,
            max_value=float(selected_stock['shares']),
            step=1.0,
            value=float(selected_stock['shares']),
            help=f"Number of shares to sell (max: {selected_stock['shares']})"
        )
    
    with col2:
        sell_price = st.number_input(
            "Sell Price per Share",
            min_value=0.0,
            step=0.01,
            value=current_price if 'current_price' in locals() else float(selected_stock['purchase_price']),
            help="Price you're selling each share for"
        )
    
    # Additional details
    col1, col2 = st.columns([2, 1])
    
    with col1:
        sell_date = st.date_input(
            "Sell Date",
            value=datetime.now().date(),
            max_value=datetime.now().date(),
            help="When did you sell these shares?"
        )
    
    with col2:
        tax_fee = st.number_input(
            "Tax / Fee",
            min_value=0.0,
            step=0.01,
            value=0.0,
            help="Any taxes or transaction fees"
        )
    
    # Calculate profit preview
    if shares_to_sell > 0:
        purchase_cost = shares_to_sell * selected_stock['purchase_price']
        sell_revenue = shares_to_sell * sell_price
        gross_profit = sell_revenue - purchase_cost
        real_profit = gross_profit - tax_fee
        
        st.markdown("### 💹 Profit Calculation")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Purchase Cost", f"{purchase_cost:,.2f}")
        with col2:
            st.metric("Sell Revenue", f"{sell_revenue:,.2f}")
        with col3:
            profit_color = "normal" if gross_profit >= 0 else "inverse"
            st.metric("Gross Profit", f"{gross_profit:,.2f}", delta_color=profit_color)
        with col4:
            real_profit_color = "normal" if real_profit >= 0 else "inverse"
            st.metric("Real Profit", f"{real_profit:.2f}", delta_color=real_profit_color)
    
    # Delete stock option
    st.markdown("---")
    st.subheader("🗑️ Delete Stock Record")
    
    if st.checkbox("Show delete option"):
        st.warning("⚠️ This will completely remove this stock from your portfolio without recording a sale.")
        if st.button(f"Delete {selected_stock['ticker']} from Portfolio", type="secondary"):
            if st.session_state.get('confirm_delete', False):
                if db.delete_stock(selected_stock_id):
                    st.success(f"✅ Successfully deleted {selected_stock['ticker']} from portfolio!")
                    st.session_state.confirm_delete = False
                    st.rerun()
                else:
                    st.error("❌ Failed to delete stock from portfolio.")
            else:
                st.session_state.confirm_delete = True
                st.warning("⚠️ Are you sure? Click again to confirm deleting this stock.")
    
    # Sell button
    if shares_to_sell > 0 and sell_price > 0:
        if st.button("Sell Shares", type="primary"):
            success, message = db.sell_stock(
                portfolio_stock_id=selected_stock_id,
                shares_sold=shares_to_sell,
                sell_price=sell_price,
                sell_date=sell_date.strftime("%Y-%m-%d"),
                tax_fee=tax_fee
            )
            
            if success:
                st.success(f"✅ {message}")
                
                # Show profit/loss summary
                if real_profit >= 0:
                    st.info(f"🟢 Realized Profit: {real_profit:.2f}")
                else:
                    st.warning(f"🔴 Realized Loss: {abs(real_profit):.2f}")
                
                # Show remaining shares if any
                remaining_shares = selected_stock['shares'] - shares_to_sell
                if remaining_shares > 0:
                    st.info(f"📊 Remaining shares: {remaining_shares:.0f}")
                else:
                    st.info("📊 All shares sold - stock removed from portfolio")
                    
                # Refresh the page after a short delay
                st.rerun()
            else:
                st.error(f"❌ {message}")
    else:
        st.warning("Please enter valid sell details.")

# Sales History Page
elif page == "Sales History":
    st.header("📜 Sales History & Realized Profits")
    
    sales_history = db.get_sales_history()
    
    if sales_history:
        # Calculate total realized profits
        total_realized = db.get_total_realized_profits()
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Sales", len(sales_history))
        with col2:
            total_shares_sold = sum(sale['shares_sold'] for sale in sales_history)
            st.metric("Total Shares Sold", f"{total_shares_sold:,.0f}")
        with col3:
            profit_color = "normal" if total_realized >= 0 else "inverse"
            st.metric("Total Realized P/L", f"{total_realized:,.2f}", delta_color=profit_color)
        
        # Sales history table
        st.subheader("📊 Sales Transactions")
        
        sales_df = pd.DataFrame(sales_history)
        
        # Format for display
        display_df = sales_df[[
            'ticker', 'company_name', 'shares_sold', 'purchase_price', 'sell_price',
            'sell_date', 'tax_fee', 'real_profit', 'created_at'
        ]].copy()
        
        # Calculate additional columns
        display_df['total_purchase'] = display_df['shares_sold'] * display_df['purchase_price']
        display_df['total_sell'] = display_df['shares_sold'] * display_df['sell_price']
        display_df['profit_percent'] = (display_df['real_profit'] / display_df['total_purchase']) * 100
        
        # Format columns
        display_df['shares_sold'] = display_df['shares_sold'].apply(lambda x: f"{x:,.0f}")
        display_df['purchase_price'] = display_df['purchase_price'].apply(lambda x: f"{x:.2f}")
        display_df['sell_price'] = display_df['sell_price'].apply(lambda x: f"{x:.2f}")
        display_df['total_purchase'] = display_df['total_purchase'].apply(lambda x: f"{x:,.2f}")
        display_df['total_sell'] = display_df['total_sell'].apply(lambda x: f"{x:,.2f}")
        display_df['tax_fee'] = display_df['tax_fee'].apply(lambda x: f"{x:.2f}")
        display_df['real_profit'] = display_df['real_profit'].apply(lambda x: f"{x:,.2f}")
        display_df['profit_percent'] = display_df['profit_percent'].apply(lambda x: f"{x:+.2f}%")
        display_df['sell_date'] = pd.to_datetime(display_df['sell_date']).dt.strftime('%Y-%m-%d')
        
        display_df.columns = [
            'Ticker', 'Company', 'Shares Sold', 'Purchase Price', 'Sell Price',
            'Sell Date', 'Tax/Fee', 'Real Profit', 'Created At',
            'Total Purchase', 'Total Sell', 'Profit %'
        ]
        
        # Reorder columns
        display_df = display_df[[
            'Ticker', 'Company', 'Shares Sold', 'Purchase Price', 'Sell Price',
            'Total Purchase', 'Total Sell', 'Tax/Fee', 'Real Profit', 'Profit %',
            'Sell Date', 'Created At'
        ]]
        
        # Color code profit columns
        def color_profit(val):
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
        
        styled_df = display_df.style.map(color_profit, subset=['Real Profit'])
        styled_df = styled_df.map(color_percent, subset=['Profit %'])
        
        st.dataframe(styled_df, width='stretch')
        
        # Edit/Delete sales transaction section
        st.markdown("---")
        st.subheader("✏️ Edit Sales Transaction")
        
        # Select sales transaction to edit
        sale_options = [(f"{sale['ticker']} - {sale['shares_sold']} shares @ {sale['sell_price']:.2f} on {sale['sell_date']}", sale['id']) for sale in sales_history]
        selected_sale_id = st.selectbox("Select Sales Transaction to Edit", [sid for _, sid in sale_options], 
                                       format_func=lambda x: next(t for t, sid in sale_options if sid == x))
        
        selected_sale = next(sale for sale in sales_history if sale['id'] == selected_sale_id)
        
        # Display current sale info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Ticker", selected_sale['ticker'])
        with col2:
            st.metric("Shares Sold", f"{selected_sale['shares_sold']:,.0f}")
        with col3:
            st.metric("Sell Price", f"{selected_sale['sell_price']:.2f}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Sell Date", selected_sale['sell_date'])
        with col2:
            st.metric("Tax/Fee", f"{selected_sale['tax_fee']:.2f}")
        with col3:
            profit_color = "normal" if selected_sale['real_profit'] >= 0 else "inverse"
            st.metric("Real Profit", f"{selected_sale['real_profit']:.2f}", delta_color=profit_color)
        
        st.markdown("---")
        
        # Edit form
        col1, col2 = st.columns([2, 1])
        
        with col1:
            new_shares_sold = st.number_input(
                "Shares Sold",
                min_value=0.0,
                step=1.0,
                value=float(selected_sale['shares_sold']),
                help="Update the number of shares sold"
            )
        
        with col2:
            new_sell_price = st.number_input(
                "Sell Price per Share",
                min_value=0.0,
                step=0.01,
                value=float(selected_sale['sell_price']),
                help="Update the sell price per share"
            )
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            new_sell_date = st.date_input(
                "Sell Date",
                value=datetime.strptime(selected_sale['sell_date'], "%Y-%m-%d").date(),
                max_value=datetime.now().date(),
                help="Update the sell date"
            )
        
        with col2:
            new_tax_fee = st.number_input(
                "Tax / Fee",
                min_value=0.0,
                step=0.01,
                value=float(selected_sale['tax_fee']),
                help="Update any taxes or transaction fees"
            )
        
        # Calculate preview
        if new_shares_sold > 0 and new_sell_price > 0:
            new_purchase_cost = new_shares_sold * selected_sale['purchase_price']
            new_sell_revenue = new_shares_sold * new_sell_price
            new_gross_profit = new_sell_revenue - new_purchase_cost
            new_real_profit = new_gross_profit - new_tax_fee
            
            st.markdown("### 💹 Updated Profit Calculation")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Purchase Cost", f"{new_purchase_cost:,.2f}")
            with col2:
                st.metric("Sell Revenue", f"{new_sell_revenue:,.2f}")
            with col3:
                profit_color = "normal" if new_gross_profit >= 0 else "inverse"
                st.metric("Gross Profit", f"{new_gross_profit:,.2f}", delta_color=profit_color)
            with col4:
                real_profit_color = "normal" if new_real_profit >= 0 else "inverse"
                st.metric("Real Profit", f"{new_real_profit:,.2f}", delta_color=real_profit_color)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Update Sales Transaction", type="primary"):
                if new_shares_sold > 0 and new_sell_price > 0:
                    success, message = db.update_sales_transaction(
                        sale_id=selected_sale_id,
                        shares_sold=new_shares_sold,
                        sell_price=new_sell_price,
                        sell_date=new_sell_date.strftime("%Y-%m-%d"),
                        tax_fee=new_tax_fee
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.warning("Please enter valid shares sold and sell price.")
        
        with col2:
            if st.checkbox("Show delete option"):
                st.warning("⚠️ This will permanently delete this sales transaction.")
                if st.button("Delete Sales Transaction", type="secondary"):
                    if st.session_state.get('confirm_delete_sale', False):
                        success, message = db.delete_sales_transaction(selected_sale_id)
                        if success:
                            st.success(f"✅ {message}")
                            st.session_state.confirm_delete_sale = False
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.session_state.confirm_delete_sale = True
                        st.warning("⚠️ Are you sure? Click again to confirm deleting this sales transaction.")
        
        # Export sales history
        csv_data = display_df.to_csv(index=False)
        st.download_button(
            label="📄 Export Sales History to CSV",
            data=csv_data,
            file_name=f"sales_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
    else:
        st.info("📝 No sales recorded yet. Go to 'Sell Stock' to record your first sale.")

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

# Watchlist Page
elif page == "Watchlist":
    st.header("👁️ Stock Watchlist")
    
    watchlist = db.get_watchlist()
    
    if watchlist:
        enriched_watchlist = []
        
        for stock in watchlist:
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
                        current_price = 0.0
                
                # Calculate price differences
                buy_diff = None
                sell_diff = None
                buy_diff_pct = None
                sell_diff_pct = None
                
                if stock['target_buy_price']:
                    buy_diff = current_price - stock['target_buy_price']
                    buy_diff_pct = (buy_diff / stock['target_buy_price']) * 100 if stock['target_buy_price'] > 0 else 0
                
                if stock['target_sell_price']:
                    sell_diff = current_price - stock['target_sell_price']
                    sell_diff_pct = (sell_diff / stock['target_sell_price']) * 100 if stock['target_sell_price'] > 0 else 0
                
                enriched_stock = {
                    'id': stock['id'],
                    'ticker': stock['ticker'],
                    'company_name': info.get('shortName', stock['ticker']),
                    'current_price': current_price,
                    'target_buy_price': stock['target_buy_price'],
                    'target_sell_price': stock['target_sell_price'],
                    'buy_diff': buy_diff,
                    'buy_diff_pct': buy_diff_pct,
                    'sell_diff': sell_diff,
                    'sell_diff_pct': sell_diff_pct,
                    'notes': stock['notes'],
                    'status': stock['status'],
                    'created_at': stock['created_at'],
                    'updated_at': stock['updated_at']
                }
                
                enriched_watchlist.append(enriched_stock)
                
            except Exception as e:
                st.error(f"Error fetching data for {stock['ticker']}: {str(e)}")
                continue
        
        # Summary metrics
        buy_alerts = sum(1 for stock in enriched_watchlist if stock['buy_diff'] is not None and stock['buy_diff'] <= 0)
        sell_alerts = sum(1 for stock in enriched_watchlist if stock['sell_diff'] is not None and stock['sell_diff'] >= 0)
        near_buy = sum(1 for stock in enriched_watchlist if stock['buy_diff_pct'] is not None and -5 <= stock['buy_diff_pct'] <= 10)
        near_sell = sum(1 for stock in enriched_watchlist if stock['sell_diff_pct'] is not None and -10 <= stock['sell_diff_pct'] <= 5)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total Watched", len(enriched_watchlist))
        with col2:
            st.metric("🟢 Buy Alerts", buy_alerts, delta=f"{buy_alerts} at/below target")
        with col3:
            st.metric("🔴 Sell Alerts", sell_alerts, delta=f"{sell_alerts} at/above target")
        with col4:
            st.metric("👀 Near Target", near_buy + near_sell, delta=f"{near_buy} buy, {near_sell} sell")
        
        # Watchlist table
        st.subheader("📋 Watchlist Details")
        
        for stock in enriched_watchlist:
            # Determine status color and alerts
            status_color = "⚪"
            alert_info = []
            
            if stock['buy_diff'] is not None and stock['buy_diff'] <= 0:
                status_color = "🟢"
                alert_info.append("BUY TARGET REACHED!")
            elif stock['buy_diff_pct'] is not None and -5 <= stock['buy_diff_pct'] <= 10:
                alert_info.append("Near buy target")
            
            if stock['sell_diff'] is not None and stock['sell_diff'] >= 0:
                status_color = "🔴"
                alert_info.append("SELL TARGET REACHED!")
            elif stock['sell_diff_pct'] is not None and -10 <= stock['sell_diff_pct'] <= 5:
                alert_info.append("Near sell target")
            
            with st.expander(f"{status_color} {stock['ticker']} - ${stock['current_price']:.2f}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Company:** {stock['company_name']}")
                    st.write(f"**Status:** {stock['status']}")
                    
            if stock['target_buy_price']:
                buy_color = "inverse" if stock['buy_diff'] <= 0 else "normal" if -5 <= stock['buy_diff_pct'] <= 10 else "off"
                st.metric(
                    "Buy Target", 
                    f"${stock['target_buy_price']:.2f}", 
                    delta=f"{stock['buy_diff_pct']:+.2f}%" if stock['buy_diff_pct'] else None,
                    delta_color=buy_color
                )
            
            if stock['target_sell_price']:
                sell_color = "inverse" if stock['sell_diff'] >= 0 else "normal" if -10 <= stock['sell_diff_pct'] <= 5 else "off"
                st.metric(
                    "Sell Target", 
                    f"${stock['target_sell_price']:.2f}", 
                    delta=f"{stock['sell_diff_pct']:+.2f}%" if stock['sell_diff_pct'] else None,
                    delta_color=sell_color
                )
                
                with col2:
                    if alert_info:
                        for alert in alert_info:
                            if "REACHED" in alert:
                                st.success(alert)
                            else:
                                st.info(alert)
                    
                    if stock['notes']:
                        st.write(f"**Notes:** {stock['notes']}")
                    
                    st.write(f"**Added:** {stock['created_at'][:10]}")
        
        # Export watchlist
        csv_data = db.export_watchlist_to_csv()
        if csv_data:
            st.download_button(
                label="📄 Export Watchlist to CSV",
                data=csv_data,
                file_name=f"watchlist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        # Clear watchlist button
        if st.button("Clear Entire Watchlist", type="secondary"):
            if st.session_state.get('confirm_clear_watchlist', False):
                db.clear_watchlist()
                st.success("Watchlist cleared successfully!")
                st.session_state.confirm_clear_watchlist = False
                st.rerun()
            else:
                st.session_state.confirm_clear_watchlist = True
                st.warning("⚠️ Are you sure? Click again to confirm clearing the entire watchlist.")
        
    else:
        st.info("📝 No stocks in your watchlist yet. Go to 'Add to Watchlist' to get started!")

# Add to Watchlist Page
elif page == "Add to Watchlist":
    st.header("➕ Add Stock to Watchlist")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        ticker = st.text_input(
            "Stock Ticker",
            placeholder="e.g., AAPL, GOOGL, MSFT",
            help="Enter the stock ticker symbol to watch"
        ).upper()
    
    # Target prices
    col1, col2 = st.columns(2)
    
    with col1:
        target_buy_price = st.number_input(
            "Target Buy Price",
            min_value=0.0,
            step=0.01,
            value=0.0,
            help="Price at which you want to buy this stock (optional)"
        )
    
    with col2:
        target_sell_price = st.number_input(
            "Target Sell Price",
            min_value=0.0,
            step=0.01,
            value=0.0,
            help="Price at which you want to sell this stock (optional)"
        )
    
    # Notes
    notes = st.text_area(
        "Notes",
        placeholder="Add any notes about why you're watching this stock...",
        help="Optional notes about your investment thesis or reasons for watching"
    )
    
    # Preview stock info
    if ticker:
        try:
            with st.spinner("Fetching stock information..."):
                stock = yf.Ticker(ticker)
                info = stock.info
                current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                
                if current_price is None:
                    hist = stock.history(period="1d")
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                    else:
                        st.error("Could not fetch current price for this ticker.")
                        current_price = 0.0
                
                st.subheader(f"📊 {ticker} - {info.get('shortName', ticker)}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Current Price", f"${current_price:.2f}")
                with col2:
                    if target_buy_price > 0:
                        buy_diff = current_price - target_buy_price
                        buy_diff_pct = (buy_diff / target_buy_price) * 100 if target_buy_price > 0 else 0
                        color = "normal" if buy_diff > 0 else "inverse"
                        st.metric("vs Buy Target", f"${target_buy_price:.2f}", f"{buy_diff_pct:+.2f}%", delta_color=color)
                with col3:
                    if target_sell_price > 0:
                        sell_diff = current_price - target_sell_price
                        sell_diff_pct = (sell_diff / target_sell_price) * 100 if target_sell_price > 0 else 0
                        color = "normal" if sell_diff < 0 else "inverse"
                        st.metric("vs Sell Target", f"${target_sell_price:.2f}", f"{sell_diff_pct:+.2f}%", delta_color=color)
                
        except Exception as e:
            st.error(f"Error fetching data for {ticker}: {str(e)}")
            st.info("Please check if the ticker symbol is correct and try again.")
    
    # Add to watchlist button
    if st.button("Add to Watchlist", type="primary"):
        if ticker:
            try:
                watchlist_id = db.add_to_watchlist(
                    ticker=ticker,
                    target_buy_price=target_buy_price if target_buy_price > 0 else None,
                    target_sell_price=target_sell_price if target_sell_price > 0 else None,
                    notes=notes if notes else None
                )
                
                st.success(f"✅ Successfully added {ticker} to watchlist!")
                
                # Show target price status if targets are set
                if target_buy_price > 0 or target_sell_price > 0:
                    if current_price and target_buy_price > 0:
                        buy_status = "🟢 BUY TARGET REACHED!" if current_price <= target_buy_price else f"👀 Waiting for price to drop to ${target_buy_price:.2f}"
                        st.info(buy_status)
                    
                    if current_price and target_sell_price > 0:
                        sell_status = "🔴 SELL TARGET REACHED!" if current_price >= target_sell_price else f"👀 Waiting for price to rise to ${target_sell_price:.2f}"
                        st.info(sell_status)
                else:
                    st.info("📝 Stock added to watchlist. You can set target prices later or get recommendations!")
                
            except Exception as e:
                st.error(f"Error adding to watchlist: {str(e)}")
        else:
            st.warning("Please enter a valid ticker symbol.")

# Edit Watchlist Page
elif page == "Edit Watchlist":
    st.header("✏️ Edit Watchlist")
    
    watchlist = db.get_watchlist()
    if not watchlist:
        st.warning("⚠️ No stocks in watchlist to edit. Add stocks first.")
        st.stop()
    
    # Select stock to edit
    stock_options = [(f"{stock['ticker']} - Buy: ${stock['target_buy_price'] or 'N/A'}, Sell: ${stock['target_sell_price'] or 'N/A'}", stock['ticker']) for stock in watchlist]
    selected_ticker = st.selectbox("Select Stock to Edit", [ticker for _, ticker in stock_options], 
                                   format_func=lambda x: next(t for t, sid in stock_options if sid == x))
    
    selected_stock = next(stock for stock in watchlist if stock['ticker'] == selected_ticker)
    
    # Display current stock info
    st.subheader(f"📊 Current Information for {selected_stock['ticker']}")
    
    try:
        stock_ticker = yf.Ticker(selected_stock['ticker'])
        info = stock_ticker.info
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        
        if current_price is None:
            hist = stock_ticker.history(period="1d")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
            else:
                current_price = 0.0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Price", f"${current_price:.2f}")
        with col2:
            if selected_stock['target_buy_price']:
                buy_diff = current_price - selected_stock['target_buy_price']
                buy_diff_pct = (buy_diff / selected_stock['target_buy_price']) * 100
                color = "normal" if buy_diff > 0 else "inverse"
                st.metric("Buy Target", f"${selected_stock['target_buy_price']:.2f}", f"{buy_diff_pct:+.2f}%", delta_color=color)
        with col3:
            if selected_stock['target_sell_price']:
                sell_diff = current_price - selected_stock['target_sell_price']
                sell_diff_pct = (sell_diff / selected_stock['target_sell_price']) * 100
                color = "normal" if sell_diff < 0 else "inverse"
                st.metric("Sell Target", f"${selected_stock['target_sell_price']:.2f}", f"{sell_diff_pct:+.2f}%", delta_color=color)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Status", selected_stock['status'])
        with col2:
            st.metric("Added", selected_stock['created_at'][:10])
        
    except Exception as e:
        st.warning(f"Could not fetch current price: {str(e)}")
    
    if selected_stock['notes']:
        st.info(f"**Notes:** {selected_stock['notes']}")
    
    st.markdown("---")
    
    # Edit form
    st.subheader("📝 Edit Watchlist Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_target_buy_price = st.number_input(
            "Target Buy Price",
            min_value=0.0,
            step=0.01,
            value=float(selected_stock['target_buy_price']) if selected_stock['target_buy_price'] else 0.0,
            help="Update the target buy price (0 to remove)"
        )
    
    with col2:
        new_target_sell_price = st.number_input(
            "Target Sell Price",
            min_value=0.0,
            step=0.01,
            value=float(selected_stock['target_sell_price']) if selected_stock['target_sell_price'] else 0.0,
            help="Update the target sell price (0 to remove)"
        )
    
    new_status = st.selectbox(
        "Status",
        ["watching", "ready_to_buy", "ready_to_sell", "paused"],
        index=["watching", "ready_to_buy", "ready_to_sell", "paused"].index(selected_stock['status']),
        help="Update the watch status"
    )
    
    new_notes = st.text_area(
        "Notes",
        value=selected_stock['notes'] or '',
        placeholder="Update your notes about this stock...",
        help="Update your investment thesis or reasons for watching"
    )
    
    # Update button
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("Update Watchlist Stock", type="primary"):
            success = db.update_watchlist_stock(
                ticker=selected_stock['ticker'],
                target_buy_price=new_target_buy_price if new_target_buy_price > 0 else None,
                target_sell_price=new_target_sell_price if new_target_sell_price > 0 else None,
                status=new_status,
                notes=new_notes if new_notes else None
            )
            
            if success:
                st.success(f"✅ Successfully updated {selected_stock['ticker']}!")
                
                # Show changes summary
                changes = []
                if new_target_buy_price != selected_stock['target_buy_price']:
                    changes.append(f"Buy Target: ${selected_stock['target_buy_price'] or 'N/A'} → ${new_target_buy_price or 'N/A'}")
                if new_target_sell_price != selected_stock['target_sell_price']:
                    changes.append(f"Sell Target: ${selected_stock['target_sell_price'] or 'N/A'} → ${new_target_sell_price or 'N/A'}")
                if new_status != selected_stock['status']:
                    changes.append(f"Status: {selected_stock['status']} → {new_status}")
                
                if changes:
                    st.info("Changes made:")
                    for change in changes:
                        st.write(f"• {change}")
            else:
                st.error("❌ Failed to update watchlist stock. Please try again.")
    
    with col2:
        if st.button(f"Remove {selected_stock['ticker']}", type="secondary"):
            if st.session_state.get('confirm_remove_watchlist', False):
                if db.remove_from_watchlist(selected_stock['ticker']):
                    st.success(f"✅ Successfully removed {selected_stock['ticker']} from watchlist!")
                    st.session_state.confirm_remove_watchlist = False
                    st.rerun()
                else:
                    st.error("❌ Failed to remove stock from watchlist.")
            else:
                st.session_state.confirm_remove_watchlist = True
                st.warning("⚠️ Are you sure? Click again to confirm removing this stock from watchlist.")
    
    # AI Recommendation Section
    st.markdown("---")
    st.subheader(f"🤖 AI Recommendation for {selected_stock['ticker']}")
    
    if st.button("Get AI Recommendation", type="primary"):
        with st.spinner("🔄 Analyzing stock with AI..."):
            try:
                # Get recommendation using the watchlist strategy
                recommendation = strategy.get_watchlist_recommendation(
                    ticker=selected_stock['ticker'],
                    current_price=current_price if 'current_price' in locals() else 0.0,
                    target_buy_price=selected_stock['target_buy_price'],
                    target_sell_price=selected_stock['target_sell_price'],
                    notes=selected_stock['notes']
                )
                
                # Display recommendation
                action_color = {
                    'BUY': '🟢',
                    'SELL': '🔴', 
                    'WATCH': '👀'
                }.get(recommendation['action'], '⚪')
                
                st.markdown(f"### {action_color} Recommendation: {recommendation['action']}")
                st.metric("Confidence", f"{recommendation['confidence']:.1%}")
                st.write(f"**Reason:** {recommendation['reason']}")
                st.write(f"**Strategy:** {recommendation['strategy'].title()}")
                
                # Display suggested prices if available
                ai_suggested_buy = recommendation.get('suggested_buy_price')
                ai_suggested_sell = recommendation.get('suggested_sell_price')
                
                if ai_suggested_buy:
                    st.write(f"💡 **AI Suggested Buy Price:** ${ai_suggested_buy:.2f}")
                
                if ai_suggested_sell:
                    st.write(f"💰 **AI Suggested Sell Price:** ${ai_suggested_sell:.2f}")
                
                # AI Suggested Target Prices Section
                if ai_suggested_buy or ai_suggested_sell:
                    st.subheader("🤖 AI-Recommended Target Prices")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if ai_suggested_buy:
                            st.metric("AI Buy Target", f"${ai_suggested_buy:.2f}")
                            if st.button("🚀 Apply AI Buy Target", key=f"apply_ai_buy_{selected_stock['ticker']}", type="primary"):
                                success = db.update_watchlist_stock(
                                    ticker=selected_stock['ticker'],
                                    target_buy_price=ai_suggested_buy,
                                    status="ready_to_buy"
                                )
                                if success:
                                    st.success("✅ AI-recommended buy target applied successfully!")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to apply AI buy target")
                        else:
                            st.write("*No AI buy suggestion available*")
                    
                    with col2:
                        if ai_suggested_sell:
                            st.metric("AI Sell Target", f"${ai_suggested_sell:.2f}")
                            if st.button("🚀 Apply AI Sell Target", key=f"apply_ai_sell_{selected_stock['ticker']}", type="primary"):
                                success = db.update_watchlist_stock(
                                    ticker=selected_stock['ticker'],
                                    target_sell_price=ai_suggested_sell,
                                    status="ready_to_sell"
                                )
                                if success:
                                    st.success("✅ AI-recommended sell target applied successfully!")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to apply AI sell target")
                        else:
                            st.write("*No AI sell suggestion available*")
                    
                    # Apply both button if both are available
                    if ai_suggested_buy and ai_suggested_sell:
                        st.markdown("---")
                        if st.button("🚀 Apply Both AI Target Prices", key=f"apply_ai_targets_{selected_stock['ticker']}", type="primary"):
                            success = db.update_watchlist_stock(
                                ticker=selected_stock['ticker'],
                                target_buy_price=ai_suggested_buy,
                                target_sell_price=ai_suggested_sell,
                                status="watching"
                            )
                            if success:
                                st.success("✅ Both AI-recommended target prices applied successfully!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to apply AI target prices")
                
                # Fallback suggested target prices based on recommendation action
                if recommendation['action'] in ['BUY', 'SELL']:
                    st.subheader("💡 Strategy-Based Target Prices")
                    
                    if recommendation['action'] == 'BUY':
                        # Suggest buy target slightly below current price
                        suggested_buy = current_price * 0.98  # 2% below current price
                        suggested_sell = current_price * 1.15  # 15% above current price
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Strategy Buy Target", f"${suggested_buy:.2f}")
                        with col2:
                            st.metric("Strategy Sell Target", f"${suggested_sell:.2f}")
                        
                        if st.button("💾 Apply Strategy Targets", key=f"apply_strategy_targets_{selected_stock['ticker']}"):
                            success = db.update_watchlist_stock(
                                ticker=selected_stock['ticker'],
                                target_buy_price=suggested_buy,
                                target_sell_price=suggested_sell,
                                status="ready_to_buy"
                            )
                            if success:
                                st.success("✅ Strategy-based targets applied!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to apply strategy targets")
                    
                    elif recommendation['action'] == 'SELL':
                        # Suggest sell target at current price
                        suggested_sell = current_price
                        
                        st.metric("Strategy Sell Target", f"${suggested_sell:.2f}")
                        
                        if st.button("💾 Apply Strategy Sell Target", key=f"apply_strategy_sell_{selected_stock['ticker']}"):
                            success = db.update_watchlist_stock(
                                ticker=selected_stock['ticker'],
                                target_sell_price=suggested_sell,
                                status="ready_to_sell"
                            )
                            if success:
                                st.success("✅ Strategy-based sell target applied!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to apply strategy sell target")
                
                # Log the recommendation
                db.log_recommendation(
                    ticker=selected_stock['ticker'],
                    action=recommendation['action'],
                    reason=recommendation['reason'],
                    confidence=recommendation['confidence'],
                    price=current_price if 'current_price' in locals() else 0.0
                )
                
            except Exception as e:
                st.error(f"Error getting recommendation: {str(e)}")

# Recommendations Page
elif page == "Recommendations":
    st.header("💡 AI Trading Recommendations")
    
    portfolio = db.get_portfolio()
    watchlist = db.get_watchlist()
    
    if not portfolio and not watchlist:
        st.warning("⚠️ No stocks in portfolio or watchlist. Add stocks first to get recommendations.")
        st.stop()
    
    # Get portfolio recommendations
    portfolio_recommendations = []
    watchlist_recommendations = []
    
    with st.spinner("🔄 Analyzing portfolio and watchlist..."):
        if portfolio:
            portfolio_recommendations = strategy.get_all_portfolio_recommendations(portfolio)
        
        if watchlist:
            watchlist_recommendations = strategy.get_watchlist_recommendations(watchlist)
    
    all_recommendations = portfolio_recommendations + watchlist_recommendations
    
    if all_recommendations:
        # Summary dashboard
        portfolio_buy = sum(1 for r in portfolio_recommendations if r['action'] == 'BUY')
        portfolio_sell = sum(1 for r in portfolio_recommendations if r['action'] == 'SELL')
        portfolio_hold = sum(1 for r in portfolio_recommendations if r['action'] == 'HOLD')
        
        watchlist_buy = sum(1 for r in watchlist_recommendations if r['action'] == 'BUY')
        watchlist_sell = sum(1 for r in watchlist_recommendations if r['action'] == 'SELL')
        watchlist_watch = sum(1 for r in watchlist_recommendations if r['action'] == 'WATCH')
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📈 Buy Signals", portfolio_buy + watchlist_buy, delta=f"Portfolio: {portfolio_buy}, Watchlist: {watchlist_buy}")
        with col2:
            st.metric("📉 Sell Signals", portfolio_sell + watchlist_sell, delta=f"Portfolio: {portfolio_sell}, Watchlist: {watchlist_sell}")
        with col3:
            st.metric("⏸️ Hold/Watch", portfolio_hold + watchlist_watch, delta=f"Hold: {portfolio_hold}, Watch: {watchlist_watch}")
        with col4:
            avg_confidence = sum(r['confidence'] for r in all_recommendations) / len(all_recommendations)
            st.metric("🎯 Avg Confidence", f"{avg_confidence:.1%}")
        
        # Portfolio recommendations
        if portfolio_recommendations:
            st.subheader("📋 Portfolio Recommendations")
            
            for rec in portfolio_recommendations:
                stock = rec['stock_data']
                
                # Color coding for action
                action_color = {
                    'BUY': '🟢',
                    'SELL': '🔴', 
                    'HOLD': '🟡'
                }.get(rec['action'], '⚪')
                
                with st.expander(f"{action_color} Portfolio: {stock['ticker']} - {rec['action']} (Confidence: {rec['confidence']:.1%})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Company:** {stock['company_name'] or stock['ticker']}")
                        st.write(f"**Current Price:** {rec['current_price']:.2f}")
                        st.write(f"**Purchase Price:** {stock['purchase_price']:.2f}")
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
        
        # Watchlist recommendations
        if watchlist_recommendations:
            st.subheader("👁️ Watchlist Recommendations")
            
            for rec in watchlist_recommendations:
                watchlist_stock = rec['watchlist_data']
                
                # Color coding for action
                action_color = {
                    'BUY': '🟢',
                    'SELL': '🔴', 
                    'WATCH': '👀'
                }.get(rec['action'], '⚪')
                
                with st.expander(f"{action_color} Watchlist: {watchlist_stock['ticker']} - {rec['action']} (Confidence: {rec['confidence']:.1%})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Current Price:** {rec['current_price']:.2f}")
                        if watchlist_stock['target_buy_price']:
                            st.write(f"**Buy Target:** ${watchlist_stock['target_buy_price']:.2f}")
                        if watchlist_stock['target_sell_price']:
                            st.write(f"**Sell Target:** ${watchlist_stock['target_sell_price']:.2f}")
                        st.write(f"**Status:** {watchlist_stock['status']}")
                        
                        if watchlist_stock['notes']:
                            st.write(f"**Notes:** {watchlist_stock['notes']}")
                    
                    with col2:
                        st.write(f"**Strategy:** {rec['strategy'].title()}")
                        st.write(f"**Reason:** {rec['reason']}")
                        
                        # Quick action buttons if target reached
                        if rec['action'] == 'BUY':
                            if st.button(f"🛒 Quick Buy {watchlist_stock['ticker']}", key=f"buy_{watchlist_stock['ticker']}"):
                                st.info(f"Redirect to buy {watchlist_stock['ticker']} at market price ${rec['current_price']:.2f}")
                        elif rec['action'] == 'SELL':
                            if st.button(f"💰 Quick Sell {watchlist_stock['ticker']}", key=f"sell_{watchlist_stock['ticker']}"):
                                st.info(f"Ready to sell {watchlist_stock['ticker']} at market price ${rec['current_price']:.2f}")
        
        # Recent recommendations history
        st.subheader("📜 Recent Recommendation History")
        recent_recs = db.get_recent_recommendations(30)
        
        if recent_recs:
            rec_df = pd.DataFrame(recent_recs)
            rec_df['created_at'] = pd.to_datetime(rec_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
            
            def color_action(val):
                if val == 'BUY':
                    return 'color: green'
                elif val == 'SELL':
                    return 'color: red'
                elif val == 'WATCH':
                    return 'color: blue'
                else:
                    return 'color: orange'
            
            styled_recs = rec_df.style.map(color_action, subset=['action'])
            st.dataframe(styled_recs, width='stretch')
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
            st.metric("Total Investment", f"{total_investment:,.2f}")
    
    with col2:
        st.subheader("🗄️ Database Operations")
        
        if st.button("📄 Export Portfolio to CSV", type="secondary"):
            csv_data = db.export_portfolio_to_csv()
            if csv_data:
                st.download_button(
                    label="Download Portfolio CSV",
                    data=csv_data,
                    file_name=f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        if st.button("👁️ Export Watchlist to CSV", type="secondary"):
            csv_data = db.export_watchlist_to_csv()
            if csv_data:
                st.download_button(
                    label="Download Watchlist CSV",
                    data=csv_data,
                    file_name=f"watchlist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        if st.button("🗑️ Clear All Data", type="secondary"):
            if st.session_state.get('confirm_clear_all', False):
                db.clear_portfolio()
                db.clear_watchlist()
                st.success("All portfolio and watchlist data cleared!")
                st.session_state.confirm_clear_all = False
                st.rerun()
            else:
                st.session_state.confirm_clear_all = True
                st.warning("⚠️ Are you sure? Click again to confirm clearing all data.")

# Footer
st.markdown("---")
st.markdown("*Data provided by Yahoo Finance. Prices are delayed and may not reflect real-time market data.*")
st.markdown("*Trading recommendations are for educational purposes only. Always consult with a financial advisor before making investment decisions.*")
