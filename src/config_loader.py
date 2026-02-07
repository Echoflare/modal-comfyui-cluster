import json
from pathlib import Path

class ConfigLoader:
    def __init__(self, config_dir="config"):
        self.config_dir = Path(config_dir)
        
        self._app_config = None
        self._comfyui_config = None
        self._files_config = None
        self._repos_config = None
        self._tokens_config = None
        self._transfers_config = None
    
    def _load(self, filename):
        target_path = self.config_dir / filename
        if not target_path.exists():
            return {}
            
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return {}

    @property
    def app_config(self):
        if self._app_config is None:
            self._app_config = self._load("app.json")
        return self._app_config

    @property
    def comfyui_config(self):
        if self._comfyui_config is None:
            self._comfyui_config = self._load("comfyui.json")
        return self._comfyui_config

    @property
    def files_config(self):
        if self._files_config is None:
            self._files_config = self._load("files.json")
        return self._files_config

    @property
    def repos_config(self):
        if self._repos_config is None:
            self._repos_config = self._load("repositories.json")
        return self._repos_config

    @property
    def tokens_config(self):
        if self._tokens_config is None:
            self._tokens_config = self._load("tokens.json")
        return self._tokens_config
        
    @property
    def transfers_config(self):
        if self._transfers_config is None:
            self._transfers_config = self._load("transfers.json")
        return self._transfers_config