import os
import shutil

def create_gazebo_model(parent_dir, model_name, dae_file_path):
    # 1. 경로 설정: 부모 폴더/모델 이름/meshes
    model_root = os.path.join(os.getcwd(), parent_dir, model_name)
    mesh_dir = os.path.join(model_root, "meshes")

    # 2. 폴더 생성 (parents=True로 부모 폴더까지 한 번에 생성)
    os.makedirs(mesh_dir, exist_ok=True)
    
    # 3. DAE 파일 복사
    dest_dae_path = os.path.join(mesh_dir, "model.dae")
    try:
        shutil.copy(dae_file_path, dest_dae_path)
    except Exception as e:
        print(f"Error copying file: {e}")
        return

    # 4. model.config & 5. model.sdf 작성 (기존 로직과 동일)
    config_content = f"""<?xml version="1.0"?><model><name>{model_name}</name><version>1.0</version><sdf version="1.6">model.sdf</sdf><description>Generated</description></model>"""

    sdf_content = f"""<?xml version="1.0" ?>
<sdf version="1.6">
  <model name="{model_name}">
    <static>false</static>
    <link name="link">
      <visual name="visual">
        <geometry><mesh><uri>model://{model_name}/meshes/model.dae</uri></mesh></geometry>
      </visual>
      <collision name="collision">
        <geometry><mesh><uri>model://{model_name}/meshes/model.dae</uri></mesh></geometry>
      </collision>
    </link>
  </model>
</sdf>"""

    with open(os.path.join(model_root, "model.config"), "w") as f: f.write(config_content)
    with open(os.path.join(model_root, "model.sdf"), "w") as f: f.write(sdf_content)

    print(f"✅ Model '{model_name}' created inside '{parent_dir}/'")

if __name__ == "__main__":
    # 부모 폴더명을 'my_models' 등으로 지정하세요.
    p_dir = "my_models" 
    m_name = input("Enter model name: ")
    d_path = input("Enter .dae path: ").strip().strip("'").strip('"')

    if os.path.exists(d_path):
        create_gazebo_model(p_dir, m_name, d_path)
    else:
        print("Invalid path.")