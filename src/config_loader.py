import json
from pathlib import Path

class ConfigLoader:
    def __init__(self, config_dir="config"):
        self.config_dir = Path(config_dir)
        self.app_config = self._load("app.json")
        self.comfyui_config = self._load("comfyui.json")
        self.files_config = self._load("files.json")
        self.repos_config = self._load("repositories.json")
        self.tokens_config = self._load("tokens.json")
        self.transfers_config = self._load("transfers.json")
    
    def _load(self, filename):
        with open(self.config_dir / filename, 'r', encoding='utf-8') as f:
            return json.load(f)