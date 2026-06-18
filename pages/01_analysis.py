import streamlit as st
import pandas as pd
import plotly.express as px
from googleapiclient.discovery import build

# ------------------
# API
# ------------------
API_KEY = st.secrets["YOUTUBE_API_KEY"]

youtube = build(
    "youtube",
    "v3",
    developerKey=API_KEY
)

# ------------------
# 채널 검색
# ------------------
def search_channel(channel_name):

    request = youtube.search().list(
        q=channel_name,
        part="snippet",
        type="channel",
        maxResults=1
    )

    response = request.execute()

    if not response["items"]:
        return None

    return response["items"][0]["snippet"]["channelId"]

# ------------------
# 채널 정보
# ------------------
def get_channel_info(channel_id):

    request = youtube.channels().list(
        part="statistics,snippet",
        id=channel_id
    )

    response = request.execute()

    item = response["items"][0]

    return {
        "name": item["snippet"]["title"],
        "subs": int(item["statistics"].get("subscriberCount",0)),
        "views": int(item["statistics"].get("viewCount",0)),
        "videos": int(item["statistics"].get("videoCount",0))
    }

# ------------------
# 최근 영상
# ------------------
def get_recent_videos(channel_id):

    request = youtube.search().list(
        channelId=channel_id,
        part="snippet",
        order="date",
        type="video",
        maxResults=20
    )

    response = request.execute()

    video_ids = [
        item["id"]["videoId"]
        for item in response["items"]
    ]

    stats = youtube.videos().list(
        part="statistics,snippet",
        id=",".join(video_ids)
    ).execute()

    data = []

    for item in stats["items"]:

        data.append({
            "제목": item["snippet"]["title"],
            "조회수": int(item["statistics"].get("viewCount",0))
        })

    return pd.DataFrame(data)

# ------------------
# 수익 계산
# ------------------
def estimate_revenue(avg_views):

    # CPM 가정
    low_cpm = 1
    high_cpm = 5

    monthly_views = avg_views * 30

    low_month = monthly_views / 1000 * low_cpm
    high_month = monthly_views / 1000 * high_cpm

    return low_month, high_month

# ------------------
# UI
# ------------------
st.title("💰 유튜브 채널 수익 분석기")

channel_name = st.text_input(
    "유튜브 채널명 입력"
)

if st.button("분석 시작"):

    with st.spinner("분석 중..."):

        channel_id = search_channel(channel_name)

        if not channel_id:
            st.error("채널을 찾을 수 없습니다.")
            st.stop()

        info = get_channel_info(channel_id)

        st.subheader(info["name"])

        c1,c2,c3 = st.columns(3)

        c1.metric("구독자", f"{info['subs']:,}")
        c2.metric("총 조회수", f"{info['views']:,}")
        c3.metric("영상 수", f"{info['videos']:,}")

        df = get_recent_videos(channel_id)

        st.subheader("최근 영상 조회수")

        st.dataframe(df)

        avg_views = df["조회수"].mean()

        low, high = estimate_revenue(avg_views)

        # 환율 (예시: 1달러 = 1,350원)
USD_TO_KRW = 1350

# 월 예상 수익 (달러)
low_month_usd = low
high_month_usd = high

# 연 예상 수익 (달러)
low_year_usd = low * 12
high_year_usd = high * 12

# 원화 변환
low_month_krw = low_month_usd * USD_TO_KRW
high_month_krw = high_month_usd * USD_TO_KRW

low_year_krw = low_year_usd * USD_TO_KRW
high_year_krw = high_year_usd * USD_TO_KRW

st.subheader("💰 예상 광고 수익")

st.success(f"""
### 📅 월 예상 수익

💵 ${low_month_usd:,.0f} ~ ${high_month_usd:,.0f}

🇰🇷 ₩{low_month_krw:,.0f}
~
₩{high_month_krw:,.0f}
""")

st.info(f"""
### 📆 연 예상 수익

💵 ${low_year_usd:,.0f} ~ ${high_year_usd:,.0f}

🇰🇷 ₩{low_year_krw:,.0f}
~
₩{high_year_krw:,.0f}
""")
        fig = px.bar(
            df,
            x="제목",
            y="조회수",
            title="최근 영상 조회수"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )
