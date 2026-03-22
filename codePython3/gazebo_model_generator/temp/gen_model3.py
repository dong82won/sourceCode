import os
import shutil
import tkinter as tk
from tkinter import filedialog

def get_dae_file_path():
    """파일 선택 창을 띄워 .dae 파일 경로를 반환합니다."""
    root = tk.Tk()
    root.withdraw()  # 메인 윈도우 창 숨기기
    root.attributes('-topmost', True)  # 선택 창을 최상단에 띄우기

    file_path = filedialog.askopenfilename(
        initialdir=os.getcwd(),
        title="가제보 모델로 사용할 .dae 파일을 선택하세요",
        filetypes=(("Collada files", "*.dae"), ("All files", "*.*"))
    )
    root.destroy() # 사용 후 리소스 해제
    return file_path

def create_gazebo_model(parent_dir, model_name, dae_file_path):
    # 1. 경로 설정 (현재폴더/부모폴더/모델이름/meshes)
    current_working_dir = os.getcwd()
    model_root = os.path.join(current_working_dir, parent_dir, model_name)
    mesh_dir = os.path.join(model_root, "meshes")

    # 2. 계층형 폴더 생성
    os.makedirs(mesh_dir, exist_ok=True)
    print(f"\n[1/3] 디렉토리 생성 완료: {model_root}")

    # 3. DAE 파일 복사
    dest_dae_path = os.path.join(mesh_dir, "model.dae")
    try:
        shutil.copy(dae_file_path, dest_dae_path)
        print(f"[2/3] 파일 복사 완료: {dest_dae_path}")
    except Exception as e:
        print(f"❌ 파일 복사 중 오류 발생: {e}")
        return

    # 4. model.config 작성
    config_content = f"""<?xml version="1.0"?>
<model>
  <name>{model_name}</name>
  <version>1.0</version>
  <sdf version="1.6">model.sdf</sdf>
  <author>
    <name>Gemini_Auto_Gen</name>
    <email>robot@creator.com</email>
  </author>
  <description>Auto-generated model from {os.path.basename(dae_file_path)}</description>
</model>
"""

    # 5. model.sdf 작성
    sdf_content = f"""<?xml version="1.0" ?>
<sdf version="1.6">
  <model name="{model_name}">
    <static>false</static>
    <link name="link">
      <inertial>
        <mass>1.0</mass>
        <inertia>
          <ixx>0.1</ixx><ixy>0</ixy><ixz>0</ixz>
          <iyy>0.1</iyy><iyz>0</iyz>
          <izz>0.1</izz>
        </inertia>
      </inertial>
      <collision name="collision">
        <geometry>
          <mesh>
            <uri>model://{model_name}/meshes/model.dae</uri>
          </mesh>
        </geometry>
      </collision>
      <visual name="visual">
        <geometry>
          <mesh>
            <uri>model://{model_name}/meshes/model.dae</uri>
          </mesh>
        </geometry>
      </visual>
    </link>
  </model>
</sdf>
"""

    # 6. 파일 저장
    with open(os.path.join(model_root, "model.config"), "w") as f:
        f.write(config_content)
    with open(os.path.join(model_root, "model.sdf"), "w") as f:
        f.write(sdf_content)

    print(f"[3/3] 설정 파일 작성 완료 (config, sdf)")
    print(f"\n✅ 성공: '{model_name}' 모델이 '{parent_dir}' 폴더 안에 생성되었습니다.")

# --- 실행부 ---
if __name__ == "__main__":
    # 1. 모델 이름 입력
    m_name = input("생성할 모델의 이름을 입력하세요 (예: my_robot): ").strip()
  
    if not m_name:
        print("모델 이름은 필수입니다.")
    else:
        # 2. 파일 선택 팝업창 실행
        print("파일 선택 창에서 .dae 파일을 선택해 주세요...")
        selected_path = get_dae_file_path()

        if selected_path:
            # 부모 폴더명을 원하는 대로 지정 (예: 'my_models_collection')
            create_gazebo_model("my_gazebo_collection", m_name, selected_path)
        else:
            print("파일 선택이 취소되었습니다.")