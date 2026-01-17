"""
Trading Pages Module

Main entry point for all trading-related pages including:
- Strategy configuration
- Trading recommendations
- Performance analysis
- Strategy management
"""

import streamlit as st
from src.trading.strategy_config import trading_strategy_config_page
from src.trading.recommendations import trading_recommendations_page
from src.utils.ui_components import display_alert_box


def trading_strategy_page():
    """Main trading strategy page with navigation"""
    
    st.header("🎯 Trading Strategy Center")
    
    # Introduction
    st.write("""
    Welcome to the Trading Strategy Center! This comprehensive suite helps you:
    - Configure and manage trading strategies for your portfolio
    - Get AI-powered trading recommendations
    - Analyze strategy performance
    - Optimize your trading decisions
    """)
    
    # Main navigation tabs
    tab1, tab2, tab3 = st.tabs(["⚙️ Strategy Configuration", "💡 Recommendations", "📈 Overview"])
    
    with tab1:
        trading_strategy_config_page()
    
    with tab2:
        trading_recommendations_page()
    
    with tab3:
        trading_overview_page()


def trading_overview_page():
    """Display trading strategy overview dashboard"""
    st.subheader("📈 Trading Strategy Overview")
    
    from src.database import db
    from src.trading_strategy import strategy
    
    # Get portfolio and watchlist data
    portfolio = db.get_portfolio() or []
    watchlist = db.get_watchlist() or []
    
    if not portfolio and not watchlist:
        display_alert_box("📝 No data available. Add stocks to your portfolio or watchlist to see trading insights.", "info")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Portfolio Stocks", len(portfolio))
    with col2:
        st.metric("Watchlist Stocks", len(watchlist))
    with col3:
        # Count configured strategies
        configured_strategies = 0
        for stock in portfolio:
            if db.get_strategy_settings(stock['ticker']):
                configured_strategies += 1
        st.metric("Configured Strategies", configured_strategies)
    with col4:
        st.metric("Available Strategies", 5)  # Simple, MA, RSI, BB, MACD
    
    # Strategy information
    st.subheader("🎯 Available Trading Strategies")
    
    strategy_info = [
        {
            'name': 'Simple Strategy',
            'description': 'Basic profit/loss targets with fixed stop losses',
            'best_for': 'Beginners and conservative trading',
            'difficulty': 'Easy',
            'timeframe': 'Short to Medium'
        },
        {
            'name': 'Moving Average Crossover',
            'description': 'Uses MA crossovers for trend following signals',
            'best_for': 'Trending markets and medium-term trading',
            'difficulty': 'Medium',
            'timeframe': 'Medium'
        },
        {
            'name': 'RSI (Relative Strength Index)',
            'description': 'Identifies overbought/oversold conditions',
            'best_for': 'Range-bound markets and reversal trading',
            'difficulty': 'Medium',
            'timeframe': 'Short to Medium'
        },
        {
            'name': 'Bollinger Bands',
            'description': 'Volatility-based breakout and reversal signals',
            'best_for': 'Volatility trading and breakout strategies',
            'difficulty': 'Medium',
            'timeframe': 'Short to Medium'
        },
        {
            'name': 'MACD',
            'description': 'Momentum indicator for trend confirmation',
            'best_for': 'Momentum trading and trend analysis',
            'difficulty': 'Advanced',
            'timeframe': 'Medium to Long'
        }
    ]
    
    # Display strategy cards
    for i, strategy in enumerate(strategy_info):
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"**{strategy['name']}**")
            st.write(strategy['description'])
            st.write(f"Best for: {strategy['best_for']}")
        
        with col2:
            st.metric("Difficulty", strategy['difficulty'])
        
        with col3:
            st.metric("Timeframe", strategy['timeframe'])
        
        if i < len(strategy_info) - 1:
            st.markdown("---")
    
    # Quick actions section
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⚙️ Configure All Portfolio Stocks", type="primary"):
            st.session_state.navigate_to = "Strategy Configuration"
            st.rerun()
    
    with col2:
        if st.button("💡 Get Portfolio Recommendations"):
            st.session_state.navigate_to = "Recommendations"
            st.rerun()
    
    with col3:
        if st.button("📊 View Performance"):
            st.session_state.navigate_to = "Recommendations"
            st.session_state.performance_tab = True
            st.rerun()
    
    # Recent activity
    st.subheader("📅 Recent Trading Activity")
    
    recent_recommendations = db.get_recent_recommendations(7)  # Last 7 days
    
    if recent_recommendations:
        # Activity summary
        buy_count = sum(1 for r in recent_recommendations if r['action'] == 'BUY')
        sell_count = sum(1 for r in recent_recommendations if r['action'] == 'SELL')
        hold_count = sum(1 for r in recent_recommendations if r['action'] == 'HOLD')
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Recent Buy Signals", buy_count, "Last 7 days")
        with col2:
            st.metric("Recent Sell Signals", sell_count, "Last 7 days")
        with col3:
            st.metric("Recent Hold Signals", hold_count, "Last 7 days")
        
        # Recent recommendations table
        st.write("**Latest Recommendations:**")
        
        # Show top 5 most recent recommendations
        recent_df = recent_recommendations[:5] if len(recent_recommendations) > 5 else recent_recommendations
        
        for rec in recent_df:
            action_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}.get(rec['action'], '⚪')
            
            col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
            
            with col1:
                st.write(f"{action_emoji} **{rec['ticker']}**")
            
            with col2:
                st.write(f"{rec['action']}")
            
            with col3:
                st.write(rec['reason'][:60] + "..." if len(rec['reason']) > 60 else rec['reason'])
            
            with col4:
                st.write(f"{rec['confidence']:.1%}")
        
        if st.button("View All Recent Activity"):
            st.session_state.navigate_to = "Recommendations"
            st.session_state.performance_tab = True
            st.rerun()
    
    else:
        display_alert_box("📝 No recent trading activity. Start by configuring strategies for your portfolio stocks!", "info")
    
    # Educational content
    st.subheader("📚 Trading Strategy Education")
    
    with st.expander("🎯 Understanding Trading Strategies", expanded=False):
        st.write("""
        **Trading strategies** are systematic approaches to making buy/sell decisions based on predefined rules and technical indicators.
        
        **Key Concepts:**
        - **Technical Indicators:** Mathematical calculations based on historical price data
        - **Signals:** Buy/sell recommendations generated by strategies
        - **Confidence:** How certain the strategy is about its recommendation
        - **Timeframes:** Different strategies work better for different trading horizons
        
        **Best Practices:**
        1. Start with simple strategies if you're a beginner
        2. Use multiple strategies for diversification
        3. Regularly review and adjust strategy parameters
        4. Consider market conditions when choosing strategies
        5. Always combine strategy signals with fundamental analysis
        """)
    
    with st.expander("⚠️ Risk Management", expanded=False):
        st.write("""
        **Important Risk Management Principles:**
        
        1. **Never risk more than you can afford to lose**
        2. **Use stop-losses** to limit potential losses
        3. **Diversify** across different stocks and sectors
        4. **Position sizing** - don't put all your capital in one trade
        5. **Keep emotions in check** - stick to your strategy
        6. **Regular portfolio review** - monthly or quarterly rebalancing
        7. **Consider tax implications** of your trading decisions
        
        **Remember:** These strategies are for educational purposes. Always consult with a financial advisor before making investment decisions.
        """)


