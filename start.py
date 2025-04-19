import asyncio
import fire
import yaml

from metagpt.context import Context
from roles.DP_owner import DPOwner
from metagpt.logs import logger


with open(".\Data Products\example-DPs\Data Contract Playground - Pflooky\data-contract-specification.yaml") as stream:
    try:
        print("YAML file loaded successfully.")
        dataproduct = str(yaml.safe_load(stream))
    except yaml.YAMLError as exc:
        print(exc)



import asyncio

from metagpt.context import Context

def main(msg=dataproduct):
    # role = SimpleCoder()
    role = DPOwner()
    logger.info(msg)
    result = asyncio.run(role.run(msg))
    logger.info(result)


if __name__ == "__main__":
    fire.Fire(main)