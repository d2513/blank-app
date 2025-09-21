# -*- coding: utf-8 -*-
import streamlit as st
import folium
import pandas as pd
import numpy as np
import plotly.express as px
import ee
import geemap.foliumap as geemap
import json
import os
from google.oauth2 import service_account

# -------------------- 페이지 설정 --------------------
st.set_page_config(page_title="물러서는 땅, 다가오는 바다 — 해수면 상승 대시보드", layout="wide", page_icon="🌊")

# -------------------- GEE 인증 --------------------
@st.cache_resource
def initialize_ee():
    try:
        creds_dict = None
        if hasattr(st, 'secrets') and st.secrets.get("gcp_service_account"):
            creds_dict = st.secrets["gcp_service_account"]
        else:
            secret_value = os.environ.get('GEE_JSON_KEY')
            if secret_value:
                creds_dict = json.loads(secret_value)
        if not creds_dict:
            st.error("GEE 인증 정보를 찾을 수 없습니다. GitHub 또는 Streamlit Secret 설정을 확인하세요.")
            st.stop()
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        scoped_credentials = credentials.with_scopes([
            'https://www.googleapis.com/auth/earthengine',
            'https://www.googleapis.com/auth/cloud-platform'
        ])
        ee.Initialize(credentials=scoped_credentials)
        st.sidebar.success("✅ GEE 인증 성공!")
        return True
    except Exception as e:
        st.error(f"🚨 GEE 인증 오류가 발생했습니다. Secret 키가 유효한지, GEE API가 활성화되어 있는지 확인해주세요.\n\n오류 상세: {e}")
        st.stop()

# -------------------------
# Helper / 투발루 그래프용 데이터
# -------------------------
@st.cache_data
def generate_tuvalu_graph_data():
    rng = np.random.RandomState(42)
    rows = []
    years = list(range(1990, 2051, 5))
    base, trend = 0.05, 0.008
    for year in years:
        years_from0 = year - min(years)
        sea = float(np.round(base + trend * years_from0 + rng.normal(scale=0.01), 3))
        rows.append({"country": "투발루", "year": year, "sea_level_m": max(0.0, sea)})
    return pd.DataFrame(rows)

df_tuvalu_graph = generate_tuvalu_graph_data()

# -------------------------
# 사이드바: 사용자 입력
# -------------------------
st.sidebar.title("🔧 설정")
st.sidebar.markdown("연도를 선택하면 지도가 실시간으로 갱신됩니다.")
sel_year = st.sidebar.slider("연도 선택", min_value=2025, max_value=2100, value=2050, step=5)
show_tuvalu = st.sidebar.checkbox("투발루 상세 보기", value=True)

# -------------------------
# 메인 화면 구성
# -------------------------

# --- 1. 앱 제목 ---
st.title("🌊 물러서는 땅, 다가오는 바다: 해수면 상승 대시보드")

# --- 2. 인터랙티브 지도 (메인 화면 최상단) ---
st.header(f"🗺️ {sel_year}년 전 세계 인구 피해 위험 지역")
initialize_ee() # GEE 인증 실행

DEM = ee.Image('NASA/NASADEM_HGT/001').select('elevation')
POPULATION = ee.ImageCollection('WorldPop/GP/100m/pop').filterDate('2020').mean()

sea_level_rise = (sel_year - 2025) / 75 * 0.8

with st.spinner("지도 데이터를 계산하고 있습니다..."):
    flooded_mask_global = DEM.lte(sea_level_rise).selfMask()
    affected_population_heatmap = POPULATION.updateMask(flooded_mask_global)
    
    heatmap_vis_params = {
        'min': 0, 
        'max': 250,
        'palette': ['orange', 'red', 'darkred']
    }
    
    m = geemap.Map(center=[20, 0], zoom=2)
    m.add_basemap('SATELLITE')
    
    map_id_dict = affected_population_heatmap.getMapId(heatmap_vis_params)
    folium.TileLayer(
        tiles=map_id_dict['tile_fetcher'].url_format,
        attr='Google Earth Engine',
        overlay=True,
        name=f'{sel_year}년 인구 피해 히트맵',
        show=True
    ).add_to(m)
    
    folium.LayerControl().add_to(m)

m.to_streamlit(height=800)

st.markdown("---")

# --- 3. 보고서 본문 ---
st.header("📘 해수면 상승의 위험과 우리의 대처법")
st.markdown("#### 서론 — 문제 제기")
st.markdown(
    "인류의 산업화 이후 대기 중 온실가스 농도는 급격히 증가했고, 그 결과 지구의 평균 기온이 상승했습니다. "
    "이로 인해 육지의 빙하와 빙상이 녹고 바닷물의 열팽창이 일어나면서 전 세계적인 해수면 상승이 관찰됩니다.  \n\n"
    "해수면 상승은 단순한 '물의 증가'가 아니라, 수자원 오염, 농업지 손실, 거주지 상실, 생계 기반 붕괴, 문화유산 소실 등 "
    "사회경제적·문화적 충격을 동반하는 재난입니다. 특히 평균 해발고가 낮은 섬나라와 연안 도시는 그 영향이 치명적입니다."
)
st.markdown("----")
st.markdown("#### 본론 1 — 데이터 분석 (요약)")
st.markdown(
    "- 이 대시보드는 **실제 위성 데이터를 기반**으로 연도별 **예상 인구 피해 위험 지역**을 시각화합니다.  \n"
    "- 지도에서는 주황색에서 붉은색으로 갈수록 해당 지역의 침수 시 인구 피해 위험이 높음을 의미합니다.  \n"
    "- 이 분석은 NASA의 지형 데이터(NASADEM)와 WorldPop의 인구 데이터를 사용합니다."
)
st.markdown("----")
st.markdown("#### 본론 2 — 원인 및 영향 탐구 (사례 중심)")
st.markdown("**투발루 (Tuvalu)** — 남태평양의 작은 섬나라인 투발루는 평균 해발고가 2~3m에 불과합니다. "
            "작은 해수면 상승조차 농지와 식수원에 치명적이며 이미 생활터전이 침식되는 사례가 보고되고 있습니다.")
st.markdown("**투발루의 실제 상황 요약**")
st.markdown(
    "- 이미 일부 저지대 지역에서 염수화(saltwater intrusion)가 발생하여 식수원이 오염되고 있습니다.  \n"
    "- 주민들이 호주·뉴질랜드 등으로 이주를 시도하였으나 이민 문턱·정책 문제로 쉽지 않은 상황입니다.  \n"
    "- 문화적·정체성 측면에서 '국토 상실' 문제는 단순한 이주 문제를 넘어섰습니다."
)
st.markdown("----")
st.markdown("#### 본론 3 — 청소년이 알면 좋은 핵심 포인트")
st.markdown(
    "1. 해수면 상승은 모든 사람의 문제가 아니라 **특정 지역과 그룹에 더 큰 타격**을 줍니다.  \n"
    "2. 기후변화 완화(온실가스 감축)와 적응(연안 복원, 이주 계획)은 함께 가야 합니다.  \n"
    "3. 개인의 실천도 중요하지만 정책·국제 협력이 더 큰 영향을 미칩니다."
)
st.markdown("----")
st.markdown("#### 결론 및 권고 (요약)")
st.markdown(
    "- **정책적 권고**: 연안 관리 계획 수립, 취약지역 개발 제한, 국제적 이주 협력 및 원조 체계 마련.  \n"
    "- **기술적 대응**: 방파제 및 자연 기반 해안 방어(맹그로브·갯벌 복원) 병행.  \n"
    "- **교육적 대응**: 청소년 대상 기후 교육 강화와 지역 캠페인 활성화."
)
st.markdown("----")
st.header("투발루 상세 사례 (그래프)")
if show_tuvalu:
    # 투발루 연도별 그래프 (실제 데이터 아님—시뮬레이션)
    fig_tuv = px.line(df_tuvalu_graph, x="year", y="sea_level_m", markers=True, title="투발루 연도별 해수면 상승 (시뮬레이션)")
    fig_tuv.update_yaxes(title_text="해수면 상승 (m)")
    st.plotly_chart(fig_tuv, use_container_width=True)
    st.markdown(
        "설명: 위 그래프는 교육용 시뮬레이션으로, 연도에 따른 해수면 상승 추이를 보여줍니다. "
        "실제 투발루의 피해사례(식수 오염, 농지 침수, 이주 압력 등)는 이미 보고되고 있습니다."
    )

# -------------------------
# 하단: 실천 체크리스트
# -------------------------
st.markdown("---")
st.header("✅ 청소년 친환경 실천 체크리스트")
options = [
    "사용하지 않는 전등 끄기", "대중교통 이용/자전거 타기", "일회용품 줄이기 (컵/빨대 등)",
    "음식물 낭비 줄이기", "분리배출 철저히 하기", "친환경 제품 사용 촉구",
    "학교 환경 동아리 참여", "지역 해변/강 정화 활동 참여", "텃밭 가꾸기 또는 나무 심기",
    "기후 관련 캠페인/청원 참여"
]
checked = []
cols = st.columns(2)
for i, opt in enumerate(options):
    with cols[i % 2]:
        if st.checkbox(opt, key=f"act_{i}"):
            checked.append(opt)

if checked:
    st.markdown(f"**{len(checked)}**개의 항목을 실천하기로 약속했어요! 👍")
    df_checked = pd.DataFrame({"실천항목": checked})
    st.download_button("나의 다짐 목록 다운로드", data=df_checked.to_csv(index=False).encode("utf-8"), file_name="my_climate_actions.csv", mime="text/csv")

# -------------------------
# 맺음말
# -------------------------
st.markdown("---")
st.markdown("### 마무리 — 지금 우리가 해야 할 일")
st.markdown(
    "해수면 상승은 이미 일부 지역에서 현실로 다가왔습니다. 이 대시보드는 실제 위성 데이터를 사용하여 미래의 위험을 예측하고, "
    "우리가 왜 지금 행동해야 하는지에 대한 경각심을 일깨우기 위해 만들어졌습니다. 작은 실천이 모여 큰 변화를 만듭니다."
)