import re
from metagpt.actions import Action

class SimpleDataProductReader(Action):
    PROMPT_TEMPLATE: str = """
    Below a data product presented as a python dictionary.
    Data product: 
    {product}
    give a brief description of the data product, including its purpose, structure, and any relevant details.
    your explanation:
    """

    name: str = "SimpleDataProductReader"

    async def run(self, product: str):
        prompt = self.PROMPT_TEMPLATE.format(product=product)
        rsp = await self._aask(prompt)
        return rsp