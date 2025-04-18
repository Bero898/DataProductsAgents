import asyncio
import fire

from metagpt.context import Context
from roles.coder import RunnableCoder
from metagpt.logs import logger



import asyncio

from metagpt.context import Context

def main(msg="write a function that calculates the product of a list and run it"):
    # role = SimpleCoder()
    role = RunnableCoder()
    logger.info(msg)
    result = asyncio.run(role.run(msg))
    logger.info(result)


if __name__ == "__main__":
    fire.Fire(main)