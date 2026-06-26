import streamlit as st
import pandas as pd
import plotly.express as px
from googleapiclient.discovery import build
import datetime

# -------------------------
# 페이지 설정
# -------------------------
st.set_page_config(
    page_title="유튜브 수익 분석기",
    page_icon="💰",
    layout="wide"
)

st.title("💰 YouTube 채널 수익 분석기")

st.markdown("""
채널명을 입력하면

- 채널 정보
- 최근 영상 분석
- 예상 광고수익
- 조회수 그래프

를 확인할 수 있습니다.
""")

# -------------------------
# API KEY
# -------------------------
if "YOUTUBE_API_KEY" not in st.secrets:
    st.error("YOUTUBE_API_KEY가 없습니다.")
    st.stop()

API_KEY = st.secrets["YOUTUBE_API_KEY"]

youtube = build(
    "youtube",
    "v3",
    developerKey=API_KEY
)

# -------------------------
# 환율
# -------------------------
USD_TO_KRW = 1350

# -------------------------
# CPM 선택
# -------------------------
country = st.sidebar.selectbox(
    "광고 국가",
    [
        "대한민국",
        "미국"
    ]
)

if country == "대한민국":
    LOW_CPM = 1.5
    HIGH_CPM = 4

else:
    LOW_CPM = 3
    HIGH_CPM = 8

# -------------------------
# 채널 검색
# -------------------------
def search_channel(name):

    request = youtube.search().list(
        q=name,
        part="snippet",
        type="channel",
        maxResults=1
    )

    response = request.execute()

    if len(response["items"]) == 0:
        return None

    return response["items"][0]["snippet"]["channelId"]

# -------------------------
# 채널 정보
# -------------------------
def get_channel_info(channel_id):

    request = youtube.channels().list(
        id=channel_id,
        part="snippet,statistics"
    )

    response = request.execute()

    item = response["items"][0]

    snippet = item["snippet"]
    stats = item["statistics"]

    thumbnail = snippet["thumbnails"]["high"]["url"]

    return {

        "title": snippet["title"],

        "description": snippet.get(
            "description",
            ""
        ),

        "thumbnail": thumbnail,

        "published": snippet["publishedAt"][:10],

        "subs": int(
            stats.get(
                "subscriberCount",
                0
            )
        ),

        "views": int(
            stats.get(
                "viewCount",
                0
            )
        ),

        "videos": int(
            stats.get(
                "videoCount",
                0
            )
        )

    }

# -------------------------
# 최근 영상
# -------------------------
def get_recent_videos(channel_id):

    search = youtube.search().list(
        channelId=channel_id,
        part="snippet",
        order="date",
        type="video",
        maxResults=50
    ).execute()

    ids = []

    for item in search["items"]:
        ids.append(item["id"]["videoId"])

    video = youtube.videos().list(
        part="statistics,snippet",
        id=",".join(ids)
    ).execute()

    rows = []

    for item in video["items"]:

        rows.append({

            "제목":
            item["snippet"]["title"],

            "게시일":
            item["snippet"]["publishedAt"][:10],

            "조회수":
            int(
                item["statistics"].get(
                    "viewCount",
                    0
                )
            ),

            "좋아요":
            int(
                item["statistics"].get(
                    "likeCount",
                    0
                )
            ),

            "댓글":
            int(
                item["statistics"].get(
                    "commentCount",
                    0
                )
            )

        })

    df = pd.DataFrame(rows)

    return df
  # -------------------------
# 예상 수익 계산
# -------------------------
def estimate_revenue(avg_views):

    monthly_views = avg_views * 30

    low_month = monthly_views / 1000 * LOW_CPM
    high_month = monthly_views / 1000 * HIGH_CPM

    return low_month, high_month


# -------------------------
# 메인 UI
# -------------------------
channel_name = st.text_input(
    "유튜브 채널명을 입력하세요"
)

analyze = st.button("🔍 분석 시작")

if analyze:

    if channel_name == "":
        st.warning("채널명을 입력해주세요.")
        st.stop()

    with st.spinner("채널을 분석하는 중입니다..."):

        channel_id = search_channel(channel_name)

        if channel_id is None:
            st.error("채널을 찾을 수 없습니다.")
            st.stop()

        info = get_channel_info(channel_id)

        df = get_recent_videos(channel_id)

# -------------------------
# 채널 정보
# -------------------------

        st.divider()

        col1, col2 = st.columns([1,3])

        with col1:

            st.image(
                info["thumbnail"],
                width=180
            )

        with col2:

            st.subheader(info["title"])

            st.write(info["description"])

            st.caption(
                f"개설일 : {info['published']}"
            )

# -------------------------
# 통계 카드
# -------------------------

        st.divider()

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "👥 구독자",
            f"{info['subs']:,}명"
        )

        c2.metric(
            "👁 총 조회수",
            f"{info['views']:,}회"
        )

        c3.metric(
            "🎥 영상 수",
            f"{info['videos']:,}개"
        )

