import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="공격적 투자자 대시보드", layout="centered")

st.title("🥈 실시간 은 & 로봇주 모니터링")

# 2. 데이터 가져오기 함수 (관심 종목 추가)
@st.cache_data(ttl=60)
def get_all_data():
    # 은 및 환율
    silver = yf.Ticker("SI=F")
    exchange = yf.Ticker("KRW=X")
    
    # 관심 종목 리스트 (미래에셋에서 보시는 종목들)
    # 하이젠알앤엠(445400.KQ), SPG(058610.KQ)
    stock_list = {
        "하이젠알앤엠": "445400.KQ",
        "삼성전자": "005930.KS"
    }
    
    silver_hist = silver.history(period="30d")
    usd_krw = exchange.history(period="1d")['Close'].iloc[-1]
    
    stock_results = {}
    for name, code in stock_list.items():
        s = yf.Ticker(code)
        stock_results[name] = s.history(period="2d")
        
    return silver_hist, usd_krw, stock_results

try:
    s_hist, ex_rate, stocks = get_all_data()
    
    # --- 섹션 1: 은 시세 ---
    st.subheader("💰 원자재 현황")
    c_usd = s_hist['Close'].iloc[-1]
    p_usd = s_hist['Close'].iloc[-2]
    c_krw = (c_usd * ex_rate) / 31.1034768
    
    st.metric("국내 은 시세", f"{c_krw:,.0f} 원/g", f"{c_krw - ((p_usd * ex_rate)/31.103):,.1f}원")
    
    # --- 섹션 2: 관심 주식 (미래에셋 종목) ---
    st.divider()
    st.subheader("🤖 로봇 및 주요 종목")
    
    # 종목별로 칸을 나누어 표시
    cols = st.columns(len(stocks))
    for i, (name, data) in enumerate(stocks.items()):
        with cols[i]:
            curr = data['Close'].iloc[-1]
            prev = data['Close'].iloc[-2]
            st.metric(label=name, value=f"{int(curr):,}원", delta=f"{int(curr-prev):,}원")

    # --- 섹션 3: 차트 흐름 ---
    st.divider()
    st.subheader("📈 은 가격 흐름 (30일)")
    st.line_chart(s_hist['Close'])

    st.caption(f"최종 업데이트: {datetime.now().strftime('%H:%M:%S')} (환율: {ex_rate:.2f}원)")

except Exception as e:
    st.error(f"데이터 연동 중 오류 발생: {e}")
