import streamlit as st
import pandas as pd
from single_agent import single_score
from double_agent import double_score
from stability import multi_test

st.set_page_config(
    page_title="AIレポート評価システム",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AIレポート評価システム（研究Demo）")
st.caption("研究テーマ：生成AIによる課題自動評価の公平性")

# -------------------------
# 左右布局
# -------------------------
left, right = st.columns([2, 1])

with left:

    question = st.text_area(
        "課題",
        value="""Pythonとは何ですか。
        Pythonの特徴を説明し、
        応用例を2つ挙げなさい。""",
        height=120
    )

    rubric = st.text_area(
        "評価基準（Rubric）",
        value="""
        ① 内容の正確性：40点
        ② 内容の完全性：30点
        ③ 論理性：20点
        ④ 具体例：10点""",
        height=180
    )

    text = st.text_area(
        "学生の回答",
        height=220,
        placeholder="学生の回答を入力してください。"
    )

with right:

    st.info(
        "現在の機能：\n"
        "① 単一Agent評価\n"
        "② 評価の安定性検証\n"
        "③ 2-Agent評価"
    )

st.divider()

tab1, tab2, tab3 = st.tabs(
    ["① 単一Agent評価", "② 安定性評価", "③ 2-Agent評価"]
)

# ==================================================
# 单Agent
# ==================================================
with tab1:

    st.subheader("単一Agent評価（Baseline）")

    if st.button("単一Agent評価開始"):

        if text.strip() == "":
            st.warning("学生の回答を入力してください。")

        else:

            score, comment = single_score(
                question,
                rubric,
                text
            )

            c1, c2 = st.columns(2)

            with c1:
                st.metric("総合得点", score)

            with c2:
                st.metric(
                    "評価",
                    "A" if score >= 80 else "B"
                )

            st.success(comment)

# ==================================================
# 稳定性测试
# ==================================================
with tab2:

    st.subheader("評価の安定性分析")

    if st.button("5回評価を実行", key="stability"):

        if text.strip() == "":
            st.warning("学生の回答を入力してください。")

        else:

            scores, avg, highest, lowest, diff, std, analysis = multi_test(
                question,
                rubric,
                text
            )

            df = pd.DataFrame({
                "回数": [1, 2, 3, 4, 5],
                "得点": scores
            })

            c1, c2, c3 = st.columns(3)

            with c1:
                st.metric("平均点", avg)

            with c2:
                st.metric("最高点", highest)

            with c3:
                st.metric("最低点", lowest)

            c4, c5 = st.columns(2)

            with c4:
                st.metric("変動幅", diff)

            with c5:
                st.metric("標準偏差", std)

            st.dataframe(df, width="stretch")

            st.line_chart(df.set_index("回数"))

            st.info(
                f"""
            ### 分析結果

            - 平均点：{avg}
            - 標準偏差：{std}
            - 変動幅：{diff}

            **考察：**

            {analysis}
            """
            )

# ==================================================
# 双Agent
# ==================================================
with tab3:

    st.subheader("2-Agentによる評価・検証")

    if st.button("2-Agent評価開始"):

        if text.strip() == "":
            st.warning("学生の回答を入力してください。")

        else:

            first_score, first_comment, final_score,final_comment, review_comment= double_score(
                question,
                rubric,
                text
            )

            c1, c2 = st.columns(2)

            with c1:
                st.metric("Evaluation Agent（評価Agent）", first_score)

            with c2:
                st.metric("Review Agent（検証Agent）", final_score)

            st.markdown("### 🧑‍🏫 Evaluation Agent の評価")

            st.info(first_comment)

            st.markdown("### 🔍 Review Agent の評価")

            st.info(review_comment)

            st.progress(final_score / 100)

st.divider()