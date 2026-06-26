import streamlit as st

st.set_page_config(
    page_title="AI 채널 리포트",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI 채널 리포트")

channel = st.text_input("유튜브 채널명을 입력하세요")

if st.button("분석하기"):

    # ------------------------
    # (임시 데이터)
    # 나중에 YouTube API와 연결
    # ------------------------

    subscribers = 520000
    avg_views = 310000
    upload = 12

    score = 0

    # 구독자 점수
    if subscribers >= 1000000:
        score += 30
    elif subscribers >= 500000:
        score += 25
    elif subscribers >= 100000:
        score += 20
    else:
        score += 10

    # 평균 조회수
    if avg_views >= 500000:
        score += 30
    elif avg_views >= 200000:
        score += 25
    elif avg_views >= 50000:
        score += 20
    else:
        score += 10

    # 업로드
    if upload >= 12:
        score += 20
    elif upload >= 8:
        score += 15
    else:
        score += 10

    # 기본 점수
    score += 20

    # ------------------------
    # 등급
    # ------------------------

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

    st.metric("종합 점수", f"{score}점")

    st.metric("유튜버 등급", grade)

    st.progress(score / 100)

    st.success("### 👍 장점")

    st.write("✔ 평균 조회수가 높습니다.")

    st.write("✔ 업로드가 꾸준합니다.")

    st.write("✔ 성장 가능성이 높습니다.")

    st.warning("### ⚠ 개선점")

    st.write("• Shorts 업로드를 늘려보세요.")

    st.write("• 댓글 참여를 유도하면 좋습니다.")

    st.info("### 🤖 AI 의견")

    st.write(
        """
현재 채널은 꾸준히 성장 중이며

팬층도 안정적입니다.

현재 업로드 주기를 유지한다면

앞으로도 성장 가능성이 높습니다.
"""
    )
