from copy import deepcopy
from smolagents import CodeAgent, LiteLLMModel  # CodeAgent, LiteLLMModel [web:7][web:6]
from smolagents.agents import EMPTY_PROMPT_TEMPLATES  # Prompt templates base [web:7]

def is_valid_python_script(answer: str, agent_memory=None) -> bool:
    """
    Accepts a pytest script if it appears to be non-empty Python code that
    imports pytest (or from pytest ...) and defines at least one test function.
    """
    try:
        if not isinstance(answer, str):
            return False  # not text [web:7]
        s = answer.strip()
        if len(s) < 40:
            return False  # minimal length floor [web:7]
        has_pytest = ("import pytest" in s) or ("from pytest" in s)
        has_test = "def test_" in s
        return has_pytest and has_test  # core heuristic [web:7]
    except Exception:
        return False  # safe fallback [web:7]

FEW_SHOT_EXAMPLES = [
    {
        "input_code": "def add(a, b):\n    return a + b",
        "output_test": "import pytest\n\nfrom target_module import add\n\ndef test_add_basic():\n    assert add(2, 3) == 5\n    assert add(-1, 1) == 0\n",
    },
    {
        "input_code": "def binary_search(arr, target):\n    # assume sorted ascending\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        if arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1\n",
        "output_test": "import pytest\n\nfrom target_module import binary_search\n\ndef test_binary_search_found():\n    assert binary_search([1,2,3,4,5], 3) == 2\n\ndef test_binary_search_not_found():\n    assert binary_search([1,2,3,4,5], 6) == -1\n\ndef test_binary_search_empty():\n    assert binary_search([], 1) == -1\n",
    },
]  # pragmatic few-shots to steer formatting [web:7]

def get_test_writer_agent(api_key: str) -> CodeAgent:
    """
    Constructs and returns a specialized CodeAgent for writing pytest scripts.
    It outputs raw Python only, does not execute code, and stops after the first valid script.
    """
    system_prompt = (
        "You are a world-class Python developer specializing in pytest.\n"
        "Input: the full text of a single Python module.\n"
        "Task: output ONLY a pytest test file as raw Python. No comments or explanations.\n"
        "Assume the module will be saved as 'target_module.py' and import from it accordingly.\n\n"
        "--- EXAMPLES ---\n"
    )  # clear constraints [web:7]

    for ex in FEW_SHOT_EXAMPLES:
        system_prompt += "EXAMPLE INPUT:\n``````\n"
        system_prompt += "CORRECT OUTPUT:\n``````\n\n"  # [web:7]

    model = LiteLLMModel(model_id="openai/gpt-4o-mini", api_key=api_key, temperature=0.2)  # fast/cheap [web:6][web:12]
    prompt_templates = deepcopy(EMPTY_PROMPT_TEMPLATES)
    prompt_templates["system_prompt"] = system_prompt  # required key [web:7]

    return CodeAgent(
        model=model,
        prompt_templates=prompt_templates,
        tools=[],  # test writer does not need tools [web:7]
        final_answer_checks=[is_valid_python_script],  # stop when a plausible test file is produced [web:7]
        max_steps=1,  # single-shot generation [web:7]
        allow_code_execution=False,  # relies on your local CodeAgent change [web:7]
    )
