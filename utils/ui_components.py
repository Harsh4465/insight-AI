import streamlit as st
import pandas as pd

def safe_dataframe(df, use_container_width=True, height=None, key=None):
    """
    Renders a dataframe using st.dataframe if possible.
    If pyarrow is blocked by system policy, falls back to raw HTML rendering
    to bypass all Streamlit-internal pyarrow imports.
    """
    try:
        # Attempt to render with st.dataframe (interactive)
        return st.dataframe(df, use_container_width=use_container_width, height=height, key=key)
    except Exception as e:
        # If it fails (e.g. DLL load failed for pyarrow), use Pandas to_html
        # This completely avoids st.dataframe, st.table, and st.write(df)
        
        # Check if it's a Styler object
        if hasattr(df, 'to_html'):
            html = df.to_html()
        else:
            # Fallback for raw dataframes
            html = df.to_html(classes='table table-striped', index=False)
            
        # Display as Markdown HTML
        st.markdown(
            f'<div style="overflow-x:auto; background:rgba(255,255,255,0.05); border-radius:10px; padding:10px; border:1px solid rgba(255,255,255,0.1); color:white;">{html}</div>', 
            unsafe_allow_html=True
        )
        return None

def scroll_to_top():
    """Forces the browser to scroll to the top of the page."""
    st.components.v1.html(
        "<script>window.parent.scrollTo({top: 0, behavior: 'smooth'});</script>",
        height=0
    )

def scroll_to_bottom():
    """Forces the browser to scroll to the bottom of the page."""
    st.components.v1.html(
        "<script>window.parent.scrollTo({top: window.parent.document.body.scrollHeight, behavior: 'smooth'});</script>",
        height=0
    )

def render_styled_df(df, styler=None, row_count=10):
    """
    Utility to render a styled dataframe with a fallback.
    """
    display_df = df.head(row_count)
    if styler:
        # Apply styler to the slice
        styled_df = display_df.style.apply(styler, axis=None) if callable(styler) else styler
        return safe_dataframe(styled_df)
    else:
        return safe_dataframe(display_df)
