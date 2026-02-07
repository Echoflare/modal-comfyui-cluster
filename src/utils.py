import subprocess
import time
import os
from pathlib import Path

def link_file_to_comfyui(source_path, target_path):
    src_root = Path(source_path).resolve()
    dst_root = Path(target_path).resolve()

    if not src_root.exists():
        print(f"源路径 {src_root} 不存在，跳过链接。")
        return

    print(f"开始递归同步数据: {src_root} -> {dst_root}")

    for root, dirs, files in os.walk(src_root):
        current_src_dir = Path(root)
        relative_path = current_src_dir.relative_to(src_root)
        
        current_dst_dir = dst_root / relative_path

        if not current_dst_dir.exists():
            current_dst_dir.mkdir(parents=True, exist_ok=True)

        for file_name in files:
            src_file = current_src_dir / file_name
            dst_file = current_dst_dir / file_name

            if dst_file.is_symlink():
                continue

            if dst_file.exists():
                print(f"警告: 实体文件已存在，跳过: {dst_file}")
                continue

            try:
                os.symlink(src_file, dst_file)
                print(f"已链接: {relative_path / file_name}")
            except Exception as e:
                print(f"链接创建失败 {dst_file}: {e}")

def run_comfyui(port, args):
    cmd = f"comfy launch -- --listen 0.0.0.0 --port {str(port)} {' '.join(args)}"
    
    print(f"启动ComfyUI: {cmd}")
    subprocess.Popen(cmd, shell=True)