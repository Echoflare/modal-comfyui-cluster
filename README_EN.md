# Modal: ComfyUI Cluster

[中文](./README.md) | [English](./README_EN.md)

This project runs a [ComfyUI](https://github.com/comfyanonymous/ComfyUI) cluster on the [Modal](https://modal.com) platform.

## Prerequisites

1.  **Sign up for a [Modal](https://modal.com) account.**
2.  **Install Python 3.10+.**
3.  **Install the Modal Client**:
    ```bash
    pip install modal
    ```
4.  **Configure your Modal account**:
    ```bash
    python3 -m modal setup
    ```

## Configuration Instructions

All configuration items are located in the `config/` directory. Before deploying, please modify the following files according to your needs:

### 1. `app.json` (App Resources)
Controls the container environment (GPU type, concurrency, timeout, etc.).
```json5
{
  "app_name": "comfyui-cluster", // ComfyUI Cluster App Name
  "node_name": "comfyui-node", // ComfyUI Cluster Node Name
  "file_volume_name": "comfyui-files", // Large file storage volume name (e.g., models)
  "output_volume_name": "comfyui-output", // Output file storage volume name (e.g., images)
  "persistence_volume_name": "comfyui-persistence", // Persistence volume name
  "python_version": "3.12", // Cluster image Python version (set to "auto" to automatically align with local Python version)
  "rebuild_on_deploy": false, // Whether to rebuild the image on every deployment
  "gpu_type": "T4", // GPU type: T4, L4, A10, A100, ... (See https://modal.com/docs/guide/gpu under Specifying GPU type)
  "num_instances": 1, // Number of GPU instances (Controls ComfyUI instance count. Note: If >1, closure functions must be serialized, and "python_version" must match local version)
  "timeout": 3600, // Idle timeout
  "max_containers": 1, // Max containers per cluster node (Controls GPU count but not ComfyUI instance count)
  "concurrent_inputs": 100, // Max concurrent inputs per container
  "extra_packages": [], // Extra Debian packages to install
  "extra_requirements": [] // Extra PyPI requirements to install
}
```

### 2. `comfyui.json` (ComfyUI Related)
Controls ComfyUI installation path, launch arguments, etc.
```json5
{
  "install_path": "/root/comfy/ComfyUI", // ComfyUI installation path
  "install_args": [], // ComfyUI installation arguments (e.g., --skip-prompt)
  "update_on_deploy": false, // Whether to update ComfyUI and all nodes on every deployment
  "nodes": [], // List of nodes to install
  "port": 8188, // ComfyUI launch port
  "launch_args": [] // ComfyUI launch arguments (e.g., --fp32-vae)
}
```

### 3. `files.json` (File Downloads)
Used for downloading files, categorized into public and private downloads (HuggingFace).
```json5
{
  "public_files": { // Public downloads (uses aria2 tool)
    "ComfyUI_internal_relative_path_1": [
      {
        "url": "File_URL_1",
        "name": "[StabilityAI]SDXL-1.0.safetensors"
      },
      {
        "url": "File_URL_2",
        "name": "Filename" // This key is optional
      }
    ],
    "ComfyUI_internal_relative_path_2": []
    // ...
  },
  "private_files": { // Private downloads (uses huggingface_hub module)
    "ComfyUI_internal_relative_path_1": [
      {
        "repo": "Repo_Name_1", // Format: User/Repository
        "path": "File_path_inside_repo_1",
        "repo_type": "Repo_Type_1" // dataset/model
      },
      {
        "repo": "Repo_Name_2", 
        "path": "File_path_inside_repo_2",
        "repo_type": "Repo_Type_2"
      }
    ]
  }
}
```
Example:
```json5
{
  "public_files": {
    "models/checkpoints": [
      {
        "url": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0_0.9vae.safetensors",
        "name": "[StabilityAI]SDXL-1.0.safetensors"
      }
    ],
    "models/vae": [
      {
        "url": "https://huggingface.co/stabilityai/sdxl-vae/resolve/main/sdxl_vae.safetensors",
        "name": "[StabilityAI]sdxl-vae.safetensors"
      }
    ],
    "models/loras": [],
    "models/controlnet": [],
    "models/upscale_models": []
  },
  "private_files": {
    "models/checkpoints": [
      {
        "repo": "stabilityai/stable-diffusion-3.5-medium",
        "path": "sd3.5_medium.safetensors",
        "repo_type": "model"
      }
    ],
    "models/vae": [],
    "models/loras": []
  }
}
```
Ready-made configuration (NewBie-image-Exp0.1):
```json5
{
  "public_files": {
    "models/diffusion_models": [
      {
        "url": "https://huggingface.co/NewBie-AI/NewBie-image-Exp0.1/resolve/main/transformer/diffusion_pytorch_model.safetensors",
        "name": "NewBie-Image-Exp0.1-bf16.safetensors"
      }
    ],
    "models/vae": [
      {
        "url": "https://huggingface.co/NewBie-AI/NewBie-image-Exp0.1/resolve/main/vae/diffusion_pytorch_model.safetensors",
        "name": "ae.safetensors"
      }
    ],
    "models/clip": [
      {
        "url": "https://huggingface.co/NewBie-AI/NewBie-image-Exp0.1/resolve/main/clip_model/jina-clip-v2.safetensors",
        "name": "jina_clip_v2_bf16.safetensors"
      },
      {
        "url": "https://huggingface.co/NewBie-AI/NewBie-image-Exp0.1/resolve/main/text_encoder/gemma3-4b-it.safetensors",
        "name": "gemma_3_4b_it_bf16.safetensors"
      }
    ]
  },
  "private_files": {}
}
```

### 4. `persistence.json` (File Persistence)
Used to persist files or folders that need to be saved.
```json5
[
  "ComfyUI_internal_file_or_folder_to_persist_1",
  "ComfyUI_internal_file_or_folder_to_persist_2"
]
```
Example:
```json5
[
    "user/comfyui.db",
    "user/default"
]
```

### 5. `repositories.json` (Repository Cloning)
Used for cloning Git repositories.
```json5
{
  "ComfyUI_internal_relative_path_1": [
    "Repo_URL_to_clone_1", // Can include Git arguments
    "Repo_URL_to_clone_2"
  ],
  "ComfyUI_internal_relative_path_2": []
}
```
Example:
```json5
{
  "custom_nodes": [
    "https://github.com/audioscavenger/save-image-extended-comfyui"
  ]
}
```

### 6. `tokens.json` (Sensitive Info)
Configure your HuggingFace Token here, used for downloading private models (if you have a requirement to download private models).
```json5
{
  "huggingface_token": ""
}
```

### 7. `transfers.json` (File Transfer)
Configures where files in the `upload/` folder should be transferred to in the cloud environment.
```json5
{
  "Path_inside_upload_folder_1": "ComfyUI_internal_relative_path_1",
  "Path_inside_upload_folder_2": "ComfyUI_internal_relative_path_2"
}
```
Example:
```json5
{
  "example.txt": "temp/example.txt"
}
```

## Deployment & Running

### Local Development/Testing
Run the following command in your local terminal. Modal will sync the code to the cloud and stream logs in real-time:
```bash
modal serve main.py
```

### Formal Deployment
Deploy the application to the Modal platform to run as a persistent service:
```bash
modal deploy main.py
```

Upon successful deployment, the terminal will output the corresponding **Web URL** (e.g., `https://your-username--comfyui-cluster-comfyui-node.modal.run`). Accessing this link will start the corresponding ComfyUI instance.