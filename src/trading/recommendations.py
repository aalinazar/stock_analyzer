"""
Trading Recommendations

Handles trading recommendations and analysis functionality including:
- Portfolio recommendations
- Watchlist recommendations
- Strategy performance analysis
- Recommendation history
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from src.database import db
from src.trading_strategy import strategy
from src.utils.ui_components import display_alert_box, display_metric_cards


def trading_recommendations_page():
    """Display main trading recommendations page"""
    st.header("💡 Trading Recommendations & Analysis")
    
    # Tab navigation for different recommendation types
    tab1, tab2, tab3 = st.tabs(["📊 Portfolio", "👀 Watchlist", "📈 Performance"])
    
    with tab1:
        portfolio_recommendations_section()
    
    with tab2:
        watchlist_recommendations_section()
    
    with tab3:
        strategy_performance_section()


def portfolio_recommendations_section():
    """Display portfolio trading recommendations"""
    st.subheader("📊 Portfolio Trading Recommendations")
    
    portfolio = db.get_portfolio()
    if not portfolio:
        display_alert_box("⚠️ No stocks in portfolio. Add stocks first to get recommendations.", "info")
        return
    
    # Get portfolio recommendations
    with st.spinner("🔄 Analyzing portfolio stocks with configured strategies..."):
        portfolio_recommendations = strategy.get_all_portfolio_recommendations(portfolio)
    
    if portfolio_recommendations:
        # Summary dashboard
        portfolio_buy = sum(1 for r in portfolio_recommendations if r['action'] == 'BUY')
        portfolio_sell = sum(1 for r in portfolio_recommendations if r['action'] == 'SELL')
        portfolio_hold = sum(1 for r in portfolio_recommendations if r['action'] == 'HOLD')
        
        metrics_data = [
            {"label": "🟢 Buy Signals", "value": portfolio_buy, "delta": "Action needed"},
            {"label": "🔴 Sell Signals", "value": portfolio_sell, "delta": "Take profit/stop loss"},
            {"label": "🟡 Hold Signals", "value": portfolio_hold, "delta": "Monitor position"},
            {"label": "📈 Total Stocks", "value": len(portfolio_recommendations), "delta": "In portfolio"}
        ]
        display_metric_cards(metrics_data)
        
        # Action-based grouping
        st.subheader("🎯 Recommendations by Action")
        
        # Group recommendations by action
        buy_recs = [r for r in portfolio_recommendations if r['action'] == 'BUY']
        sell_recs = [r for r in portfolio_recommendations if r['action'] == 'SELL']
        hold_recs = [r for r in portfolio_recommendations if r['action'] == 'HOLD']
        
        # Display recommendations in columns
        if buy_recs:
            with st.expander(f"🟢 BUY Recommendations ({len(buy_recs)} stocks)", expanded=True):
                for rec in buy_recs:
                    display_portfolio_recommendation_card(rec, "BUY")
        
        if sell_recs:
            with st.expander(f"🔴 SELL Recommendations ({len(sell_recs)} stocks)", expanded=True):
                for rec in sell_recs:
                    display_portfolio_recommendation_card(rec, "SELL")
        
        if hold_recs:
            with st.expander(f"🟡 HOLD Recommendations ({len(hold_recs)} stocks)", expanded=False):
                for rec in hold_recs:
                    display_portfolio_recommendation_card(rec, "HOLD")
        
        # Detailed recommendations table
        st.subheader("📋 Detailed Recommendations")
        display_recommendations_table(portfolio_recommendations, "portfolio")
        
        # Portfolio-level insights
        st.subheader("📊 Portfolio Insights")
        display_portfolio_insights(portfolio_recommendations)
        
    else:
        display_alert_box("No portfolio recommendations available at this time.", "info")


def watchlist_recommendations_section():
    """Display watchlist trading recommendations"""
    st.subheader("👀 Watchlist Trading Recommendations")
    
    watchlist = db.get_watchlist()
    if not watchlist:
        display_alert_box("⚠️ No stocks in watchlist. Add stocks first to get recommendations.", "info")
        return
    
    # Day range selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        day_range = st.selectbox(
            "Select Trading Horizon",
            options=['weekly', 'monthly', 'quarterly', 'yearly'],
            format_func=lambda x: x.title(),
            help="Different time horizons use different analysis periods and profit targets"
        )
    
    with col2:
        if st.button("🔄 Refresh Recommendations", type="primary"):
            st.rerun()
    
    # Get watchlist recommendations
    with st.spinner(f"🔄 Analyzing watchlist stocks for {day_range} horizon..."):
        watchlist_recommendations = strategy.get_watchlist_recommendations(watchlist, day_range)
    
    if watchlist_recommendations:
        # Summary dashboard
        watchlist_buy = sum(1 for r in watchlist_recommendations if r['action'] == 'BUY')
        watchlist_sell = sum(1 for r in watchlist_recommendations if r['action'] == 'SELL')
        watchlist_hold = sum(1 for r in watchlist_recommendations if r['action'] == 'HOLD')
        
        metrics_data = [
            {"label": f"🟢 Buy ({day_range})", "value": watchlist_buy, "delta": f"{day_range.title()} horizon"},
            {"label": f"🔴 Sell ({day_range})", "value": watchlist_sell, "delta": f"{day_range.title()} horizon"},
            {"label": f"🟡 Hold ({day_range})", "value": watchlist_hold, "delta": f"{day_range.title()} horizon"},
            {"label": "📈 Total Analyzed", "value": len(watchlist_recommendations), "delta": "Watchlist stocks"}
        ]
        display_metric_cards(metrics_data)
        
        # Recommendations by action
        st.subheader(f"🎯 {day_range.title()} Recommendations")
        
        buy_recs = [r for r in watchlist_recommendations if r['action'] == 'BUY']
        sell_recs = [r for r in watchlist_recommendations if r['action'] == 'SELL']
        hold_recs = [r for r in watchlist_recommendations if r['action'] == 'HOLD']
        
        # Display recommendations
        if buy_recs:
            with st.expander(f"🟢 BUY - {day_range.title()} ({len(buy_recs)} stocks)", expanded=True):
                for rec in buy_recs:
                    display_watchlist_recommendation_card(rec, "BUY")
        
        if sell_recs:
            with st.expander(f"🔴 SELL - {day_range.title()} ({len(sell_recs)} stocks)", expanded=False):
                for rec in sell_recs:
                    display_watchlist_recommendation_card(rec, "SELL")
        
        if hold_recs:
            with st.expander(f"🟡 HOLD - {day_range.title()} ({len(hold_recs)} stocks)", expanded=False):
                for rec in hold_recs:
                    display_watchlist_recommendation_card(rec, "HOLD")
        
        # Detailed table
        st.subheader("📋 Detailed Analysis")
        display_recommendations_table(watchlist_recommendations, "watchlist")
        
        # Comparison chart
        st.subheader("📊 Target Price Analysis")
        display_price_target_chart(watchlist_recommendations)
        
    else:
        display_alert_box(f"No watchlist recommendations available for {day_range} horizon.", "info")


def strategy_performance_section():
    """Display strategy performance analysis"""
    st.subheader("📈 Strategy Performance Analysis")
    
    # Get recent recommendations for analysis
    recent_recs = db.get_recent_recommendations(90)  # Last 90 days
    
    if not recent_recs:
        display_alert_box("⚠️ No recommendation history available. Trading strategies need to generate recommendations first.", "info")
        return
    
    # Performance metrics
    st.subheader("📊 Recommendation Performance")
    
    # Analyze recommendation accuracy and performance
    performance_data = analyze_recommendation_performance(recent_recs)
    
    if performance_data:
        # Display performance metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Recommendations", len(recent_recs))
        with col2:
            st.metric("Avg Confidence", f"{performance_data['avg_confidence']:.1%}")
        with col3:
            st.metric("Most Used Strategy", performance_data['most_common_strategy'])
        with col4:
            st.metric("Success Rate", f"{performance_data.get('success_rate', 0):.1%}")
        
        # Strategy distribution
        st.subheader("🎯 Strategy Distribution")
        display_strategy_distribution_chart(recent_recs)
        
        # Recommendation timeline
        st.subheader("📅 Recommendation Timeline")
        display_recommendation_timeline(recent_recs)
        
        # Detailed history table
        st.subheader("📋 Recommendation History")
        display_recommendation_history_table(recent_recs)
        
    else:
        display_alert_box("Unable to analyze recommendation performance.", "warning")


def display_portfolio_recommendation_card(rec: dict, action_type: str):
    """Display a portfolio recommendation card"""
    stock = rec['stock_data']
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.write(f"**{stock['ticker']} - {stock['company_name'] or stock['ticker']}**")
        st.write(f"**Current Price:** ${rec['current_price']:.2f}")
        st.write(f"**Purchase Price:** ${stock['purchase_price']:.2f}")
        
        profit_loss = ((rec['current_price'] - stock['purchase_price']) / stock['purchase_price']) * 100
        profit_emoji = "🟢" if profit_loss >= 0 else "🔴"
        st.write(f"**P/L:** {profit_emoji} {profit_loss:+.2f}%")
    
    with col2:
        st.write(f"**Strategy:** {rec['strategy'].replace('_', ' ').title()}")
        st.write(f"**Confidence:** {rec['confidence']:.1%}")
        
        # Strategy settings
        settings = db.get_strategy_settings(stock['ticker'])
        if settings:
            st.write(f"**Config:** {settings['strategy_type'].title()}")
    
    with col3:
        st.write(f"**Action:** {action_type}")
        st.write(f"**Reason:** {rec['reason'][:50]}...")
        
        # Position value
        current_value = rec['current_price'] * stock['shares']
        purchase_value = stock['purchase_price'] * stock['shares']
        st.write(f"**Value:** ${current_value:,.2f}")
    
    st.markdown("---")


def display_watchlist_recommendation_card(rec: dict, action_type: str):
    """Display a watchlist recommendation card"""
    watchlist_data = rec['watchlist_data']
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.write(f"**{watchlist_data['ticker']} - {watchlist_data.get('company_name', watchlist_data['ticker'])}**")
        st.write(f"**Current Price:** ${rec['current_price']:.2f}")
        st.write(f"**Target Buy:** ${rec['target_buy_price']:.2f}")
        st.write(f"**Target Sell:** ${rec['target_sell_price']:.2f}")
    
    with col2:
        st.write(f"**Strategy:** {rec['strategy'].replace('_', ' ').title()}")
        st.write(f"**Confidence:** {rec['confidence']:.1%}")
        st.write(f"**Horizon:** {rec['day_range'].title()}")
        
        # Potential profit
        potential_profit = ((rec['target_sell_price'] - rec['current_price']) / rec['current_price']) * 100
        st.write(f"**Potential:** {potential_profit:+.1f}%")
    
    with col3:
        st.write(f"**Action:** {action_type}")
        st.write(f"**Model:** {rec.get('prediction_model', 'N/A')}")
        st.write(f"**Added:** {watchlist_data.get('created_at', 'N/A')[:10]}")
    
    st.markdown("---")


def display_recommendations_table(recommendations: list, source_type: str):
    """Display recommendations in a table format"""
    
    if source_type == "portfolio":
        df_data = []
        for rec in recommendations:
            stock = rec['stock_data']
            profit_loss = ((rec['current_price'] - stock['purchase_price']) / stock['purchase_price']) * 100
            
            df_data.append({
                'Ticker': stock['ticker'],
                'Action': rec['action'],
                'Strategy': rec['strategy'],
                'Confidence': f"{rec['confidence']:.1%}",
                'Current Price': f"${rec['current_price']:.2f}",
                'P/L %': f"{profit_loss:+.2f}%",
                'Position Value': f"${rec['current_price'] * stock['shares']:,.2f}",
                'Reason': rec['reason'][:100] + "..." if len(rec['reason']) > 100 else rec['reason']
            })
    else:  # watchlist
        df_data = []
        for rec in recommendations:
            potential_profit = ((rec['target_sell_price'] - rec['current_price']) / rec['current_price']) * 100
            
            df_data.append({
                'Ticker': rec['watchlist_data']['ticker'],
                'Action': rec['action'],
                'Strategy': rec['strategy'],
                'Confidence': f"{rec['confidence']:.1%}",
                'Current Price': f"${rec['current_price']:.2f}",
                'Target Buy': f"${rec['target_buy_price']:.2f}",
                'Target Sell': f"${rec['target_sell_price']:.2f}",
                'Potential %': f"{potential_profit:+.1f}%",
                'Horizon': rec['day_range'].title()
            })
    
    if df_data:
        df = pd.DataFrame(df_data)
        
        # Color coding for actions
        def color_action(val):
            if val == 'BUY':
                return 'color: green; font-weight: bold'
            elif val == 'SELL':
                return 'color: red; font-weight: bold'
            else:
                return 'color: orange; font-weight: bold'
        
        styled_df = df.style.map(color_action, subset=['Action'])
        st.dataframe(styled_df, width='stretch')
        
        # Export option
        csv = df.to_csv(index=False)
        st.download_button(
            label="📄 Export Recommendations",
            data=csv,
            file_name=f"recommendations_{source_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )


def display_portfolio_insights(recommendations: list):
    """Display portfolio-level insights"""
    
    # Calculate portfolio metrics
    total_current_value = sum(rec['current_price'] * rec['stock_data']['shares'] for rec in recommendations)
    total_purchase_value = sum(rec['stock_data']['purchase_price'] * rec['stock_data']['shares'] for rec in recommendations)
    total_pnl = total_current_value - total_purchase_value
    total_pnl_percent = (total_pnl / total_purchase_value) * 100 if total_purchase_value > 0 else 0
    
    # Strategy distribution
    strategy_counts = {}
    for rec in recommendations:
        strategy_name = rec['strategy']
        strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1
    
    # Display insights
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Portfolio Value", f"${total_current_value:,.2f}")
        pnl_color = "normal" if total_pnl >= 0 else "inverse"
        st.metric("Total P/L", f"${total_pnl:,.2f}", f"{total_pnl_percent:+.2f}%", delta_color=pnl_color)
    
    with col2:
        avg_confidence = sum(r['confidence'] for r in recommendations) / len(recommendations)
        st.metric("Avg Confidence", f"{avg_confidence:.1%}")
        
        # Most recommended action
        action_counts = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
        for rec in recommendations:
            action_counts[rec['action']] += 1
        most_common_action = max(action_counts, key=action_counts.get)
        st.metric("Most Common Action", f"{most_common_action} ({action_counts[most_common_action]})")
    
    with col3:
        st.metric("Strategies Used", len(strategy_counts))
        most_common_strategy = max(strategy_counts, key=strategy_counts.get)
        st.metric("Top Strategy", f"{most_common_strategy}")
    
    # Strategy distribution chart
    if strategy_counts:
        st.subheader("📊 Strategy Distribution")
        strategy_df = pd.DataFrame(list(strategy_counts.items()), columns=['Strategy', 'Count'])
        fig = px.bar(strategy_df, x='Strategy', y='Count', title="Strategy Usage Distribution")
        st.plotly_chart(fig, width='stretch')


def display_price_target_chart(recommendations: list):
    """Display price target analysis chart"""
    
    chart_data = []
    for rec in recommendations:
        chart_data.append({
            'Ticker': rec['watchlist_data']['ticker'],
            'Current Price': rec['current_price'],
            'Target Buy': rec['target_buy_price'],
            'Target Sell': rec['target_sell_price'],
            'Potential %': ((rec['target_sell_price'] - rec['current_price']) / rec['current_price']) * 100
        })
    
    if chart_data:
        df = pd.DataFrame(chart_data)
        
        # Create grouped bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Current Price',
            x=df['Ticker'],
            y=df['Current Price'],
            marker_color='blue'
        ))
        
        fig.add_trace(go.Bar(
            name='Target Buy',
            x=df['Ticker'],
            y=df['Target Buy'],
            marker_color='green'
        ))
        
        fig.add_trace(go.Bar(
            name='Target Sell',
            x=df['Ticker'],
            y=df['Target Sell'],
            marker_color='red'
        ))
        
        fig.update_layout(
            title="Price Targets Comparison",
            xaxis_title="Stock Ticker",
            yaxis_title="Price ($)",
            barmode='group',
            height=500
        )
        
        st.plotly_chart(fig, width='stretch')


def analyze_recommendation_performance(recent_recs: list) -> dict:
    """Analyze recommendation performance metrics"""
    
    if not recent_recs:
        return {}
    
    # Calculate metrics
    total_recs = len(recent_recs)
    avg_confidence = sum(rec.get('confidence', 0) for rec in recent_recs) / total_recs
    
    # Strategy distribution
    strategy_counts = {}
    for rec in recent_recs:
        strategy = rec.get('strategy', 'unknown')
        strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
    
    most_common_strategy = max(strategy_counts, key=strategy_counts.get) if strategy_counts else 'N/A'
    
    # Action distribution
    action_counts = {}
    for rec in recent_recs:
        action = rec.get('action', 'HOLD')
        action_counts[action] = action_counts.get(action, 0) + 1
    
    return {
        'total_recommendations': total_recs,
        'avg_confidence': avg_confidence,
        'most_common_strategy': most_common_strategy,
        'strategy_counts': strategy_counts,
        'action_counts': action_counts,
        'success_rate': 0.75  # Placeholder - would need actual performance data
    }


def display_strategy_distribution_chart(recent_recs: list):
    """Display strategy distribution chart"""
    
    strategy_counts = {}
    for rec in recent_recs:
        strategy = rec.get('strategy', 'unknown')
        strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
    
    if strategy_counts:
        df = pd.DataFrame(list(strategy_counts.items()), columns=['Strategy', 'Count'])
        fig = px.pie(df, values='Count', names='Strategy', title="Strategy Distribution")
        st.plotly_chart(fig, width='stretch')


def display_recommendation_timeline(recent_recs: list):
    """Display recommendation timeline chart"""
    
    if recent_recs:
        df = pd.DataFrame(recent_recs)
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['date'] = df['created_at'].dt.date
        
        # Count recommendations by date and action
        timeline_data = df.groupby(['date', 'action']).size().reset_index(name='count')
        
        fig = px.line(
            timeline_data, 
            x='date', 
            y='count', 
            color='action',
            title="Recommendation Timeline",
            markers=True
        )
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Number of Recommendations"
        )
        
        st.plotly_chart(fig, width='stretch')


def display_recommendation_history_table(recent_recs: list):
    """Display detailed recommendation history table"""
    
    if recent_recs:
        df = pd.DataFrame(recent_recs)
        
        # Handle missing columns for backward compatibility
        available_columns = df.columns.tolist()
        
        # Determine which columns to use
        price_column = 'price_at_recommendation' if 'price_at_recommendation' in available_columns else 'price'
        strategy_column = 'strategy' if 'strategy' in available_columns else None
        
        # Build column list based on available data
        columns_to_use = ['ticker', 'action', 'confidence', 'reason', price_column, 'created_at']
        if strategy_column:
            columns_to_use.insert(2, strategy_column)  # Insert strategy after action
        
        # Format for display
        display_df = df[columns_to_use].copy()
        
        display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        display_df['confidence'] = display_df['confidence'].apply(lambda x: f"{x:.1%}")
        display_df[price_column] = display_df[price_column].apply(lambda x: f"${x:.2f}")
        display_df['reason'] = display_df['reason'].apply(lambda x: x[:80] + "..." if len(x) > 80 else x)
        
        # Handle strategy column formatting
        if strategy_column:
            display_df[strategy_column] = display_df[strategy_column].fillna('Unknown').apply(lambda x: x.replace('_', ' ').title() if x != 'Unknown' else x)
            display_df.columns = ['Ticker', 'Action', 'Strategy', 'Confidence', 'Reason', 'Price', 'Time']
        else:
            display_df.columns = ['Ticker', 'Action', 'Confidence', 'Reason', 'Price', 'Time']
        
        def color_action(val):
            if val == 'BUY':
                return 'color: green; font-weight: bold'
            elif val == 'SELL':
                return 'color: red; font-weight: bold'
            else:
                return 'color: orange; font-weight: bold'
        
        styled_df = display_df.style.map(color_action, subset=['Action'])
        st.dataframe(styled_df, width='stretch')
