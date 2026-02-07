import os
import subprocess
import re
from pathlib import Path

class FileDownloader:
    def __init__(self, base_path, hf_token=None):
        self.base_path = Path(base_path)
        self.hf_token = hf_token
        if hf_token:
            from huggingface_hub import login
            login(token=hf_token)
    
    def download_public_files(self, file_dict):
        for relative_path, files in file_dict.items():
            target_dir = self.base_path / relative_path
            target_dir.mkdir(parents=True, exist_ok=True)
            
            for file_info in files:
                url = file_info.get("url")
                if not url:
                    continue
                    
                filename = file_info.get("name")
                if filename:
                    output_path = target_dir / filename
                else:
                    match = re.search(r'/([^/?]+)(?:\?download=true)?$', url)
                    if match:
                        filename = match.group(1)
                        output_path = target_dir / filename
                    else:
                        continue
                
                if output_path.exists():
                    print(f"已存在: {output_path}")
                    continue
                
                print(f"下载: {url}")
                cmd = [
                    "aria2c",
                    "--console-log-level=error",
                    "-c",
                    "-x", "16",
                    "-s", "16",
                    "-k", "1M",
                    "-d", str(target_dir),
                    "-o", filename,
                    url
                ]
                
                subprocess.run(cmd, check=True)
    
    def download_private_files(self, private_dict):
        from huggingface_hub import hf_hub_download
        if not self.hf_token:
            return
            
        for relative_path, items in private_dict.items():
            target_dir = self.base_path / relative_path
            target_dir.mkdir(parents=True, exist_ok=True)
            
            for item in items:
                try:
                    hf_hub_download(
                        repo_id=item['repo'],
                        filename=item['path'],
                        repo_type=item.get('repo_type', 'model'),
                        local_dir=str(target_dir),
                        local_dir_use_symlinks=False
                    )
                    print(f"下载私有文件: {item['path']}")
                except Exception as e:
                    print(f"下载失败: {e}")