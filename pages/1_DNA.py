import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import requests
import re
from bisect import bisect_right
from Bio.Align import PairwiseAligner

st.set_page_config(page_title="DNA 분석", page_icon="🧬", layout="wide")

NCBI_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
API = {"tool": "BioLabAnalyzer", "email": st.secrets["NCBI_EMAIL"], "api_key": st.secrets["NCBI_API_KEY"]}

# -------------------- 공통 함수 --------------------
def ncbi_get(endpoint, db, **params):
    r = requests.get(NCBI_URL + endpoint, params={"db": db, **params, **API}, timeout=20)
    r.raise_for_status()
    return r


@st.cache_data(ttl=600, show_spinner=False)
def search_db(db, term, retmax=10, retstart=0):
    data = ncbi_get("esearch.fcgi", db, term=term, retmode="json", retmax=retmax, retstart=retstart).json()["esearchresult"]
    return data["idlist"], int(data["count"])


@st.cache_data(ttl=600, show_spinner=False)
def summaries(db, ids):
    if not ids:
        return []
    data = ncbi_get("esummary.fcgi", db, id=",".join(ids), retmode="json").json()["result"]
    return [data.get(i, {}) for i in ids]


@st.cache_data(ttl=600, show_spinner=False, max_entries=32)
def fetch_sequence(record_id):
    text = ncbi_get("efetch.fcgi", "nuccore", id=record_id, rettype="fasta", retmode="text").text
    return "".join(x.strip() for x in text.splitlines() if not x.startswith(">" )).upper()


def clean_dna(seq):
    lines = seq.strip().splitlines()
    headers = [line for line in lines if line.lstrip().startswith(">")]
    if len(headers) > 1:
        return "INVALID_MULTIPLE_FASTA"
    return "".join("".join(line.split()) for line in lines if not line.lstrip().startswith(">")).upper()


def gc_percent(seq):
    return 100 * (seq.count("G") + seq.count("C")) / len(seq) if seq else 0


# -------------------- 번역 / ORF --------------------
codon_table = {
    "TTT":"F","TTC":"F","TTA":"L","TTG":"L","TCT":"S","TCC":"S","TCA":"S","TCG":"S",
    "TAT":"Y","TAC":"Y","TAA":"*","TAG":"*","TGT":"C","TGC":"C","TGA":"*","TGG":"W",
    "CTT":"L","CTC":"L","CTA":"L","CTG":"L","CCT":"P","CCC":"P","CCA":"P","CCG":"P",
    "CAT":"H","CAC":"H","CAA":"Q","CAG":"Q","CGT":"R","CGC":"R","CGA":"R","CGG":"R",
    "ATT":"I","ATC":"I","ATA":"I","ATG":"M","ACT":"T","ACC":"T","ACA":"T","ACG":"T",
    "AAT":"N","AAC":"N","AAA":"K","AAG":"K","AGT":"S","AGC":"S","AGA":"R","AGG":"R",
    "GTT":"V","GTC":"V","GTA":"V","GTG":"V","GCT":"A","GCC":"A","GCA":"A","GCG":"A",
    "GAT":"D","GAC":"D","GAA":"E","GAG":"E","GGT":"G","GGC":"G","GGA":"G","GGG":"G"
}

def translate(seq):
    return "".join(codon_table.get(seq[i:i+3], "?") for i in range(0, len(seq)-2, 3))


@st.cache_data(ttl=600, max_entries=16, show_spinner=False)
def find_orfs(seq):
    orfs = []
    for frame in range(3):
        starts = []
        for pos in range(frame, len(seq)-2, 3):
            codon = seq[pos:pos+3]
            if codon == "ATG":
                starts.append(pos)
            elif codon in {"TAA", "TAG", "TGA"}:
                for start in starts:
                    dna = seq[start:pos+3]
                    orfs.append(dict(frame=frame+1,start=start+1,end=pos+3,dna=dna,protein=translate(dna)))
                starts.clear()
    return orfs


# -------------------- 서열 정렬 / 변이 영향 분석 --------------------
def align_variants(reference, sample):
    """기준 DNA와 비교 DNA의 유사한 구간을 정렬해 치환·삽입·결실을 찾습니다.

    정방향 국소 정렬이므로 서로 맞지 않는 서열의 양 끝은 비교에서 제외될 수 있습니다.
    """
    aligner = PairwiseAligner()
    aligner.mode = "local"
    aligner.match_score = 2
    aligner.mismatch_score = -1
