import streamlit as st
import os
import sys
from view import chatgen
from view import dashboard_2
from view import dashboard_1
from view import about_df

sys.path.append(os.path.join(os.path.dirname(__file__), 'view'))

def load_css(css_file):
    with open(css_file) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def main():
    st.set_page_config(
        layout="wide",
        initial_sidebar_state="expanded"
    )

    load_css('style.css')

    PAGES = {
        "Tổng quan dữ liệu mẫu": about_df.main,
        "Chuyển việc": dashboard_1.main,    
        "Làm trái ngành": dashboard_2.main,    
        "Chart Generator": chatgen.main
    }

    with st.sidebar:
        st.markdown("<h1 class='nav-title'>Job Analysis</h1>", unsafe_allow_html=True)
        for page_name in PAGES:
            if st.button(
                page_name,
                key=page_name,
                use_container_width=True,
            ):
                st.session_state.page = page_name

    st.markdown("""
        <div class="footer">
            <p>© Nguyen Tien Thinh - GCH200796</p>
        </div>
    """, unsafe_allow_html=True)

    if "page" not in st.session_state:
        st.session_state.page = list(PAGES.keys())[0]

    PAGES[st.session_state.page]()

if __name__ == "__main__":
    main()
