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

# Gather all unique file names
all_files = set()
for d in dirs.values():
    full_dir = os.path.join(base_dir, d)
    if os.path.exists(full_dir):
        all_files.update(f for f in os.listdir(full_dir) if f.endswith(".json"))

# Helper to extract DP numbers from filename
def get_dp_pair_and_agent(filename):
    parts = filename.split("_")
    if len(parts) < 3:
        return filename, ""
    dp1 = product_numbers.get(parts[0], "?")
    dp2 = product_numbers.get(parts[1], "?")
    agent = parts[2].replace(".json", "")
    # Map agent file to readable name
    if agent.lower() == "alice":
        agent_str = "Agent1"
    elif agent.lower() == "bob":
        agent_str = "Agent2"
    else:
        agent_str = agent
    return f"DP{dp1} - DP{dp2}", agent_str

# Load all results into a dict
results = defaultdict(dict)
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
        key = fname
        if metric == "BLEU":
            results[key]["BLEU Score"] = f"{data.get('bleu_score', ''):.4g}" if data.get("bleu_score") is not None else ""
        elif metric == "BERTScore":
            results[key]["BERTScore Precision"] = f"{data.get('bertscore_precision', ''):.4g}" if data.get("bertscore_precision") is not None else ""
            results[key]["BERTScore Recall"] = f"{data.get('bertscore_recall', ''):.4g}" if data.get("bertscore_recall") is not None else ""
            results[key]["BERTScore F1"] = f"{data.get('bertscore_f1', ''):.4g}" if data.get("bertscore_f1") is not None else ""
        elif metric == "G-eval Deepseek":
            results[key]["G-eval Score (Deepseek-r1)"] = f"{data.get('score', ''):.4g}" if data.get("score") is not None else ""
        elif metric == "G-eval LLaMa3":
            results[key]["G-eval Score (LLaMa-3)"] = f"{data.get('score', ''):.4g}" if data.get("score") is not None else ""

# LaTeX table header
columns = [
    "BLEU Score",
    "G-eval Score (LLaMa-3)",
    "G-eval Score (Deepseek-r1)",
    "BERTScore Precision",
    "BERTScore Recall",
    "BERTScore F1"
]
header = " & ".join(["Pair"] + columns) + " \\\\ \\hline"

# Build rows
rows = []
for fname in sorted(all_files):
    pair, agent = get_dp_pair_and_agent(fname)
    row_label = f"{pair} {agent}" if agent else pair
    row = [row_label]
    for col in columns:
        row.append(results.get(fname, {}).get(col, ""))
    rows.append(" & ".join(row) + " \\\\")

# Output LaTeX table
print(r"""\begin{tabular}{|l|c|c|c|c|c|c|}
\hline
""" + header)
for row in rows:
    print(row)
print(r"\hline" + "\n\end{tabular}")