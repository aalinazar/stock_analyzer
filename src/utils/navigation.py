"""
Navigation Constants and Functions

Centralized navigation structure and helpers for the stock analyzer application.
"""

# Define navigation structure
CATEGORIES = {
    "Portfolio Management": [
        "Portfolio Overview", 
        "Add Stock", 
        "Edit Portfolio",
        "Sell Stock",
        "Sales History",
        "Portfolio Recommendations"
    ],
    "Watchlist Management": [
        "Watchlist",
        "Add to Watchlist",
        "Edit Watchlist",
        "Import Watchlist from CSV",
        "Watchlist Recommendations"
    ],
    "Analysis & Tools": [
        "Trading Strategy"
    ],
    "Settings": [
        "Settings"
    ]
}


def initialize_session_state():
    """Initialize session state for navigation"""
    import streamlit as st
    
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = "Portfolio Management"
    if 'selected_page' not in st.session_state:
        st.session_state.selected_page = "Portfolio Overview"


def update_category():
    """Reset selected page when category changes"""
    import streamlit as st
    
    if st.session_state.selected_category in CATEGORIES:
        st.session_state.selected_page = CATEGORIES[st.session_state.selected_category][0]


def update_page():
    """Update page selection"""
    pass


def render_navigation():
    """Render the navigation sidebar"""
    import streamlit as st
    
    # Sidebar for navigation
    st.sidebar.title("📈 Portfolio Management")
    
    # Initialize session state
    initialize_session_state()
    
    # Category dropdown
    category = st.sidebar.selectbox(
        "Choose a category",
        list(CATEGORIES.keys()),
        index=list(CATEGORIES.keys()).index(st.session_state.selected_category),
        key="selected_category",
        on_change=update_category
    )
    
    # Dynamic page dropdown based on selected category
    available_pages = CATEGORIES[category]
    page_index = available_pages.index(st.session_state.selected_page) if st.session_state.selected_page in available_pages else 0
    
    page = st.sidebar.selectbox(
        "Choose a page",
        available_pages,
        index=page_index,
        key="selected_page",
        on_change=update_page
    )
    
    return page
