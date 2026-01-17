"""
Watchlist Utility Functions

Helper functions for watchlist management and data processing.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
from src.database import db


def load_enriched_watchlist():
    """Load watchlist from database and enrich with current data"""
    watchlist = db.get_watchlist()
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
    
    return enriched_watchlist


def get_watchlist_summary_metrics(enriched_watchlist):
    """Calculate summary metrics for watchlist"""
    if not enriched_watchlist:
        return {
            'total_watched': 0,
            'buy_alerts': 0,
            'sell_alerts': 0,
            'near_buy': 0,
            'near_sell': 0
        }
    
    buy_alerts = sum(1 for stock in enriched_watchlist if stock['buy_diff'] is not None and stock['buy_diff'] <= 0)
    sell_alerts = sum(1 for stock in enriched_watchlist if stock['sell_diff'] is not None and stock['sell_diff'] >= 0)
    near_buy = sum(1 for stock in enriched_watchlist if stock['buy_diff_pct'] is not None and -5 <= stock['buy_diff_pct'] <= 10)
    near_sell = sum(1 for stock in enriched_watchlist if stock['sell_diff_pct'] is not None and -10 <= stock['sell_diff_pct'] <= 5)
    
    return {
        'total_watched': len(enriched_watchlist),
        'buy_alerts': buy_alerts,
        'sell_alerts': sell_alerts,
        'near_buy': near_buy,
        'near_sell': near_sell
    }


def get_stock_info_safe(ticker):
    """Safely get stock information with error handling"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        return {
            'ticker': ticker.upper(),
            'company_name': info.get('shortName', ticker),
            'current_price': info.get('currentPrice') or info.get('regularMarketPrice'),
            'currency': info.get('currency', 'USD'),
            'market_cap': info.get('marketCap'),
            'sector': info.get('sector'),
            'industry': info.get('industry')
        }
    except Exception as e:
        st.error(f"Error fetching stock info for {ticker}: {str(e)}")
        return {}


def display_watchlist_summary_cards(enriched_watchlist):
    """Display summary metrics cards for watchlist"""
    metrics = get_watchlist_summary_metrics(enriched_watchlist)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total Watched", metrics['total_watched'])
    with col2:
        st.metric("🟢 Buy Alerts", metrics['buy_alerts'], delta=f"{metrics['buy_alerts']} at/below target")
    with col3:
        st.metric("🔴 Sell Alerts", metrics['sell_alerts'], delta=f"{metrics['sell_alerts']} at/above target")
    with col4:
        st.metric("👀 Near Target", metrics['near_buy'] + metrics['near_sell'], delta=f"{metrics['near_buy']} buy, {metrics['near_sell']} sell")


def determine_stock_status(stock):
    """Determine status color and alert information for a stock"""
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
    
    return status_color, alert_info


def display_target_metrics(current_price, target_buy_price=None, target_sell_price=None):
    """Display target price metrics with proper formatting"""
    metrics = {}
    
    if target_buy_price:
        buy_diff = current_price - target_buy_price
        buy_diff_pct = (buy_diff / target_buy_price) * 100 if target_buy_price > 0 else 0
        buy_color = "inverse" if buy_diff <= 0 else "normal" if -5 <= buy_diff_pct <= 10 else "off"
        metrics['buy_target'] = {
            'price': f"${target_buy_price:.2f}",
            'delta': f"{buy_diff_pct:+.2f}%" if buy_diff_pct else None,
            'color': buy_color
        }
    
    if target_sell_price:
        sell_diff = current_price - target_sell_price
        sell_diff_pct = (sell_diff / target_sell_price) * 100 if target_sell_price > 0 else 0
        sell_color = "inverse" if sell_diff >= 0 else "normal" if -10 <= sell_diff_pct <= 5 else "off"
        metrics['sell_target'] = {
            'price': f"${target_sell_price:.2f}",
            'delta': f"{sell_diff_pct:+.2f}%" if sell_diff_pct else None,
            'color': sell_color
        }
    
    return metrics


