import streamlit as st
import yfinance as yf
import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta

# 1. 페이지 설정 (넓게 보기)
st.set_page_config(page_title="시장 주도주 대시보드", layout="wide")

st.title("🥈 실시간 은 & 🔥 코스닥 거래량 TOP 10")

# 2. 데이터 가져오기 함수
@st.cache_data(ttl=300) # 5분마다 시장 데이터 새로고침
def get_market_data():
    # (1) 은 시세 및 환율
    silver = yf.Ticker("SI=F")
    exchange = yf.Ticker("KRW=X")
    s_hist = silver.history(period="5d")
    ex_rate = exchange.history(period="1d")['Close'].iloc[-1]
    
    # (2) 코스닥 거래량 TOP 10 (진짜 전 종목 대상)
    today = datetime.now().strftime("%Y%m%d")
    try:
        # 오늘 거래량 순위 가져오기
        df = stock.get_market_ohlcv_by_ticker(today, market="KOSDAQ")
        
        # 만약 장 전이거나 휴일이라 데이터가 없으면 전날 데이터 찾기
        count = 1
        while df.empty and count < 7:
            target_date = (datetime.now() - timedelta(days=count)).strftime("%Y%m%d")
            df = stock.get_market_ohlcv_by_ticker(target_date, market="KOSDAQ")
            count += 1
            
        # 거래량 순으로 정렬 후 상위 10개 추출
        df_sorted = df.sort_values(by="거래량", ascending=False).head(10)
        
        market_list = []
        for ticker in df_sorted.index:
            name = stock.get_market_ticker_name(ticker)
            market_list.append({
                "종목명": name,
                "현재가": df_sorted.loc[ticker, "종가"],
                "등락률": df_sorted.loc[ticker, "등락률"],
                "거래량": df_sorted.loc[ticker, "거래량"]
            })
        market_df = pd.DataFrame(market_list)
    except:
        market_df = pd.DataFrame()
        
    return s_hist, ex_rate, market_df

try:
    s_hist, ex_rate, top10_df = get_market_data()

    # 상단: 은 시세 (심플하게)
    st.subheader("💰 실시간 국내 은 가격")
    c_usd = s_hist['Close'].iloc[-1]
    c_krw = (c_usd * ex_rate) / 31.1034768
    st.metric(label="은 가격(원/g)", value=f"{c_krw:,.0f}원")
    
    st.divider()

    # 하단: 코스닥 거래량 TOP 10 (큼직한 카드 형태)
    st.subheader("🚀 오늘 코스닥 거래량 상위 10개 종목")
    
    if not top10_df.empty:
        # 5개씩 두 줄로 표시
        for i in range(0, 10, 5):
            cols = st.columns(5)
            for j in range(5):
                idx = i + j
                if idx < len(top10_df):
                    row = top10_df.iloc[idx]
                    with cols[j]:
                        st.metric(
                            label=f"{idx+1}위: {row['종목명']}",
                            value=f"{int(row['현재가']):,}원",
                            delta=f"{row['등락률']:.2f}%"
                        )
                        st.caption(f"거래량: {int(row['거래량']):,}")
    else:
        st.write("데이터를 불러오는 중입니다... 잠시 후 새로고침 하세요.")

    st.caption(f"업데이트: {datetime.now().strftime('%H:%M:%S')} (데이터: KRW/Yahoo)")

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
