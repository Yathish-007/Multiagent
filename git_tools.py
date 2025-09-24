from smolagents.tools import Tool  # [web:1]
from git import Repo  # GitPython [web:11]
import tempfile
import os
import shutil

class GetFileFromRepoTool(Tool):
    name = "get_file_from_repo"
    description = "Clones a public GitHub repository shallowly, reads a specific text file, and returns its UTF-8 content."
    inputs = {
        "repo_url": {"type": "string", "description": "Public Git URL (https)."},  # [web:1][web:22]
        "file_path": {"type": "string", "description": "Path to the file within the repo."}  # [web:1][web:22]
    }
    output_type = "string"  # [web:1][web:22]

    def forward(self, repo_url: str, file_path: str) -> str:
        # Basic input guards
        if not isinstance(repo_url, str) or not repo_url.startswith("https://"):
            return "Error: repo_url must start with 'https://'."  # [web:11]
        if not isinstance(file_path, str) or len(file_path.strip()) == 0:
            return "Error: file_path must be a non-empty string."  # [web:11]

        # Normalize path separators and collapse '..'
        norm_rel_path = os.path.normpath(file_path.replace("\\", "/")).lstrip("/\\")  # [web:11][web:14]

        temp_dir = tempfile.mkdtemp()
        try:
            Repo.clone_from(repo_url, temp_dir, depth=1)  # shallow clone [web:11][web:14]
            full_file_path = os.path.abspath(os.path.join(temp_dir, norm_rel_path))

            # Prevent path traversal
            if not full_file_path.startswith(os.path.abspath(temp_dir)):
                return "Error: Invalid file path."  # [web:11][web:14]

            if not os.path.exists(full_file_path):
                return f"Error: File '{file_path}' not found in repository."  # [web:11]

            # Size guard (~2 MB)
            if os.path.getsize(full_file_path) > 2 * 1024 * 1024:
                return "Error: File too large (>2MB) for inline return."  # [web:11][web:14]

            # Read with UTF-8 first, fallback to latin-1
            try:
                with open(full_file_path, "r", encoding="utf-8") as f:
                    return f.read()
            except UnicodeDecodeError:
                try:
                    with open(full_file_path, "r", encoding="latin-1") as f:
                        return f.read()
                except Exception:
                    return "Error: Unable to decode file content as text."

        except Exception as e:
            return f"An error occurred: {e}"  # [web:11]
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)  # [web:11][web:14]

get_file_from_repo = GetFileFromRepoTool()  # [web:1]
