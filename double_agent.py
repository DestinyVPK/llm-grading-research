from api_client import call_model
from single_agent import create_initial_prompt
import re

def extract_score(result, label):
    """
    AI的输出结果中から指定した見出しの得点を抽出する。
    """

    # 例：総合得点：100点中80点
    match = re.search(
        rf"{re.escape(label)}\s*[:：]\s*100\s*点?\s*中\s*(\d+)\s*点?",
        result,
        re.IGNORECASE
    )

    if match:
        return int(match.group(1))

    # 例：総合得点：80点／100点、80/100
    match = re.search(
        rf"{re.escape(label)}\s*[:：]\s*(\d+)\s*点?\s*[／/]\s*100\s*点?",
        result,
        re.IGNORECASE
    )

    if match:
        return int(match.group(1))

    # 例：総合得点：80点、Final Score：80
    match = re.search(
        rf"{re.escape(label)}\s*[:：]\s*(\d+)\s*点?",
        result,
        re.IGNORECASE
    )

    if match:
        return int(match.group(1))

    return None



def evaluation_agent(
        question,
        rubric,
        text,
        review_feedback=None
):
    # ==========================
    # Evaluation Agent
    # ==========================

    print("Evaluation Agent Start") #运行测试

    if review_feedback:
        prompt1 = f"""
    あなたは大学教員（Evaluation Agent）です。

    以下の課題、評価基準、学生の回答、およびReview Agentの修正提案を確認し、
    評価結果を再検討してください。

    【課題】
    {question}

    【評価基準（Rubric）】
    {rubric}

    【学生の回答】
    {text}

    【Review Agentからの修正提案】
    {review_feedback}

    評価は必ず評価基準（Rubric）に従って行ってください。

    各評価項目について、
    Rubricに記載された順番で採点し、
    各項目ごとに簡潔なコメントを記述してください。

    Rubricに存在しない評価項目を追加してはいけません。
    各評価項目の得点は、
    Rubricに記載された上限点を超えてはいけません。

    すべての評価項目の得点合計は、
    必ず総合得点と一致させてください。

    Review Agentの提案を無条件に受け入れるのではなく、
    課題、Rubric、学生の回答に基づいて判断してください。

    最後に必ず以下の形式で出力してください。

    総合得点：80
    コメント：
    """
    else:
        prompt1 = create_initial_prompt(question, rubric, text)

    first_result = call_model(prompt1)

    print("Evaluation Agent End")#运行测试

    first_score = extract_score(
        first_result,
        "総合得点"
    )

    if first_score is None:
        print(first_result)
        raise ValueError("AIの出力から総合得点を取得できませんでした")


    return (
        first_score,
        first_result
    )


def review_agent(
    question,
    rubric,
    text,
    evaluation_result
):
    # ==========================
    # Review Agent
    # ==========================
    print("Review Agent Start")
    prompt2 = f"""
あなたは大学教員ではなく、
Evaluation Agentの評価結果を確認するReview Agentです。

あなたの役割は、
Evaluation Agentの評価結果を確認し、
Rubricに基づいて評価が適切であるかを判断することです。

新しい評価を行ってはいけません。
新しい得点を決定してはいけません。

学生の回答を書き換えたり、
不足している内容を補ったり、
模範回答を作成したりしてはいけません。

以下の情報を確認してください。

【課題】
{question}

【評価基準（Rubric）】
{rubric}

【学生の回答】
{text}

【Evaluation Agentの評価結果】
{evaluation_result}

以下の点を確認してください。

① 評価がRubricに従っているか

② Rubricの全評価項目が評価されているか

③ Rubricに存在しない評価項目が追加されていないか

④ 各評価項目の得点が上限点を超えていないか

⑤ 各項目の得点合計と総合得点が一致しているか

⑥ 学生の回答に存在しない内容を評価していないか

⑦ 評価理由と得点が矛盾していないか

--------------------------------------------------

以下の場合は必ずNeed RevisionをYesにしてください。

・Rubricに存在しない評価項目が追加されている

・各評価項目の得点が上限点を超えている

・各評価項目の得点合計と総合得点が一致していない

・Score CorrectがNoである

上記以外では必ずNeed RevisionをNoにしてください。

以下の場合は必ずNeed RevisionをNoにしてください。

・文章表現を改善できるだけ

・コメントをもっと詳しく書けるだけ

・軽微な改善のみ

・評価結果は概ね妥当である

Review Agentの目的は、
評価結果を書き直すことではありません。

重大な評価ミスが存在する場合だけ、
Need RevisionをYesにしてください。

--------------------------------------------------

Need RevisionがYesの場合は、
Evaluation Agentが修正できるように、
具体的な修正内容だけをSuggestionに記載してください。

新しい評価結果を書いてはいけません。

新しい得点を書いてはいけません。

--------------------------------------------------

最後に必ず以下の形式で出力してください。

見出しの文字は変更しないでください。

Need Revision：Yes または No

Reason：
修正が必要、または不要と判断した理由

Affected Rubric：
該当するRubricの番号
（該当しない場合は「なし」）

Suggestion：
Evaluation Agentへの具体的な修正提案
（修正不要の場合は「なし」）

Score Correct：Yes または No
    """

    second_result = call_model(prompt2)
    print("Review Agent End")

    need_match = re.search(
        r"Need Revision\s*[:：]\s*(Yes|No)",
        second_result,
        re.IGNORECASE
    )

    if need_match:
        need_revision = need_match.group(1).lower() == "yes"
    else:
        print("Warning: Need Revisionを取得できませんでした")
        print(second_result)
        need_revision = True


    return (
        need_revision,
        second_result
    )

def double_score(question, rubric, text):

    first_score, first_result = evaluation_agent(
        question,
        rubric,
        text
    )

    current_score = first_score
    current_result = first_result

    final_score = first_score
    second_result = ""

    for i in range(3):

        print(f"Loop {i + 1}")

        need_revision, second_result = review_agent(
            question,
            rubric,
            text,
            current_result
        )

        print("Need Revision:", need_revision)

        if not need_revision:
            print("Revision is not required")
            break

        if i == 2:
            print("Maximum number of reviews reached")
            break

        current_score, current_result = evaluation_agent(
            question,
            rubric,
            text,
            second_result
        )


    final_score = current_score

    print("First Score:", first_score)
    print("Current Score:", current_score)
    print("Final Score:", final_score)

    return (
        first_score,
        first_result,
        final_score,
        current_result,
        second_result
    )