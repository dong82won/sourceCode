import os
import shutil
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

def generate_config_content(model_name, dae_filename):
    """model.config 파일의 XML 내용을 생성합니다."""
    return f"""<?xml version="1.0"?>
<model>
  <name>{model_name}</name>
  <version>1.0</version>
  <sdf version="1.6">model.sdf</sdf>
  <author>
    <name>LEE D.W</name>
    <email>2dongwon@gmail.com</email>
  </author>
  <description>Auto-generated from {dae_filename}</description>
</model>"""

def generate_sdf_content(model_name):
    """model.sdf 파일의 XML 내용을 생성합니다."""
    return f"""<?xml version="1.0" ?>
<sdf version="1.6">
  <model name="{model_name}">
    <static>false</static>
    <link name="link">
      <inertial>
        <mass>1.0</mass>
        <inertia>
          <ixx>0.01</ixx><ixy>0</ixy><ixz>0</ixz>
          <iyy>0.01</iyy><iyz>0</iyz>
          <izz>0.01</izz>
        </inertia>
      </inertial>
      <collision name="collision">
        <geometry>
          <mesh><uri>model://{model_name}/meshes/model.dae</uri></mesh>
        </geometry>
      </collision>
      <visual name="visual">
        <geometry>
          <mesh><uri>model://{model_name}/meshes/model.dae</uri></mesh>
        </geometry>
      </visual>
    </link>
  </model>
</sdf>"""

def get_files_path():
    """파일 선택 창을 통해 DAE와 텍스처 이미지 경로를 가져옵니다."""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    # 1. DAE 파일 (필수)
    dae_path = filedialog.askopenfilename(
        title="1. Select .dae file",
        filetypes=(("Collada files", "*.dae"), ("All files", "*.*"))
    )
    
    if not dae_path:
        root.destroy()
        return None, None

    texture_paths = filedialog.askopenfilenames(
        title="2. Select Texture files (Optional)",
        filetypes=(("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*"))
    )
    
    root.destroy()
    return dae_path, texture_paths

def create_gazebo_model(parent_dir, model_name, dae_file_path, texture_paths):
    # 1. 경로 설정
    model_root = os.path.join(os.getcwd(), parent_dir, model_name)
    mesh_dir = os.path.join(model_root, "meshes")
    texture_dir = os.path.join(model_root, "materials", "textures")

    if os.path.exists(model_root):
        print(f"❌ 오류: '{model_name}' 폴더가 이미 존재합니다.")
        return False

    # 2. 디렉토리 구조 생성
    try:
        os.makedirs(mesh_dir, exist_ok=True)
        os.makedirs(texture_dir, exist_ok=True)
        print(f"\n[1/4] 폴더 구조 생성 완료")
    except Exception as e:
        print(f"❌ 폴더 생성 실패: {e}")
        return False

    # 3. 파일 복사 (DAE & Textures)
    try:
        # DAE 복사
        shutil.copy(dae_file_path, os.path.join(mesh_dir, "model.dae"))
        # 텍스처 복사
        for t_path in texture_paths:
            shutil.copy(t_path, os.path.join(texture_dir, os.path.basename(t_path)))
        print(f"[2/4] 리소스 파일 복사 완료 (DAE + 이미지 {len(texture_paths)}개)")
    except Exception as e:
        print(f"❌ 파일 복사 중 오류 발생: {e}")
        return False

    # 4. 설정 파일(SDF, Config) 생성 - 분리된 함수 호출
    try:
        config_data = generate_config_content(model_name, os.path.basename(dae_file_path))
        sdf_data = generate_sdf_content(model_name)

        with open(os.path.join(model_root, "model.config"), "w", encoding="utf-8") as f:
            f.write(config_data)
        with open(os.path.join(model_root, "model.sdf"), "w", encoding="utf-8") as f:
            f.write(sdf_data)
        print(f"[3/4] XML 설정 파일 생성 완료")
    except Exception as e:
        print(f"❌ 설정 파일 작성 중 오류 발생: {e}")
        return False

    print(f"\n✅ 완료: '{model_name}' 모델이 성공적으로 생성되었습니다!")
    print(f"📍 위치: {model_root}")
    return True

if __name__ == "__main__":
    TARGET_DIR = "my_models"
    
    model_name_input = input("생성할 모델의 이름을 입력하세요: ").strip()
    if not model_name_input:
        print("이름이 입력되지 않았습니다.")
        sys.exit()

    dae_file, textures = get_files_path()
    
    if dae_file:
        create_gazebo_model(TARGET_DIR, model_name_input, dae_file, textures)
    else:
        print("파일 선택이 취소되었습니다.")