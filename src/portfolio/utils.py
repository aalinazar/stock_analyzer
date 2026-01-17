"""
Portfolio Utility Functions

Helper functions for portfolio management and data processing.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
from src.database import db


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


def color_profit_loss(val):
    """Color function for profit/loss values"""
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
    """Color function for percentage values"""
    if isinstance(val, str) and '%' in val:
        if val.startswith('+'):
            return 'color: green'
        elif val.startswith('-'):
            return 'color: red'
    return ''


def get_current_stock_price(ticker):
    """Get current stock price with fallback methods"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        
        if current_price is None:
            hist = stock.history(period="1d")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
            else:
                current_price = None
        
        return current_price
    except Exception as e:
        st.error(f"Error fetching current price for {ticker}: {str(e)}")
        return None


def calculate_stock_metrics(shares, purchase_price, current_price):
    """Calculate profit/loss metrics for a stock"""
    if current_price is None:
        return None
    
    current_total_value = current_price * shares
    purchase_total_value = purchase_price * shares
    profit_loss = current_total_value - purchase_total_value
    profit_loss_percent = (profit_loss / purchase_total_value) * 100 if purchase_total_value > 0 else 0
    
    return {
        'current_total': current_total_value,
        'purchase_total': purchase_total_value,
        'profit_loss': profit_loss,
        'profit_loss_percent': profit_loss_percent
    }


def display_portfolio_summary_cards(portfolio_df):
    """Display summary metrics cards for portfolio"""
    if portfolio_df.empty:
        return
    
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
        st.metric("Total Stocks", len(portfolio_df))
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
