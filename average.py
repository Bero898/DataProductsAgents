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

# Directories for each metric
base_dir = "./GEvalTest"
dirs = {
    "BLEU": "bleu_results",
    "BERTScore": "bertscore_results",
    "G-eval Deepseek": "results_deepseek",
    "G-eval LLaMa3": "results-llama",
}

columns = [
    "BLEU Score",
    "G-eval Score (LLaMa-3)",
    "G-eval Score (Deepseek-r1)",
    "BERTScore Precision",
    "BERTScore Recall",
    "BERTScore F1"
]

agents = ["Alice", "Bob"]

# Helper to extract DP numbers and agent from filename
def get_dp_pair_and_agent(filename):
    parts = filename.split("_")
    if len(parts) < 3:
        return filename, None
    dp1 = product_numbers.get(parts[0], "?")
    dp2 = product_numbers.get(parts[1], "?")
    agent = parts[2].replace(".json", "")
    return f"DP{dp1} - DP{dp2}", agent

# Gather all unique (DP pair, agent) combinations
dp_agent_pairs = set()
all_files = set()
for d in dirs.values():
    full_dir = os.path.join(base_dir, d)
    if os.path.exists(full_dir):
        for f in os.listdir(full_dir):
            if f.endswith(".json"):
                pair, agent = get_dp_pair_and_agent(f)
                if agent in agents:
                    dp_agent_pairs.add((pair, agent))
                all_files.add(f)

# Load all results into a dict, grouped by (DP pair, agent)
pair_agent_results = defaultdict(lambda: defaultdict(dict))
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
        pair, agent = get_dp_pair_and_agent(fname)
        if agent not in agents:
            continue
        if metric == "BLEU":
            val = data.get('bleu_score', None)
            if val is not None:
                pair_agent_results[(pair, agent)]["BLEU Score"] = val
        elif metric == "BERTScore":
            for k, col in zip(
                ['bertscore_precision', 'bertscore_recall', 'bertscore_f1'],
                ["BERTScore Precision", "BERTScore Recall", "BERTScore F1"]
            ):
                val = data.get(k, None)
                if val is not None:
                    pair_agent_results[(pair, agent)][col] = val
        elif metric == "G-eval Deepseek":
            val = data.get('score', None)
            if val is not None:
                pair_agent_results[(pair, agent)]["G-eval Score (Deepseek-r1)"] = val
        elif metric == "G-eval LLaMa3":
            val = data.get('score', None)
            if val is not None:
                pair_agent_results[(pair, agent)]["G-eval Score (LLaMa-3)"] = val

# Compute averages for each metric for Alice and Bob separately
for agent in agents:
    metric_sums = {col: 0.0 for col in columns}
    metric_counts = {col: 0 for col in columns}
    for pair, ag in dp_agent_pairs:
        if ag != agent:
            continue
        for col in columns:
            val = pair_agent_results.get((pair, agent), {}).get(col, None)
            if val is not None:
                metric_sums[col] += val
                metric_counts[col] += 1
            # If no value for this pair+agent, do not count it (skip)
    print(f"\nAverages for {agent}:")
    for col in columns:
        if metric_counts[col] > 0:
            overall_avg = metric_sums[col] / metric_counts[col]
            print(f"{col}: {overall_avg:.4f}")
        else:
            print(f"{col}: N/A")