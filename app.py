import re
import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
from youtube_comment_downloader import YoutubeCommentDownloader

# ------------------------
# 기본 설정
# ------------------------
st.set_page_config(
    page_title="YouTube 댓글 분석기",
    layout="wide"
)

st.title("📺 YouTube 댓글 분석기")
st.write("유튜브 링크를 입력하면 댓글을 수집하고 분석합니다.")

# ------------------------
# 유튜브 링크에서 ID 추출
# ------------------------
def extract_video_id(url):
    patterns = [
        r"v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})"
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None

# ------------------------
# 댓글 수집
# ------------------------
@st.cache_data(show_spinner=False)
def get_comments(video_url, limit):
    downloader = YoutubeCommentDownloader()
    comments = downloader.get_comments_from_url(video_url)

    data = []

    for i, comment in enumerate(comments):
        if i >= limit:
            break

        data.append({
            "author": comment.get("author"),
            "text": comment.get("text"),
            "likes": comment.get("votes", 0),
            "time": comment.get("time")
        })

    return pd.DataFrame(data)

# ------------------------
# 시간 문자열 변환
# ------------------------
def parse_time_column(df):
    hours = []

    for t in df["time"]:
        t = str(t)

        if "hour" in t:
            num = int(re.findall(r"\d+", t)[0])
            hours.append(num)

        elif "minute" in t:
            hours.append(0)

        elif "day" in t:
            num = int(re.findall(r"\d+", t)[0])
            hours.append(num * 24)

        else:
            hours.append(None)

    df["hours_ago"] = hours
    return df

# ------------------------
# 단어 추출
# ------------------------
def extract_words(texts):
    words = []

    stopwords = {
        "영상", "진짜", "너무", "정말",
        "이거", "그냥", "있어요", "합니다",
        "오늘", "제가", "ㅋㅋ", "ㅎㅎ"
    }

    for text in texts:
        text = str(text)

        # 한글 2글자 이상
        tokens = re.findall(r"[가-힣]{2,}", text)

        for word in tokens:
            if word not in stopwords:
                words.append(word)

    return words

# ------------------------
# 입력 UI
# ------------------------
url = st.text_input("🔗 유튜브 영상 링크 입력")

limit = st.slider(
    "댓글 수 선택",
    min_value=20,
    max_value=10000,
    value=500,
    step=20
)

# ------------------------
# 분석 버튼
# ------------------------
if st.button("댓글 분석 시작"):

    if not url:
        st.warning("유튜브 링크를 입력하세요.")
        st.stop()

    video_id = extract_video_id(url)

    if not video_id:
        st.error("올바른 유튜브 링크가 아닙니다.")
        st.stop()

    with st.spinner("댓글 수집 중..."):
        df = get_comments(url, limit)

    if df.empty:
        st.error("댓글을 불러오지 못했습니다.")
        st.stop()

    st.success(f"{len(df)}개 댓글 수집 완료!")

    # ------------------------
    # 데이터 보기
    # ------------------------
    with st.expander("댓글 데이터 보기"):
        st.dataframe(df)

    # ------------------------
    # 시간대별 댓글 추이
    # ------------------------
    st.subheader("🕒 시간대별 댓글 추이")

    df = parse_time_column(df)

    time_df = (
        df["hours_ago"]
        .dropna()
        .value_counts()
        .reset_index()
    )

    time_df.columns = ["hours_ago", "count"]

    fig_time = px.bar(
        time_df.sort_values("hours_ago"),
        x="hours_ago",
        y="count",
        labels={
            "hours_ago": "몇 시간 전",
            "count": "댓글 수"
        }
    )

    st.plotly_chart(fig_time, use_container_width=True)

    # ------------------------
    # 좋아요 분석
    # ------------------------
    st.subheader("👍 댓글 좋아요 수 분석")

    fig_likes = px.histogram(
        df,
        x="likes",
        nbins=30
    )

    st.plotly_chart(fig_likes, use_container_width=True)

    st.write("🔥 좋아요 많은 댓글 TOP 10")

    top_comments = (
        df.sort_values("likes", ascending=False)
        .head(10)
    )

    st.dataframe(
        top_comments[
            ["author", "likes", "text"]
        ]
    )

    # ------------------------
    # 워드클라우드
    # ------------------------
    st.subheader("☁️ 자주 등장하는 단어")

    words = extract_words(df["text"])

    if words:

        freq = Counter(words)

        wordcloud = WordCloud(
            font_path="NanumGothic.ttf",
            width=1000,
            height=500,
            background_color="white"
        ).generate_from_frequencies(freq)

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.imshow(wordcloud)
        ax.axis("off")

        st.pyplot(fig)

    else:
        st.info("표시할 단어가 없습니다.")
