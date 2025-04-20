import re
from metagpt.actions import Action

class SimpleDataProductComposer(Action):
    PROMPT_TEMPLATE: str = """
    Are the descriptions of two data products. These descriptions contain information specific to 
    each data product. Consider factors that are negotiable and non-negotiable, such as data formats, schemas, and any other relevant aspects.
    Data product A: 
    {productA}

    Data product B:
    {productB}
    
    Based on the above descriptions, please provide assessment of the compatibility between the two data products.
    Be sure to consider the previously mentioned non-negotiable and negotiable factors.
    your assessment:
    """

    name: str = "CompatibilityAssessment"

    async def run(self, productA: str, productB: str):
        prompt = self.PROMPT_TEMPLATE.format(productA=productA, productB=productB)
        rsp = await self._aask(prompt)
        return rsp