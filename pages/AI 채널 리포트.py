import streamlit as st
import pandas as pd
from googleapiclient.discovery import build

# -----------------------------------
# 페이지 설정
# -----------------------------------
st.set_page_config(
    page_title="🤖 AI 채널 리포트",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI 채널 리포트")
st.caption("유튜브 채널을 AI가 분석하여 등급과 성장 가능성을 알려드립니다.")

# -----------------------------------
# API KEY
# -----------------------------------
if "YOUTUBE_API_KEY" not in st.secrets:
    st.error("YOUTUBE_API_KEY가 설정되어 있지 않습니다.")
    st.stop()

youtube = build(
    "youtube",
    "v3",
    developerKey=st.secrets["YOUTUBE_API_KEY"]
)

# -----------------------------------
# 채널 검색
# -----------------------------------
def search_channel(channel_name):

    request = youtube.search().list(
        q=channel_name,
        part="snippet",
        type="channel",
        maxResults=1
    )

    response = request.execute()

    if len(response["items"]) == 0:
        return None

    return response["items"][0]["snippet"]["channelId"]


# -----------------------------------
# 채널 정보 가져오기
# -----------------------------------
def get_channel_info(channel_id):

    request = youtube.channels().list(
        part="snippet,statistics",
        id=channel_id
    )

    response = request.execute()

    item = response["items"][0]

    return {
        "title": item["snippet"]["title"],
        "description": item["snippet"]["description"],
        "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
        "subscriber": int(item["statistics"].get("subscriberCount", 0)),
        "view": int(item["statistics"].get("viewCount", 0)),
        "video": int(item["statistics"].get("videoCount", 0))
    }


# -----------------------------------
# 최근 영상 가져오기
# -----------------------------------
def get_recent_videos(channel_id):

    search = youtube.search().list(
        channelId=channel_id,
        part="snippet",
        order="date",
        type="video",
        maxResults=20
    ).execute()

    ids = [
        item["id"]["videoId"]
        for item in search["items"]
    ]

    videos = youtube.videos().list(
        part="statistics,snippet",
        id=",".join(ids)
    ).execute()

    rows = []

    for item in videos["items"]:

        rows.append({
            "제목": item["snippet"]["title"],
            "조회수": int(item["statistics"].get("viewCount", 0)),
            "좋아요": int(item["statistics"].get("likeCount", 0)),
            "댓글": int(item["statistics"].get("commentCount", 0))
        })

    return pd.DataFrame(rows)


# -----------------------------------
# 화면
# -----------------------------------
channel_name = st.text_input("📺 채널명을 입력하세요")

if st.button("🤖 AI 분석 시작"):

    if channel_name == "":
        st.warning("채널명을 입력해주세요.")
        st.stop()

    with st.spinner("AI가 채널을 분석하고 있습니다..."):

        channel_id = search_channel(channel_name)

        if channel_id is None:
            st.error("채널을 찾을 수 없습니다.")
            st.stop()

        info = get_channel_info(channel_id)

        df = get_recent_videos(channel_id)

        st.success("채널 정보를 불러왔습니다!")

        col1, col2 = st.columns([1,3])

        with col1:
            st.image(info["thumbnail"], width=180)

        with col2:
            st.subheader(info["title"])
            st.write(info["description"])

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "👥 구독자",
            f"{info['subscriber']:,}명"
        )

        c2.metric(
            "👁 총 조회수",
            f"{info['view']:,}회"
        )

        c3.metric(
            "🎥 영상 수",
            f"{info['video']:,}개"
        )

        st.divider()

        st.subheader("📺 최근 업로드 영상")

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
                # -----------------------------------
        # 평균값 계산
        # -----------------------------------

        avg_views = int(df["조회수"].mean())
        avg_likes = int(df["좋아요"].mean())
        avg_comments = int(df["댓글"].mean())

        st.divider()

        st.subheader("📊 평균 통계")

        a1, a2, a3 = st.columns(3)

        a1.metric(
            "평균 조회수",
            f"{avg_views:,}회"
        )

        a2.metric(
            "평균 좋아요",
            f"{avg_likes:,}개"
        )

        a3.metric(
            "평균 댓글",
            f"{avg_comments:,}개"
        )

        # -----------------------------------
        # AI 점수 계산
        # -----------------------------------

        score = 0

        # 구독자
        subs = info["subscriber"]

        if subs >= 10000000:
            score += 30

        elif subs >= 1000000:
            score += 25

        elif subs >= 100000:
            score += 20

        elif subs >= 10000:
            score += 15

        else:
            score += 10

        # 평균 조회수

        if avg_views >= 1000000:
            score += 30

        elif avg_views >= 300000:
            score += 25

        elif avg_views >= 100000:
            score += 20

        elif avg_views >= 30000:
            score += 15

        else:
            score += 10

        # 업로드 수

        videos = info["video"]

        if videos >= 1000:
            score += 20

        elif videos >= 500:
            score += 18

        elif videos >= 200:
            score += 16

        elif videos >= 50:
            score += 14

        else:
            score += 10

        # 좋아요 비율

        like_rate = avg_likes / avg_views if avg_views > 0 else 0

        if like_rate >= 0.05:
            score += 20

        elif like_rate >= 0.03:
            score += 18

        elif like_rate >= 0.02:
            score += 16

        elif like_rate >= 0.01:
            score += 14

        else:
            score += 10

        # 점수 최대 100

        score = min(score, 100)

        # -----------------------------------
        # 등급 계산
        # -----------------------------------

        if score >= 95:
            grade = "👑 Legend"

        elif score >= 90:
            grade = "💎 Diamond"

        elif score >= 80:
            grade = "🥇 Gold"

        elif score >= 70:
            grade = "🥈 Silver"

        elif score >= 60:
            grade = "🥉 Bronze"

        else:
            grade = "🌱 Rookie"

        st.divider()

        st.subheader("🏆 AI 채널 평가")

        g1, g2 = st.columns(2)

        g1.metric(
            "종합 점수",
            f"{score}점"
        )

        g2.metric(
            "유튜버 등급",
            grade
        )

        st.progress(score / 100)

        st.caption(f"성장 가능성 : {score}%")
                # -----------------------------------
        # AI 장점 분석
        # -----------------------------------

        strengths = []

        if avg_views >= 300000:
            strengths.append("📈 평균 조회수가 매우 높아 콘텐츠 경쟁력이 뛰어납니다.")

        if like_rate >= 0.04:
            strengths.append("❤️ 좋아요 비율이 높아 구독자의 만족도가 높습니다.")

        if info["subscriber"] >= 100000:
            strengths.append("👥 많은 구독자를 확보하여 안정적인 팬층을 보유하고 있습니다.")

        if info["video"] >= 200:
            strengths.append("🎥 업로드된 영상이 많아 꾸준한 활동을 이어가고 있습니다.")

        if avg_comments >= 300:
            strengths.append("💬 댓글 참여가 활발하여 시청자와의 소통이 우수합니다.")

        if len(strengths) == 0:
            strengths.append("🌱 성장 가능성이 높은 채널입니다.")

        # -----------------------------------
        # 개선점
        # -----------------------------------

        improvements = []

        if avg_views < 50000:
            improvements.append("📈 조회수를 높이기 위해 썸네일과 제목 개선을 추천합니다.")

        if like_rate < 0.02:
            improvements.append("❤️ 좋아요 참여를 유도하는 멘트를 활용해 보세요.")

        if avg_comments < 100:
            improvements.append("💬 댓글 이벤트 등으로 시청자 참여를 늘려보세요.")

        if info["video"] < 100:
            improvements.append("🎥 꾸준한 업로드가 채널 성장에 도움이 됩니다.")

        if len(improvements) == 0:
            improvements.append("🎉 현재 특별한 개선점은 보이지 않습니다.")

        # -----------------------------------
        # AI 종합 의견
        # -----------------------------------

        if score >= 90:

            opinion = """
현재 채널은 매우 우수한 성장세를 보이고 있습니다.

조회수와 구독자 규모가 안정적이며
팬들의 반응도 매우 좋습니다.

현재 업로드 주기를 유지한다면
앞으로도 지속적인 성장이 기대됩니다.
"""

        elif score >= 80:

            opinion = """
채널이 꾸준히 성장하고 있습니다.

콘텐츠 품질이 우수하며
앞으로의 성장 가능성도 높습니다.

쇼츠나 트렌드 콘텐츠를 활용하면
더 빠른 성장이 가능합니다.
"""

        elif score >= 70:

            opinion = """
안정적으로 운영되고 있는 채널입니다.

콘텐츠 업로드를 꾸준히 유지하고
썸네일과 제목을 개선한다면
조회수 증가를 기대할 수 있습니다.
"""

        else:

            opinion = """
현재 성장 초기 단계의 채널입니다.

꾸준한 업로드와
시청자와의 소통을 늘리면
채널 성장에 큰 도움이 될 것입니다.
"""

        # -----------------------------------
        # 화면 출력
        # -----------------------------------

        st.divider()

        st.subheader("🤖 AI 분석 결과")

        st.success("### 👍 장점")

        for item in strengths:
            st.write(item)

        st.warning("### ⚠ 개선점")

        for item in improvements:
            st.write(item)

        st.info("### 🤖 AI 종합 의견")

        st.write(opinion)
                # -----------------------------------
        # 예상 광고 수익 계산
        # -----------------------------------

        USD_TO_KRW = 1350

        # CPM (예상값)
        LOW_CPM = 1
        HIGH_CPM = 5

        monthly_views = avg_views * 30

        low_month_usd = monthly_views / 1000 * LOW_CPM
        high_month_usd = monthly_views / 1000 * HIGH_CPM

        low_year_usd = low_month_usd * 12
        high_year_usd = high_month_usd * 12

        low_month_krw = low_month_usd * USD_TO_KRW
        high_month_krw = high_month_usd * USD_TO_KRW

        low_year_krw = low_year_usd * USD_TO_KRW
        high_year_krw = high_year_usd * USD_TO_KRW

        st.divider()

        st.subheader("💰 예상 광고 수익")

        c1, c2 = st.columns(2)

        with c1:

            st.success(f"""
### 📅 월 예상 수익

💵 ${low_month_usd:,.0f} ~ ${high_month_usd:,.0f}

🇰🇷 ₩{low_month_krw:,.0f}
~
₩{high_month_krw:,.0f}
""")

        with c2:

            st.info(f"""
### 📆 연 예상 수익

💵 ${low_year_usd:,.0f} ~ ${high_year_usd:,.0f}

🇰🇷 ₩{low_year_krw:,.0f}
~
₩{high_year_krw:,.0f}
""")

        # -----------------------------------
        # AI 성적표
        # -----------------------------------

        st.divider()

        st.subheader("🏆 AI 채널 성적표")

        report = pd.DataFrame({

            "항목":[

                "채널명",

                "구독자",

                "평균 조회수",

                "AI 점수",

                "등급",

                "성장 가능성"

            ],

            "결과":[

                info["title"],

                f"{info['subscriber']:,}명",

                f"{avg_views:,}회",

                f"{score}점",

                grade,

                f"{score}%"

            ]

        })

        st.dataframe(
            report,
            use_container_width=True,
            hide_index=True
        )

        # -----------------------------------
        # CSV 다운로드
        # -----------------------------------

        csv = report.to_csv(index=False).encode("utf-8-sig")

        st.download_button(

            "📥 AI 리포트 다운로드(CSV)",

            csv,

            file_name="AI_Report.csv",

            mime="text/csv"

        )

        st.divider()

        st.success("🎉 AI 분석이 완료되었습니다!")
