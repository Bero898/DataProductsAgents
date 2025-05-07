from metagpt.actions import Action

class CreateCompatibilityReport(Action):
    PROMPT_TEMPLATE: str = """
    You are tasked with determining if two data products are compatible. You will be given the mismatches
    that have been identified by two data product owners who are attempting to compose their data products.
    Your task is to create a report that summarizes the compatibility of the two data products based on the provided mismatches.
    The report should include the following:   

    - A summary of the mismatches identified by both data product owners.
    - An analysis of the compatibility of the two data products based on the mismatches (considering
    if the mismatches are negotiable or not).
    - Recommendations for resolving the mismatches, if applicable.
    - A conclusion on the overall compatibility of the two data products. If there remain any non-negotiable mismatches,
    state that the data products are not compatible. If there are only negotiable mismatches, 
    state that the data products are compatible. 

    mismatches idnetified by data product owner A:
    {mismatchA}

    mismatches idnetified by data product owner B:
    {mismatchB}


    """

    name: str = "CreateCompatibilityReport"

    async def run(self, mismatchA: str, mismatchB: str):
        prompt = self.PROMPT_TEMPLATE.format(mismatchA=mismatchA, mismatchB=mismatchB)
        rsp = await self._aask(prompt)
        return rsp