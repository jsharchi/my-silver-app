import streamlit as st
import yfinance as yf
import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
import pytz

# 1. 페이지 설정
st.set_page_config(page_title="단타 타점 정밀 감지기", layout="wide")

def get_now_kst():
    return datetime.now(pytz.timezone('Asia/Seoul'))

st.title("⚡ 실시간 단타 타점 감지기 (PRO)")

# 2. 데이터 가져오기 (30초 캐시)
@st.cache_data(ttl=30)
def get_final_trading_data():
    now_kst = get_now_kst()
    today_str = now_kst.strftime("%Y%m%d")
    
    # (1) 은 시세 및 환율
    silver = yf.Ticker("SI=F")
    exchange = yf.Ticker("KRW=X")
    s_hist = silver.history(period="2d")
    ex_rate = exchange.history(period="1d")['Close'].iloc[-1]
    
    # (2) 코스닥 순위 및 단타 지표 분석
    try:
        df_today = stock.get_market_ohlcv_by_ticker(today_str, market="KOSDAQ")
        
        count = 1
        while df_today.empty and count < 7:
            target_date = (now_kst - timedelta(days=count)).strftime("%Y%m%d")
            df_today = stock.get_market_ohlcv_by_ticker(target_date, market="KOSDAQ")
            count += 1
            
        # 전일 거래량 가져오기
        target_idx = df_today.index.name if df_today.index.name else today_str
        prev_date = (datetime.strptime(target_idx, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
        df_prev = stock.get_market_ohlcv_by_ticker(prev_date, market="KOSDAQ")
        while df_prev.empty:
            prev_date = (datetime.strptime(prev_date, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
            df_prev = stock.get_market_ohlcv_by_ticker(prev_date, market="KOSDAQ")

        # 거래량 상위 10개
        df_sorted = df_today.sort_values(by="거래량", ascending=False).head(10)
        
        final_list = []
        for ticker in df_sorted.index:
            name = stock.get_market_ticker_name(ticker)
            curr = df_sorted.loc[ticker, "종가"]
            open_p = df_sorted.loc[ticker, "시가"]
            vol_today = df_sorted.loc[ticker, "거래량"]
            
            vol_prev = df_prev.loc[ticker, "거래량"] if ticker in df_prev.index else 1
            vol_ratio = (vol_today / vol_prev) * 100 if vol_prev > 0 else 0
            open_diff = ((curr - open_p) / open_p) * 100 if open_p > 0 else 0
            
            final_list.append({
                "종목명": name,
                "현재가": curr,
                "등락률": df_sorted.loc[ticker, "등락률"],
                "시초가대비": open_diff,
                "거래량비율": vol_ratio,
                "거래량": vol_today
            })
        return s_hist, ex_rate, pd.DataFrame(final_list)
    except:
        return s_hist, ex_rate, pd.DataFrame()

try:
    s_hist, ex_rate, df = get_final_trading_data()
    now_kst_display = get_now_kst().strftime('%H:%M:%S')

    # 상단 정보 바
    c_usd = s_hist['Close'].iloc[-1]
    c_krw = (c_usd * ex_rate) / 31.1034768
    st.info(f"🥈 실시간 은: {c_krw:,.0f}원 | 🕒 한국 시각: {now_kst_display} (30초 자동 갱신)")

    if not df.empty:
        # 2열 카드로 표시
        for i in range(0, 10, 2):
            cols = st.columns(2)
            for j in range(2):
                idx = i + j
                if idx < len(df):
                    row = df.iloc[idx]
                    with cols[j]:
                        # 핵심 조건 체크 (거래량 50% & 시초대비 +2%)
                        is_strong = row['거래량비율'] >= 50 and row['시초가대비'] >= 2
                        
                        # 강조 효과 적용
                        title_prefix = "⭐ [강력 매수 타점!] " if is_strong else ""
                        
                        # 컨테이너 사용하여 강조 효과
                        with st.container():
                            if is_strong:
                                st.success(f"{title_prefix} {row['종목명']}")
                            else:
                                st.subheader(f"{row['종목명']}")
                                
                            st.metric(
                                label="현재가", 
                                value=f"{int(row['현재가']):,}원", 
                                delta=f"{row['등락률']:.2f}%"
                            )
                            
                            c1, c2 = st.columns(2)
                            c1.write(f"📈 시초가대비: **{row['시초가대비']:+.2f}%**")
                            c2.write(f"📊 거래량비율: **{row['거래량비율']:.1f}%**")
                            
                            st.caption(f"🎯 목표(+3%): {int(row['현재가']*1.03):,}원 | 🛑 손절(-2%): {int(row['현재가']*0.98):,}원")
                            st.divider()
    else:
        st.warning("데이터를 가져오는 중입니다. 9시 이후에 확인해 주세요.")

except Exception as e:
    st.error("데이터 업데이트 중...")

if st.button('🔄 수동 새로고침'):
    st.cache_data.clear()
    st.rerun()
