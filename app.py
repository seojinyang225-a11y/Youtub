# app.py
# 유튜브 댓글 분석 웹앱 (Streamlit)
# 실행 방법:
# 1. pip install streamlit pandas matplotlib wordcloud google-api-python-client konlpy
# 2. streamlit run app.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
from googleapiclient.discovery import build
from konlpy.tag import Okt
import re

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(
    page_title="유튜브 댓글 분석기",
    layout="wide"
)

st.title("📺 유튜브 댓글 분석 웹앱")
st.write("유튜브 영상 링크를 입력하면 댓글을 수집하고 분석합니다.")

# -----------------------------
# 유튜브 API KEY 입력
# -----------------------------
api_key = st.text_input(
    "🔑 YouTube Data API Key 입력",
    type="password"
)

# -----------------------------
# 영상 링크 입력
# -----------------------------
video_url = st.text_input(
    "🎬 유튜브 영상 링크 입력",
    placeholder="https://www.youtube.com/watch?v=..."
)

# -----------------------------
# 댓글 개수 슬라이더
# -----------------------------
comment_count = st.slider(
    "💬 수집할 댓글 수",
    min_value=20,
    max_value=10000,
    value=200,
    step=20
)

# -----------------------------
# 영상 ID 추출 함수
# -----------------------------
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

# -----------------------------
# 댓글 수집 함수
# -----------------------------
def get_comments(api_key, video_id, max_comments):

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

# -----------------------------
# 워드클라우드 생성
# -----------------------------
def make_wordcloud(text_data):

    okt = Okt()

    nouns = []

    for text in text_data:
        nouns.extend(okt.nouns(str(text)))

    # 2글자 이상만 사용
    nouns = [word for word in nouns if len(word) >= 2]

    count = Counter(nouns)

    wc = WordCloud(
        font_path="malgun.ttf",   # 윈도우 한글 폰트
        background_color="white",
        width=1000,
        height=500
    )

    return wc.generate_from_frequencies(count)

# -----------------------------
# 분석 시작
# -----------------------------
if st.button("🚀 댓글 분석 시작"):

    if not api_key:
        st.error("YouTube API Key를 입력해주세요.")
        st.stop()

    if not video_url:
        st.error("유튜브 링크를 입력해주세요.")
        st.stop()

    video_id = extract_video_id(video_url)

    if not video_id:
        st.error("올바른 유튜브 링크가 아닙니다.")
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

    st.success(f"✅ 댓글 {len(df)}개 수집 완료!")

    # -----------------------------
    # 데이터 전처리
    # -----------------------------
    df["publishedAt"] = pd.to_datetime(df["publishedAt"])
    df["hour"] = df["publishedAt"].dt.hour

    # -----------------------------
    # 데이터 보기
    # -----------------------------
    st.subheader("📄 수집된 댓글 데이터")

    st.dataframe(df)

    # -----------------------------
    # 시간대별 댓글 분석
    # -----------------------------
    st.subheader("⏰ 시간대별 댓글 추이")

    hourly_comments = (
        df.groupby("hour")
        .size()
        .reset_index(name="count")
    )

    fig1, ax1 = plt.subplots(figsize=(10, 5))

    ax1.plot(
        hourly_comments["hour"],
        hourly_comments["count"],
        marker="o"
    )

    ax1.set_xlabel("시간")
    ax1.set_ylabel("댓글 수")
    ax1.set_title("시간대별 댓글 수")

    st.pyplot(fig1)

    # -----------------------------
    # 좋아요 수 분석
    # -----------------------------
    st.subheader("👍 좋아요 수 분석")

    fig2, ax2 = plt.subplots(figsize=(10, 5))

    ax2.hist(df["likes"], bins=20)

    ax2.set_xlabel("좋아요 수")
    ax2.set_ylabel("댓글 개수")
    ax2.set_title("댓글 좋아요 분포")

    st.pyplot(fig2)

    st.metric(
        "평균 좋아요 수",
        round(df["likes"].mean(), 2)
    )

    st.metric(
        "최대 좋아요 수",
        int(df["likes"].max())
    )

    # -----------------------------
    # 워드클라우드
    # -----------------------------
    st.subheader("☁️ 자주 등장하는 단어")

    wordcloud = make_wordcloud(df["comment"])

    fig3, ax3 = plt.subplots(figsize=(15, 7))

    ax3.imshow(wordcloud, interpolation="bilinear")
    ax3.axis("off")

    st.pyplot(fig3)

    # -----------------------------
    # 인기 댓글 TOP10
    # -----------------------------
    st.subheader("🔥 좋아요 TOP 10 댓글")

    top_comments = df.sort_values(
        by="likes",
        ascending=False
    ).head(10)

    st.dataframe(
        top_comments[["comment", "likes"]]
    )