def get_strategy_recommendation_for_new_user():
    """Get strategy recommendations for new users based on their profile"""
    
    st.subheader("🎯 Strategy Recommendations for You")
    
    st.write("Answer a few questions to get personalized strategy recommendations:")
    
    # User profile questions
    col1, col2 = st.columns(2)
    
    with col1:
        experience = st.selectbox(
            "Trading Experience",
            options=["Beginner", "Intermediate", "Advanced", "Expert"],
            help="Your level of trading experience"
        )
        
        risk_tolerance = st.selectbox(
            "Risk Tolerance",
            options=["Very Low", "Low", "Medium", "High", "Very High"],
            help="How much risk are you comfortable with?"
        )
    
    with col2:
        time_commitment = st.selectbox(
            "Time Commitment",
            options=["Minimal (15 min/day)", "Low (30 min/day)", "Medium (1 hour/day)", "High (2+ hours/day)"],
            help="How much time can you dedicate to trading?"
        )
        
        trading_style = st.selectbox(
            "Trading Style",
            options=["Long-term Investor", "Swing Trader", "Position Trader", "Active Trader"],
            help="Your preferred trading approach"
        )
    
    if st.button("Get Recommendations", type="primary"):
        # Generate recommendations based on profile
        recommendations = generate_profile_recommendations(
            experience, risk_tolerance, time_commitment, trading_style
        )
        
        st.subheader("🎯 Your Recommended Strategies")
        
        for i, rec in enumerate(recommendations, 1):
            with st.expander(f"{i}. {rec['name']} - {rec['priority']}", expanded=i==1):
                st.write(f"**Why this strategy:** {rec['reason']}")
                st.write(f"**Best suited for:** {rec['best_for']}")
                st.write(f"**Expected performance:** {rec['performance']}")
                st.write(f"**Complexity:** {rec['complexity']}")


