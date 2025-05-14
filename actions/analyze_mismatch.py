import re
from metagpt.actions import Action

class MismatchIdentifier(Action):
    PROMPT_TEMPLATE: str = """
    You will identify the mismatches between two compatibility assessments (Assessment A and Assessment B). 
    These compatibility assessments concern two data products. Additionally, you will be 
    given an assessment of how composing the two data products could impact the
    rest of the data mesh (Assessment C). 
    
    Once the mismatches have been identified provide a list of suggestions to resolve 
    the mismatches. Consider the negotiable and non-negotiable factors, such as data formats, 
    schemas, and any other relevant aspects of each data product.

    Assessment A:
    {assessmentA}
    
    Assessment B:
    {assessmentB}

    Assessment C:
    {assessmentC}

    Mismatches identified and your suggestions:
    """

    name: str = "MismatchIdentifier"

    async def run(self, assessmentA: str, assessmentB: str, assessmentC: str):
        prompt = self.PROMPT_TEMPLATE.format(assessmentA=assessmentA, assessmentB=assessmentB, assessmentC=assessmentC)
        rsp = await self._aask(prompt)
        return rsp