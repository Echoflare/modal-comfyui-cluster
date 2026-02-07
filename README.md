# Modal: ComfyUI Cluster

这是一个在[Modal](https://modal.com)平台上运行[ComfyUI](https://github.com/comfyanonymous/ComfyUI)集群的项目。

## 前置要求

1.  **注册 [Modal](https://modal.com) 账号**
2.  **安装 Python 3.10+**
3.  **安装 Modal 客户端**：
    ```bash
    pip install modal
    ```
4.  **配置 Modal 账户**：
    ```bash
    python3 -m modal setup
    ```

## 配置说明

项目所有的配置项位于 `config/` 目录下。在部署前，请根据您的需求修改以下文件：

### 1. `app.json` (应用资源)
控制容器环境 (GPU 类型、并发数和超时时间等)。
```json5
{
  "app_name": "comfyui-cluster", // ComfyUI集群应用命名
  "file_volume_name": "comfyui-files", // 大文件存放媒介命名 (例如: 模型)
  "output_volume_name": "comfyui-output", // 输出文件存放媒介命名 (例如: 图片)
  "python_version": "3.12", // 集群镜像的Python环境版本
  "rebuild_on_deploy": false, // 是否在每次部署的时候都重新构建镜像
  "gpu_type": "T4", // GPU类型: T4、L4、A10、A100、... (查看 https://modal.com/docs/guide/gpu 的 Specifying GPU type 条目)
  "num_instances": 1, // GPU实例数量 (控制ComfyUI实例数量)
  "timeout": 3600, // 空闲超时时间
  "max_containers": 1, // 集群单个节点最大的容器数量 (控制GPU数量但不控制ComfyUI实例数量)
  "concurrent_inputs": 100, // 单个容器支持的最大并发输入
  "extra_packages": [], // 额外安装的Debian软件包
  "extra_requirements": [] // 额外安装的Pypi依赖
}
```

### 2. `comfyui.json` (ComfyUI相关)
控制ComfyUI安装路径、启动参数等。
```json5
{
  "install_path": "/root/comfy/ComfyUI", // ComfyUI安装路径
  "install_args": [], // ComfyUI安装参数 (例如: --skip-prompt)
  "update_on_deploy": false, // 是否在每次部署的时候都更新ComfyUI及全部节点
  "nodes": [], // 节点安装列表
  "port": 8188, // ComfyUI启动端口
  "launch_args": [] // ComfyUI启动参数 (例如: --fp32-vae)
}
```

### 3. `files.json` (文件下载)
用于下载文件，分为公有、私有下载 (HuggingFace)。
```json5
{
  "public_files": { // 公有下载 (使用aria2工具)
    "ComfyUI内部相对路径1": [
      {
        "url": "文件地址1",
        "name": "[StabilityAI]SDXL-1.0.safetensors"
      },
      {
        "url": "文件地址2",
        "name": "文件名" // 本键可选择性设置
      }
    ],
    "ComfyUI内部相对路径2": []
    // ...
  },
  "private_files": { // 私有下载 (使用huggingface_hub模块)
    "ComfyUI内部相对路径1": [
      {
        "repo": "仓库名1", // 格式为User/Repository
        "path": "仓库内文件地址1",
        "repo_type": "仓库类型1" // dataset/model
      },
      {
        "repo": "仓库名2", 
        "path": "仓库内文件地址2",
        "repo_type": "仓库类型2"
      }
    ]
  }
}
```
示例:
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
现成配置文件 (NewBie-image-Exp0.1):
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

### 4. `repositories.json` (仓库克隆)
用于克隆Git仓库。
```json5
{
  "ComfyUI内部相对路径1": [
    "需要克隆的仓库地址1", // 可携带Git参数
    "需要克隆的仓库地址2"
  ],
  "ComfyUI内部相对路径2": []
}
```
示例:
```json5
{
  "custom_nodes": [
    "https://github.com/audioscavenger/save-image-extended-comfyui"
  ]
}
```

### 5. `tokens.json` (敏感信息)
配置您的 HuggingFace Token，用于下载私有模型 (如果有下载私有模型的需求)。
```json5
{
  "huggingface_token": ""
}
```

## 部署与运行

### 本地开发/测试
在本地终端运行以下命令，Modal 会将代码同步到云端并实时流式传输日志：
```bash
modal serve main.py
```

### 正式部署
将应用部署到 Modal 平台，使其作为持久服务运行：
```bash
modal deploy main.py
```

部署成功后，终端会输出对应的 **Web URL** (例如 `https://your-username--comfyui-cluster-comfy-node-0.modal.run`)，访问该链接后，将会启动对应的ComfyUI实例。