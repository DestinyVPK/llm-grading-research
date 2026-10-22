
import csv
import re
import sys
from pathlib import Path

import pandas as pd

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api_client import call_model

DATA_DIR = ROOT / "data" / "asap2"
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(exist_ok=True)

RESULT_FILE = RESULT_DIR / "asap2_baseline_results.csv"

# 先测试3篇，确认正常后改成30
MAX_ESSAYS = 30


def extract_score(response):
    """从LLM回答中提取1～6分。"""
    match = re.search(r"(?im)^\s*Score\s*:\s*([1-6])\s*(?:/6)?\s*$", response)

    if match:
        return int(match.group(1))

    return None


def build_prompt(assignment, source_text, rubric, essay_text):
    """构建评分提示词。"""
    return f"""
You are an essay evaluator.

Evaluate the student's essay using the official holistic rubric.

[Writing Assignment]
{assignment}

[Source Article]
{source_text}

[Holistic Rubric]
{rubric}

[Student Essay]
{essay_text}

Instructions:
- Evaluate only the student's actual writing.
- Use the source article to check the essay's evidence.
- Follow the holistic rubric.
- Assign exactly one integer score from 1 to 6.
- Do not treat the assignment or source article as student writing.
- Provide a brief explanation.

Respond in this format:
Score: <integer from 1 to 6>
Reason: <brief explanation>
"""


def load_completed_ids():
    """读取已完成评分的Essay ID，支持断点续跑。"""
    if not RESULT_FILE.exists():
        return set()

    results = pd.read_csv(RESULT_FILE, dtype={"essay_id": str})
    valid = results[results["llm_score"].notna()]
    return set(valid["essay_id"])


def save_result(result):
    """每完成一篇，就追加保存到CSV。"""
    fieldnames = [
        "essay_id",
        "human_score",
        "llm_score",
        "absolute_error",
        "reason",
    ]

    file_exists = RESULT_FILE.exists()

    with open(RESULT_FILE, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(result)


def show_metrics():
    """计算已成功评分作文的实验指标。"""
    results = pd.read_csv(RESULT_FILE)
    results = results.dropna(subset=["llm_score"])

    if results.empty:
        print("暂无有效评分结果")
        return

    mae = results["absolute_error"].mean()
    exact_match = (
        results["human_score"] == results["llm_score"]
    ).mean()

    print("\n===== 实验统计 =====")
    print(f"已评分作文数: {len(results)}")
    print(f"MAE: {mae:.3f}")
    print(f"完全一致率: {exact_match:.2%}")


def main():
    df = pd.read_csv(DATA_DIR / "sample_30.csv", dtype={"essay_id": str})

    source_text = (
        DATA_DIR / "driverless_cars_source.txt"
    ).read_text(encoding="utf-8")

    rubric = (
        DATA_DIR / "holistic_rubric.txt"
    ).read_text(encoding="utf-8")

    completed_ids = load_completed_ids()
    selected = df.head(MAX_ESSAYS)

    print(f"本次计划评分: {len(selected)} 篇")
    print(f"已完成: {len(set(selected['essay_id']) & completed_ids)} 篇")

    for index, (_, essay) in enumerate(selected.iterrows(), start=1):
        essay_id = str(essay["essay_id"])

        if essay_id in completed_ids:
            print(f"[{index}/{len(selected)}] 跳过已完成: {essay_id}")
            continue

        prompt = build_prompt(
            assignment=essay["assignment"],
            source_text=source_text,
            rubric=rubric,
            essay_text=essay["full_text"],
        )

        print(f"\n[{index}/{len(selected)}] 正在评分: {essay_id}", flush=True)

        try:
            response = call_model(prompt)
            llm_score = extract_score(response)

            if llm_score is None:
                print("评分格式解析失败，原始回答:")
                print(response)
                continue

            human_score = int(essay["score"])
            absolute_error = abs(llm_score - human_score)

            reason_match = re.search(
                r"(?is)\bReason\s*:\s*(.*)",
                response,
            )
            reason = reason_match.group(1).strip() if reason_match else response.strip()

            save_result({
                "essay_id": essay_id,
                "human_score": human_score,
                "llm_score": llm_score,
                "absolute_error": absolute_error,
                "reason": reason,
            })

            completed_ids.add(essay_id)

            print(
                f"人工: {human_score} | "
                f"LLM: {llm_score} | "
                f"误差: {absolute_error}"
            )

        except Exception as e:
            print(f"评分失败: {essay_id}")
            print(f"错误信息: {e}")
            continue

    if RESULT_FILE.exists():
        show_metrics()
        print(f"\n结果已保存: {RESULT_FILE}")


if __name__ == "__main__":
    main()
