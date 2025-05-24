import os
import itertools
import time
import json
import nltk

GROUND_TRUTH_PATH = "./GEvalTest/full_detailed_compatibility_report.txt"
MODEL_OUTPUT_DIR = "./Data Products/example-DPs/ChatGPT_DMesh/Results"
OUTPUT_FILENAMES = ["Broker.txt"]
RESULTS_DIR = "./GEvalTest/bleu_results"
COMPLETED_LOG = "./GEvalTest/completed_bleu_eval.txt"

data_products = [
    ("CustomerProfile", 1, "./Data Products/example-DPs/ChatGPT_DMesh/Customer/CustomerProfile.yaml"),
    ("ViewingHistory", 2, "./Data Products/example-DPs/ChatGPT_DMesh/Customer/ViewingHistory.yaml"),
    ("SubscriptionOverview", 3, "./Data Products/example-DPs/ChatGPT_DMesh/Sales/SubscriptionOverview.yaml"),
    ("MarketingCampaignPerformance", 4, "./Data Products/example-DPs/ChatGPT_DMesh/Marketing/MarketingCampaignPerformance.yaml"),
    ("ChurnPredictionModelOutput", 5, "./Data Products/example-DPs/ChatGPT_DMesh/DataScience/ChurnPredictionModelOutput.yaml"),
    ("ContentMetadata", 6, "./Data Products/example-DPs/ChatGPT_DMesh/ContentOperations/ContentMetadata.yaml"),
    ("SupportTickets", 7, "./Data Products/example-DPs/ChatGPT_DMesh/CustomerSupport/SupportTickets.yaml"),
    ("RevenueAttribution", 8, "./Data Products/example-DPs/ChatGPT_DMesh/Finance/RevenueAttribution.yaml"),
]

def parse_ground_truth(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    reports = content.split("="*100)
    report_dict = {}
    for report in reports:
        report = report.strip()
        if not report:
            continue
        lines = report.splitlines()
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        report_dict[title] = body
    return report_dict

def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def get_report_title(dp1_name, dp1_num, dp2_name, dp2_num):
    return f"### Compatibility Report: {dp1_name.replace('_', ' ')} (DP{dp1_num}) ↔ {dp2_name.replace('_', ' ')} (DP{dp2_num})"

def load_completed():
    if not os.path.exists(COMPLETED_LOG):
        return set()
    with open(COMPLETED_LOG, "r") as f:
        return set(line.strip() for line in f)

def save_completed(pair_key):
    with open(COMPLETED_LOG, "a") as f:
        f.write(pair_key + "\n")

def save_result(pair_key, result):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    result_path = os.path.join(RESULTS_DIR, f"{pair_key}.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

def safe_bleu(reference, hypothesis):
    # Tokenize by whitespace for simplicity
    ref_tokens = reference.split()
    hyp_tokens = hypothesis.split()
    n = min(4, len(ref_tokens), len(hyp_tokens))
    if n == 0:
        return 0.0
    weights = tuple([1.0/n]*n)
    try:
        score = nltk.translate.bleu_score.sentence_bleu([ref_tokens], hyp_tokens, weights=weights)
    except ZeroDivisionError:
        score = 0.0
    return score

def main():
    ground_truth = parse_ground_truth(GROUND_TRUTH_PATH)
    completed = load_completed()
    pairs = list(itertools.combinations(data_products, 2))
    for dp1, dp2 in pairs:
        dp1_name, dp1_num, dp1_path = dp1
        dp2_name, dp2_num, dp2_path = dp2

        possible_titles = [
            get_report_title(dp1_name, dp1_num, dp2_name, dp2_num),
            get_report_title(dp2_name, dp2_num, dp1_name, dp1_num),
        ]
        gt_body = None
        for title in possible_titles:
            if title in ground_truth:
                gt_body = ground_truth[title]
                break
        if not gt_body:
            print(f"Ground truth not found for {dp1_name} (DP{dp1_num}) ↔ {dp2_name} (DP{dp2_num})")
            continue

        dir_name = f"{dp1_name}_{dp2_name}"
        alt_dir_name = f"{dp2_name}_{dp1_name}"
        output_dir = os.path.join(MODEL_OUTPUT_DIR, dir_name)
        if not os.path.exists(output_dir):
            output_dir = os.path.join(MODEL_OUTPUT_DIR, alt_dir_name)
            if not os.path.exists(output_dir):
                print(f"Model output dir not found for {dp1_name}_{dp2_name}")
                continue

        for output_file in OUTPUT_FILENAMES:
            pair_key = f"{dp1_name}_{dp2_name}_{output_file.replace('.txt','')}"
            if pair_key in completed:
                print(f"Skipping already completed: {pair_key}")
                continue
            output_path = os.path.join(output_dir, output_file)
            if not os.path.exists(output_path):
                print(f"Output file missing: {output_path}")
                continue
            with open(output_path, "r", encoding="utf-8") as f:
                model_output = f.read()
            bleu_score = safe_bleu(gt_body, model_output)
            result = {
                "bleu_score": bleu_score
            }
            save_result(pair_key, result)
            save_completed(pair_key)

    print("All outputs processed!")

if __name__ == "__main__":
    main()