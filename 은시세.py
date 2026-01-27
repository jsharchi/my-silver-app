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
            vol_ratio = (vol_today / vol_prev) * 10
