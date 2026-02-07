import os
import subprocess
import re
from pathlib import Path

class RepoCloner:
    def __init__(self, base_path, hf_token=None):
        self.base_path = Path(base_path)
    
    def clone_repositories(self, repo_dict):
        for relative_path, repos in repo_dict.items():
            target_dir = self.base_path / relative_path
            target_dir.mkdir(parents=True, exist_ok=True)
            
            for repo in repos:
                print(f"克隆: {repo}")
                subprocess.run([
                    "git", "clone", repo
                ], cwd=str(target_dir), check=False)