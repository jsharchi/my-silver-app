import streamlit as st
import yfinance as yf
import pandas as pd

st.title("🥈 실시간 은 & 로봇주 거래량 모니터링")

# 1. 감시할 종목 리스트 (더 추가하셔도 됩니다)
watch_list = {
    "하이젠알앤엠": "445400.KQ",
    "SPG": "058610.KQ",
    "레인보우로보틱스": "272410.KQ",
    "에스비비테크": "307070.KQ",
    "뉴로메카": "348340.KQ",
    "이랜시스": "264850.KQ",
    "유진로봇": "056080.KQ",
    "로보티즈": "108490.KQ"
}

@st.cache_data(ttl=300) # 5분마다 갱신
def get_top_volume_stocks(stocks_dict):
    data_list = []
    for name, code in stocks_dict.items():
        ticker = yf.Ticker(code)
        df = ticker.history(period="2d")
        if not df.empty:
            current_vol = df['Volume'].iloc[-1]
            current_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
            data_list.append({
                "종목명": name,
                "현재가": current_price,
                "변동": current_price - prev_price,
                "거래량": current_vol
            })
    
    # 거래량 순으로 내림차순 정렬
    df_sorted = pd.DataFrame(data_list).sort_values(by="거래량", ascending=False)
    return df_sorted

try:
    st.subheader("🔥 등록 종목 거래량 순위 (Top 5)")
    top_df = get_top_volume_stocks(watch_list)
    
    # 상위 5개 종목을 카드 형태로 표시
    cols = st.columns(5)
    for i in range(min(5, len(top_df))):
        row = top_df.iloc[i]
        with cols[i]:
            st.metric(
                label=f"{i+1}위: {row['종목명']}", 
                value=f"{int(row['현재가']):,}원", 
                delta=f"{int(row['변동']):,}원"
            )
            st.caption(f"거래량: {int(row['거래량']):,}")

    st.divider()
    # 전체 리스트 표로 보여주기
    st.write("📊 전체 감시 종목 상세 현황")
    st.dataframe(top_df, use_container_width=True)

except Exception as e:
    st.error("거래량 데이터를 가져오는 중 오류가 발생했습니다.")
