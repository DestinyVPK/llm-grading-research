from api_client import call_model
import re


def create_initial_prompt(question, rubric, text):
    return f"""
あなたは大学教員として、以下の課題を評価してください。

【課題】
{question}

【評価基準（Rubric）】
{rubric}

【学生の回答】
{text}

評価の根拠として使用できるのは、
【学生の回答】に実際に記述されている内容だけです。

課題文やRubricに記載されている内容を、
学生が回答した内容として扱ってはいけません。

学生の回答が空白、無関係な文字列、
課題文またはRubricの単なるコピーである場合は、
回答として成立していないため、原則として0点としてください。

学生の回答に存在しない説明、特徴、具体例を、
推測または補完して評価してはいけません。

評価は必ず評価基準に従ってください。
各項目をRubricに記載された順番で採点し、
各項目の得点と簡潔なコメントを記述してください。

Rubricに存在しない評価項目を追加してはいけません。
各項目の得点は上限点を超えてはいけません。
各項目の得点合計と総合得点を一致させてください。

最後に必ず以下の形式で出力してください。

総合得点：（各項目の得点合計）
コメント：
"""


def single_score(question, rubric, text):
    prompt = create_initial_prompt(question, rubric, text)
    result = call_model(prompt)

    match = re.search(r"総合得点\s*[:：]\s*(\d+)", result)

    if match:
        score = int(match.group(1))
    else:
        print("===== SCORE EXTRACTION FAILED =====")
        print(result)
        raise ValueError("AIの出力から総合得点を取得できませんでした")

    return score, result