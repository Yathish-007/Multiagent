import streamlit as st
import sys
import os
from copy import deepcopy

# --- STEP 1: MODIFY PYTHON'S PATH (MUST RUN FIRST) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
smolagents_src_path = os.path.join(current_dir, "src")
sys.path.insert(0, smolagents_src_path)  # ensure local smolagents import [web:7]

# --- STEP 2: PERFORM LOCAL IMPORTS ---
from smolagents.tools import Tool  # [web:1]
from smolagents import CodeAgent, LiteLLMModel  # [web:7][web:6]
from smolagents.agents import EMPTY_PROMPT_TEMPLATES  # [web:7]
from git_tools import get_file_from_repo  # local tool
from test_writer_agent import get_test_writer_agent, is_valid_python_script  # local factory

# --- PAGE CONFIG ---
st.set_page_config(page_title="AI Test Generation Agent", layout="wide")  # [web:12]
st.title("AI-Powered Python Test Generator")  # [web:12]

# --- FINAL ANSWER TOOL (LOCAL) ---
class CustomFinalAnswerTool(Tool):
    name = "final_answer"
    description = "Use this tool to provide the final answer when you have successfully fetched the file content."
    inputs = {
        "answer": {"type": "string", "description": "The final content to be returned."}  # [web:1][web:30][web:22]
    }
    output_type = "string"  # [web:1][web:30][web:22]

    def forward(self, answer: str) -> str:
        return answer  # [web:1]

def _non_empty_string(answer: str, agent_memory=None) -> bool:
    return isinstance(answer, str) and len(answer.strip()) > 0  # [web:7]

# --- SECRETS / API KEY ---
openai_api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", None)  # [web:12]
if not openai_api_key:
    st.error("OPENAI_API_KEY not found in environment or .streamlit/secrets.toml")  # [web:12]
    st.stop()

# --- GIT AGENT WITH STRICT CODE BLOCK FORMAT ---
git_agent_model = LiteLLMModel(model_id="openai/gpt-4o", api_key=openai_api_key, temperature=0)  # [web:6][web:12]
tools_for_git_agent = [get_file_from_repo, CustomFinalAnswerTool()]  # [web:1]

git_agent_system_prompt = (
    "You are a file retrieval specialist.\n"
    "- Wrap ALL tool calls in a single code block using literal tags <code> and </code>.\n"
    "- Inside that one block, first call get_file_from_repo with named parameters repo_url and file_path.\n"
    "- Then immediately call final_answer with named parameter answer set to the exact fetched file content.\n"
    "- Do NOT output anything outside the code block. Do NOT add extra code, imports, or comments.\n\n"
    "Example:\n"
    "<code>\n"
    "get_file_from_repo(repo_url='https://github.com/org/repo.git', file_path='path/to/file.py')\n"
    "final_answer(answer='<FILE_CONTENT>')\n"
    "</code>\n"
)  # strict block format to satisfy parser [web:7]

prompt_templates = deepcopy(EMPTY_PROMPT_TEMPLATES)
prompt_templates["system_prompt"] = git_agent_system_prompt  # [web:7][web:13][web:33]

git_agent = CodeAgent(
    tools=tools_for_git_agent,
    model=git_agent_model,
    prompt_templates=prompt_templates,
    final_answer_checks=[_non_empty_string],  # stop when content is returned [web:7]
    max_steps=3,  # allow one retry + final [web:7][web:33]
)

# --- TEST WRITER AGENT (no code exec, 1-step) ---
test_writer_agent = get_test_writer_agent(api_key=openai_api_key)  # [web:7]

# --- UI AND ORCHESTRATION ---
st.write("Provide a link to a Python file in a public GitHub repository. The system will fetch the code and generate a pytest script for it.")  # [web:12]
repo_url = st.text_input("Enter Git Repository URL:", "https://github.com/huggingface/smolagents.git")  # [web:12]
file_path = st.text_input("Enter the path to the Python file:", "src/smolagents/models.py")  # [web:12]

if st.button("Generate Test Script"):
    if not repo_url or not file_path:
        st.warning("Please provide both a repository URL and a file path.")  # [web:12]
        st.stop()

    # Agent 1: fetch code
    with st.spinner("Agent 1 (Git Agent) is fetching the file..."):
        try:
            prompt_fetch = f"Please get the content of the file '{file_path}' from the repository '{repo_url}'."
            python_code = git_agent.run(prompt_fetch)  # [web:7]
            st.success("Agent 1 finished: File content fetched!")  # [web:12]
        except Exception as e:
            st.error(f"An error occurred while running the Git Agent: {e}")  # [web:12]
            st.stop()

    with st.expander("Show Fetched Python Code"):
        st.code(python_code or "", language='python')  # [web:12]

    if not python_code or python_code.startswith("Error:"):
        st.error(python_code or "Unknown error fetching file.")  # [web:11]
        st.stop()

    # Agent 2: generate tests
    with st.spinner("Agent 2 (Test Writer) is generating the pytest script..."):
        try:
            test_script = test_writer_agent.run(python_code)  # [web:7]
        except Exception as e:
            st.error(f"An error occurred while running the Test Writer Agent: {e}")  # [web:12]
            st.stop()

    # Always show what was generated for review
    if isinstance(test_script, str) and len(test_script.strip()) > 0:
        st.subheader("Generated Pytest Script")  # [web:12]
        st.code(test_script, language='python')  # [web:12]
        # Then decide how to mark status and stop
        if is_valid_python_script(test_script):
            st.success("Agent 2 finished: Test script generated!")  # [web:12]
            st.stop()
        else:
            st.warning("Generated output did not pass strict validation, but is shown above for review.")  # [web:12]
            st.stop()
    else:
        st.error("No test script returned.")  # [web:12]
        st.stop()
