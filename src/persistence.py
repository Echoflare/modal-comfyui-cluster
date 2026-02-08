import os
import shutil
import time
import hashlib
from pathlib import Path
from threading import Thread

def calculate_checksum(file_path):
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except FileNotFoundError:
        return None

def restore_files(file_list, persistence_root, comfyui_root, node_name):
    persist_dir = Path(persistence_root) / node_name
    comfy_dir = Path(comfyui_root)
    
    if not file_list: return
    
    for rel_path in file_list:
        src = persist_dir / rel_path
        dst = comfy_dir / rel_path
        
        if src.exists():
            if dst.exists():
                src_hash = calculate_checksum(src)
                dst_hash = calculate_checksum(dst)
                if src_hash == dst_hash:
                    continue
            
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
            
            print(f"恢复 ({node_name}): {src} -> {dst}")

def start_persistence_sync(file_list, persistence_root, comfyui_root, node_name, interval=10):
    def sync_loop():
        persist_dir = Path(persistence_root) / node_name
        comfy_dir = Path(comfyui_root)
        
        if not file_list: return
        
        while True:
            for rel_path in file_list:
                src = comfy_dir / rel_path
                dst = persist_dir / rel_path
                
                if src.exists():
                    if src.is_dir():
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        src_hash = calculate_checksum(src)
                        dst_hash = calculate_checksum(dst)
                        
                        if src_hash == dst_hash:
                            continue
                        else:
                            dst.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(src, dst)
                    
                    print(f"保存 ({node_name}): {src} -> {dst}", flush=True)
            
            time.sleep(interval)

    thread = Thread(target=sync_loop, daemon=True)
    thread.start()