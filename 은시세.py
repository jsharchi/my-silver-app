import streamlit as st
import yfinance as yf
import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
import pytz

# 1. 페이지 설정
st.set_page_config(page_title="오전 단타 대시보드 PRO", layout="wide")

def get_now_kst():
    return datetime.now(pytz.timezone('Asia/Seoul'))

st.title("⚡ 실시간 단타 감지기 (시초가/거래량 분석)")

# 2. 데이터 가져오기 (30초 캐시)
@st.cache_data(ttl=30)
def get_pro_trading_data():
    now_kst = get_now_kst()
    today_str = now_kst.strftime("%Y%m%d")
    
    # (1) 은 시세 및 환율
    silver = yf.Ticker("SI=F")
    exchange = yf.Ticker("KRW=X")
    s_hist = silver.history(period="2d")
    ex_rate = exchange.history(period="1d")['Close'].iloc[-1]
    
    # (2) 코스닥 거래량 순위 및 상세 분석
    try:
        # 오늘 데이터 (현재가, 시가, 거래량 등)
        df_today = stock.get_market_ohlcv_by_ticker(today_str, market="KOSDAQ")
        
        count = 1
        while df_today.empty and count < 7:
            target_date = (now_kst - timedelta(days=count)).strftime("%Y%m%d")
            df_today = stock.get_market_ohlcv_by_ticker(target_date, market="KOSDAQ")
            count += 1
            
        # 전일 거래량 가져오기 (비율 계산용)
        prev_date = (datetime.strptime(df_today.index.name if df_today.index.name else today_str, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
        # 실제 전일 영업일 찾기
        df_prev = stock.get_market_ohlcv_by_ticker(prev_date, market="KOSDAQ")
        while df_prev.empty:
            prev_date = (datetime.strptime(prev_date, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
            df_prev = stock.get_market_ohlcv_by_ticker(prev_date, market="KOSDAQ")

        # 거래량 상위 10개 추출
        df_sorted = df_today.sort_values(by="거래량", ascending=False).head(10)
        
        pro_list = []
        for ticker in df_sorted.index:
            name = stock.get_market_ticker_name(ticker)
            curr = df_sorted.loc[ticker, "종가"]
            open_p = df_sorted.loc[ticker, "시가"]
            vol_today = df_sorted.loc[ticker, "거래량"]
            
            # 전일 거래량 확인
            vol_prev = df_prev.loc[ticker, "거래량"] if ticker in df_prev.index else 1
            vol_ratio = (vol_today / vol_prev) * 100 if vol_prev > 0 else 0
            
            # 시초가 대비 등락률
            open_diff = ((curr - open_p) / open_p) * 100 if open_p > 0 else 0
            
            pro_list.append({
                "종목명": name,
                "현재가": curr,
                "등락률": df_sorted.loc[ticker, "등락률"],
                "시초가대비": open_diff,
                "거래량비율": vol_ratio,
                "거래량": vol_today
            })
        return s_hist, ex_rate, pd.DataFrame(pro_list)
    except Exception as e:
        print(f"Error: {e}")
        return s_hist, ex_rate, pd.DataFrame()

try:
    s_hist, ex_rate, df = get_pro_trading_data()
    now_kst_display = get_now_kst().strftime('%H:%M:%S')

    # 은 시세 상단 표시
    c_usd = s_hist['Close'].iloc[-1]
    c_krw = (c_usd * ex_rate) / 31.1034768
    st.markdown(f"🥈 은: **{c_krw:,.0f}원** | 🕒 갱신: **{now_kst_display}**")
    
    st.divider()

    if not df.empty:
        # 10개 종목을 카드 형태로 표시
        for i in range(0, 10, 2):
            cols = st.columns(2)
            for j in range(2):
                idx = i + j
                if idx < len(df):
                    row = df.iloc[idx]
                    with cols[j]:
                        # 시초가 대비 플러스면 빨간색, 마이너스면 파란색 느낌 (텍스트)
                        open_color = "🔴" if row['시초가대비'] > 0 else "🔵"
                        vol_fire = "🔥" if row['거래량비율'] > 100 else "" # 전일 거래량 돌파 시 불꽃
                        
                        st.metric(
                            label=f"{idx+1}위: {row['종목명']} {vol_fire}",
                            value=f"{int(row['현재가']):,}원",
                            delta=f"{row['등락률']:.2f}% (전일대비)"
                        )
                        
                        # 핵심 지표 강조
                        c1, c2 = st.columns(2)
                        c1.write(f"{open_color} **시초가 대비:** {row['시초가대비']:+.2f}%")
                        c2.write(f"📊 **전일 거래량의:** {row['거래량비율']:.1f}%")
                        
                        # 단타 가이드
                        st.caption(f"🎯 목표가(+3%): {int(row['현재가']*1.03):,}원 | 🛑 손절가(-2%): {int(row['현재가']*0.98):,}원")
                        st.divider()
    else:
        st.info("장 시작 전입니다. 오전 9시 이후 데이터가 표시됩니다.")

except Exception as e:
    st.error("데이터 업데이트 대기 중...")

if st.button('🔄 즉시 새로고침'):
    st.cache_data.clear()
    st.rerun()
