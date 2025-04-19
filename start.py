import asyncio
import fire
import yaml

from metagpt.context import Context
from roles.DP_owner import DPOwner
from metagpt.logs import logger


def load_yaml_file(file_path):
    with open(file_path) as stream:
        try:
            print(f"YAML file {file_path} loaded successfully.")
            return str(yaml.safe_load(stream))
        except yaml.YAMLError as exc:
            print(exc)
            return None


# Load first data product
dataproduct1 = load_yaml_file("./Data Products/example-DPs/data mesh manager - Simon Harrer/shelf_warmers.yml")

# Load second data product - replace with your actual second data product path
dataproduct2 = load_yaml_file("./Data Products/example-DPs/data mesh manager - Simon Harrer/stock_updated.yml")
# Note: You should replace the above with a different data product file path


def main(dp1=dataproduct1, dp2=dataproduct2):
    # Initialize the DPOwner role
    role = DPOwner()
    
    # Create a message to analyze both data products
    message = {
        "data_product_1": dp1,
        "data_product_2": dp2
    }
    
    # Run the analysis process
    result = asyncio.run(role.run(message))
    logger.info(result)


if __name__ == "__main__":
    fire.Fire(main)