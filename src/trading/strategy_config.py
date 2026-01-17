"""
Trading Strategy Configuration

Handles strategy configuration and management functionality including:
- Strategy settings per stock
- Parameter configuration
- Strategy selection and optimization
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from src.database import db
from src.trading_strategy import strategy
from src.utils.ui_components import display_alert_box, display_metric_cards


def trading_strategy_config_page():
    """Display trading strategy configuration page"""
    st.header("⚙️ Trading Strategy Configuration")
    
    # Get portfolio for strategy configuration
    portfolio = db.get_portfolio()
    if not portfolio:
        display_alert_box("⚠️ No stocks in portfolio. Add stocks first to configure strategies.", "info")
        return
    
    # Strategy overview
    st.subheader("📊 Strategy Overview")
    
    # Count strategies in use
    strategy_counts = {}
    for stock in portfolio:
        settings = db.get_strategy_settings(stock['ticker'])
        if settings:
            strategy_type = settings['strategy_type']
            strategy_counts[strategy_type] = strategy_counts.get(strategy_type, 0) + 1
        else:
            strategy_counts['simple'] = strategy_counts.get('simple', 0) + 1
    
    # Display strategy distribution
    if strategy_counts:
        metrics_data = [
            {"label": f"{strategy.title()}", "value": count}
            for strategy, count in strategy_counts.items()
        ]
        display_metric_cards(metrics_data, columns=len(strategy_counts))
    
    # Available strategies information
    st.subheader("🎯 Available Trading Strategies")
    
    strategy_info = {
        'simple': {
            'name': 'Simple Strategy',
            'description': 'Basic profit/loss based trading with fixed targets and stop losses',
            'parameters': ['profit_target', 'stop_loss', 'hold_threshold'],
            'best_for': 'Beginners and conservative trading'
        },
        'moving_average': {
            'name': 'Moving Average Crossover',
            'description': 'Uses moving average crossovers to generate buy/sell signals',
            'parameters': ['short_ma', 'long_ma'],
            'best_for': 'Trend following and medium-term trading'
        },
        'rsi': {
            'name': 'RSI (Relative Strength Index)',
            'description': 'Identifies overbought and oversold conditions',
            'parameters': ['rsi_period', 'oversold_level', 'overbought_level'],
            'best_for': 'Range-bound markets and reversal trading'
        },
        'bollinger_bands': {
            'name': 'Bollinger Bands',
            'description': 'Uses price volatility and standard deviations for signals',
            'parameters': ['bb_period', 'bb_std'],
            'best_for': 'Volatility trading and breakout strategies'
        },
        'macd': {
            'name': 'MACD (Moving Average Convergence Divergence)',
            'description': 'Momentum indicator measuring trend strength and direction',
            'parameters': ['macd_fast', 'macd_slow', 'macd_signal'],
            'best_for': 'Momentum trading and trend confirmation'
        }
    }
    
    # Display strategy cards
    for strategy_key, info in strategy_info.items():
        with st.expander(f"📈 {info['name']}"):
            st.write(f"**Description:** {info['description']}")
            st.write(f"**Best for:** {info['best_for']}")
            st.write(f"**Parameters:** {', '.join(info['parameters'])}")
    
    # Strategy configuration section
    st.markdown("---")
    st.subheader("🔧 Configure Strategy for Individual Stocks")
    
    # Stock selection
    stock_options = [(f"{stock['ticker']} - {stock['shares']} shares", stock['ticker']) for stock in portfolio]
    selected_ticker = st.selectbox(
        "Select Stock to Configure",
        [ticker for _, ticker in stock_options],
        format_func=lambda x: next(t for t, ticker in stock_options if ticker == x)
    )
    
    if selected_ticker:
        display_stock_strategy_config(selected_ticker, strategy_info)
    
    # Bulk strategy configuration
    st.markdown("---")
    st.subheader("🚀 Bulk Strategy Configuration")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        bulk_strategy = st.selectbox(
            "Select Strategy for All Portfolio Stocks",
            options=list(strategy_info.keys()),
            format_func=lambda x: strategy_info[x]['name']
        )
    
    with col2:
        if st.button("Apply to All Stocks", type="primary"):
            success_count = 0
            for stock in portfolio:
                default_params = get_default_strategy_parameters(bulk_strategy)
                success = db.save_strategy_settings(
                    ticker=stock['ticker'],
                    strategy_type=bulk_strategy,
                    parameters=default_params
                )
                if success:
                    success_count += 1
            
            if success_count > 0:
                display_alert_box(f"✅ Successfully applied {strategy_info[bulk_strategy]['name']} to {success_count} stocks!", "success")
            else:
                display_alert_box("❌ Failed to apply strategy to stocks.", "error")


def display_stock_strategy_config(ticker: str, strategy_info: dict):
    """Display strategy configuration for a specific stock"""
    
    # Get current strategy settings
    current_settings = db.get_strategy_settings(ticker)
    current_strategy = current_settings['strategy_type'] if current_settings else 'simple'
    current_params = current_settings['parameters'] if current_settings else get_default_strategy_parameters('simple')
    
    # Get stock info
    stock = next((s for s in db.get_portfolio() if s['ticker'] == ticker), None)
    if stock:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Ticker", stock['ticker'])
        with col2:
            st.metric("Shares", f"{stock['shares']:,.0f}")
        with col3:
            st.metric("Purchase Price", f"${stock['purchase_price']:.2f}")
    
    # Strategy selection
    st.subheader(f"📊 Configure Strategy for {ticker}")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_strategy = st.selectbox(
            "Select Trading Strategy",
            options=list(strategy_info.keys()),
            index=list(strategy_info.keys()).index(current_strategy),
            format_func=lambda x: strategy_info[x]['name']
        )
    
    with col2:
        if st.button("Reset to Default", key=f"reset_{ticker}"):
            default_params = get_default_strategy_parameters(selected_strategy)
            success = db.save_strategy_settings(
                ticker=ticker,
                strategy_type=selected_strategy,
                parameters=default_params
            )
            if success:
                display_alert_box(f"✅ Reset {ticker} to default {strategy_info[selected_strategy]['name']} parameters!", "success")
                st.rerun()
    
    # Parameter configuration
    st.subheader(f"⚙️ {strategy_info[selected_strategy]['name']} Parameters")
    
    params = get_strategy_parameters_ui(selected_strategy, current_params)
    
    # Save configuration
    if st.button("Save Strategy Configuration", type="primary", key=f"save_{ticker}"):
        success = db.save_strategy_settings(
            ticker=ticker,
            strategy_type=selected_strategy,
            parameters=params
        )
        
        if success:
            display_alert_box(f"✅ Successfully saved strategy configuration for {ticker}!", "success")
            
            # Show test recommendation
            with st.spinner("🔄 Testing strategy with recent data..."):
                try:
                    current_price = strategy.get_historical_data(ticker, "1d")['Close'].iloc[-1] if not strategy.get_historical_data(ticker, "1d").empty else stock['purchase_price']
                    test_rec = strategy.get_recommendation(
                        ticker, stock['shares'], stock['purchase_price'], current_price
                    )
                    
                    st.info(f"🎯 Test Recommendation: {test_rec['action']} - {test_rec['reason']}")
                except Exception as e:
                    st.warning(f"Could not generate test recommendation: {str(e)}")
        else:
            display_alert_box(f"❌ Failed to save strategy configuration for {ticker}.", "error")


def get_strategy_parameters_ui(strategy_type: str, current_params: dict) -> dict:
    """Generate UI for strategy parameters"""
    
    params = current_params.copy()
    
    if strategy_type == 'simple':
        col1, col2, col3 = st.columns(3)
        
        with col1:
            params['profit_target'] = st.number_input(
                "Profit Target (%)",
                min_value=0.01,
                max_value=2.00,
                value=current_params.get('profit_target', 0.20),
                step=0.01,
                format="%.2f",
                help="Target profit percentage (e.g., 0.20 = 20%)"
            )
        
        with col2:
            params['stop_loss'] = st.number_input(
                "Stop Loss (%)",
                min_value=0.01,
                max_value=1.00,
                value=current_params.get('stop_loss', 0.10),
                step=0.01,
                format="%.2f",
                help="Maximum loss percentage (e.g., 0.10 = 10%)"
            )
        
        with col3:
            params['hold_threshold'] = st.number_input(
                "Hold Threshold (%)",
                min_value=0.01,
                max_value=0.50,
                value=current_params.get('hold_threshold', 0.05),
                step=0.01,
                format="%.2f",
                help="Small P/L range where you hold (e.g., 0.05 = 5%)"
            )
    
    elif strategy_type == 'moving_average':
        col1, col2 = st.columns(2)
        
        with col1:
            params['short_ma'] = st.number_input(
                "Short Moving Average Period",
                min_value=5,
                max_value=50,
                value=current_params.get('short_ma', 20),
                step=1,
                help="Short-term moving average period (e.g., 20 days)"
            )
        
        with col2:
            params['long_ma'] = st.number_input(
                "Long Moving Average Period",
                min_value=20,
                max_value=200,
                value=current_params.get('long_ma', 50),
                step=1,
                help="Long-term moving average period (e.g., 50 days)"
            )
    
    elif strategy_type == 'rsi':
        col1, col2, col3 = st.columns(3)
        
        with col1:
            params['rsi_period'] = st.number_input(
                "RSI Period",
                min_value=5,
                max_value=30,
                value=current_params.get('rsi_period', 14),
                step=1,
                help="RSI calculation period (standard is 14)"
            )
        
        with col2:
            params['oversold_level'] = st.number_input(
                "Oversold Level",
                min_value=10,
                max_value=40,
                value=current_params.get('oversold_level', 30),
                step=1,
                help="RSI level considered oversold (buy signal)"
            )
        
        with col3:
            params['overbought_level'] = st.number_input(
                "Overbought Level",
                min_value=60,
                max_value=90,
                value=current_params.get('overbought_level', 70),
                step=1,
                help="RSI level considered overbought (sell signal)"
            )
    
    elif strategy_type == 'bollinger_bands':
        col1, col2 = st.columns(2)
        
        with col1:
            params['bb_period'] = st.number_input(
                "Bollinger Bands Period",
                min_value=10,
                max_value=50,
                value=current_params.get('bb_period', 20),
                step=1,
                help="Moving average period for bands (standard is 20)"
            )
        
        with col2:
            params['bb_std'] = st.number_input(
                "Standard Deviations",
                min_value=1.0,
                max_value=3.0,
                value=current_params.get('bb_std', 2.0),
                step=0.1,
                format="%.1f",
                help="Number of standard deviations (standard is 2.0)"
            )
    
    elif strategy_type == 'macd':
        col1, col2, col3 = st.columns(3)
        
        with col1:
            params['macd_fast'] = st.number_input(
                "Fast EMA Period",
                min_value=5,
                max_value=20,
                value=current_params.get('macd_fast', 12),
                step=1,
                help="Fast exponential moving average period"
            )
        
        with col2:
            params['macd_slow'] = st.number_input(
                "Slow EMA Period",
                min_value=15,
                max_value=50,
                value=current_params.get('macd_slow', 26),
                step=1,
                help="Slow exponential moving average period"
            )
        
        with col3:
            params['macd_signal'] = st.number_input(
                "Signal Line Period",
                min_value=5,
                max_value=15,
                value=current_params.get('macd_signal', 9),
                step=1,
                help="Signal line smoothing period"
            )
    
    return params


def get_default_strategy_parameters(strategy_type: str) -> dict:
    """Get default parameters for a strategy"""
    
    defaults = {
        'simple': {
            'profit_target': 0.20,  # 20%
            'stop_loss': 0.10,      # 10%
            'hold_threshold': 0.05   # 5%
        },
        'moving_average': {
            'short_ma': 20,
            'long_ma': 50
        },
        'rsi': {
            'rsi_period': 14,
            'oversold_level': 30,
            'overbought_level': 70
        },
        'bollinger_bands': {
            'bb_period': 20,
            'bb_std': 2.0
        },
        'macd': {
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9
        }
    }
    
    return defaults.get(strategy_type, defaults['simple'])
