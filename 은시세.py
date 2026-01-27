import streamlit as st
import yfinance as yf
import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
import pytz  # 한국 시간 설정을 위해 필요
import time

# 1. 페이지 설정
st.set_page_config(page_title="실전 단타 대시보드", layout="wide")

# 2. 한국 시간(KST) 설정 함수
def get_now_kst():
    return datetime.now(pytz.timezone('Asia/Seoul'))

# 3. 30초마다 자동 새로고침 설정 (단타용 필수 기능)
# 주의: 너무 자주하면 차단될 수 있어 30초가 가장 적당합니다.
st.empty() 
if 'count' not in st.session_state:
    st.session_state.count = 0
    
# 자동 새로고침 트리거 (수동 새로고침 없이도 데이터가 갱신됩니다)
# 단, Streamlit Cloud 환경에 따라 수동 새로고침이 필요할 수도 있습니다.

st.title("⚡ 실시간 코스닥 단타 TOP 10")

# 4. 시장 데이터 추출 함수
@st.cache_data(ttl=30) # 캐시 유지 시간을 30초로 단축 (단타 최적화)
def get_market_data():
    now_kst = get_now_kst()
    today_str = now_kst.strftime("%Y%m%d")
    
    # (1) 은 시세 및 환율
    silver = yf.Ticker("SI=F")
    exchange = yf.Ticker("KRW=X")
    s_hist = silver.history(period="2d")
    ex_rate = exchange.history(period="1d")['Close'].iloc[-1]
    
    # (2) 코스닥 거래량 순위
    try:
