"""
Watchlist Management Pages

All watchlist-related Streamlit pages including:
- Watchlist Overview
- Add to Watchlist
- Edit Watchlist
- Import Watchlist from CSV
- Watchlist Recommendations
"""

import streamlit as st
import yfinance as yfinance
import pandas as pd
from datetime import datetime, timedelta
from .utils import (
    load_enriched_watchlist, get_watchlist_summary_metrics, get_stock_info_safe,
    display_watchlist_summary_cards, determine_stock_status, display_target_metrics,
    generate_watchlist_template, validate_csv_structure, standardize_csv_data
)
from src.database import db
from src.trading_strategy import strategy
from src.utils.ui_components import display_alert_box, display_download_button


def watchlist_page():
    """Display watchlist overview page"""
    st.header("👁️ Stock Watchlist")
    
    enriched_watchlist = load_enriched_watchlist()
    
    if enriched_watchlist:
        # Display summary metrics
        display_watchlist_summary_cards(enriched_watchlist)
        
        # Watchlist table
        st.subheader("📋 Watchlist Details")
        
        for stock in enriched_watchlist:
            # Determine status color and alerts
            status_color, alert_info = determine_stock_status(stock)
            
            with st.expander(f"{status_color} {stock['ticker']} - ${stock['current_price']:.2f}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Company:** {stock['company_name']}")
                    st.write(f"**Status:** {stock['status']}")
                    
                    # Display target metrics
                    target_metrics = display_target_metrics(
                        stock['current_price'],
                        stock['target_buy_price'],
                        stock['target_sell_price']
                    )
                    
                    if 'buy_target' in target_metrics:
                        st.metric(
                            "Buy Target", 
                            target_metrics['buy_target']['price'], 
                            delta=target_metrics['buy_target'].get('delta'),
                            delta_color=target_metrics['buy_target']['color']
                        )
                
                    if 'sell_target' in target_metrics:
                        st.metric(
                            "Sell Target", 
                            target_metrics['sell_target']['price'], 
                            delta=target_metrics['sell_target'].get('delta'),
                            delta_color=target_metrics['sell_target']['color']
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
            display_download_button(
                csv_data,
                "watchlist",
                "Export Watchlist to CSV"
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


def add_to_watchlist_page():
    """Display add to watchlist page"""
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
    current_price = None
    if ticker:
        try:
            with st.spinner("Fetching stock information..."):
                stock_info = get_stock_info_safe(ticker)
                if stock_info:
                    current_price = stock_info['current_price']
                
                if current_price:
                    st.subheader(f"📊 {ticker} - {stock_info['company_name']}")
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


def edit_watchlist_page():
    """Display edit watchlist page"""
    st.header("✏️ Edit Watchlist")
    
    watchlist = db.get_watchlist()
    if not watchlist:
        st.warning("⚠️ No stocks in watchlist to edit. Add stocks first.")
        st.stop()
    
    # Select stock to edit
    stock_options = [(f"{stock['ticker']} - Buy: ${stock['target_buy_price'] or 'N/A'}, Sell: ${stock['target_sell_price'] or 'N/A'}", stock['ticker']) for stock in watchlist]
    selected_ticker = st.selectbox("Select Stock to Edit", [ticker for _, ticker in stock_options], 
                                   format_func=lambda x: next(t for t, ticker in stock_options if ticker == x))
    
    selected_stock = next(stock for stock in watchlist if stock['ticker'] == selected_ticker)
    
    # Display current stock info
    st.subheader(f"📊 Current Information for {selected_stock['ticker']}")
    
    current_price = None
    try:
        stock_info = get_stock_info_safe(selected_stock['ticker'])
        if stock_info:
            current_price = stock_info['current_price']
    
        if current_price is None:
            current_price = selected_stock['purchase_price'] if 'purchase_price' in selected_stock else 0.0
        
        # Display current metrics
        target_metrics = display_target_metrics(
            current_price,
            selected_stock['target_buy_price'],
            selected_stock['target_sell_price']
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Price", f"${current_price:.2f}")
        with col2:
            if 'buy_target' in target_metrics:
                st.metric(
                    "Buy Target", 
                    target_metrics['buy_target']['price'], 
                    delta=target_metrics['buy_target'].get('delta'),
                    delta_color=target_metrics['buy_target']['color']
                )
        with col3:
            if 'sell_target' in target_metrics:
                st.metric(
                    "Sell Target", 
                    target_metrics['sell_target']['price'], 
                    delta=target_metrics['sell_target'].get('delta'),
                    delta_color=target_metrics['sell_target']['color']
                )
        
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
                    current_price=current_price if current_price else 0.0,
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
                    st.write(f"💰 **AI Suggested Sell Price:** ${ai_suggested_sell_price:.2f}")
                
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
                    price=current_price if current_price else 0.0
                )
                
            except Exception as e:
                st.error(f"Error getting recommendation: {str(e)}")


def import_watchlist_page():
    """Display import watchlist from CSV page"""
    st.header("📁 Import Watchlist from CSV")
    
    st.markdown("### 📋 CSV Format Requirements")
    st.info("""
    Your CSV file should contain the following columns:
    - **ticker** (required): Stock ticker symbol (e.g., AAPL, GOOGL, MSFT)
    - **target_buy_price** (optional): Target price to buy the stock
    - **target_sell_price** (optional): Target price to sell the stock
    - **notes** (optional): Your notes about the stock
    - **status** (optional): Watch status (watching, ready_to_buy, ready_to_sell, paused)
    """)
    
    # Template download
    st.subheader("📄 Download Template")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        display_download_button(
            generate_watchlist_template(),
            "watchlist_template",
            "Download CSV Template"
        )
    
    st.markdown("---")
    
    # File upload section
    st.subheader("📤 Upload CSV File")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=['csv'],
            help="Upload a CSV file containing watchlist data"
        )
    
    with col2:
        handle_duplicates = st.selectbox(
            "Handle Duplicates",
            ["skip", "update", "replace"],
            index=0,
            help="How to handle tickers already in your watchlist"
        )
        
        validate_tickers = st.checkbox(
            "Validate Tickers",
            value=True,
            help="Check if ticker symbols are valid using Yahoo Finance"
        )
    
    if uploaded_file:
        try:
            # Read and preview the CSV
            df = pd.read_csv(uploaded_file)
            
            st.subheader("👀 CSV Preview")
            st.dataframe(df.head(10))
            
            # Show CSV info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rows", len(df))
            with col2:
                st.metric("Columns", len(df.columns))
            with col3:
                if 'ticker' in df.columns:
                    unique_tickers = df['ticker'].nunique()
                    st.metric("Unique Tickers", unique_tickers)
                else:
                    st.error("❌ Missing 'ticker' column!")
            
            # Validate CSV structure
            is_valid, errors, warnings = validate_csv_structure(df)
            
            if not is_valid:
                st.error(f"❌ {', '.join(errors)}")
                st.stop()
            
            # Check for existing tickers
            if 'ticker' in df.columns:
                existing_watchlist = db.get_watchlist()
                existing_tickers = {stock['ticker'] for stock in existing_watchlist}
                csv_tickers = set(df['ticker'].str.strip().str.upper())
                duplicates = csv_tickers.intersection(existing_tickers)
                
                if duplicates and handle_duplicates != 'replace':
                    st.warning(f"⚠️ {len(duplicates)} tickers already exist in your watchlist:")
                    for ticker in sorted(duplicates):
                        st.write(f"• {ticker}")
                    
                    if handle_duplicates == 'skip':
                        st.info("These tickers will be skipped during import.")
                    elif handle_duplicates == 'update':
                        st.info("These tickers will be updated with new data.")
            
            # Import confirmation
            st.markdown("---")
            st.subheader("🚀 Import Confirmation")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("⚡ Import Watchlist", type="primary", use_container_width=True):
                    with st.spinner("🔄 Importing watchlist..."):
                        # Reset file pointer for reading
                        uploaded_file.seek(0)
                        
                        # Import the data
                        results = db.import_watchlist_from_csv(
                            csv_data=uploaded_file,
                            handle_duplicates=handle_duplicates,
                            validate_tickers=validate_tickers
                        )
                        
                        # Display results
                        st.subheader("📊 Import Results")
                        
                        # Summary metrics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("✅ Successfully Imported", results['success_count'])
                        with col2:
                            st.metric("❌ Errors", results['error_count'])
                        with col3:
                            st.metric("⚠️ Warnings", len(results['warnings']))
                        with col4:
                            if handle_duplicates == 'skip':
                                st.metric("⏭️ Skipped", len(results['skipped_stocks']))
                            elif handle_duplicates == 'update':
                                st.metric("🔄 Updated", len(results['updated_stocks']))
                        
                        # Detailed results
                        if results['success_count'] > 0:
                            st.success(f"🎉 Successfully imported {results['success_count']} stocks to watchlist!")
                            
                            if results['imported_stocks']:
                                st.subheader("📥 Imported Stocks")
                                for ticker in results['imported_stocks']:
                                    st.write(f"✅ {ticker}")
                            
                            if results['updated_stocks']:
                                st.subheader("🔄 Updated Stocks")
                                for ticker in results['updated_stocks']:
                                    st.write(f"🔄 {ticker}")
                        
                        if results['skipped_stocks']:
                            st.subheader("⏭️ Skipped Stocks")
                            for ticker in results['skipped_stocks']:
                                st.write(f"⏭️ {ticker}")
                        
                        if results['warnings']:
                            st.subheader("⚠️ Warnings")
                            for warning in results['warnings']:
                                st.warning(warning)
                        
                        if results['errors']:
                            st.subheader("❌ Errors")
                            for error in results['errors']:
                                st.error(error)
                        
                        # Refresh button if successful
                        if results['success_count'] > 0 and results['error_count'] == 0:
                            st.markdown("---")
                            if st.button("🔄 Go to Watchlist", use_container_width=True):
                                st.session_state.selected_page = "Watchlist"
                                st.rerun()
        
        except Exception as e:
            st.error(f"❌ Error reading CSV file: {str(e)}")
            st.info("Please check your CSV file format and try again.")


def watchlist_recommendations_page():
    """Display watchlist recommendations page"""
    st.header("👁️ Watchlist Trading Recommendations")
    
    watchlist = db.get_watchlist()
    if not watchlist:
        st.warning("⚠️ No stocks in watchlist. Add stocks first to get recommendations.")
        st.stop()
    
    # Day range selector for AI predictions
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        selected_day_range = st.selectbox(
            "📅 Select Trading Horizon",
            ["weekly", "monthly", "quarterly", "yearly"],
            index=1,  # Default to monthly
            help="Choose the time horizon for AI price predictions"
        )
    
    # Get watchlist recommendations with selected day range
    with st.spinner(f"🔄 Analyzing watchlist stocks for {selected_day_range} horizon..."):
        watchlist_recommendations = strategy.get_watchlist_recommendations(watchlist, selected_day_range)
    
    if watchlist_recommendations:
        # Summary dashboard
        watchlist_buy = sum(1 for r in watchlist_recommendations if r['action'] == 'BUY')
        watchlist_sell = sum(1 for r in watchlist_recommendations if r['action'] == 'SELL')
        watchlist_watch = sum(1 for r in watchlist_recommendations if r['action'] == 'WATCH')
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🟢 Buy Signals", watchlist_buy, delta="Good entry points")
        with col2:
            st.metric("🔴 Sell Signals", watchlist_sell, delta="Take profits/alerts")
        with col3:
            st.metric("👀 Watch Signals", watchlist_watch, delta="Monitor closely")
        with col4:
            avg_confidence = sum(r['confidence'] for r in watchlist_recommendations) / len(watchlist_recommendations)
            st.metric("🎯 Avg Confidence", f"{avg_confidence:.1%}")
        
        # Watchlist recommendations
        st.subheader("📋 Individual Stock Recommendations")
        
        for rec in watchlist_recommendations:
            watchlist_stock = rec['watchlist_data']
            
            # Color coding for action
            action_color = {
                'BUY': '🟢',
                'SELL': '🔴', 
                'WATCH': '👀'
            }.get(rec['action'], '⚪')
            
            with st.expander(f"{action_color} {watchlist_stock['ticker']} - {rec['action']} (Confidence: {rec['confidence']:.1%})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Current Price:** ${rec['current_price']:.2f}")
                    if watchlist_stock['target_buy_price']:
                        buy_diff = rec['current_price'] - watchlist_stock['target_buy_price']
                        buy_diff_pct = (buy_diff / watchlist_stock['target_buy_price']) * 100 if watchlist_stock['target_buy_price'] > 0 else 0
                        buy_status = "🟢 TARGET REACHED!" if buy_diff <= 0 else f"{buy_diff_pct:+.2f}% away"
                        st.write(f"**Buy Target:** ${watchlist_stock['target_buy_price']:.2f} ({buy_status})")
                    
                    if watchlist_stock['target_sell_price']:
                        sell_diff = rec['current_price'] - watchlist_stock['target_sell_price']
                        sell_diff_pct = (sell_diff / watchlist_stock['target_sell_price']) * 100 if watchlist_stock['target_sell_price'] > 0 else 0
                        sell_status = "🔴 TARGET REACHED!" if sell_diff >= 0 else f"{sell_diff_pct:+.2f}% away"
                        st.write(f"**Sell Target:** ${watchlist_stock['target_sell_price']:.2f} ({sell_status})")
                    
                    st.write(f"**Status:** {watchlist_stock['status']}")
                    
                    if watchlist_stock['notes']:
                        st.write(f"**Notes:** {watchlist_stock['notes']}")
                    
                    # AI predicted prices if available
                    if 'target_buy_price' in rec and rec['target_buy_price']:
                        st.write(f"**💡 AI Buy Target:** ${rec['target_buy_price']:.2f}")
                    if 'target_sell_price' in rec and rec['target_sell_price']:
                        st.write(f"**💰 AI Sell Target:** ${rec['target_sell_price']:.2f}")
                
                with col2:
                    st.write(f"**Strategy:** {rec['strategy'].title()}")
                    st.write(f"**Reason:** {rec['reason']}")
                    st.write(f"**Day Range:** {rec.get('day_range', 'monthly').title()}")
                    
                    # Quick action buttons
                    if rec['action'] == 'BUY':
                        if st.button(f"🛒 Quick Buy {watchlist_stock['ticker']}", key=f"quick_buy_{watchlist_stock['ticker']}", type="primary"):
                            st.info(f"🛒 Ready to buy {watchlist_stock['ticker']} at ${rec['current_price']:.2f}")
                            st.info("Navigate to 'Add Stock' to complete the purchase")
                    elif rec['action'] == 'SELL':
                        if st.button(f"💰 Alert {watchlist_stock['ticker']}", key=f"alert_sell_{watchlist_stock['ticker']}", type="secondary"):
                            st.warning(f"🔴 Price alert: {watchlist_stock['ticker']} at ${rec['current_price']:.2f}")
                    
                    # Apply AI suggested prices if available
                    if ('target_buy_price' in rec and rec['target_buy_price'] and 
                        'target_sell_price' in rec and rec['target_sell_price']):
                        if st.button(f"🚀 Apply AI Targets", key=f"apply_ai_{watchlist_stock['ticker']}", type="primary"):
                            success = db.update_watchlist_stock(
                                ticker=watchlist_stock['ticker'],
                                target_buy_price=rec['target_buy_price'],
                                target_sell_price=rec['target_sell_price'],
                                status="watching"
                            )
                            if success:
                                st.success("✅ AI-recommended targets applied!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to apply AI targets")
        
        # Watchlist-level insights
        st.subheader("📊 Watchlist Insights")
        
        # Target reach analysis
        from .utils import calculate_target_reach_analysis
        target_analysis = calculate_target_reach_analysis(watchlist_recommendations)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎯 Buy Targets Hit", target_analysis['buy_targets_reached'])
        with col2:
            st.metric("🎯 Sell Targets Hit", target_analysis['sell_targets_reached'])
        with col3:
            st.metric("👀 Near Buy Target", target_analysis['near_buy_targets'])
        with col4:
            st.metric("👀 Near Sell Target", target_analysis['near_sell_targets'])
        
        # Action distribution chart
        action_counts = {}
        for rec in watchlist_recommendations:
            action_name = rec['action']
            action_counts[action_name] = action_counts.get(action_name, 0) + 1
        
        st.subheader("📈 Recommendation Distribution")
        action_data = pd.DataFrame(list(action_counts.items()), columns=['Action', 'Stocks'])
        st.bar_chart(action_data.set_index('Action'))
        
        # Day range analysis
        day_range_counts = {}
        for rec in watchlist_recommendations:
            range_name = rec.get('day_range', 'monthly')
            day_range_counts[range_name] = day_range_counts.get(range_name, 0) + 1
        
        if day_range_counts:
            st.subheader("📅 Trading Horizon Distribution")
            range_data = pd.DataFrame(list(day_range_counts.items()), columns=['Time Horizon', 'Stocks'])
            st.bar_chart(range_data.set_index('Time Horizon'))
        
        # Recent watchlist recommendation history
        st.subheader("📜 Recent Watchlist Recommendations")
        recent_recs = db.get_recent_recommendations(30)
        
        if recent_recs:
            # Filter for watchlist stocks
            watchlist_tickers = [stock['ticker'] for stock in watchlist]
            watchlist_recs = [rec for rec in recent_recs if rec['ticker'] in watchlist_tickers]
            
            if watchlist_recs:
                rec_df = pd.DataFrame(watchlist_recs)
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
                st.info("No recent watchlist recommendations found.")
        else:
            st.info("No previous recommendations found.")
    
    else:
        st.info("No watchlist recommendations available at this time. Try refreshing your watchlist data or adding stocks with target prices.")
