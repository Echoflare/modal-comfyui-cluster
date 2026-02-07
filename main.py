import modal
import modal.experimental
import subprocess
from pathlib import Path
from src.config_loader import ConfigLoader
from src.utils import run_comfyui, link_file_to_comfyui

config = ConfigLoader()
app_cfg = config.app_config
comfyui_cfg = config.comfyui_config
files_cfg = config.files_config
repos_cfg = config.repos_config
tokens_cfg = config.tokens_config

comfyui_path = comfyui_cfg['install_path']
data_path = "/comfy_data/"

def install_nodes(node_list):
    for node in node_list:
        cmd = [
            "comfy", "--skip-prompt",
            "node", "install",
            "--fast-deps", node
        ]
        subprocess.run(cmd, check=False)

def run_clone_repos(repos, path):
    from src.cloner import RepoCloner 
    cloner = RepoCloner(path)
    cloner.clone_repositories(repos)

def run_download_public(files, path, token):
    from src.downloader import FileDownloader
    downloader = FileDownloader(path, token)
    downloader.download_public_files(files)

def run_download_private(files, path, token):
    from src.downloader import FileDownloader
    downloader = FileDownloader(path, token)
    downloader.download_private_files(files)

image = (
    modal.Image.debian_slim(python_version=app_cfg["python_version"], force_build=app_cfg["rebuild_on_deploy"])
    .apt_install("git", "wget", "aria2", *app_cfg["extra_packages"])
    .uv_pip_install("huggingface_hub", "fastapi[standard]", *app_cfg["extra_requirements"])
    .uv_pip_install("comfy-cli")
    .add_local_dir("src", remote_path="/root/src", copy=True)
    .add_local_dir("config", remote_path="/root/config", copy=True)
    .run_commands(f"comfy --workspace={comfyui_path} --skip-prompt install --fast-deps --nvidia {' '.join(comfyui_cfg['install_args'])}")
)
vol_files = modal.Volume.from_name(app_cfg["file_volume_name"], create_if_missing=True)
vol_outputs = modal.Volume.from_name(app_cfg["output_volume_name"], create_if_missing=True)

image = (
    image.run_function(
        install_nodes,
        args=(comfyui_cfg['nodes'], )
    )
    .run_function(
        run_clone_repos,
        args=(repos_cfg, comfyui_path)
    )
    .run_function(
        run_download_public,
        args=(files_cfg["public_files"], data_path, tokens_cfg.get("huggingface_token")),
        volumes={data_path: vol_files}
    )
    .run_function(
        run_download_private,
        args=(files_cfg["private_files"], data_path, tokens_cfg.get("huggingface_token")),
        volumes={data_path: vol_files}
    )
    .run_function(
        link_file_to_comfyui,
        args=(data_path, comfyui_path),
        volumes={data_path: vol_files}
    )
)

image = image.run_commands(f"rm -rf {Path(comfyui_path)/'output'}")

if comfyui_cfg["update_on_deploy"]:
    image = image.run_commands("comfy update comfy && comfy node update all || true", force_build=True)

app = modal.App(app_cfg["app_name"], image=image)

def create_comfy_instance(index):
    func_name = f"comfy-node-{index}"
    
    @app.function(
        name=func_name,
        max_containers=app_cfg["max_containers"],
        gpu=app_cfg["gpu_type"],
        volumes={data_path: vol_files, Path(comfyui_path)/"output": vol_outputs},
        timeout=app_cfg["timeout"],
        image=image,
        serialized=True
    )
    @modal.concurrent(max_inputs=app_cfg["concurrent_inputs"])
    @modal.web_server(comfyui_cfg["port"], startup_timeout=300)
    def run_ui():
        run_comfyui(
            comfyui_cfg["port"],
            comfyui_cfg["launch_args"]
        )
    
    return run_ui

@app.local_entrypoint()
def deploy():
    print(f"启动ComfyUI: 将创建{app_cfg['num_instances']}个GPU实例")

for i in range(app_cfg["num_instances"]):
    create_comfy_instance(i)