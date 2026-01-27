import streamlit as st
import yfinance as yf
import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="공격적 투자자 대시보드", layout="wide")

st.title("🥈 실시간 은 & 🚀 코스닥 거래량 TOP 10")

# 2. 데이터 가져오기 함수
@st.cache_data(ttl=600) # 10분마다 데이터 갱신
def get_dashboard_data():
    # (1) 은 시세 및 환율 (yfinance 사용)
    silver = yf.Ticker("SI=F")
    exchange = yf.Ticker("KRW=X")
    s_hist = silver.history(period="5d")
    ex_rate = exchange.history(period="1d")['Close'].iloc[-1]
    
    # (2) 코스닥 거래량 TOP 10 (pykrx 사용)
    # 오늘 날짜 혹은 가장 최근 장날 확인
    target_date = datetime.now().strftime("%Y%m%d")
    
    try:
        # 코스닥 전종목 거래량 정보
        df = stock.get_market_ohlcv_by_ticker(target_date, market="KOSDAQ")
        if df.empty: # 장 전이거나 휴일일 경우 전일 데이터 가져오기
            target_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
            df = stock.get_market_ohlcv_by_ticker(target_date, market="KOSDAQ")
            
        df_sorted = df.sort_values(by="거래량", ascending=False).head(10)
        
        krx_list = []
        for ticker in df_sorted.index:
            name = stock.get_market_ticker_name(ticker)
            krx_list.append({
                "종목명": name,
                "현재가": f"{int(df_sorted.loc[ticker, '종가']):,}원",
                "등락률": f"{df_sorted.loc[ticker, '등락률']:.2f}%",
                "거래량": f"{int(df_sorted.loc[ticker, '거래량']):,}"
            })
        krx_df = pd.DataFrame(krx_list)
    except:
        krx_df = pd.DataFrame(["데이터를 불러올 수 없습니다."])
        
    return s_hist, ex_rate, krx_df

try:
    s_hist, ex_rate, top10_df = get_dashboard_data()

    # 좌측: 은 시세 / 우측: 코스닥 순위 레이아웃
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.subheader("💰 실시간 은 시세")
        c_usd = s_hist['Close'].iloc[-1]
        c_krw = (c_usd * ex_rate) / 31.1034768
        st.metric("국내 은 가격", f"{c_krw:,.0f} 원/g")
        st.line_chart(s_hist['Close'])

    with col_right:
        st.subheader("🔥 오늘 코스닥 거래량 TOP 10")
        st.table(top10_df) # 깔끔한 표 형태로 표시

    st.caption(f"업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (데이터 출처: KRX, Yahoo Finance)")

except Exception as e:
    st.error(f"대시보드를 구성하는 중 오류가 발생했습니다.")
