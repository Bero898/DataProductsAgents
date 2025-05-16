import re
from metagpt.actions import Action

class MismatchIdentifier(Action):
    PROMPT_TEMPLATE: str = """
    You will identify the mismatches between two compatibility assessments (Assessment A and Assessment B). 
    These compatibility assessments concern two data products.
    
    Once the mismatches have been identified provide a list of suggestions to resolve 
    the mismatches. Consider the negotiable and non-negotiable factors, such as data formats, 
    schemas, and any other relevant aspects of each data product.

    You will follow the structure below to provide your response:
    ** Mismatches **
    - A summary of the mismatches identified by both data product owners.
  
    ** Compatibility Analysis **
    - An analysis of the compatibility of the two data products based on the mismatches (considering
      if the mismatches are negotiable or not).

    ** Recommendations **
    - Recommendations for resolving the mismatches, if applicable.

    ** Conclusion **
    - A conclusion on the overall compatibility of the two data products. If there remain any non-negotiable mismatches,
      state that the data products are not compatible. If there are only negotiable mismatches, 
      state that the data products are compatible.

    Below is the information required to identify the mismatches and provide suggestions:
    Assessment A:
    {assessmentA}
    
    Assessment B:
    {assessmentB}


    Mismatches identified and your suggestions:
    """

    name: str = "MismatchIdentifier"

    async def run(self, assessmentA: str, assessmentB: str):
        prompt = self.PROMPT_TEMPLATE.format(assessmentA=assessmentA, assessmentB=assessmentB)
        rsp = await self._aask(prompt)
        return rsp