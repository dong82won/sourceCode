import os
import shutil
from pathlib import Path

def setup_folders(model_name):
    base_dir = Path("My_Gazebo_Model") / model_name
    mesh_dir = base_dir / "meshes"
    scripts_dir = base_dir / "materials" / "scripts"
    textures_dir = base_dir / "materials" / "textures"
    
    # 필요한 모든 폴더 생성
    mesh_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir.mkdir(parents=True, exist_ok=True)
    textures_dir.mkdir(parents=True, exist_ok=True)
    
    return base_dir, mesh_dir, scripts_dir, textures_dir

def copy_resources(dae_path, image_paths, mesh_dir, textures_dir):
    # DAE 파일은 meshes 폴더로 복사
    shutil.copy2(dae_path, mesh_dir / os.path.basename(dae_path))
    
    # 이미지 파일들은 textures 폴더로 복사
    for img in image_paths:
        shutil.copy2(img, textures_dir / os.path.basename(img))