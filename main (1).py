import streamlit as st
from common import style

# 페이지 설정
st.set_page_config(
    page_title="BioLab Analyzer",
    page_icon="B",
    layout="wide"
)

style()
st.sidebar.markdown("**BioLab Analyzer**")
st.sidebar.caption("Research workspace")

# DNA 분석 페이지
dna_page = st.Page(
    "pages/1_DNA.py",
    title="DNA 분석",
    default=True,
    icon=":material/genetics:"
)

# BCA 단백질 정량 페이지
bca_page = st.Page(
    "pages/2_BCA_protein.py",
    title="BCA 단백질 정량",
    icon=":material/science:"
)

# PCR 프라이머 분석 페이지
pcr_page = st.Page(
    "pages/3_PCR.py",
    title="PCR 프라이머 분석",
    icon=":material/biotech:"
)

# AI 챗봇 페이지
ai_page = st.Page(
    "pages/4_AI_teacher.py",
    title="AI 생명공학교사",
    icon=":material/chat:"
)

# 사이드바 페이지 이동 메뉴
pg = st.navigation(
    {
        "BioLab Analyzer": [
            dna_page,
            bca_page,
            pcr_page,
            ai_page
        ]
    }
)

# 현재 선택된 페이지 실행
pg.run()