# -------------------------
# 평균 조회수
# -------------------------

        avg_views = int(df["조회수"].mean())

        max_views = int(df["조회수"].max())

        min_views = int(df["조회수"].min())

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "평균 조회수",
            f"{avg_views:,}"
        )

        c2.metric(
            "최고 조회수",
            f"{max_views:,}"
        )

        c3.metric(
            "최저 조회수",
            f"{min_views:,}"
        )

# -------------------------
# 최근 영상 목록
# -------------------------

        st.divider()

        st.subheader("📺 최근 업로드 영상")

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

# -------------------------
# TOP10 조회수
# -------------------------

        top10 = (
            df
            .sort_values(
                "조회수",
                ascending=False
            )
            .head(10)
        )

        st.subheader("🏆 조회수 TOP10")

        st.dataframe(
            top10,
            use_container_width=True,
            hide_index=True
        )
      # -------------------------
# 조회수 그래프
# -------------------------

        st.divider()

        st.subheader("📊 최근 영상 조회수 그래프")

        fig = px.bar(
            df.sort_values("조회수", ascending=False),
            x="조회수",
            y="제목",
            orientation="h",
            text="조회수",
            height=700
        )

        fig.update_layout(
            yaxis=dict(autorange="reversed"),
            xaxis_title="조회수",
            yaxis_title="영상 제목"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# -------------------------
# 예상 광고 수익
# -------------------------

        low_month, high_month = estimate_revenue(avg_views)

        low_year = low_month * 12
        high_year = high_month * 12

        low_month_krw = low_month * USD_TO_KRW
        high_month_krw = high_month * USD_TO_KRW

        low_year_krw = low_year * USD_TO_KRW
        high_year_krw = high_year * USD_TO_KRW

        st.divider()

        st.subheader("💰 예상 광고 수익")

        c1, c2 = st.columns(2)

        with c1:

            st.success(f"""
### 📅 월 예상 수익

💵 **${low_month:,.0f} ~ ${high_month:,.0f}**

🇰🇷 **₩{low_month_krw:,.0f} ~ ₩{high_month_krw:,.0f}**
""")

        with c2:

            st.info(f"""
### 📆 연 예상 수익

💵 **${low_year:,.0f} ~ ${high_year:,.0f}**

🇰🇷 **₩{low_year_krw:,.0f} ~ ₩{high_year_krw:,.0f}**
""")

# -------------------------
# 분석 요약
# -------------------------

        st.divider()

        st.subheader("📈 분석 요약")

        st.write(f"""
- 평균 조회수 : **{avg_views:,}회**
- 최고 조회수 : **{max_views:,}회**
- 최근 영상 수 : **{len(df)}개**
- 예상 월수익 : **₩{low_month_krw:,.0f} ~ ₩{high_month_krw:,.0f}**
- 예상 연수익 : **₩{low_year_krw:,.0f} ~ ₩{high_year_krw:,.0f}**
""")

# -------------------------
# CSV 다운로드
# -------------------------

        csv = df.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            label="📥 영상 데이터 CSV 다운로드",
            data=csv,
            file_name="youtube_analysis.csv",
            mime="text/csv"
        )
      # -------------------------
# 채널 성장도 분석
# -------------------------

        st.divider()
        st.subheader("📈 채널 성장도")

        if avg_views >= 1_000_000:
            grade = "★★★★★"
            comment = "매우 높은 성장세의 채널입니다."
        elif avg_views >= 300_000:
            grade = "★★★★☆"
            comment = "성장세가 좋은 채널입니다."
        elif avg_views >= 100_000:
            grade = "★★★☆☆"
            comment = "안정적으로 성장 중인 채널입니다."
        elif avg_views >= 30_000:
            grade = "★★☆☆☆"
            comment = "성장 가능성이 있는 채널입니다."
        else:
            grade = "★☆☆☆☆"
            comment = "더 많은 콘텐츠 업로드가 필요합니다."

        st.metric("성장 등급", grade)
        st.write(comment)

# -------------------------
# CPM 설명
# -------------------------

        with st.expander("💡 예상 수익 계산 기준"):

            st.markdown(f"""
**현재 선택한 국가:** {country}

사용된 CPM(1000회 조회당 광고수익)

- 최소 CPM : **${LOW_CPM}**
- 최대 CPM : **${HIGH_CPM}**

> 실제 광고수익은
> - 시청 국가
> - 광고 종류
> - 시청 시간
> - 광고 클릭률
> 등에 따라 달라질 수 있습니다.

본 프로그램은 최근 영상의 평균 조회수를 기준으로 **예상 광고수익**을 계산합니다.
""")

# -------------------------
# 푸터
# -------------------------

        st.divider()

        st.caption("© 2026 YouTube Income Analyzer")
        st.caption("Made with ❤️ using Streamlit")

else:
    st.info("왼쪽(또는 위)의 입력창에 유튜브 채널명을 입력한 후 **'분석 시작'** 버튼을 눌러주세요.")
