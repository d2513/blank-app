import streamlit as st
import ee
import geemap.foliumap as geemap
import folium
import json
import os
import pandas as pd
from google.oauth2 import service_account

# -------------------- 페이지 설정 --------------------
st.set_page_config(layout="wide", page_title="전 세계 해수면 상승 시뮬레이터")

# -------------------- GEE 인증 (두 환경 모두 지원) --------------------
@st.cache_resource
def initialize_ee():
    try:
        creds_dict = None
        # 1. Streamlit Cloud에서 실행 중인지 확인하고 st.secrets을 먼저 시도
        if hasattr(st, 'secrets') and st.secrets.get("gcp_service_account"):
            creds_dict = st.secrets["gcp_service_account"]
        # 2. st.secrets이 없으면 Codespaces/로컬 환경으로 간주하고 환경 변수 시도
        else:
            secret_value = os.environ.get('GEE_JSON_KEY')
            if secret_value:
                creds_dict = json.loads(secret_value)

        # 위 두 방법 중 하나로도 인증 정보를 찾지 못한 경우 오류 발생
        if not creds_dict:
            st.sidebar.error("GEE 인증 정보를 찾을 수 없습니다. GitHub 또는 Streamlit Secret 설정을 확인하세요.")
            return False

        # 인증 정보로 GEE 초기화
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        scoped_credentials = credentials.with_scopes([
            'https://www.googleapis.com/auth/earthengine',
            'https://www.googleapis.com/auth/cloud-platform'
        ])
        ee.Initialize(credentials=scoped_credentials)
        st.sidebar.success("✅ GEE 인증 성공!")
        return True
    except Exception as e:
        st.sidebar.error(f"🚨 GEE 인증 오류:\n{e}")
        return False

# -------------------- 메인 앱 UI --------------------
st.title("🌊 전 세계 해수면 상승 시뮬레이터")
st.write("연도를 조절하여 전 세계의 인구 피해 위험 지역을 히트맵으로 확인합니다.")

if initialize_ee():
    # --- GEE 데이터셋 정의 ---
    DEM = ee.Image('NASA/NASADEM_HGT/001').select('elevation')
    POPULATION = ee.ImageCollection('WorldPop/GP/100m/pop').filterDate('2020').mean()

    # --- 사용자 입력 (사이드바) ---
    st.sidebar.header("⚙️ 시뮬레이션 설정")
    year = st.sidebar.slider("🗓️ 연도 선택:", 2025, 2100, 2050, step=5)
    
    # --- 메인 패널 ---
    sea_level_rise = (year - 2025) / 75 * 0.8
    
    with st.spinner("지도 데이터를 계산하고 있습니다..."):
        flooded_mask_global = DEM.lte(sea_level_rise).selfMask()
        affected_population_heatmap = POPULATION.updateMask(flooded_mask_global)
        
        heatmap_vis_params = {
            'min': 0, 
            'max': 250,
            'palette': ['orange', 'red', 'darkred']
        }
        
        # --- 지도 생성 및 히트맵 표시 ---
        m = geemap.Map(center=[20, 0], zoom=2)
        m.add_basemap('SATELLITE')
        
        map_id_dict = affected_population_heatmap.getMapId(heatmap_vis_params)
        folium.TileLayer(
            tiles=map_id_dict['fetcher'].url_format,
            attr='Google Earth Engine',
            overlay=True,
            name=f'{year}년 인구 피해 히트맵',
            show=True
        ).add_to(m)
        
        folium.LayerControl().add_to(m)

    # --- 지도 출력 ---
    st.header(f"🗺️ {year}년 전 세계 인구 피해 위험 지역")
    m.to_streamlit(height=600)

else:
    # 이 부분은 initialize_ee()가 False를 반환했을 때를 대비한 것으로,
    # 사이드바에 표시된 오류 메시지를 사용자가 볼 수 있도록 안내합니다.
    st.info("GEE 인증에 실패했습니다. 사이드바의 오류 메시지를 확인하고 Secret 설정을 점검해주세요.")

# --- SSP2-4.5 해수면 상승 그래프 ---
st.header("🌊 SSP2-4.5 해수면 상승 예측 (2020~2100)")

ssp_data = {
    "연도": [2020, 2030, 2040, 2050, 2060, 2070, 2080, 2090, 2100],
    "해수면 상승 (m)": [0.00, 0.03, 0.07, 0.12, 0.18, 0.25, 0.32, 0.40, 0.44]
}
ssp_df = pd.DataFrame(ssp_data).set_index("연도")

st.line_chart(ssp_df)