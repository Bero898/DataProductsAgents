from metagpt.actions import Action

class PerformBrokerAnalysis(Action):
    PROMPT_TEMPLATE: str = """
    Below are the descriptions of two data products. These descriptions contain information specific to
    each data product. You are tasked with identifying how allowing dataproductA to use information from dataproductB
    could affect the rest of the data mesh. Consider aspects like syntax, semantics, cataloging, and any other relevant factors.

    dataproductA:
    {productA}

    dataproductB:
    {productB}



    """

    name: str = "PerformBrokerAnalysis"

    async def run(self, productA: str, productB: str):
        prompt = self.PROMPT_TEMPLATE.format(productA=productA, productB=productB)
        rsp = await self._aask(prompt)
        return rsp