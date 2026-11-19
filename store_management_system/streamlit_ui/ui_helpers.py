"""
UI Helper functions for Streamlit Store Management System.
Uses native Streamlit st.html() to render HTML/CSS directly without Markdown parsing,
preventing whitespace/indentation from triggering Markdown code blocks (<pre><code>).
"""

import streamlit as st


def render_html(html_str: str):
    """Renders HTML directly into the DOM using native st.html without Markdown parsing."""
    if html_str and html_str.strip():
        st.html(html_str)
