import os
import shutil
from pathlib import Path

def setup_folders(model_name):
    base_dir = Path("My_Gazebo_Model") / model_name
    mesh_dir = base_dir / "meshes"
    mesh_dir.mkdir(parents=True, exist_ok=True)
    return base_dir, mesh_dir

def copy_resources(dae_path, image_paths, dest_dir):
    shutil.copy2(dae_path, dest_dir / os.path.basename(dae_path))
    for img in image_paths:
        shutil.copy2(img, dest_dir / os.path.basename(img))