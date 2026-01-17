"""
Portfolio Management Pages

All portfolio-related Streamlit pages including:
- Portfolio Overview
- Add Stock
- Edit Portfolio
- Sell Stock
- Sales History
- Portfolio Recommendations
"""

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from src.portfolio.utils import (
    load_portfolio, format_portfolio_for_display, color_profit_loss, 
    color_percent, get_current_stock_price, calculate_stock_metrics,
    display_portfolio_summary_cards
)
from src.database import db
from src.trading_strategy import strategy


def portfolio_overview_page():
    """Display portfolio overview page"""
    st.header("📊 Portfolio Overview")
    
    portfolio = load_portfolio()
    
    if portfolio:
        portfolio_df = pd.DataFrame(portfolio)
        
        # Display summary cards
        display_portfolio_summary_cards(portfolio_df)
        
        # Portfolio details table
        st.header("📈 Portfolio Details & Performance")
        display_df = format_portfolio_for_display(portfolio_df)
        
        # Color code the profit/loss columns
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


def add_stock_page():
    """Display add stock page"""
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
                current_price = get_current_stock_price(ticker)
                if current_price is None:
                    current_price = purchase_price
                
                # Calculate values
                metrics = calculate_stock_metrics(shares, purchase_price, current_price)
                if metrics:
                    profit_loss = metrics['profit_loss']
                    profit_loss_percent = metrics['profit_loss_percent']
                else:
                    profit_loss = 0
                    profit_loss_percent = 0
                
                # Show success message
                profit_emoji = "🟢" if profit_loss >= 0 else "🔴"
                st.success(f"{profit_emoji} Successfully added {shares} shares of {ticker} ({info.get('shortName', ticker)}) to your portfolio!")
                st.info(f"Current P/L: {profit_loss:,.2f} ({profit_loss_percent:+.2f}%)")
                
            except Exception as e:
                st.error(f"Error fetching data for {ticker}: {str(e)}")
                st.info("Please check if the ticker symbol is correct and try again.")
        else:
            st.warning("Please enter all required fields: ticker, shares, and purchase price.")


def edit_portfolio_page():
    """Display edit portfolio page"""
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
                    current_price = get_current_stock_price(new_ticker)
                    if current_price is None:
                        current_price = new_purchase_price
                    
                    metrics = calculate_stock_metrics(new_shares, new_purchase_price, current_price)
                    if metrics:
                        profit_loss = metrics['profit_loss']
                        profit_loss_percent = metrics['profit_loss_percent']
                        
                        profit_emoji = "🟢" if profit_loss >= 0 else "🔴"
                        st.info(f"{profit_emoji} Updated P/L: {profit_loss:,.2f} ({profit_loss_percent:+.2f}%)")
                    
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


def sell_stock_page():
    """Display sell stock page"""
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
        current_price = get_current_stock_price(selected_stock['ticker'])
        if current_price is None:
            current_price = selected_stock['purchase_price']
        st.metric("Current Price", f"{current_price:.2f}")
    
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
            value=current_price,
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


def sales_history_page():
    """Display sales history page"""
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
        display_df['real_profit'] = display_df['real_profit'].apply(lambda x: f"{x:.2f}")
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
        styled_df = display_df.style.map(color_profit_loss, subset=['Real Profit'])
        styled_df = styled_df.map(color_percent, subset=['Profit %'])
        
        st.dataframe(styled_df, width='stretch')
        
        # Edit/Delete sales transaction section
        _sales_transaction_edit_section(sales_history)
        
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


def _sales_transaction_edit_section(sales_history):
    """Helper function for editing sales transactions"""
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


