import os
from pydantic import BaseModel
from deepeval.models import DeepEvalBaseLLM
from groq import ask_groq  # Adjust import if needed

class GroqDeepSeekLLM(DeepEvalBaseLLM):
    def __init__(self):
        pass  # No model object needed, just API key in env

    def load_model(self):
        return None  # Not needed for API-based models

    def get_model_name(self):
        return "Groq DeepSeek R1 Distill"

    def generate(self, prompt: str, schema: BaseModel) -> BaseModel:
        import re
        import json
        # Strong system prompt to force JSON output
        system_prompt = (
            "You are an expert evaluator. "
            "Respond ONLY with a valid JSON object matching this schema:"
            f" {schema.model_json_schema()}. "
            "Do NOT include any explanation, commentary, or extra text. "
            "Output ONLY the JSON object, nothing else. If you include anything else, "
            "your answer will be considered invalid."
        )
        response = ask_groq(
            message=prompt,
            system_prompt=system_prompt,
            temperature=0.0,
            max_completion_tokens=1024,
            top_p=1.0
        )
        response = response.strip()
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            raise ValueError(f"Model did not return valid JSON: {response}")
        json_str = json_match.group(0)
        try:
            json_result = json.loads(json_str)
        except Exception as e:
            raise ValueError(f"Model did not return valid JSON: {json_str}") from e
        return schema(**json_result)
    async def a_generate(self, prompt: str, schema: BaseModel) -> BaseModel:
        # For now, just call the sync version (can be improved with threads)
        return self.generate(prompt, schema)