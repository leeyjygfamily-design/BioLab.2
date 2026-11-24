st.subheader("⑤ AI 생명공학교사 연동")
st.write("현재 DNA 분석 결과를 저장한 뒤 AI 생명공학교사에게 질문할 수 있습니다.")
st.caption("선택한 분석 결과는 이 Streamlit 세션에 저장됩니다. AI 페이지에서 선택하면 Gemini API로 전송됩니다.")

# 프라이머 검토 등에 필요한 실제 염기서열 구간을 선택해 전달합니다.
st.markdown("**AI에 포함할 실제 DNA 염기서열 구간**")
st.caption("좌표는 현재 기준 DNA의 1-based 위치입니다. 선택 구간의 A/T/G/C 배열을 AI에 전달합니다.")
include_region = st.checkbox("선택 구간의 염기서열 포함", value=True, key="dna_ai_include_region")
max_region_bp = 4000
region_start_default = 1
region_end_default = min(len(sequence), 1200)
if "dna_ai_sequence_identity" not in st.session_state or st.session_state.dna_ai_sequence_identity != sequence:
    st.session_state.dna_ai_sequence_identity = sequence
    st.session_state.dna_ai_region_start = region_start_default
    st.session_state.dna_ai_region_end = region_end_default

region_col1, region_col2 = st.columns(2)
with region_col1:
    region_start = st.number_input(
        "시작 위치 (bp)", min_value=1, max_value=len(sequence),
        step=1, key="dna_ai_region_start", disabled=not include_region,
    )
with region_col2:
    region_end = st.number_input(
        "종료 위치 (bp)", min_value=1, max_value=len(sequence),
        step=1, key="dna_ai_region_end", disabled=not include_region,
    )
region_valid = (not include_region or
                (region_start <= region_end and region_end - region_start + 1 <= max_region_bp))
if include_region:
    if region_start > region_end:
        st.error("시작 위치는 종료 위치보다 작거나 같아야 합니다.")
    elif region_end - region_start + 1 > max_region_bp:
        st.error(f"한 번에 전달할 수 있는 실제 염기서열은 최대 {max_region_bp:,} bp입니다.")
    else:
        st.caption(f"전달할 구간: {region_start:,}–{region_end:,} bp "
                   f"({region_end - region_start + 1:,} bp)")
        with st.expander("AI에 전달할 실제 염기서열 미리보기"):
            st.code(sequence[region_start - 1:region_end], language="text")

if st.button("현재 DNA 분석 결과를 AI에게 전달하기", use_container_width=True, disabled=not region_valid):
    dna_result = {
        "데이터 출처": st.session_state.get("dna_record", {"유형": "현재 선택한 DNA 서열"}),
        "DNA 기본 분석": {
            "길이_bp": len(sequence),
            "GC_함량_퍼센트": round(gc_percent(sequence), 4),
            "염기서열_앞부분_최대_300bp": sequence[:300],
            "서열_일부만_제공": len(sequence) > 300,
        },
        "분석 제한": [
            "ORF 탐색은 정방향 3개 읽기 틀만 분석한 예측 결과입니다.",
            "변이 분석은 국소 정렬이며 정렬되지 않은 양 끝은 비교에서 제외될 수 있습니다.",
            "예측 단백질 영향은 실험적 검증이나 임상적 판정을 의미하지 않습니다.",
        ],
    }

    all_orfs = st.session_state.get("orfs")
    if all_orfs is not None:
        dna_result["ORF 분석"] = {
            "발견된_ORF_수": len(all_orfs),
            "ORF_목록_최대_30개": [
                {"읽기틀": o["frame"], "시작": o["start"], "끝": o["end"],
                 "길이_bp": len(o["dna"]), "예측_아미노산_앞부분": o["protein"][:120]}
                for o in all_orfs[:30]
            ],
            "목록_일부_생략": len(all_orfs) > 30,
        }
        current_orf = st.session_state.get("selected_orf")
        if current_orf is not None:
            dna_result["ORF 분석"]["선택한_ORF"] = {
                "읽기틀": current_orf["frame"],
                "시작": current_orf["start"],
                "끝": current_orf["end"],
                "길이_bp": len(current_orf["dna"]),
                "예측_아미노산_앞부분": current_orf["protein"][:300],
            }

    alignment = st.session_state.get("variant_result")
    if alignment is not None:
        changes = alignment["variants"]
        dna_result["서열 정렬 및 변이 분석"] = {
            "기준_서열_정렬_시작": alignment["start"],
            "기준_서열_정렬_끝": alignment["end"],
            "일치도_퍼센트": round(alignment["identity"], 4),
            "비교_서열_정렬_비율_퍼센트": round(alignment["coverage"], 4),
            "정렬된_비교_서열_염기수": alignment["aligned_bases"],
            "변이_항목_수": len(changes),
            "변이_목록_최대_100개": [
                {**v, "치환 유형": substitution_type(v["기준 염기"], v["비교 염기"])}
                for v in changes[:100]
            ],
            "변이_목록_일부_생략": len(changes) > 100,
        }
        ranked_orfs = st.session_state.get("orfs", [])
        selected_index = st.session_state.get("recommended_orf_choice")
        if isinstance(selected_index, int) and 0 <= selected_index < len(ranked_orfs):
            effect_orf = ranked_orfs[selected_index]
        else:
            effect_orf = None
        protein_effect, limitation = analyze_orf_effect(sequence, alignment, effect_orf)
        if protein_effect is not None:
            dna_result["선택한 ORF의 예측 단백질 영향"] = {
                "요약": protein_effect["summary"],
                "코돈별_영향_최대_50개": protein_effect["rows"][:50],
                "코돈별_영향_일부_생략": len(protein_effect["rows"]) > 50,
                "기준_아미노산_앞부분": protein_effect["ref_protein"][:300],
                "비교_아미노산_앞부분": protein_effect["alt_protein"][:300],
            }
        elif limitation:
            dna_result["단백질 영향 분석 제한"] = limitation

    if include_region:
        selected_sequence = sequence[region_start - 1:region_end]
        dna_result["AI용 실제 DNA 구간"] = {
            "좌표_기준": "현재 기준 DNA, 1-based, 시작과 끝 포함, 정방향 5′→3′",
            "시작_bp": int(region_start),
            "끝_bp": int(region_end),
            "길이_bp": len(selected_sequence),
            "실제_염기서열_5to3": selected_sequence,
            "설명": "이 구간에 대해서만 실제 염기서열이 제공되었습니다. 다른 위치의 염기를 추측하지 마세요.",
        }

    st.session_state["dna_result"] = dna_result
    st.success("DNA 분석 결과를 저장했습니다. AI 생명공학교사 페이지에서 확인할 수 있습니다.")
    st.switch_page("pages/4_AI_teacher.py")
