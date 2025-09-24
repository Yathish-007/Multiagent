import os
import git
import tempfile
from smolagents import tool

@tool
def get_file_from_repo(repo_url: str, file_path: str) -> str:
    """
    Clones a Git repository to a temporary directory and returns the content of a specific file.

    Args:
        repo_url (str): The URL of the Git repository to clone.
        file_path (str): The path to the file within the repository.

    Returns:
        str: The content of the specified file, or an error message if the file cannot be read.
    """
    try:
        # Create a temporary directory to clone the repo
        temp_dir = tempfile.mkdtemp()
        
        # Clone the repository
        git.Repo.clone_from(repo_url, temp_dir)
        
        # Construct the full path to the file
        full_file_path = os.path.join(temp_dir, file_path)
        
        # Check if the file exists
        if not os.path.exists(full_file_path):
            return f"Error: File '{file_path}' not found in the repository."
            
        # Read and return the file content
        with open(full_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
        
    except Exception as e:
        return f"An error occurred: {e}"

