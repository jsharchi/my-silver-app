import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="공격적 투자자 대시보드", layout="centered")

st.title("🥈 실시간 은 & 로봇주 모니터링")

# 2. 데이터 가져오기 함수
@st.cache_data(ttl=60)
def get_all_data():
    # 은 및 환율
    silver = yf.Ticker("SI=F")
    exchange = yf.Ticker("KRW=X")
    
    # 관심 종목 리스트 (필요시 여기서 수정하세요)
    stock_list = {
        "하이젠알앤엠": "445400.KQ",
        "SPG": "058610.KQ",
        "삼성전자": "005930.KS",
        "테슬라": "TSLA"
    }
    
    silver_hist = silver.history(period="5d") # 넉넉하게 5일치 호출
    usd_krw_data = exchange.history(period="1d")
    usd_krw = usd_krw_data['Close'].iloc[-1] if not usd_krw_data.empty else 1350.0 # 예외처리
    
    stock_results = {}
    for name, code in stock_list.items():
        s = yf.Ticker(code)
        # 종목별 최근 5일 데이터 (휴일 대비)
        df = s.history(period="5d")
        if not df.empty and len(df) >= 1:
            stock_results[name] = df
        else:
            stock_results[name] = None # 데이터 없는 경우 표시용
            
    return silver_hist, usd_krw, stock_results

try:
    s_hist, ex_rate, stocks = get_all_data()
    
    # --- 섹션 1: 은 시세 ---
    st.subheader("💰 원자재 현황")
    if not s_hist.empty:
        c_usd = s_hist['Close'].iloc[-1]
        p_usd = s_hist['Close'].iloc[-2] if len(s_hist) > 1 else c_usd
        c_krw = (c_usd * ex_rate) / 31.1034768
        p_krw = (p_usd * ex_rate) / 31.1034768
        
        st.metric("국내 은 시세", f"{c_krw:,.0f} 원/g", f"{c_krw - p_krw:,.1f}원")
    
    # --- 섹션 2: 관심 주식 ---
    st.divider()
    st.subheader("🤖 로봇 및 주요 종목")
    
    cols = st.columns(len(stocks))
    for i, (name, data) in enumerate(stocks.items()):
        with cols[i]:
            if data is not None:
                curr = data['Close'].iloc[-1]
                # 어제 데이터가 없으면 오늘 데이터로 대체 (에러 방지)
                prev = data['Close'].iloc[-2] if len(data) > 1 else curr
                st.metric(label=name, value=f"{int(curr):,}원", delta=f"{int(curr-prev):,}원")
            else:
                st.write(f"{name}\n준비중")

    # --- 섹션 3: 차트 흐름 ---
    st.divider()
    st.subheader("📈 은 가격 흐름 (최근)")
    if not s_hist.empty:
        st.line_chart(s_hist['Close'])

    st.caption(f"최종 업데이트: {datetime.now().strftime('%H:%M:%S')} (환율: {ex_rate:.2f}원)")

except Exception as e:
    st.error(f"알 수 없는 에러가 발생했습니다. 잠시 후 새로고침 하세요.")
    # 실제 에러 내용은 개발자만 알 수 있게 콘솔에만 출력
    print(f"DEBUG ERROR: {e}")
