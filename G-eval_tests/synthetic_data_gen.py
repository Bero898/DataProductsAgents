from deepeval.synthesizer import Synthesizer
from deepeval.synthesizer.config import StylingConfig
from ask_groq import GroqDeepSeekLLM
import os

# 1. Set up the custom LLM and styling config for YAML data products

script_dir = os.path.dirname(os.path.abspath(__file__))
yaml_path = os.path.join(script_dir, "../Data Products/ProMoTe.yaml")
with open(yaml_path, "r", encoding="utf-8") as f:
    promote_yaml = f.read()

custom_llm = GroqDeepSeekLLM()
styling_config = StylingConfig(
    input_format="YAML data product in the style of the following ontology.",
    expected_output_format="YAML data product in the style of the following ontology.",
    task="Generate a data product specification in YAML using the provided ontology.",
    scenario="Data product owners are documenting their products for interoperability analysis."
)

synthesizer = Synthesizer(model=custom_llm, styling_config=styling_config)

# Pass the ontology as context
synthesizer.generate_goldens_from_contexts(
    contexts=[[promote_yaml], [promote_yaml]],  # One context per golden
    include_expected_output=True,
    max_goldens_per_context=1  # 1 golden per context, so 2 total
)

dp1 = synthesizer.synthetic_goldens[0].input
dp2 = synthesizer.synthetic_goldens[1].input

print("Data Product 1:\n", dp1)
print("Data Product 2:\n", dp2)

# 3. Compose a compatibility report using the LLM
compatibility_prompt = f"""
You are an expert in data product interoperability. The following is the ontology to use for data product structure:

{promote_yaml}

Given these two data products (in the above ontology style):

Data Product 1:
{dp1}

Data Product 2:
{dp2}

Analyze whether these two data products can be composed or are compatible. Your report must follow this structure:

**Mismatches**
- A summary of the mismatches identified by both data product owners.

**Compatibility Analysis**
- An analysis of the compatibility of the two data products based on the mismatches (considering if the mismatches are negotiable or not).

**Recommendations**
- Recommendations for resolving the mismatches, if applicable.

**Conclusion**
- A conclusion on the overall compatibility of the two data products. If there remain any non-negotiable mismatches, state that the data products are not compatible. If there are only negotiable mismatches, state that the data products are compatible.
"""

report = custom_llm.generate(compatibility_prompt, schema=None)  # schema=None for free-form text
print("\nCompatibility Report:\n", report)