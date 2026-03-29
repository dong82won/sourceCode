import os
import shutil
from pathlib import Path
from tkinter import Tk, filedialog, messagebox, simpledialog

def create_gazebo_model_gui():
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

    image_paths = filedialog.askopenfilenames(title="이미지 파일들 선택 (다중 선택 가능)", 
                                            filetypes=[("Image files", "*.png *.jpg *.jpeg")])

    # 3. 가제보 폴더 계층 구조 생성
    # 구조: model_name/ (meshes/, materials/scripts/, materials/textures/)
    base_dir = Path(model_name)
    mesh_dir = base_dir / "meshes"
    script_dir = base_dir / "materials" / "scripts"
    texture_dir = base_dir / "materials" / "textures"

    for directory in [mesh_dir, script_dir, texture_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    # 4. 파일 복사 (DAE 경로는 수정하지 않음)
    dae_filename = os.path.basename(dae_path)
    shutil.copy2(dae_path, mesh_dir / dae_filename)

    image_filenames = []
    for img in image_paths:
        fname = os.path.basename(img)
        shutil.copy2(img, texture_dir / fname)
        image_filenames.append(fname)

    # 5. model.config 생성
    with open(base_dir / "model.config", "w", encoding='utf-8') as f:
        f.write(f'''<?xml version="1.0"?>
<model>
  <name>{model_name}</name>
  <version>1.0</version>
  <sdf version="1.6">model.sdf</sdf>
  <author><name>Gemini_GUI_Builder</name></author>
  <description>Auto-generated Gazebo model hierarchy.</description>
</model>''')

    # 6. model.sdf 생성 (제공된 URDF 수치 반영 )
    # Inertia: ixx="0.00296", iyy="0.00287", izz="0.00582" 
    # Mass: 0.10000 
    # Collision Box Size: 0.02718 0.59563 0.58630 
    sdf_content = f'''<?xml version="1.0" ?>
<sdf version="1.6">
  <model name="{model_name}">
    <link name="base_link">
      <inertial>
        <pose>-0.00006 -0.00001 -0.00024 0.00000 0.00000 0.00000</pose>
        <mass>0.10000</mass>
        <inertia>
          <ixx>0.00296</ixx><ixy>0</ixy><ixz>0</ixz>
          <iyy>0.00287</iyy><iyz>0</iyz>
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
        <material>
          <script>
            <uri>model://{model_name}/materials/scripts</uri>
            <name>{model_name}/Material</name>
          </script>
        </material>
      </visual>
    </link>
  </model>
</sdf>'''
    with open(base_dir / "model.sdf", "w", encoding='utf-8') as f:
        f.write(sdf_content)

    # 7. .material 스크립트 생성 (첫 번째 이미지 기준)
    tex_line = f"texture {image_filenames[0]}" if image_filenames else ""
    with open(script_dir / f"{model_name}.material", "w", encoding='utf-8') as f:
        f.write(f'''material {model_name}/Material
{{
  technique
  {{
    pass
    {{
      ambient 1 1 1 1
      diffuse 1 1 1 1
      texture_unit
      {{
        {tex_line}
      }}
    }}
  }}
}}''')

    messagebox.showinfo("성공", f"'{model_name}' 모델의 계층 구조 생성이 완료되었습니다!")

if __name__ == "__main__":
    create_gazebo_model_gui()