def portfolio_recommendations_page():
    """Display portfolio recommendations page"""
    st.header("💡 Portfolio Trading Recommendations")
    
    portfolio = db.get_portfolio()
    if not portfolio:
        st.warning("⚠️ No stocks in portfolio. Add stocks first to get recommendations.")
        st.stop()
    
    # Get portfolio recommendations
    with st.spinner("🔄 Analyzing portfolio stocks..."):
        portfolio_recommendations = strategy.get_all_portfolio_recommendations(portfolio)
    
    if portfolio_recommendations:
        # Summary dashboard
        portfolio_buy = sum(1 for r in portfolio_recommendations if r['action'] == 'BUY')
        portfolio_sell = sum(1 for r in portfolio_recommendations if r['action'] == 'SELL')
        portfolio_hold = sum(1 for r in portfolio_recommendations if r['action'] == 'HOLD')
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📈 Buy Signals", portfolio_buy, delta="Based on your strategies")
        with col2:
            st.metric("📉 Sell Signals", portfolio_sell, delta="Take profit/stop loss")
        with col3:
            st.metric("⏸️ Hold Signals", portfolio_hold, delta="Monitor position")
        with col4:
            avg_confidence = sum(r['confidence'] for r in portfolio_recommendations) / len(portfolio_recommendations)
            st.metric("🎯 Avg Confidence", f"{avg_confidence:.1%}")
        
        # Portfolio recommendations
        st.subheader("📋 Individual Stock Recommendations")
        
        for rec in portfolio_recommendations:
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
                    profit_color = "🟢" if profit_loss >= 0 else "🔴"
                    st.write(f"**P/L:** {profit_color} {profit_loss:+.2f}%")
                    
                    # Calculate position values
                    current_value = rec['current_price'] * stock['shares']
                    purchase_value = stock['purchase_price'] * stock['shares']
                    st.write(f"**Current Value:** ${current_value:,.2f}")
                    st.write(f"**Purchase Value:** ${purchase_value:,.2f}")
                
                with col2:
                    st.write(f"**Strategy:** {rec['strategy'].title()}")
                    st.write(f"**Reason:** {rec['reason']}")
                    
                    # Strategy settings badge
                    settings = db.get_strategy_settings(stock['ticker'])
                    if settings:
                        st.info(f"⚙️ {settings['strategy_type'].title()} Strategy")
                    
                    # Action-specific insights
                    if rec['action'] == 'SELL':
                        if profit_loss > 0:
                            st.success(f"💰 Profit target reached!")
                        else:
                            st.warning(f"⚠️ Stop loss triggered")
                    elif rec['action'] == 'BUY':
                        st.info("📈 Consider adding to position")
                    else:
                        st.info("👀 Continue monitoring")
        
        # Portfolio-level insights
        st.subheader("📊 Portfolio Insights")
        
        # Calculate portfolio metrics
        total_current_value = sum(rec['current_price'] * rec['stock_data']['shares'] for rec in portfolio_recommendations)
        total_purchase_value = sum(rec['stock_data']['purchase_price'] * rec['stock_data']['shares'] for rec in portfolio_recommendations)
        total_pnl = total_current_value - total_purchase_value
        total_pnl_percent = (total_pnl / total_purchase_value) * 100 if total_purchase_value > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Portfolio Value", f"${total_current_value:,.2f}")
        with col2:
            pnl_color = "normal" if total_pnl >= 0 else "inverse"
            st.metric("Total P/L", f"${total_pnl:,.2f}", f"{total_pnl_percent:+.2f}%", delta_color=pnl_color)
        with col3:
            total_shares = sum(rec['stock_data']['shares'] for rec in portfolio_recommendations)
            st.metric("Total Shares", f"{total_shares:,.0f}")
        with col4:
            avg_stock_performance = total_pnl_percent / len(portfolio_recommendations) if portfolio_recommendations else 0
            st.metric("Avg Stock Performance", f"{avg_stock_performance:+.2f}%")
        
        # Strategy distribution
        strategy_counts = {}
        for rec in portfolio_recommendations:
            strategy_name = rec['strategy']
            strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1
        
        st.subheader("🎯 Strategy Distribution")
        strategy_data = pd.DataFrame(list(strategy_counts.items()), columns=['Strategy', 'Stocks'])
        st.bar_chart(strategy_data.set_index('Strategy'))
        
        # Recent portfolio recommendation history
        st.subheader("📜 Recent Portfolio Recommendations")
        recent_recs = db.get_recent_recommendations(30)
        
        if recent_recs:
            # Filter for portfolio stocks
            portfolio_tickers = [stock['ticker'] for stock in portfolio]
            portfolio_recs = [rec for rec in recent_recs if rec['ticker'] in portfolio_tickers]
            
            if portfolio_recs:
                rec_df = pd.DataFrame(portfolio_recs)
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
                st.info("No recent portfolio recommendations found.")
        else:
            st.info("No previous recommendations found.")
    
    else:
        st.info("No portfolio recommendations available at this time. Try refreshing your portfolio data.")
