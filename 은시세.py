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
        df = stock.get_market_ohlcv_by_ticker(today_str, market="KOSDAQ")
        
        # 장 전이거나 휴일일 경우 가장 최근 장날 데이터 찾기
        count = 1
        while df.empty and count < 7:
            target_date = (now_kst - timedelta(days=count)).strftime("%Y%m%d")
            df = stock.get_market_ohlcv_by_ticker(target_date, market="KOSDAQ")
            count += 1
            
        df_sorted = df.sort_values(by="거래량", ascending=False).head(10)
        
        res_list = []
        for ticker in df_sorted.index:
            name = stock.get_market_ticker_name(ticker)
            price = df_sorted.loc[ticker, "종가"]
            change = df_sorted.loc[ticker, "등락률"]
            vol = df_sorted.loc[ticker, "거래량"]
            
            res_list.append({
                "종목명": name,
                "현재가": price,
                "등락률": change,
                "거래량": vol,
                "목표(+3%)": price * 1.03,
                "손절(-2%)": price * 0.98
            })
        return s_hist, ex_rate, pd.DataFrame(res_list)
    except:
        return s_hist, ex_rate, pd.DataFrame()

try:
    s_hist, ex_rate, top10_df = get_market_data()
    now_kst_display = get_now_kst().strftime('%Y-%m-%d %H:%M:%S')

    # 상단 요약 정보
    c_usd = s_hist['Close'].iloc[-1]
    c_krw = (c_usd * ex_rate) / 31.1034768
    st.write(f"🥈 **은 시세:** {c_krw:,.0f}원/g | 📅 **현재 시간(KST):** {now_kst_display}")
    
    st.divider()

    # 코스닥 TOP 10 카드 출력
    if not top10_df.empty:
        for i in range(0, 10, 2):
            cols = st.columns(2)
            for j in range(2):
                idx = i + j
                if idx < len(top10_df):
                    row = top10_df.iloc[idx]
                    with cols[j]:
                        color = "normal" # 기본
                        st.metric(
                            label=f"{idx+1}위: {row['종목명']}",
                            value=f"{int(row['현재가']):,}원",
                            delta=f"{row['등락률']:.2f}%"
                        )
                        st.write(f"🎯 **목표:** {int(row['목표(+3%)']):,}원 | 🛑 **손절:** {int(row['손절(-2%)']):,}원")
                        st.caption(f"현재 거래량: {int(row['거래량']):,}")
                        st.divider()
    else:
        st.info("실시간 시장 데이터를 분석 중입니다. 장 개시 후에 확인하세요.")

except Exception as e:
    st.error(f"데이터 연동 대기 중... (잠시 후 새로고침)")

# 하단 수동 새로고침 버튼
if st.button('🔄 수동 새로고침'):
    st.cache_data.clear()
    st.rerun()
