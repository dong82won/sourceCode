import os
import shutil
from pathlib import Path
from tkinter import Tk, filedialog, messagebox, simpledialog

def create_simple_gazebo_model():
    # GUI 초기화 (창 숨기기)
    root = Tk()
    root.withdraw()

    # 1. 모델 이름 입력
    model_name = simpledialog.askstring("모델 이름", "생성할 가제보 모델 이름을 입력하세요:", initialvalue="body_weight")
    if not model_name:
        return

    # 2. 파일 선택 (URDF, DAE, Images)
    urdf_path = filedialog.askopenfilename(title="URDF 파일 선택", filetypes=[("URDF files", "*.urdf")])
    if not urdf_path: return

    dae_path = filedialog.askopenfilename(title="DAE(Mesh) 파일 선택", filetypes=[("DAE files", "*.dae")])
    if not dae_path: return

    # 이미지 파일 선택 (선택 사항)
    image_paths = filedialog.askopenfilenames(title="이미지 파일들 선택 (모두 meshes 폴더로 복사됨)", 
                                            filetypes=[("Image files", "*.png *.jpg *.jpeg")])

    # 3. 폴더 구조 생성 (materials 폴더 제외)
    base_dir = Path(model_name)
    mesh_dir = base_dir / "meshes"
    mesh_dir.mkdir(parents=True, exist_ok=True)

    # 4. 파일 복사 (모든 리소스를 meshes 폴더에 저장)
    dae_filename = os.path.basename(dae_path)
    shutil.copy2(dae_path, mesh_dir / dae_filename)

    for img in image_paths:
        fname = os.path.basename(img)
        shutil.copy2(img, mesh_dir / fname)

    # 5. model.config 생성
    with open(base_dir / "model.config", "w", encoding='utf-8') as f:
        f.write(f'''<?xml version="1.0"?>
<model>
  <name>{model_name}</name>
  <version>1.0</version>
  <sdf version="1.6">model.sdf</sdf>
  <author><name>Gemini_Simple_Builder</name></author>
  <description>Integrated mesh and texture model.</description>
</model>''')

    # 6. model.sdf 생성 (요구사항 반영: material 태그 제외)
    # URDF 데이터 기반 수치 적용 
    sdf_content = f'''<?xml version="1.0" ?>
<sdf version="1.6">
  <model name="{model_name}">
    <link name="base_link">
      <inertial>
        <pose>-0.00006 -0.00001 -0.00024 0.00000 0.00000 0.00000</pose>
        <mass>0.10000</mass>
        <inertia>
          <ixx>0.00296</ixx><ixy>-0.00000</ixy><ixz>0.00000</ixz>
          <iyy>0.00287</iyy><iyz>0.00000</iyz>
          <izz>0.00582</izz>
        </inertia>
      </inertial>
      <collision name="collision">
        <pose>-0.00006 -0.00001 -0.00024 3.14159 -1.57080 0.00000</pose>
        <geometry>
          <box><size>0.02718 0.59563 0.58630</size></box>
        </geometry>
      </collision>
      <visual name="visual">
        <pose>0.00000 0.00000 0.00000 3.14159 -1.57080 0.00000</pose>
        <geometry>
          <mesh><uri>model://{model_name}/meshes/{dae_filename}</uri></mesh>
        </geometry>
        </visual>
    </link>
  </model>
</sdf>'''
    
    with open(base_dir / "model.sdf", "w", encoding='utf-8') as f:
        f.write(sdf_content)

    messagebox.showinfo("완료", f"'{model_name}' 모델이 성공적으로 생성되었습니다.\n모든 파일은 {model_name}/meshes/ 폴더에 저장되었습니다.")

if __name__ == "__main__":
    create_simple_gazebo_model()