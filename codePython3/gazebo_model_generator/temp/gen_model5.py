import os
import shutil
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

def get_dae_file_path():
    """파일 선택 창을 띄워 .dae 파일 경로를 반환합니다."""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    file_path = filedialog.askopenfilename(
        initialdir=os.getcwd(),
        title="Select .dae file for Gazebo",
        filetypes=(("Collada files", "*.dae"), ("All files", "*.*"))
    )
    root.destroy()
    return file_path

def create_gazebo_model(parent_dir, model_name, dae_file_path):
    # 1. 경로 설정
    current_working_dir = os.getcwd()
    # 부모 폴더가 없을 경우를 대비해 상위 경로까지 포함하여 설정
    parent_path = os.path.join(current_working_dir, parent_dir)
    model_root = os.path.join(parent_path, model_name)

    # [추가] 중복 폴더 체크 로직
    if os.path.exists(model_root):
        print(f"\n❌ 오류: '{parent_dir}' 내에 '{model_name}'이 이미 존재합니다.")
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("중복 오류", f"이미 존재하는 모델 이름: {model_name}")
        root.destroy()
        return False

    mesh_dir = os.path.join(model_root, "meshes")

    # 2. 폴더 생성 (exist_ok=True와 parents=True 개념 적용)
    try:
        os.makedirs(mesh_dir, exist_ok=True)
        print(f"\n[1/3] 디렉토리 생성 완료: {model_root}")
    except Exception as e:
        print(f"❌ 폴더 생성 실패: {e}")
        return False

    # 3. DAE 파일 복사
    dest_dae_path = os.path.join(mesh_dir, "model.dae")
    try:
        shutil.copy(dae_file_path, dest_dae_path)
        print(f"[2/3] 파일 복사 완료")
    except Exception as e:
        print(f"❌ 파일 복사 오류: {e}")
        return False

    # 4. model.config 작성
    config_content = f"""<?xml version="1.0"?>
<model>
  <name>{model_name}</name>
  <version>1.0</version>
  <sdf version="1.6">model.sdf</sdf>
  <author><name>Gemini_Auto_Gen</name><email>2dongwon@gmail.com</email></author>
  <description>Auto-generated from {os.path.basename(dae_file_path)}</description>
</model>"""""

    # 5. model.sdf 작성 (Inertial 태그 추가 및 가독성 개선)
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
        print(f"[3/3] 설정 파일(SDF, Config) 작성 완료")
    except Exception as e:
        print(f"❌ 파일 쓰기 오류: {e}")
        return False

    print(f"\n✅ 성공: '{model_name}' 모델 생성 완료!")
    print(f"📍 위치: {model_root}")
    
    # print(f"📢 주의: Gazebo 실행 전 아래 명령어를 입력하세요:")
    # print(f"   export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:{parent_path}")
    return True

if __name__ == "__main__":
    p_dir = "my_models"
    m_name = input("생성할 모델의 이름을 입력하세요: ").strip()

    if not m_name:
        print("이름이 입력되지 않아 종료합니다.")
        sys.exit()

    full_parent_path = os.path.join(os.getcwd(), p_dir)
    if os.path.exists(os.path.join(full_parent_path, m_name)):
        print(f"❌ '{m_name}'은(는) 이미 존재하는 폴더입니다.")
        sys.exit()

    selected_path = get_dae_file_path()
    if selected_path:
        create_gazebo_model(p_dir, m_name, selected_path)
    else:
        print("파일 선택이 취소되었습니다.")