import os
import itertools
import time
import json

from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval import evaluate
from GEvalTest.ask_groq import GroqDeepSeekLLM

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

GROUND_TRUTH_PATH = os.path.join(BASE_DIR, "../GEvalTest/full_detailed_compatibility_report.txt")
MODEL_OUTPUT_DIR = os.path.join(BASE_DIR, "../Data Products/example-DPs/ChatGPT_DMesh/Results")
OUTPUT_FILENAMES = ["Broker.txt"]
RESULTS_DIR = os.path.join(BASE_DIR, "../GEvalTest/results")
COMPLETED_LOG = os.path.join(BASE_DIR, "../GEvalTest/completed_g_eval.txt")

# Map data file path to (DP name, DP number)
data_products = [
    ("CustomerProfile", 1, os.path.join(BASE_DIR, "../Data Products/example-DPs/ChatGPT_DMesh/Customer/CustomerProfile.yaml")),
    ("ViewingHistory", 2, os.path.join(BASE_DIR, "../Data Products/example-DPs/ChatGPT_DMesh/Customer/ViewingHistory.yaml")),
    ("SubscriptionOverview", 3, os.path.join(BASE_DIR, "../Data Products/example-DPs/ChatGPT_DMesh/Sales/SubscriptionOverview.yaml")),
    ("MarketingCampaignPerformance", 4, os.path.join(BASE_DIR, "../Data Products/example-DPs/ChatGPT_DMesh/Marketing/MarketingCampaignPerformance.yaml")),
    ("ChurnPredictionModelOutput", 5, os.path.join(BASE_DIR, "../Data Products/example-DPs/ChatGPT_DMesh/DataScience/ChurnPredictionModelOutput.yaml")),
    ("ContentMetadata", 6, os.path.join(BASE_DIR, "../Data Products/example-DPs/ChatGPT_DMesh/ContentOperations/ContentMetadata.yaml")),
    ("SupportTickets", 7, os.path.join(BASE_DIR, "../Data Products/example-DPs/ChatGPT_DMesh/CustomerSupport/SupportTickets.yaml")),
    ("RevenueAttribution", 8, os.path.join(BASE_DIR, "../Data Products/example-DPs/ChatGPT_DMesh/Finance/RevenueAttribution.yaml")),
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

def robust_evaluate(test_case, metric, max_retries=5):
    for attempt in range(max_retries):
        try:
            metric.measure(test_case)
            return {
                "score": metric.score,
                "reason": metric.reason
            }
        except Exception as e:
            print(f"Error during evaluation: {e}")
            if attempt < max_retries - 1:
                sleep_time = 5 * (2 ** attempt)
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                print("Max retries reached, skipping this output.")
                return {"score": None, "reason": f"Evaluation failed: {e}"}

def main():
    ground_truth = parse_ground_truth(GROUND_TRUTH_PATH)
    custom_llm = GroqDeepSeekLLM()
    correctness_metric = GEval(
        name="Correctness",
        evaluation_steps=[
            "Check whether the facts in 'actual output' contradict any facts in 'expected output'",
            "Heavily penalize omission of detail",
            "Vague language, or contradicting OPINIONS, are OK"
        ],
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
        model=custom_llm
    )

    completed = load_completed()
    pairs = list(itertools.combinations(data_products, 2))
    for dp1, dp2 in pairs:
        dp1_name, dp1_num, dp1_path = dp1
        dp2_name, dp2_num, dp2_path = dp2

        # Try both orderings for ground truth
        possible_titles = [
            get_report_title(dp1_name, dp1_num, dp2_name, dp2_num),
            get_report_title(dp2_name, dp2_num, dp1_name, dp1_num),
        ]
        gt_body = None
        for title in possible_titles:
            print(f"Checking for ground truth: {title}")
            if title in ground_truth:
                print(f"Found ground truth for {title}")
                gt_body = ground_truth[title]
                break
        if not gt_body:
            print(f"Ground truth not found for {dp1_name} (DP{dp1_num}) ↔ {dp2_name} (DP{dp2_num})")
            continue

        # Model output directory
        dir_name = f"{dp1_name}_{dp2_name}"
        alt_dir_name = f"{dp2_name}_{dp1_name}"
        output_dir = os.path.join(MODEL_OUTPUT_DIR, dir_name)
        print(f"Checking for model output dir: {output_dir}")
        print(f"Checking for alt model output dir: {alt_dir_name}")
        if not os.path.exists(output_dir):
            output_dir = os.path.join(MODEL_OUTPUT_DIR, alt_dir_name)
            if not os.path.exists(output_dir):
                print(f"Model output dir not found for {dp1_name}_{dp2_name}")
                continue

        # Input YAMLs
        input1 = load_yaml(dp1_path)
        input2 = load_yaml(dp2_path)
        input_prompt = f"DP1 YAML:\n{input1}\n\nDP2 YAML:\n{input2}"

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
            test_case = LLMTestCase(
                input=input_prompt,
                actual_output=model_output,
                expected_output=gt_body
            )
            print(f"Evaluating {pair_key} ...")
            result = robust_evaluate(test_case, correctness_metric)
            save_result(pair_key, result)
            save_completed(pair_key)
            print(f"Saved result for {pair_key}. Sleeping 30 seconds...\n")
            time.sleep(30)

    print("All outputs processed!")

if __name__ == "__main__":
    main()