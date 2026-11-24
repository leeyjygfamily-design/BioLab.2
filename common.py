import streamlit as st
import json

NAMES = ("DNA 분석", "BCA 단백질 정량", "PCR 프라이머 분석", "AI 생명공학교사")

def style():
    st.markdown("""<style>
    .block-container {max-width: 1440px; padding: 2.2rem 2.8rem 4rem;}
    [data-testid="stSidebar"] {border-right:1px solid #dbe3ec;}
    [data-testid="stSidebarNav"] {padding-top:.5rem;}
    [data-testid="stSidebarNav"] a {border-radius:4px; font-size:.9rem;}
    [data-testid="stSidebarNav"] a[aria-current="page"] {background:#dce9fa; color:#174a91; font-weight:600;}
    h1 {font-size:1.85rem !important; font-weight:650 !important; letter-spacing:-.035em;}
    h2 {font-size:1.25rem !important; font-weight:600 !important;}
    h3 {font-size:1.05rem !important; font-weight:600 !important;}
    h1,h2,h3,[data-testid="stMetricLabel"] {overflow-wrap:anywhere;}
    [data-testid="stCaptionContainer"] {color:#596b80;}
    [data-testid="stButton"] button, [data-testid="stDownloadButton"] button, [data-testid="stFormSubmitButton"] button {border-radius:4px; font-weight:500;}
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {border-radius:4px;}
    [data-testid="stTextArea"] textarea {font-family:ui-monospace, monospace; font-size:.86rem;}
    [data-testid="stExpander"] details, [data-testid="stForm"] {border-radius:5px; border-color:#dbe3ec;}
    [data-testid="stMetricValue"] {font-size:1.65rem; font-weight:600; font-variant-numeric:tabular-nums;}
    [data-testid="stMetric"] {border-left:2px solid #dbe3ec; padding-left:14px;}
    [data-testid="stTabs"] [role="tab"] {font-size:.9rem; font-weight:500;}
    [data-testid="stPageLink"] a {border-radius:4px; color:#245ca6;}
    [data-testid="stChatMessage"] {border-radius:5px;}
    @media(max-width:640px) {
      .block-container {padding:1.5rem 1rem 3rem;}
      h1 {font-size:1.5rem !important;}
      [data-testid="stHorizontalBlock"] {flex-wrap:wrap;}
      [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {flex:1 1 100% !important; min-width:0 !important;}
      [data-testid="stButton"] button {white-space:normal;}
    }
    </style>""", unsafe_allow_html=True)

def remember(widget, key):
    # Separate durable values from widgets removed on navigation.
    saved = "ui_saved_" + key
    temporary = "ui_widget_" + key
    if temporary not in st.session_state and saved in st.session_state:
        st.session_state[temporary] = st.session_state[saved]
    value = widget(key=temporary)
    st.session_state[saved] = value
    return value

def guide(text):
    st.caption(text)
    st.caption("제출한 데이터는 같은 세션에서 유지됩니다. 새로고침 전에는 필요한 자료를 다운로드하세요. 넓은 표는 좌우로 스크롤할 수 있습니다.")

def export_summary():
    # Export only non-sensitive settings, not raw sequences, chat or API credentials.
    settings = {k: st.session_state[k] for k in ("bio_teacher_level_saved",) if k in st.session_state}
    st.download_button("설명 수준 설정 백업", json.dumps({"version":1,"settings":settings}, ensure_ascii=False), "biolab_settings.json", "application/json")
    uploaded = st.file_uploader("설정 복원", type=["json"], key="settings_restore")
    if st.button("설정 복원 적용", disabled=uploaded is None):
        try:
            if uploaded.size > 10000: raise ValueError()
            obj=json.loads(uploaded.getvalue())
            if obj.get("version") != 1: raise ValueError()
            level=obj["settings"].get("bio_teacher_level_saved", "고등학생")
            if level not in ("고등학생","기초","심화"): raise ValueError()
            st.session_state["bio_teacher_level_saved"]=level
            st.session_state.pop("bio_teacher_level",None)
            st.success("설정을 복원했습니다.")
        except (ValueError, TypeError, KeyError, AttributeError):
            st.error("올바른 BioLab 설정 백업 파일을 선택하세요.")
