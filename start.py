import asyncio
import fire
import yaml
import platform
from typing import Any

from metagpt.context import Context
from metagpt.logs import logger
from metagpt.team import Team
from roles.DP_owner import DPOwner


def load_data_product(file_path):
    with open(file_path) as stream:
        try:
            print(f"YAML file {file_path} loaded successfully.")
            return str(yaml.safe_load(stream))
        except yaml.YAMLError as exc:
            print(f"Error loading {file_path}: {exc}")
            return ""


async def compatibility_assessment(dp1_path, dp2_path, investment: float = 3.0, n_round: int = 3):
    """Run a team of data product owners to assess compatibility between their products."""
    # Load data products
    dp1 = load_data_product(dp1_path)
    dp2 = load_data_product(dp2_path)
    
    # Create data product owners
    alice = DPOwner(name="Alice", data_product=dp1, opponent_name="Bob")
    bob = DPOwner(name="Bob", data_product=dp2, opponent_name="Alice")
    
    # Create team
    team = Team()
    team.hire([alice, bob])
    team.invest(investment)
    
    # Start with reading data products
    team.run_project("Read and analyze data products", send_to="All")
    
    # Run the interaction
    await team.run(n_round=n_round)


def main(dp1_path: str = "./Data Products/example-DPs/Data Contract Playground - Pflooky/data-contract-specification.yaml", 
         dp2_path: str = "./Data Products/example-DPs/Data Contract Playground - Pflooky/data-contract-specification.yaml", 
         investment: float = 3.0, 
         n_round: int = 3):
    """
    Run data product compatibility assessment.
    
    :param dp1_path: Path to the first data product YAML file
    :param dp2_path: Path to the second data product YAML file
    :param investment: Contribution amount for team
    :param n_round: Maximum number of interaction rounds
    """
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(compatibility_assessment(dp1_path, dp2_path, investment, n_round))


if __name__ == "__main__":
    fire.Fire(main)