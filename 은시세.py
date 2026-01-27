import streamlit as st
import yfinance as yf
import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta

# 1. 페이지 설정 (모바일에서도 보기 좋게 가로로 넓게)
st.set_page_config(page_title="오전 단타 대시보드", layout="wide")

st.title("⚡ 코스닥 단타 TOP 10 & 🥈 은 시세")

# 2. 시장 데이터 추출 함수
@st.cache_data(ttl=60) # 단타용이므로 1분마다 갱신 (매우 중요)
def get_scalping_data():
    # (1) 은 시세 및 환율
    silver = yf.Ticker("SI=F")
    exchange = yf.Ticker("KRW=X")
    s_hist = silver.history(period="5d")
    ex_rate = exchange.history(period="1d")['Close'].iloc[-1]
    
    # (2) 코스닥 전종목 거래량 순위
    today = datetime.now().strftime("%Y%m%d")
    try:
        df = stock.get_market_ohlcv_by_ticker(today, market="KOSDAQ")
        
        # 장 전이거나 데이터 부족 시 직전 장날 데이터
        count = 1
        while df.empty and count < 7:
            target_date = (datetime.now() - timedelta(days=count)).strftime("%Y%m%d")
            df = stock.get_market_ohlcv_by_ticker(target_date, market="KOSDAQ")
            count += 1
            
        # 거래량 기준 정렬 후 상위 10개
        df_sorted = df.sort_values(by="거래량", ascending=False).head(10)
        
        market_list = []
        for ticker in df_sorted.index:
            name = stock.get_market_ticker_name(ticker)
            price = df_sorted.loc[ticker, "종가"]
            change = df_sorted.loc[ticker, "등락률"]
            vol = df_sorted.loc[ticker, "거래량"]
            
            market_list.append({
                "종목명": name,
                "현재가": price,
                "등락률": change,
                "거래량": vol,
                "목표가(+3%)": price * 1.03,
                "손절가(-2%)": price * 0.98
            })
        return s_hist, ex_rate, pd.DataFrame(market_list)
    except:
        return s_hist, ex_rate, pd.DataFrame()

try:
    s_hist, ex_rate, top10_df = get_scalping_data()

    # --- 섹션 1: 은 시세 (상단에 작게) ---
    c_usd = s_hist['Close'].iloc[-1]
    c_krw = (c_usd * ex_rate) / 31.1034768
    st.caption(f"🥈 실시간 은: {c_krw:,.0f}원/g | 환율: {ex_rate:.2f}원")
    
    st.divider()

    # --- 섹션 2: 코스닥 단타 TOP 10 ---
    st.subheader("🔥 코스닥 거래량 순위 & 단타 가이드")
    
    if not top10_df.empty:
        # 1위부터 10위까지 카드 형태로 출력
        for i in range(0, 10, 2): # 2개씩 한 줄에 표시 (가독성)
            cols = st.columns(2)
            for j in range(2):
                idx = i + j
                if idx < len(top10_df):
                    row = top10_df.iloc[idx]
                    with cols[j]:
                        # 등락률에 따라 색상 강조 느낌 주기
                        emoji = "🚀" if row['등락률'] > 0 else "📉"
                        st.metric(
                            label=f"{idx+1}위: {row['종목명']} {emoji}",
                            value=f"{int(row['현재가']):,}원",
                            delta=f"{row['등락률']:.2f}%"
                        )
                        # 단타 가이드 정보
                        st.write(f"🎯 **목표(+3%):** {int(row['목표가(+3%)']):,}원 | 🛑 **손절(-2%):** {int(row['손절가(-2%)']):,}원")
                        st.caption(f"현재 거래량: {int(row['거래량']):,}")
                        st.divider()
    else:
        st.warning("시장 데이터를 불러올 수 없습니다. 장 개시 전이거나 점검 중일 수 있습니다.")

    st.caption(f"마지막 업데이트: {datetime.now().strftime('%H:%M:%S')}")

except Exception as e:
    st.error(f"대시보드 실행 중 오류: {e}")
