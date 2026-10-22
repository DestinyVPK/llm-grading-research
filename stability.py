from single_agent import single_score
import statistics


def multi_test(question, rubric, text):

    scores = []

    for _ in range(5):

        score, _ = single_score(
            question,
            rubric,
            text
        )

        scores.append(score)

    # 统计数据
    avg = round(statistics.mean(scores), 2)

    highest = max(scores)

    lowest = min(scores)

    diff = highest - lowest

    std = round(statistics.stdev(scores), 2)

    # 简单分析
    if std < 2:
        analysis = "評価結果は非常に安定しています。"

    elif std < 5:
        analysis = "評価結果には多少のばらつきがあります。"

    else:
        analysis = (
            "評価結果のばらつきが大きく、"
            "公平性に影響を与える可能性があります。"
        )

    return (
        scores,
        avg,
        highest,
        lowest,
        diff,
        std,
        analysis
    )