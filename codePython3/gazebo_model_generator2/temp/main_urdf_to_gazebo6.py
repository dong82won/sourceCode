import os
import shutil
import glob
from pathlib import Path

def main():
    # 1. 실행 폴더에서 파일 찾기
    urdf_files = glob.glob("*.urdf")
    dae_files = glob.glob("*.dae")
    png_files = glob.glob("*.png")

    if not urdf_files or not dae_files:
        print("❌ 에러: 폴더 내에 .urdf 또는 .dae 파일이 없습니다.")
        return

    # 모델 이름 설정 (URDF 파일명 기준)
    model_name = os.path.splitext(urdf_files[0])[0]
    base_path = Path(model_name)
    
    print(f"🚀 모델 생성 시작: {model_name}")

    # 2. 폴더 구조 생성
    mesh_dir = base_path / "meshes"
    tex_dir = base_path / "materials" / "textures"
    script_dir = base_path / "materials" / "scripts"

    for d in [mesh_dir, tex_dir, script_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # 3. 파일 복사 (DAE 경로 수정 로직 제거)
    target_dae = dae_files[0]
    shutil.copy2(target_dae, mesh_dir / target_dae)
    print(f"  [Mesh] 복사 완료 (수정 없음): {target_dae}")

    # PNG 모든 파일 복사
    for png in png_files:
        shutil.copy2(png, tex_dir / png)
        print(f"  [Texture] 복사 완료: {png}")

    # 4. model.config 생성
    with open(base_path / "model.config", "w", encoding='utf-8') as f:
        f.write(f'''<?xml version="1.0"?>
<model>
  <name>{model_name}</name>
  <version>1.0</version>
  <sdf version="1.6">model.sdf</sdf>
  <author><name>Gemini_Auto</name></author>
  <description>Auto-generated from local files (Original DAE)</description>
</model>''')

    # 5. model.sdf 생성 (요청하신 정확한 수치 적용)
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
          <mesh><uri>model://{model_name}/meshes/{target_dae}</uri></mesh>
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
    with open(base_path / "model.sdf", "w", encoding='utf-8') as f:
        f.write(sdf_content)

    # 6. .material 생성 (첫 번째 PNG 기준)
    tex_line = f"texture {png_files[0]}" if png_files else ""
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

    print(f"\n✅ 완료: '{model_name}' 모델 폴더가 생성되었습니다.")

if __name__ == "__main__":
    main()