import streamlit as st
from common import export_summary
st.title("BioLab Analyzer")
st.write("생명공학 데이터 분석 및 학습 지원 도구")
for title, path, desc in [
    ("DNA 분석", "pages/1_DNA.py", "기준 서열 설정 → 기본 특성 및 ORF 확인 → 변이 결과 해석"),
    ("BCA 단백질 정량", "pages/2_BCA_protein.py", "표준용액과 미지 시료 입력 → 분석 → 표준곡선 및 농도 확인"),
    ("PCR 프라이머 분석", "pages/3_PCR.py", "교육용 예시 및 기존 분석 결과 확인"),
    ("AI 생명공학교사", "pages/4_AI_teacher.py", "참고 데이터 선택 → 질문 → 답변 검증")]:
    st.subheader(title)
    st.write(desc)
    st.page_link(path, label=title + " 열기")
st.divider()
st.subheader("데이터 보관 안내")
st.write("페이지 이동과 브라우저 새로고침은 다릅니다. BCA 입력표는 ZIP으로 백업하고 AI 대화는 TXT로 내려받을 수 있습니다. TXT는 열람용이며 대화 복원 파일이 아닙니다.")
export_summary()
st.caption("교육용 도구이며 실제 실험 성공이나 의료적 판단을 보장하지 않습니다.")
