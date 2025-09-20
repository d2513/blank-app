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

# -------------------- GEE 인증 --------------------
@st.cache_resource
def initialize_ee():
    try:
        secret_value = os.environ.get('GEE_JSON_KEY')
        if not secret_value:
            st.sidebar.error("🚨 GEE_JSON_KEY Secret을 찾을 수 없습니다.")
            return False
        
        secret_json = json.loads(secret_value)
        credentials = service_account.Credentials.from_service_account_info(secret_json)
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
            tiles=map_id_dict['tile_fetcher'].url_format,
            attr='Google Earth Engine',
            overlay=True,
            name=f'{year}년 인구 피해 히트맵',
            show=True
        ).add_to(m)
        
        folium.LayerControl().add_to(m)

    # --- 지도 출력 ---
st.header(f"🗺️ {year}년 전 세계 인구 피해 위험 지역")
m.to_streamlit(height=600)

# --- SSP2-4.5 해수면 상승 그래프 ---
st.header("🌊 SSP2-4.5 해수면 상승 예측 (2020~2100)")

ssp_data = {
    "연도": [2020, 2030, 2040, 2050, 2060, 2070, 2080, 2090, 2100],
    "해수면 상승 (m)": [0.00, 0.03, 0.07, 0.12, 0.18, 0.25, 0.32, 0.40, 0.44]
}
ssp_df = pd.DataFrame(ssp_data).set_index("연도")

st.line_chart(ssp_df)
