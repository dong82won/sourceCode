import os

def create_gazebo_model(model_name, dae_file_path):
    # 1. 경로 설정 (기본 Gazebo 모델 경로)
    home = os.path.expanduser("~")
    model_root = os.path.join(home, ".gazebo/models", model_name)
    mesh_dir = os.path.join(model_root, "meshes")

    # 2. 폴더 생성
    os.makedirs(mesh_dir, exist_ok=True)
    print(f"Directory created: {model_root}")

    # 3. DAE 파일 복사 (선택 사항: 원본을 meshes 폴더로 이동/복사)
    # 여기서는 원본 파일 이름을 'model.dae'로 통일하여 관리하기 편하게 합니다.
    dest_dae_path = os.path.join(mesh_dir, "model.dae")
    import shutil
    try:
        shutil.copy(dae_file_path, dest_dae_path)
        print(f"File copied to: {dest_dae_path}")
    except Exception as e:
        print(f"Error copying file: {e}")
        return

    # 4. model.config 내용 작성
    config_content = f"""<?xml version="1.0"?>
<model>
  <name>{model_name}</name>
  <version>1.0</version>
  <sdf version="1.6">model.sdf</sdf>
  <author>
    <name>Auto Generated</name>
    <email>robot@creator.com</email>
  </author>
  <description>Auto-generated model from {os.path.basename(dae_file_path)}</description>
</model>
"""

    # 5. model.sdf 내용 작성 (기본 Inertia 포함)
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

    print(f"Successfully created Gazebo model: {model_name}")
    print("Restart Gazebo and check the 'Insert' tab.")

# --- 실행 부분 ---
if __name__ == "__main__":
    m_name = input("Enter model name (e.g., my_robot): ")
    d_path = input("Enter full path to .dae file: ").strip()

    if os.path.exists(d_path) and d_path.lower().endswith('.dae'):
        create_gazebo_model(m_name, d_path)
    else:
        print("Invalid file path. Please provide a valid .dae file.")