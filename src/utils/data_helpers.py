"""
Data Processing Helper Functions

Common data processing and formatting utilities used across the application.
"""

import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime


def get_stock_price_safe(ticker):
    """
    Safely get current stock price with multiple fallback methods.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Current price or None if unavailable
    """
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


def get_stock_info_safe(ticker):
    """
    Safely get stock information with error handling.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with stock info or empty dict on error
    """
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


def format_currency(amount, currency_symbol="$", decimal_places=2):
    """
    Format a number as currency.
    
    Args:
        amount: Numeric amount
        currency_symbol: Currency symbol
        decimal_places: Number of decimal places
        
    Returns:
        Formatted currency string
    """
    if amount is None:
        return "N/A"
    
    return f"{currency_symbol}{amount:,{decimal_places}f}"


def format_percentage(value, include_sign=True, decimal_places=2):
    """
    Format a number as percentage.
    
    Args:
        value: Numeric value (as decimal, e.g., 0.25 for 25%)
        include_sign: Whether to include + sign for positive values
        decimal_places: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    if value is None:
        return "N/A"
    
    sign = "+" if include_sign and value >= 0 else ""
    return f"{sign}{value * 100:.{decimal_places}f}%"


def format_number(number, decimal_places=0):
    """
    Format a number with thousands separator.
    
    Args:
        number: Numeric value
        decimal_places: Number of decimal places
        
    Returns:
        Formatted number string
    """
    if number is None:
        return "N/A"
    
    return f"{number:,{decimal_places}f}"


def calculate_return_metrics(purchase_price, current_price, shares=1):
    """
    Calculate return metrics for a stock position.
    
    Args:
        purchase_price: Purchase price per share
        current_price: Current price per share
        shares: Number of shares
        
    Returns:
        Dictionary with calculated metrics
    """
    if purchase_price is None or current_price is None:
        return {}
    
    purchase_value = purchase_price * shares
    current_value = current_price * shares
    
    profit_loss = current_value - purchase_value
    profit_loss_percent = (profit_loss / purchase_value) * 100 if purchase_value > 0 else 0
    
    return {
        'purchase_value': purchase_value,
        'current_value': current_value,
        'profit_loss': profit_loss,
        'profit_loss_percent': profit_loss_percent,
        'profit_loss_per_share': current_price - purchase_price
    }


def create_summary_metrics(data, metrics_config):
    """
    Create summary metrics from data based on configuration.
    
    Args:
        data: Dictionary or DataFrame with data
        metrics_config: List of metric configurations
        
    Returns:
        List of metric dictionaries for display
    """
    metrics = []
    
    for config in metrics_config:
        field = config['field']
        label = config['label']
        
        if isinstance(data, dict):
            value = data.get(field, 0)
        else:  # DataFrame
            value = data[field].sum() if field in data.columns else 0
        
        # Apply formatting
        if 'format' in config:
            if config['format'] == 'currency':
                formatted_value = format_currency(value)
            elif config['format'] == 'percentage':
                formatted_value = format_percentage(value / 100)  # Assume value is already percentage
            elif config['format'] == 'number':
                formatted_value = format_number(value)
            else:
                formatted_value = str(value)
        else:
            formatted_value = str(value)
        
        metric = {'label': label, 'value': formatted_value}
        
        # Add delta if specified
        if 'delta_field' in config:
            if isinstance(data, dict):
                delta_value = data.get(config['delta_field'], 0)
            else:
                delta_value = data[config['delta_field']].sum() if config['delta_field'] in data.columns else 0
            
            if 'delta_format' in config and config['delta_format'] == 'percentage':
                metric['delta'] = format_percentage(delta_value)
            else:
                metric['delta'] = str(delta_value)
        
        metrics.append(metric)
    
    return metrics


def validate_ticker_symbol(ticker):
    """
    Validate if a ticker symbol is legitimate by checking with Yahoo Finance.
    
    Args:
        ticker: Ticker symbol to validate
        
    Returns:
        Tuple of (is_valid, company_name_or_error)
    """
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info
        
        # Check if we got valid data
        if info.get('regularMarketPrice') is not None or info.get('currentPrice') is not None:
            return True, info.get('shortName', ticker.upper())
        else:
            # Try history as fallback
            hist = stock.history(period="5d")
            if not hist.empty:
                return True, info.get('shortName', ticker.upper())
            else:
                return False, "No data found for ticker"
                
    except Exception as e:
        return False, f"Error: {str(e)}"


def export_to_csv_filename(base_name, extension="csv"):
    """
    Generate a timestamped filename for CSV export.
    
    Args:
        base_name: Base filename
        extension: File extension
        
    Returns:
        Timestamped filename string
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{base_name}_{timestamp}.{extension}"


def parse_csv_file(file_obj):
    """
    Safely parse a CSV file with error handling.
    
    Args:
        file_obj: File object to parse
        
    Returns:
        Tuple of (success, dataframe or error_message)
    """
    try:
        df = pd.read_csv(file_obj)
        return True, df
    except Exception as e:
        return False, f"Error reading CSV file: {str(e)}"


def clean_numeric_column(df, column_name, default_value=0):
    """
    Clean and convert a numeric column in a DataFrame.
    
    Args:
        df: DataFrame to clean
        column_name: Column name to clean
        default_value: Default value for invalid entries
        
    Returns:
        Cleaned DataFrame
    """
    if column_name not in df.columns:
        return df
    
    # Convert to numeric, coercing errors to NaN
    df[column_name] = pd.to_numeric(df[column_name], errors='coerce')
    
    # Fill NaN with default value
    df[column_name] = df[column_name].fillna(default_value)
    
    return df


def standardize_ticker_column(df, column_name='ticker'):
    """
    Standardize ticker column format (uppercase, no spaces).
    
    Args:
        df: DataFrame to clean
        column_name: Name of ticker column
        
    Returns:
        Cleaned DataFrame
    """
    if column_name not in df.columns:
        return df
    
    # Convert to string, strip whitespace, and uppercase
    df[column_name] = df[column_name].astype(str).str.strip().str.upper()
    
    # Remove any empty tickers
    df = df[df[column_name] != 'NAN']
    df = df[df[column_name] != '']
    
    return df


def calculate_portfolio_allocation(portfolio_data):
    """
    Calculate allocation percentages for a portfolio.
    
    Args:
        portfolio_data: List of portfolio stocks with current values
        
    Returns:
        Dictionary with allocation percentages
    """
    if not portfolio_data:
        return {}
    
    total_value = sum(stock.get('current_total', 0) for stock in portfolio_data)
    
    if total_value == 0:
        return {}
    
    allocations = {}
    for stock in portfolio_data:
        ticker = stock.get('ticker', 'Unknown')
        current_value = stock.get('current_total', 0)
        allocations[ticker] = (current_value / total_value) * 100
    
    return allocations


def create_chart_data_from_dict(data_dict, sort_by='value', ascending=False):
    """
    Create chart-ready data from a dictionary.
    
    Args:
        data_dict: Dictionary with labels as keys and values as values
        sort_by: Sort by 'key' or 'value'
        ascending: Sort order
        
    Returns:
        Pandas DataFrame ready for charting
    """
    if not data_dict:
        return pd.DataFrame()
    
    df = pd.DataFrame(list(data_dict.items()), columns=['label', 'value'])
    
    if sort_by == 'key':
        df = df.sort_values('label', ascending=ascending)
    else:
        df = df.sort_values('value', ascending=ascending)
    
    return df.set_index('label')
