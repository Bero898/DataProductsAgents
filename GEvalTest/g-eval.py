from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from ask_groq import GroqDeepSeekLLM
from deepeval import evaluate

custom_llm = GroqDeepSeekLLM()
correctness_metric = GEval(
    name="Correctness",
    evaluation_steps=[
        "Check whether the facts in 'actual output' contradict any facts in 'expected output'",
        "Heavily penalize omission of detail",
        "Vague language, or contradicting OPINIONS, are OK"
    ],
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
    model=custom_llm
)

# Example test case
test_case = LLMTestCase(
    input="The dog chased the cat up the tree, who ran up the tree?",
    actual_output="It depends, some might consider the cat, while others might argue the dog.",
    expected_output="The cat."
)

# Run evaluation
if __name__ == "__main__":
    evaluate(test_cases=[test_case], metrics=[correctness_metric])
    # Or, for standalone metric run:
    # correctness_metric.measure(test_case)
    # print(correctness_metric.score, correctness_metric.reason)