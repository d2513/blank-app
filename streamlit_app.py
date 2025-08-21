import streamlit as st
import random

# 세션 상태 초기화
if "number" not in st.session_state:
    st.session_state.number = random.randint(1, 100)
    st.session_state.attempts = 0
    st.session_state.finished = False

st.title("숫자 맞추기 게임 🎯")

# 폼 사용으로 엔터 키 제출 가능
with st.form("guess_form", clear_on_submit=False):
    guess = st.number_input("숫자를 입력하세요 (1~100):", min_value=1, max_value=100, step=1)
    submitted = st.form_submit_button("제출")

    if submitted:
        st.session_state.attempts += 1
        if guess < st.session_state.number:
            st.info("업 ⬆", icon="⬆")
        elif guess > st.session_state.number:
            st.info("다운 ⬇", icon="⬇")
        else:
            st.success(f"정답 🎉 {st.session_state.attempts}번 만에 맞췄어요!")
            st.session_state.finished = True

# 리셋 버튼을 제출 버튼과 동일 높이, 왼쪽 정렬
st.markdown(
    """
    <style>
    .reset-button-container {
        display: flex;
        justify-content: flex-start;
        margin-top: -50px; /* 높이 조정 */
        margin-left: 10px;  /* 왼쪽으로 살짝 이동 */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.container():
    st.markdown('<div class="reset-button-container">', unsafe_allow_html=True)
    if st.button("리셋"):
        st.session_state.number = random.randint(1, 100)
        st.session_state.attempts = 0
        st.session_state.finished = False
    st.markdown('</div>', unsafe_allow_html=True)
