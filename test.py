import itertools
import os
import time
import yaml
from GEvalTest.groq import groqcall

data_files = [
    "./Data Products/example-DPs/ChatGPT_DMesh/ContentOperations/ContentMetadata.yaml",
    "./Data Products/example-DPs/ChatGPT_DMesh/Customer/CustomerProfile.yaml",
    "./Data Products/example-DPs/ChatGPT_DMesh/Customer/ViewingHistory.yaml",
    "./Data Products/example-DPs/ChatGPT_DMesh/CustomerSupport/SupportTickets.yaml",
    "./Data Products/example-DPs/ChatGPT_DMesh/DataScience/ChurnPredictionModelOutput.yaml",
    "./Data Products/example-DPs/ChatGPT_DMesh/Finance/RevenueAttribution.yaml",
    "./Data Products/example-DPs/ChatGPT_DMesh/Marketing/MarketingCampaignPerformance.yaml",
    "./Data Products/example-DPs/ChatGPT_DMesh/Sales/SubscriptionOverview.yaml",
]

COMPLETED_LOG = "completed_pairs_llm.txt"

def get_product_name(path):
    return os.path.splitext(os.path.basename(path))[0]

def load_completed_pairs():
    if not os.path.exists(COMPLETED_LOG):
        return set()
    with open(COMPLETED_LOG, "r") as f:
        return set(line.strip() for line in f)

def save_completed_pair(pair_name):
    with open(COMPLETED_LOG, "a") as f:
        f.write(pair_name + "\n")

def load_yaml_content(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def build_prompt(yaml1, yaml2):
    return f"""You are tasked with composing two data products that are provided in a YAML structure
```
You will follow the structure below to provide your response:
    ** Mismatches **
    - A summary of the mismatches that you find between data products. Consider the negotiable and non-negotiable factors, such as data formats, schemas, and any other relevant aspects of each data product
  
    ** Compatibility Analysis **
    - An analysis of the compatibility of the two data products based on the mismatches (considering
      if the mismatches are negotiable or not).

    ** Recommendations **
    - Recommendations for resolving the mismatches, if applicable.

    ** Conclusion **
    - A conclusion on the overall compatibility of the two data products. If there remain any non-negotiable mismatches,
      state that the data products are not compatible. If there are only negotiable mismatches, 
      state that the data products are compatible.

Here are the Data Products:
{yaml1}

{yaml2}
```"""

def main():
    completed_pairs = load_completed_pairs()
    pairs = list(itertools.combinations(data_files, 2))
    for idx, (dp1, dp2) in enumerate(pairs, 1):
        name1 = get_product_name(dp1)
        name2 = get_product_name(dp2)
        pair_name = f"{name1}_{name2}"
        save_path = f"./Data Products/example-DPs/ChatGPT_DMesh/Results_LLM/{pair_name}"
        result_file = os.path.join(save_path, "llm_result.txt")
        if pair_name in completed_pairs:
            print(f"Skipping pair {idx}/{len(pairs)} ({name1}, {name2}) - already processed.")
            continue
        os.makedirs(save_path, exist_ok=True)
        print(f"\n=== LLM Testing pair {idx}/{len(pairs)} ===\n{dp1}\n{dp2}\nResults will be saved to: {result_file}\n")
        yaml1 = load_yaml_content(dp1)
        yaml2 = load_yaml_content(dp2)
        prompt = build_prompt(yaml1, yaml2)
        try:
            response = groqcall(prompt, temperature=0.6, max_completion_tokens=2048)
        except Exception as e:
            print(f"Error calling Groq API for {pair_name}: {e}")
            continue
        with open(result_file, "w", encoding="utf-8") as f:
            f.write(response)
        save_completed_pair(pair_name)
        print("Waiting 5 seconds before next pair...\n")
        time.sleep(30)
    print("All pairs processed!")

if __name__ == "__main__":
    main()