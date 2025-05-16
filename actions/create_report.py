from metagpt.actions import Action

class CreateCompatibilityReport(Action):
    PROMPT_TEMPLATE: str = """
    You are tasked with determining if two data products are compatible. You will be given the mismatches
    that have been identified by two data product owners who are attempting to compose their data products.
    Additionally, you will be provided with the current state of the compatibility report (if it exists).
    Your task is to create or update the report based on the provided mismatches and the existing report content.
    The report should have the following structure:

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

  Below is the information required to create the report
      
  Existing report content (if any):
  {existing_report}

  Mismatches identified by data product owner A:
  {mismatchA}

  Mismatches identified by data product owner B:
  {mismatchB}
    """

    name: str = "CreateCompatibilityReport"

    async def run(self, mismatchA: str, mismatchB: str, existing_report: str = ""):
        prompt = self.PROMPT_TEMPLATE.format(
            mismatchA=mismatchA,
            mismatchB=mismatchB,
            existing_report=existing_report or "No existing report."
        )
        rsp = await self._aask(prompt)
        return rsp