def generate_watchlist_template():
    """Generate a CSV template with sample data"""
    template_lines = ["ticker,target_buy_price,target_sell_price,notes,status"]
    sample_data = [
        ("AAPL", "150.00", "200.00", "Apple Inc - Strong fundamentals", "watching"),
        ("GOOGL", "120.00", "180.00", "Alphabet - Good long term prospect", "ready_to_buy"),
        ("MSFT", "300.00", "400.00", "Microsoft - Cloud growth story", "watching"),
        ("TSLA", "200.00", "300.00", "Tesla - High volatility but potential", "paused")
    ]
    
    for ticker, buy_price, sell_price, notes, status in sample_data:
        template_lines.append(f"{ticker},{buy_price},{sell_price},{notes},{status}")
    
    return "\n".join(template_lines)


def validate_csv_structure(df):
    """Validate CSV structure for watchlist import"""
    errors = []
    warnings = []
    
    # Check required columns
    required_columns = ['ticker']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        errors.append(f"Missing required columns: {', '.join(missing_columns)}")
    
    # Check column names (case-insensitive)
    df.columns = [col.strip().lower() for col in df.columns]
    
    return len(errors) == 0, errors, warnings


def standardize_csv_data(df):
    """Standardize CSV data for processing"""
    # Standardize column names
    df.columns = [col.strip().lower() for col in df.columns]
    
    # Clean numeric columns
    if 'target_buy_price' in df.columns:
        df = clean_numeric_column(df, 'target_buy_price')
    
    if 'target_sell_price' in df.columns:
        df = clean_numeric_column(df, 'target_sell_price')
    
    # Standardize ticker column
    if 'ticker' in df.columns:
        df = standardize_ticker_column(df, 'ticker')
    
    # Clean status column
    if 'status' in df.columns:
        valid_statuses = ['watching', 'ready_to_buy', 'ready_to_sell', 'paused']
        df['status'] = df['status'].apply(
            lambda x: x if x in valid_statuses else 'watching'
        )
    
    # Clean notes column
    if 'notes' in df.columns:
        df['notes'] = df['notes'].apply(
            lambda x: None if pd.isna(x) or str(x).strip().upper() == 'NAN' else str(x).strip()
        )
    
    return df


def clean_numeric_column(df, column_name, default_value=0):
    """Clean and convert a numeric column in a DataFrame"""
    if column_name not in df.columns:
        return df
    
    # Convert to numeric, coercing errors to NaN
    df[column_name] = pd.to_numeric(df[column_name], errors='coerce')
    
    # Fill NaN with default value
    df[column_name] = df[column_name].fillna(default_value)
    
    return df


def standardize_ticker_column(df, column_name='ticker'):
    """Standardize ticker column format (uppercase, no spaces)"""
    if column_name not in df.columns:
        return df
    
    # Convert to string, strip whitespace, and uppercase
    df[column_name] = df[column_name].astype(str).str.strip().str.upper()
    
    # Remove any empty tickers
    df = df[df[column_name] != 'NAN']
    df = df[df[column_name] != '']
    
    return df


def calculate_target_reach_analysis(watchlist_recommendations):
    """Calculate target reach analysis for watchlist"""
    if not watchlist_recommendations:
        return {
            'buy_targets_reached': 0,
            'sell_targets_reached': 0,
            'near_buy_targets': 0,
            'near_sell_targets': 0
        }
    
    buy_targets_reached = sum(1 for rec in watchlist_recommendations 
                            if rec['watchlist_data']['target_buy_price'] and 
                            rec['current_price'] <= rec['watchlist_data']['target_buy_price'])
    sell_targets_reACHED = sum(1 for rec in watchlist_recommendations 
                             if rec['watchlist_data']['target_sell_price'] and 
                             rec['current_price'] >= rec['watchlist_data']['target_sell_price'])
    near_buy_targets = sum(1 for rec in watchlist_recommendations 
                         if rec['watchlist_data']['target_buy_price'] and 
                         -5 <= ((rec['current_price'] - rec['watchlist_data']['target_buy_price']) / rec['watchlist_data']['target_buy_price'] * 100) <= 10)
    near_sell_targets = sum(1 for rec in watchlist_recommendations 
                          if rec['watchlist_data']['target_sell_price'] and 
                         -10 <= ((rec['current_price'] - rec['watchlist_data']['target_sell_price']) / rec['watchlist_data']['target_sell_price'] * 100) <= 5)
    
    return {
        'buy_targets_reached': buy_targets_reached,
        'sell_targets_reached': sell_targets_reACHED,
        'near_buy_targets': near_buy_targets,
        'near_sell_targets': near_sell_targets
    }
