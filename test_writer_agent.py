from smolagents import CodeAgent, LiteLLMModel
# --- THE FIX: Import the default templates ---
from smolagents.agents import EMPTY_PROMPT_TEMPLATES
from copy import deepcopy

# --- FEW-SHOT EXAMPLES (UNCHANGED) ---
FEW_SHOT_EXAMPLES = [
    {
        "input_code": "def add(a, b):\n    return a + b",
        "output_test": "import pytest\nfrom main import add\n\ndef test_add():\n    assert add(2, 3) == 5\n    assert add(-1, 1) == 0",
    },
    {
        "input_code": "class Calculator:\n    def multiply(self, a, b):\n        return a * b",
        "output_test": "import pytest\nfrom main import Calculator\n\n@pytest.fixture\ndef calculator():\n    return Calculator()\n\ndef test_multiply(calculator):\n    assert calculator.multiply(3, 4) == 12\n    assert calculator.multiply(-1, 5) == -5",
    },
]

def get_test_writer_agent(api_key: str) -> CodeAgent:
    """
    Constructs and returns a specialized CodeAgent for writing pytest scripts.
    """
    system_prompt = (
        "You are a world-class Python developer with a specialization in software testing. "
        "Your sole task is to write a comprehensive and robust test script for the given Python code using the pytest framework. "
        "The tests should cover all functions, methods, and edge cases. Only output the raw Python code for the test file, with no explanations, comments, or pleasantries.\n\n"
        "--- EXAMPLES ---\n"
    )

    for example in FEW_SHOT_EXAMPLES:
        system_prompt += f"EXAMPLE INPUT:\n``````\n"
        system_prompt += f"CORRECT OUTPUT:\n``````\n\n"

    model = LiteLLMModel(model_id="openai/gpt-4o", api_key=api_key)

    # --- THE FIX: Start with default templates and modify them ---
    # 1. Make a deep copy of the default templates to avoid side effects.
    prompt_templates = deepcopy(EMPTY_PROMPT_TEMPLATES)
    # 2. Update only the 'system' prompt with our custom one.
    prompt_templates["system"] = system_prompt
    
    # Create and return the CodeAgent instance
    agent = CodeAgent(
        model=model,
        prompt_templates=prompt_templates,  # Pass the complete, correctly structured dictionary
        tools=[]
    )
    
    return agent
