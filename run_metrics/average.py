import os
import json
from collections import defaultdict

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

product_names = list(product_numbers.keys())

# Directories for each metric
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

base_dir = os.path.join(BASE_DIR, "../GEvalTest")
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

# Enumerate all possible DP pairs (excluding self-pairs)
all_dp_pairs = []
for i, dp1 in enumerate(product_names):
    for j, dp2 in enumerate(product_names):
        if i != j:
            all_dp_pairs.append(f"DP{product_numbers[dp1]} - DP{product_numbers[dp2]}")

total_pairs = len(all_dp_pairs)  # Should be 8*7 = 56 if all pairs, but you want 28 (maybe only unique unordered pairs)
if total_pairs > 28:
    # If you want only unique unordered pairs (DP1-DP2 == DP2-DP1), filter:
    seen = set()
    filtered_pairs = []
    for pair in all_dp_pairs:
        a, b = pair.split(" - ")
        key = tuple(sorted([a, b]))
        if key not in seen:
            seen.add(key)
            filtered_pairs.append(pair)
    all_dp_pairs = filtered_pairs
    total_pairs = len(all_dp_pairs)

# Compute averages for each metric, always dividing by 28, and count Nones
metric_sums = {col: 0.0 for col in columns}
metric_nones = {col: 0 for col in columns}

for pair in all_dp_pairs:
    for col in columns:
        vals = pair_results[pair].get(col, [])
        if vals:
            metric_sums[col] += sum(vals) / len(vals)  # average if multiple values for this pair
        else:
            metric_nones[col] += 1  # missing, count as None (and sum as 0)

print(f"Averages for each metric (dividing by {total_pairs}, missing counted as 0):")
for col in columns:
    avg = metric_sums[col] / total_pairs
    print(f"{col}: {avg:.10f} (missing: {metric_nones[col]}, present: {total_pairs - metric_nones[col]})")