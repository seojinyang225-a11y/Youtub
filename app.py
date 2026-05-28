import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
from collections import Counter
from googleapiclient.discovery import build
from konlpy.tag import Okt
import matplotlib.pyplot as plt
import re

# ------------------
# 페이지 설정
# ------------------
st.set_page_config(
    page_title="유튜브 댓글 분석기",
    layout="wide"
)

st.title("📺 유튜브 댓글 분석기")
st.write("유튜브 링크를 입력하면 댓글을 분석합니다.")

# ------------------
# API KEY
# ------------------
api_key = st.secrets["YOUTUBE_API_KEY"]

# ------------------
# 입력
# ------------------
video_url = st.text_input(
    "유튜브 영상 링크"
)

comment_count = st.slider(
    "수집할 댓글 수",
    20,
    10000,
    200,
    step=20
)

# ------------------
# 영상 ID 추출
# ------------------
def extract_video_id(url):

    patterns = [
        r"v=([a-zA-Z0-9_-]+)",
        r"youtu\.be/([a-zA-Z0-9_-]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None

# ------------------
# 댓글 수집
# ------------------
def get_comments(
    api_key,
    video_id,
    max_comments
):

    youtube = build(
        "youtube",
        "v3",
        developerKey=api_key
    )

    comments = []

    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=100,
        textFormat="plainText"
    )

    while request and len(comments) < max_comments:

        response = request.execute()

        for item in response["items"]:

            snippet = item["snippet"]["topLevelComment"]["snippet"]

            comments.append({
                "comment": snippet["textDisplay"],
                "likes": snippet["likeCount"],
                "publishedAt": snippet["publishedAt"]
            })

            if len(comments) >= max_comments:
                break

        request = youtube.commentThreads().list_next(
            request,
            response
        )

    return pd.DataFrame(comments)

# ------------------
# 워드클라우드
# ------------------
def create_wordcloud(texts):

    okt = Okt()

    nouns = []

    for text in texts:
        nouns.extend(
            okt.nouns(str(text))
        )

    nouns = [
        word for word in nouns
        if len(word) >= 2
    ]

    count = Counter(nouns)

    wc = WordCloud(
        font_path="fonts/NanumGothic.ttf",
        background_color="white",
        width=1200,
        height=600
    )

    return wc.generate_from_frequencies(count)

# ------------------
# 버튼
# ------------------
if st.button("댓글 분석 시작"):

    video_id = extract_video_id(video_url)

    if not video_id:
        st.error("올바른 유튜브 링크를 입력해주세요.")
        st.stop()

    with st.spinner("댓글 수집 중..."):

        df = get_comments(
            api_key,
            video_id,
            comment_count
        )

    if df.empty:
        st.warning("댓글이 없습니다.")
        st.stop()

    df["publishedAt"] = pd.to_datetime(
        df["publishedAt"]
    )

    df["hour"] = df["publishedAt"].dt.hour

    st.success(
        f"{len(df)}개 댓글 수집 완료"
    )

    # ------------------
    # 시간대별
    # ------------------
    st.subheader("⏰ 시간대별 댓글 추이")

    hourly = (
        df.groupby("hour")
        .size()
        .reset_index(name="count")
    )

    fig1 = px.line(
        hourly,
        x="hour",
        y="count",
        markers=True
    )

    st.plotly_chart(
        fig1,
        use_container_width=True
    )

    # ------------------
    # 좋아요 분석
    # ------------------
    st.subheader("👍 좋아요 수 분석")

    fig2 = px.histogram(
        df,
        x="likes"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "평균 좋아요",
            round(df["likes"].mean(), 2)
        )

    with col2:
        st.metric(
            "최대 좋아요",
            int(df["likes"].max())
        )

    # ------------------
    # 워드클라우드
    # ------------------
    st.subheader("☁️ 자주 등장한 단어")

    wc = create_wordcloud(
        df["comment"]
    )

    fig3, ax = plt.subplots(
        figsize=(14, 7)
    )

    ax.imshow(wc)
    ax.axis("off")

    st.pyplot(fig3)

    # ------------------
    # CSV 다운로드
    # ------------------
    csv = df.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        "CSV 다운로드",
        csv,
        "comments.csv",
        "text/csv"
    )
