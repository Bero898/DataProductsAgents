import os
import json
from collections import defaultdict

# this code works because there are no missing pairs. The code for ReAct agents are different due to this.

# Map product names to numbers
product_numbers = {
    "CustomerProfile": 1,
    "ViewingHistory": 2,
    "SubscriptionOverview": 3,
    "MarketingCampaignPerformance": 4,
    "ChurnPredictionModelOutput": 5,
    "ContentMetadata": 6,
    "SupportTickets": 7,
    "RevenueAttribution": 8,
}

# Directories for each metric
base_dir = "./GEvalTest"
dirs = {
    "BLEU": "bleu_results",
    "BERTScore": "bertscore_results",
    "G-eval Deepseek": "results-deepseek",
    "G-eval LLaMa3": "results-llama3",
}

columns = [
    "BLEU Score",
    "G-eval Score (LLaMa-3)",
    "G-eval Score (Deepseek-r1)",
    "BERTScore Precision",
    "BERTScore Recall",
    "BERTScore F1"
]

# Helper to extract DP numbers from filename (ignoring agent)
def get_dp_pair_key(filename):
    parts = filename.split("_")
    if len(parts) < 3:
        return filename
    dp1 = product_numbers.get(parts[0], "?")
    dp2 = product_numbers.get(parts[1], "?")
    return f"DP{dp1} - DP{dp2}"

# Gather all unique DP pairs
dp_pairs = set()
all_files = set()
for d in dirs.values():
    full_dir = os.path.join(base_dir, d)
    if os.path.exists(full_dir):
        for f in os.listdir(full_dir):
            if f.endswith(".json"):
                dp_pairs.add(get_dp_pair_key(f))
                all_files.add(f)

# Load all results into a dict, grouped by DP pair
pair_results = defaultdict(lambda: defaultdict(list))
for metric, d in dirs.items():
    full_dir = os.path.join(base_dir, d)
    if not os.path.exists(full_dir):
        continue
    for fname in os.listdir(full_dir):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(full_dir, fname)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        pair_key = get_dp_pair_key(fname)
        if metric == "BLEU":
            val = data.get('bleu_score', None)
            if val is not None:
                pair_results[pair_key]["BLEU Score"].append(val)
        elif metric == "BERTScore":
            for k, col in zip(
                ['bertscore_precision', 'bertscore_recall', 'bertscore_f1'],
                ["BERTScore Precision", "BERTScore Recall", "BERTScore F1"]
            ):
                val = data.get(k, None)
                if val is not None:
                    pair_results[pair_key][col].append(val)
        elif metric == "G-eval Deepseek":
            val = data.get('score', None)
            if val is not None:
                pair_results[pair_key]["G-eval Score (Deepseek-r1)"].append(val)
        elif metric == "G-eval LLaMa3":
            val = data.get('score', None)
            if val is not None:
                pair_results[pair_key]["G-eval Score (LLaMa-3)"].append(val)

# Compute averages for each metric across all DP pairs (ignoring agents)
metric_sums = {col: 0.0 for col in columns}
metric_counts = {col: 0 for col in columns}

for pair in dp_pairs:
    for col in columns:
        vals = pair_results[pair].get(col, [])
        if vals:
            avg = sum(vals)
            metric_sums[col] += avg
            metric_counts[col] += 1
        # If no value for this pair, do not count it (skip, as per your instructions)

print("Averages for each metric (across all DP pairs):")
for col in columns:
    if metric_counts[col] > 0:
        overall_avg = metric_sums[col] / metric_counts[col]
        print(f"{col}: {overall_avg:.4f}")
    else:
        print(f"{col}: N/A")