import re
from metagpt.actions import Action

class SimpleDataProductComposer(Action):
    PROMPT_TEMPLATE: str = """
    Are the descriptions of two data products. These descriptions contain information specific to 
    each data product. Consider factors that are negotiable and non-negotiable, such as data formats, schemas, and any other relevant aspects.
    Your Data Product: 
    {productA}

    Data Product to Compose with:
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
    
class ContextAwareProductComposer(Action):
    PROMPT_TEMPLATE: str = """
    Here are the descriptions of two data products. These descriptions contain information specific to 
    each product. Consider negotiable and non-negotiable factors like data formats, schemas, compatibility constraints, etc.

    Your Data Product:
    {productA}

    Data Product to Compose with:
    {productB}

    Your Contextual Notes:
    - Compatibility analysis: {compatibilityA}
    - Notable mismatches: {mismatchesA}

    Colleague's Contextual Notes:
    - Compatibility analysis: {compatibilityB}
    - Notable mismatches: {mismatchesB}

    Based on the above, please assess the compatibility of the two data products, and explain your reasoning.
    Your assessment:
    """

    async def run(self, productA: str, productB: str, compatibilityA: str, mismatchesA: str,  compatibilityB: str, mismatchesB: str):
        prompt = self.PROMPT_TEMPLATE.format(productA=productA, productB=productB, compatibilityA=compatibilityA, compatibilityB=compatibilityB, mismatchesA=mismatchesA, mismatchesB=mismatchesB)
        rsp = await self._aask(prompt)
        return rsp