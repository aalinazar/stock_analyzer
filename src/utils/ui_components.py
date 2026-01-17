"""
Reusable UI Components

Common Streamlit UI components used across the application.
"""

import streamlit as st
import pandas as pd
from datetime import datetime


def display_metric_cards(metrics_data, columns=4):
    """
    Display metric cards in a grid layout.
    
    Args:
        metrics_data: List of dictionaries with 'label', 'value', and optionally 'delta' and 'delta_color'
        columns: Number of columns to display (default: 4)
    """
    cols = st.columns(columns)
    
    for i, metric in enumerate(metrics_data):
        col = cols[i % columns]
        
        with col:
            if 'delta' in metric and 'delta_color' in metric:
                st.metric(
                    metric['label'],
                    metric['value'],
                    metric['delta'],
                    delta_color=metric['delta_color']
                )
            elif 'delta' in metric:
                st.metric(
                    metric['label'],
                    metric['value'],
                    metric['delta']
                )
            else:
                st.metric(metric['label'], metric['value'])


def display_confirmation_button(label, confirm_key, message="Are you sure?", button_type="secondary"):
    """
    Display a confirmation button that requires two clicks.
    
    Args:
        label: Button label text
        confirm_key: Session state key for confirmation tracking
        message: Warning message to display
        button_type: Streamlit button type
    """
    if st.session_state.get(confirm_key, False):
        if st.button(label, type=button_type):
            st.session_state[confirm_key] = False
            return True
    else:
        if st.button(label, type=button_type):
            st.session_state[confirm_key] = True
            st.warning(f"⚠️ {message} Click again to confirm.")
    
    return False


def display_stock_info_card(ticker, current_price, purchase_price=None, shares=None):
    """
    Display a compact stock information card.
    
    Args:
        ticker: Stock ticker symbol
        current_price: Current stock price
        purchase_price: Optional purchase price
        shares: Optional number of shares
    """
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Ticker", ticker)
    
    with col2:
        st.metric("Current Price", f"${current_price:.2f}")
    
    with col3:
        if purchase_price:
            pl_percent = ((current_price - purchase_price) / purchase_price) * 100
            pl_color = "normal" if pl_percent >= 0 else "inverse"
            st.metric("P/L %", f"{pl_percent:+.2f}%", delta_color=pl_color)
        elif shares:
            st.metric("Shares", f"{shares:,.0f}")
        else:
            st.metric("Status", "Active")


def display_profit_calculation(purchase_cost, sell_revenue, tax_fee=0):
    """
    Display profit calculation metrics.
    
    Args:
        purchase_cost: Total purchase cost
        sell_revenue: Total sell revenue
        tax_fee: Tax/fee amount
    """
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
    
    return real_profit


def color_dataframe_by_values(df, color_functions):
    """
    Apply color styling to dataframe based on values.
    
    Args:
        df: DataFrame to style
        color_functions: Dictionary mapping column names to color functions
    
    Returns:
        Styled DataFrame
    """
    styled_df = df.style
    
    for column, color_func in color_functions.items():
        if column in df.columns:
            styled_df = styled_df.map(color_func, subset=[column])
    
    return styled_df


def display_expander_card(title, content_func, expanded=False, **expand_kwargs):
    """
    Display content in an expandable card.
    
    Args:
        title: Title of the expander
        content_func: Function that renders the content
        expanded: Whether to start expanded
        **expand_kwargs: Additional arguments for st.expander
    """
    with st.expander(title, expanded=expanded, **expand_kwargs):
        content_func()


def display_download_button(data, filename, label="Download", mime="text/csv"):
    """
    Display a download button with consistent formatting.
    
    Args:
        data: Data to download
        filename: Filename for download
        label: Button label
        mime: MIME type
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    full_filename = f"{filename}_{timestamp}.{mime.split('/')[-1]}"
    
    if isinstance(data, pd.DataFrame):
        data = data.to_csv(index=False)
    
    st.download_button(
        label=f"📄 {label}",
        data=data,
        file_name=full_filename,
        mime=mime
    )


def display_alert_box(message, alert_type="info"):
    """
    Display an alert box with consistent styling.
    
    Args:
        message: Message to display
        alert_type: Type of alert ('info', 'success', 'warning', 'error')
    """
    if alert_type == "success":
        st.success(message)
    elif alert_type == "warning":
        st.warning(message)
    elif alert_type == "error":
        st.error(message)
    else:
        st.info(message)


def display_loading_spinner(message="Loading...", callback=None):
    """
    Display a loading spinner with optional callback.
    
    Args:
        message: Message to display while loading
        callback: Optional function to execute while showing spinner
    """
    with st.spinner(f"🔄 {message}"):
        if callback:
            return callback()
        return None


def create_two_column_layout(left_content=None, right_content=None, ratio=[2, 1]):
    """
    Create a two-column layout with content.
    
    Args:
        left_content: Function or content for left column
        right_content: Function or content for right column
        ratio: Column width ratio
    """
    col1, col2 = st.columns(ratio)
    
    with col1:
        if callable(left_content):
            left_content()
        elif left_content:
            st.write(left_content)
    
    with col2:
        if callable(right_content):
            right_content()
        elif right_content:
            st.write(right_content)
    
    return col1, col2
