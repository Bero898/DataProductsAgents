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
    
class ContextAwareProductReader(Action):
    PROMPT_TEMPLATE: str = """
    Below a data product presented as a python dictionary.
    Data product: 
    {product}

    Here is additional context that highlights compatibility issues and mismatches with another data product:
   
    Compatibility analysis:
    {compatibility}

    Mismatch analysis:
    {Mismatches}

    give a brief description of the data product, including its purpose, structure, and any relevant details. 
    Try looking for elements that were not highlighted in the previous anaylsis if they could
    be relevant to the compatibility of the data product.
    your explanation:
    """

    name: str = "ContextAwareProductReader"

    async def run(self, product: str, compatibility: str, mismatches: str):
        prompt = self.PROMPT_TEMPLATE.format(product=product, compatibility=compatibility, mismatches=mismatches)
        rsp = await self._aask(prompt)
        return rsp
