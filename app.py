import streamlit as st
import sys
import os

# --- PATH LOGIC (UNCHANGED) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
smolagents_src_path = os.path.join(current_dir, "src")
sys.path.insert(0, smolagents_src_path)

# --- IMPORTS ---
try:
    from smolagents import CodeAgent, LiteLLMModel
    from git_tools import get_file_from_repo
    from test_writer_agent import get_test_writer_agent # <-- IMPORT OUR NEW FUNCTION
except ImportError as e:
    st.error(f"A file failed to import. Error: {e}")
    st.stop()

# --- PAGE CONFIG ---
st.set_page_config(page_title="AI Test Generation Agent", layout="wide")
st.title("AI-Powered Python Test Generator")

# --- AGENT CONFIGURATION ---
try:
    openai_api_key = st.secrets["OPENAI_API_KEY"]
except (KeyError, FileNotFoundError):
    st.error("OPENAI_API_KEY not found in .streamlit/secrets.toml. Please create it.")
    st.stop()

# Agent 1: The Git Agent (remains the same)
git_agent_model = LiteLLMModel(model_id="openai/gpt-4-turbo", api_key=openai_api_key)
git_agent = CodeAgent(tools=[get_file_from_repo], model=git_agent_model)

# Agent 2: The Test Writer Agent (now created via our function)
test_writer_agent = get_test_writer_agent(api_key=openai_api_key)

# --- UI AND ORCHESTRATION (UNCHANGED) ---
st.write("Provide a link to a Python file in a public GitHub repository. The system will fetch the code and generate a pytest script for it.")
repo_url = st.text_input("Enter Git Repository URL:", "https://github.com/huggingface/smolagents.git")
file_path = st.text_input("Enter the path to the Python file:", "src/smolagents/models.py")

if st.button("Generate Test Script"):
    if repo_url and file_path:
        python_code = ""
        with st.spinner("Agent 1 (Git Agent) is fetching the file..."):
            try:
                prompt_fetch = f"Please get the content of the file '{file_path}' from the repository '{repo_url}'."
                python_code = git_agent.run(prompt_fetch)
                st.success("Agent 1 finished: File content fetched!")
            except Exception as e:
                st.error(f"An error occurred while running the Git Agent: {e}")
                st.stop()
        
        with st.expander("Show Fetched Python Code"):
            st.code(python_code, language='python')

        if python_code:
            with st.spinner("Agent 2 (Test Writer) is generating the pytest script..."):
                try:
                    test_script = test_writer_agent.run(python_code)
                    st.success("Agent 2 finished: Test script generated!")
                    st.subheader("Generated Pytest Script")
                    st.code(test_script, language='python')
                except Exception as e:
                    st.error(f"An error occurred while running the Test Writer Agent: {e}")
                    st.stop()
    else:
        st.warning("Please provide both a repository URL and a file path.")

