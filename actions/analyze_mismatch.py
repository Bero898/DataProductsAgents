import re
from metagpt.actions import Action

class MismatchIdentifier(Action):
    PROMPT_TEMPLATE: str = """
    The following is an assessment of compatibility between two data products: 

    Assessment of compatiblity:
    {assessment}
    
    Identify the mismatches between the two data products based on the assessment.
    Based on the mismatches provide a list of suggestions to resolve the mismatches.
    Consider the negotiable and non-negotiable factors, such as data formats, schemas, 
    and any other relevant aspects of each data product.
    your suggestions:
    """

    name: str = "MismatchIdentifier"

    async def run(self, assessment: str):
        prompt = self.PROMPT_TEMPLATE.format(assessment=assessment)

        rsp = await self._aask(prompt)

        product_description = MismatchIdentifier(rsp)

        return product_description