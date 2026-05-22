import modal
import modal.experimental
import subprocess
import shutil
import sys
from pathlib import Path
from src.config_loader import ConfigLoader
from src.utils import run_comfyui, link_file_to_comfyui
from src.persistence import restore_files, start_persistence_sync

config = ConfigLoader()
app_cfg = config.app_config
comfyui_cfg = config.comfyui_config
files_cfg = config.files_config
repos_cfg = config.repos_config
tokens_cfg = config.tokens_config
transfers_cfg = config.transfers_config
persistence_cfg = config.persistence_config

comfyui_path = comfyui_cfg.get('install_path', "/root/comfy/ComfyUI")
data_path = "/root/comfy_files"
persistence_path = "/root/comfy_persistence"

def install_nodes(node_list, comfyui_path):
    for node in node_list:
        print(f"安装: {node}")
        cmd = [
            "comfy", "--skip-prompt",
            "--workspace", comfyui_path,
            "node", "install",
            "--fast-deps", node
        ]
        subprocess.run(cmd, check=False)

def run_clone_repos(repos, path):
    from src.cloner import RepoCloner 
    cloner = RepoCloner(path)
    cloner.clone_repositories(repos)

def run_download_public(files, path):
    from src.downloader import FileDownloader
    downloader = FileDownloader(path)
    downloader.download_public_files(files)

def run_download_private(files, path, token):
    from src.downloader import FileDownloader
    downloader = FileDownloader(path, token)
    downloader.download_private_files(files)

def run_upload_and_transfer(transfers_cfg, upload_path, target_base_path):
    upload_root = Path(upload_path)
    target_root = Path(target_base_path)
    
    for src_rel_path, dst_rel_path in transfers_cfg.items():
        src_file = upload_root / src_rel_path
        dst_file = target_root / dst_rel_path
        if src_file.exists():
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)
            print(f"已复制: {src_rel_path} -> {dst_file}")
        else:
            print(f"警告: 源文件未找到 {src_file}")

sys_python = f"{sys.version_info.major}.{sys.version_info.minor}"
env_python = app_cfg.get("python_version", sys_python)
image = (
    modal.Image.debian_slim(python_version=env_python if env_python.lower() != "auto" else sys_python, force_build=app_cfg.get("rebuild_on_deploy", False))
    .apt_install("git", "wget", "aria2", *app_cfg.get("extra_packages", []))
    .uv_pip_install("huggingface_hub", "fastapi[standard]", *app_cfg.get("extra_requirements", []))
    .uv_pip_install("comfy-cli")
    .run_commands(f"comfy --workspace={comfyui_path} --skip-prompt install --fast-deps --nvidia {' '.join(comfyui_cfg.get('install_args', []))}")
    
)
vol_files = modal.Volume.from_name(app_cfg.get("file_volume_name", "comfyui-files"), create_if_missing=True)
vol_outputs = modal.Volume.from_name(app_cfg.get("output_volume_name", "comfyui-output"), create_if_missing=True)
vol_persistence = modal.Volume.from_name(app_cfg.get("persistence_volume_name", "comfyui-persistence"), create_if_missing=True)

image = (
    image.add_local_python_source("src", copy=True)
    .add_local_file("config/app.json", remote_path="/root/config/app.json", copy=True)
)

image = (
    image.add_local_file("config/comfyui.json", remote_path="/root/config/comfyui.json", copy=True)
    .run_function(
        install_nodes,
        args=(comfyui_cfg.get('nodes', []), comfyui_path)
    )
)

image = (
    image.add_local_file("config/repositories.json", remote_path="/root/config/repositories.json", copy=True)
    .run_function(
        run_clone_repos,
        args=(repos_cfg, comfyui_path)
    )
)

image = (
    image.add_local_file("config/files.json", remote_path="/root/config/files.json", copy=True)
    .add_local_file("config/tokens.json", remote_path="/root/config/tokens.json", copy=True)
    .run_commands(f"rm -rf {data_path}")
    .run_function(
        run_download_public,
        args=(files_cfg.get("public_files", {}), data_path),
        volumes={data_path: vol_files}
    )
    .run_function(
        run_download_private,
        args=(files_cfg.get("private_files", {}), data_path, tokens_cfg.get("huggingface_token")),
        volumes={data_path: vol_files}
    )
    .run_function(
        link_file_to_comfyui,
        args=(data_path, comfyui_path),
        volumes={data_path: vol_files}
    )
)

if Path("upload").exists():
    image = image.add_local_file("config/transfers.json", remote_path="/root/config/transfers.json", copy=True)
    image = (
        image.add_local_dir("upload", remote_path="/root/upload", copy=True)
        .run_function(
            run_upload_and_transfer,
            args=(transfers_cfg, "/root/upload", comfyui_path),
        )
    )

image = image.run_commands(f"rm -rf {Path(comfyui_path)/'output'}")

if comfyui_cfg.get("update_on_deploy", False):
    image = image.run_commands("comfy update comfy && comfy node update all || true", force_build=True)

image = image.add_local_file("config/persistence.json", remote_path="/root/config/persistence.json", copy=True)

app = modal.App(app_cfg.get("app_name", "comfyui-cluster"), image=image)

volume_mounts = {
    data_path: vol_files, 
    Path(comfyui_path)/"output": vol_outputs,
    persistence_path: vol_persistence
}

node_name = app_cfg.get("node_name", "comfyui-node")

def create_comfy_instance(index):
    node_name_unique = f"{node_name}-{index}"
    
    @app.function(
        name=node_name_unique,
        max_containers=app_cfg.get("max_containers", 1),
        gpu=app_cfg.get("gpu_type", "T4"),
        volumes=volume_mounts,
        timeout=app_cfg.get("timeout", 3600),
        image=image,
        serialized=True
    )
    @modal.concurrent(max_inputs=app_cfg.get("concurrent_inputs", 100))
    @modal.web_server(comfyui_cfg.get("port", 8188), startup_timeout=300)
    def run_ui():
        restore_files(persistence_cfg, persistence_path, comfyui_path, node_name_unique)
        start_persistence_sync(persistence_cfg, persistence_path, comfyui_path, node_name_unique)
        run_comfyui(
            comfyui_cfg.get("port", 8188),
            comfyui_cfg.get("launch_args", [])
        )
    
    return run_ui

num_instances = app_cfg.get('num_instances', 1)

if num_instances == 1:
    @app.function(
        name=node_name,
        max_containers=app_cfg.get("max_containers", 1),
        gpu=app_cfg.get("gpu_type", "T4"),
        volumes=volume_mounts,
        timeout=app_cfg.get("timeout", 3600),
        scaledown_window=app_cfg.get("scaledown_window", 3600),
        image=image
    )
    @modal.concurrent(max_inputs=app_cfg.get("concurrent_inputs", 100))
    @modal.web_server(comfyui_cfg.get("port", 8188), startup_timeout=300)
    def run_ui():
        restore_files(persistence_cfg, persistence_path, comfyui_path, node_name)
        start_persistence_sync(persistence_cfg, persistence_path, comfyui_path, node_name)
        run_comfyui(
            comfyui_cfg.get("port", 8188),
            comfyui_cfg.get("launch_args", [])
        )
elif num_instances <= 0:
    print(f"实例数量设置错误: 不能创建{num_instances}个实例")
else:
    for i in range(num_instances):
        create_comfy_instance(i)