def generate_profile_recommendations(experience: str, risk_tolerance: str, 
                                   time_commitment: str, trading_style: str) -> list:
    """Generate strategy recommendations based on user profile"""
    
    recommendations = []
    
    # Simple strategy for beginners and low risk tolerance
    if experience in ["Beginner", "Intermediate"] or risk_tolerance in ["Very Low", "Low"]:
        recommendations.append({
            'name': 'Simple Strategy',
            'priority': 'Highly Recommended',
            'reason': 'Easy to understand and implement with clear entry/exit rules',
            'best_for': 'Beginners and conservative traders',
            'performance': 'Conservative but steady returns',
            'complexity': 'Easy'
        })
    
    # Moving Average for trend followers
    if trading_style in ["Swing Trader", "Position Trader"] and experience != "Beginner":
        recommendations.append({
            'name': 'Moving Average Crossover',
            'priority': 'Recommended',
            'reason': 'Excellent for identifying trends and momentum shifts',
            'best_for': 'Trend following and medium-term trading',
            'performance': 'Good in trending markets',
            'complexity': 'Medium'
        })
    
    # RSI for active traders
    if time_commitment in ["Medium", "High"] and trading_style in ["Active Trader", "Swing Trader"]:
        recommendations.append({
            'name': 'RSI',
            'priority': 'Recommended',
            'reason': 'Great for identifying overbought/oversold conditions',
            'best_for': 'Range-bound markets and short-term trading',
            'performance': 'Good in volatile, ranging markets',
            'complexity': 'Medium'
        })
    
    # Bollinger Bands for volatility trading
    if risk_tolerance in ["Medium", "High"] and experience != "Beginner":
        recommendations.append({
            'name': 'Bollinger Bands',
            'priority': 'Consider',
            'reason': 'Effective for volatility-based breakout strategies',
            'best_for': 'Volatility trading and market analysis',
            'performance': 'High potential in volatile markets',
            'complexity': 'Medium'
        })
    
    # MACD for advanced traders
    if experience in ["Advanced", "Expert"] and time_commitment in ["Medium", "High"]:
        recommendations.append({
            'name': 'MACD',
            'priority': 'Advanced Option',
            'reason': 'Sophisticated momentum analysis with multiple signals',
            'best_for': 'Advanced technical analysis and trend confirmation',
            'performance': 'Excellent for experienced traders',
            'complexity': 'Advanced'
        })
    
    return recommendations
