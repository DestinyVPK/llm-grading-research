
from pathlib import Path
import pandas as pd

# 数据文件路径
data_dir = Path(__file__).parent / "data" / "asap2"
input_file = data_dir / "ASAP_2_Final_github_train.csv"
output_file = data_dir / "sample_30.csv"

# 读取原始数据
df = pd.read_csv(input_file)

# 只选择 Driverless cars 题目
df = df[df["prompt_name"] == "Driverless cars"]

# 每个评分等级随机抽取5篇
samples = []

for score in range(1, 7):
    group = df[df["score"] == score]
    selected = group.sample(n=5, random_state=42)
    samples.append(selected)

# 合并并保存实验样本
result = pd.concat(samples, ignore_index=True)
result.to_csv(output_file, index=False, encoding="utf-8-sig")

# 输出抽样结果
print("抽样完成！")
print("作文总数：", len(result))
print(result["score"].value_counts().sort_index())
print("保存位置：", output_file)
