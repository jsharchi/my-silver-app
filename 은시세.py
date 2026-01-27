import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 페이지 기본 설정
st.set_page_config(page_title="실시간 은 시세", layout="centered")

# 제목
st.title("🥈 나만의 실시간 은 시세")

# 2. 데이터 가져오기 (캐시 처리로 속도 향상)
@st.cache_data(ttl=60) # 1분마다 새로고침
def get_data():
    # 은 선물(SI=F), 원/달러 환율(KRW=X)
    silver = yf.Ticker("SI=F")
    exchange = yf.Ticker("KRW=X")
    
    # 최근 30일치 기록 및 현재 환율
    hist = silver.history(period="30d")
    usd_krw = exchange.history(period="1d")['Close'].iloc[-1]
    
    return hist, usd_krw

try:
    hist, ex_rate = get_data()
    
    # 현재가 및 전일가 추출
    current_usd = hist['Close'].iloc[-1]
    prev_usd = hist['Close'].iloc[-2]
    
    # 국내 가격 환산 (1온스 = 31.1034768g)
    current_krw = (current_usd * ex_rate) / 31.1034768
    prev_krw = (prev_usd * ex_rate) / 31.1034768
    
    # 3. 화면 레이아웃 (모바일 배려)
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="국내 은 시세 (원/g)", 
            value=f"{current_krw:,.0f}원", 
            delta=f"{current_krw - prev_krw:,.1f}원"
        )
    
    with col2:
        st.metric(
            label="국제 은 ($/oz)", 
            value=f"${current_usd:.2f}", 
            delta=f"{current_usd - prev_usd:.2f}"
        )

    # 4. 차트 표시
    st.subheader("최근 30일 가격 추이")
    st.line_chart(hist['Close'])

    # 하단 정보
    st.caption(f"기준 환율: {ex_rate:.2f}원 | 업데이트: {datetime.now().strftime('%H:%M:%S')}")

except Exception as e:
    st.error(f"데이터 로딩 중 오류 발생: {e}")
    