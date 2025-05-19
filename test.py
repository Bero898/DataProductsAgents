import itertools
import asyncio
import time
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

async def main():
    pairs = list(itertools.combinations(data_files, 2))
    for idx, (dp1, dp2) in enumerate(pairs, 1):
        name1 = get_product_name(dp1)
        name2 = get_product_name(dp2)
        save_path = f"./Data Products/example-DPs/ChatGPT_DMesh/Results/{name1}_{name2}"
        # Check if this pair has already been processed (e.g., Broker.txt exists)
        broker_file = os.path.join(save_path, "Broker.txt")
        if os.path.exists(broker_file):
            print(f"Skipping pair {idx}/{len(pairs)} ({name1}, {name2}) - already processed.")
            continue
        os.makedirs(save_path, exist_ok=True)
        print(f"\n=== Testing pair {idx}/{len(pairs)} ===\n{dp1}\n{dp2}\nResults will be saved to: {save_path}\n")
        await compatibility_assessment(dp1, dp2, investment=3.0, n_round=10, save_path=save_path)
        print("Waiting 5 seconds before next pair...\n")
        time.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())