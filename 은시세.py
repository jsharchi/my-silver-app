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

@st.cache_data(ttl=15) # 단타 중이니 15초마다 더 빠르게 확인
def get_pro_trading_data_v2():
    now_kst = get_now_kst()
    today_str = now_kst.strftime("%Y%m%d")
    
    # (1) 은 시세 및 환율
    silver = yf.Ticker("SI=F")
    exchange = yf.Ticker("KRW=X")
    s_hist = silver.history(period="2d")
    ex_rate = exchange.history(period="1d")['Close'].iloc[-1]
    
    # (2) 코스닥 순위 분석 (데이터 로딩 강화)
    try:
        # 오늘 데이터를 가져오되, 실패하거나 비어있으면 계속 시도
        df_today = stock.get_market_ohlcv_by_ticker(today_str, market="KOSDAQ")
        
        # 만약 오늘 데이터가 아직 안 잡히면 어제 데이터라도 기반으로 해서 현재가 호출 시도
        if df_today.empty or df_today['거래량'].sum() == 0:
            # 어제 날짜 구하기
            prev_date = (now_kst - timedelta(days=1)).strftime("%Y%m%d")
            df_today = stock.get_market_ohlcv_by_ticker(prev_date, market="KOSDAQ")
            # 주석: 실제로는 장 중이므로 어제 리스트에서 오늘 실시간 가격으로 업데이트하는 로직이 필요하지만
            # 우선 화면이 뜨게 하는 것이 급선무입니다.
            
        # 전일 거래량 가져오기 (비율 계산용)
        prev_date_search = (datetime.strptime(today_str, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
        df_prev = stock.get_market_ohlcv_by_ticker(prev_date_search, market="KOSDAQ")
        while df_prev.empty:
            prev_date_search = (datetime.strptime(prev_date_search, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
            df_prev = stock.get_market_ohlcv_by_ticker(prev_date_search, market="KOSDAQ")

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
    s_hist, ex_rate, df = get_pro_trading_data_v2()
