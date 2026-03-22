import os
import shutil
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

def get_files_path():
    """파일 선택 창을 띄워 .dae 파일과 이미지 파일을 선택합니다."""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    # 1. DAE 파일 선택
    dae_path = filedialog.askopenfilename(
        initialdir=os.getcwd(),
        title="1. Select .dae file for Gazebo",
        filetypes=(("Collada files", "*.dae"), ("All files", "*.*"))
    )
    
    if not dae_path:
        root.destroy()
        return None, None

    # 2. 이미지 파일 선택 (여러 개 선택 가능)
    texture_paths = filedialog.askopenfilenames(
        initialdir=os.path.dirname(dae_path),
        title="2. Select Texture files (PNG/JPG) - Cancel if none",
        filetypes=(("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*"))
    )
    
    root.destroy()
    return dae_path, texture_paths

def create_gazebo_model(parent_dir, model_name, dae_file_path, texture_paths):
    # 1. 경로 설정
    current_working_dir = os.getcwd()
    model_root = os.path.join(current_working_dir, parent_dir, model_name)

    if os.path.exists(model_root):
        print(f"\n❌ 오류: '{model_name}'이 이미 존재합니다.")
        return False

    # 상세 경로 정의
    mesh_dir = os.path.join(model_root, "meshes")
    texture_dir = os.path.join(model_root, "materials", "textures")

    # 2. 폴더 생성 (materials/textures 포함)
    try:
        os.makedirs(mesh_dir, exist_ok=True)
        os.makedirs(texture_dir, exist_ok=True) # 신규 추가
        print(f"\n[1/4] 디렉토리 구조 생성 완료: {model_root}")
    except Exception as e:
        print(f"❌ 폴더 생성 실패: {e}")
        return False

    # 3. DAE 파일 복사
    dest_dae_path = os.path.join(mesh_dir, "model.dae")
    try:
        shutil.copy(dae_file_path, dest_dae_path)
        print(f"[2/4] DAE 파일 복사 완료")
    except Exception as e:
        print(f"❌ DAE 복사 오류: {e}")
        return False

    # 4. 텍스처 파일 복사 (신규 추가)
    if texture_paths:
        try:
            for t_path in texture_paths:
                shutil.copy(t_path, os.path.join(texture_dir, os.path.basename(t_path)))
            print(f"[3/4] 텍스처 파일 {len(texture_paths)}개 복사 완료")
        except Exception as e:
            print(f"❌ 텍스처 복사 오류: {e}")

    # 5. 설정 파일 작성 (SDF/Config)
    config_content = f"""<?xml version="1.0"?>
<model>
  <name>{model_name}</name>
  <version>1.0</version>
  <sdf version="1.6">model.sdf</sdf>
  <author>
   <name>LEE D.W.</name>
   <email>2dongwon@gmail.com</email>
   </author>
  <description>Auto-generated with textures</description>
</model>"""

    sdf_content = f"""<?xml version="1.0" ?>
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

    try:
        with open(os.path.join(model_root, "model.config"), "w") as f: f.write(config_content)
        with open(os.path.join(model_root, "model.sdf"), "w") as f: f.write(sdf_content)
        print(f"[4/4] 설정 파일 작성 완료")
    except Exception as e:
        print(f"❌ 파일 쓰기 오류: {e}")
        return False

    print(f"\n✅ 성공: '{model_name}' 모델 생성 완료!")
    return True

if __name__ == "__main__":
    p_dir = "my_models"
    m_name = input("생성할 모델의 이름을 입력하세요: ").strip()

    if not m_name:
        sys.exit()
        
    selected_dae, selected_textures = get_files_path()
    if selected_dae:
        create_gazebo_model(p_dir, m_name, selected_dae, selected_textures)
    else:
        print("작업이 취소되었습니다.")