"""
Stock Analyzer Application - Main Entry Point

A comprehensive stock portfolio and watchlist management application
with AI-powered trading recommendations.
"""

import streamlit as st
import sys
import os

# Add the src directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from src.database import db
from src.trading_strategy import strategy
from src.utils.navigation import render_navigation
from src.portfolio.pages import (
    portfolio_overview_page,
    add_stock_page,
    edit_portfolio_page,
    sell_stock_page,
    sales_history_page,
    portfolio_recommendations_page
)
from src.utils.ui_components import display_alert_box

# Import watchlist pages
from src.watchlist.pages import (
    watchlist_page,
    add_to_watchlist_page,
    edit_watchlist_page,
    import_watchlist_page,
    watchlist_recommendations_page
)

# TODO: Import trading and settings pages when created
# from trading.strategy_config import trading_strategy_page
# from settings.pages import settings_page


def main():
    """Main application entry point"""
    
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

    # Render navigation and get selected page
    page = render_navigation()

    # Route to appropriate page based on selection
    try:
        if page == "Portfolio Overview":
            portfolio_overview_page()
        elif page == "Add Stock":
            add_stock_page()
        elif page == "Edit Portfolio":
            edit_portfolio_page()
        elif page == "Sell Stock":
            sell_stock_page()
        elif page == "Sales History":
            sales_history_page()
        elif page == "Portfolio Recommendations":
            portfolio_recommendations_page()
        
        # Watchlist pages
        elif page == "Watchlist":
            watchlist_page()
        elif page == "Add to Watchlist":
            add_to_watchlist_page()
        elif page == "Edit Watchlist":
            edit_watchlist_page()
        elif page == "Import Watchlist from CSV":
            import_watchlist_page()
        elif page == "Watchlist Recommendations":
            watchlist_recommendations_page()
        
        # Trading Strategy page (placeholder for now)
        elif page == "Trading Strategy":
            display_alert_box("🚧 Trading Strategy page is being refactored. Please check back later.", "info")
        
        # Settings page (placeholder for now)
        elif page == "Settings":
            display_alert_box("🚧 Settings page is being refactored. Please check back later.", "info")
        
        else:
            display_alert_box(f"Page '{page}' not found.", "error")
            
    except Exception as e:
        display_alert_box(f"Error loading page '{page}': {str(e)}", "error")
        st.exception(e)

    # Footer
    st.markdown("---")
    st.markdown("*Data provided by Yahoo Finance. Prices are delayed and may not reflect real-time market data.*")
    st.markdown("*Trading recommendations are for educational purposes only. Always consult with a financial advisor before making investment decisions.*")


if __name__ == "__main__":
    main()
