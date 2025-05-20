import itertools
import asyncio
import os
from start import compatibility_assessment

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

def get_product_name(path):
    # Extracts the filename without extension
    return os.path.splitext(os.path.basename(path))[0]

COMPLETED_LOG = "completed_pairs.txt"

def load_completed_pairs():
    if not os.path.exists(COMPLETED_LOG):
        return set()
    with open(COMPLETED_LOG, "r") as f:
        return set(line.strip() for line in f)

def save_completed_pair(pair_name):
    with open(COMPLETED_LOG, "a") as f:
        f.write(pair_name + "\n")

async def main():
    completed_pairs = load_completed_pairs()
    pairs = list(itertools.combinations(data_files, 2))
    for idx, (dp1, dp2) in enumerate(pairs, 1):
        name1 = get_product_name(dp1)
        name2 = get_product_name(dp2)
        pair_name = f"{name1}_{name2}"
        save_path = f"./Data Products/example-DPs/ChatGPT_DMesh/Results/{pair_name}"
        if pair_name in completed_pairs:
            print(f"Skipping pair {idx}/{len(pairs)} ({name1}, {name2}) - already processed.")
            continue
        os.makedirs(save_path, exist_ok=True)
        print(f"\n=== Testing pair {idx}/{len(pairs)} ===\n{dp1}\n{dp2}\nResults will be saved to: {save_path}\n")
        await compatibility_assessment(dp1, dp2, investment=3.0, n_round=3, save_path=save_path)
        save_completed_pair(pair_name)
        print("Waiting 5 seconds before next pair...\n")
        await asyncio.sleep(5)
    print("All pairs processed!")

if __name__ == "__main__":
    asyncio.run(main())