import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from tkinter import Tk, filedialog, messagebox, simpledialog

def parse_urdf_values(urdf_path):
    """URDF 파일에서 SDF 생성에 필요한 수치들을 안전하게 추출합니다."""
    try:
        tree = ET.parse(urdf_path)
        root = tree.getroot()

        # 1. link 태그 탐색 (네임스페이스 무시를 위해 .// 사용)
        link = root.find('.//link')
        if link is None:
            return None, "URDF 내에서 <link> 태그를 찾을 수 없습니다."

        # Helper: URDF origin(xyz, rpy)을 SDF pose(x y z r p y) 문자열로 변환
        def get_pose(element):
            if element is None: return "0 0 0 0 0 0"
            origin = element.find('origin')
            if origin is None: return "0 0 0 0 0 0"
            xyz = origin.get('xyz', '0 0 0')
            rpy = origin.get('rpy', '0 0 0')
            return f"{xyz} {rpy}"

        # 2. Inertial 데이터 추출 (태그가 없을 경우 기본값 할당)
        inertial = link.find('inertial')
        mass_val = "0.1"
        ixx=ixy=ixz=iyy=iyz=izz = "0.01"
        i_pose = "0 0 0 0 0 0"

        if inertial is not None:
            mass_tag = inertial.find('mass')
            if mass_tag is not None: mass_val = mass_tag.get('value', '0.1')
            i_pose = get_pose(inertial)
            inertia = inertial.find('inertia')
            if inertia is not None:
                ixx = inertia.get('ixx', '0.01')
                ixy = inertia.get('ixy', '0.0')
                ixz = inertia.get('ixz', '0.0')
                iyy = inertia.get('iyy', '0.01')
                iyz = inertia.get('iyz', '0.0')
                izz = inertia.get('izz', '0.01')

        # 3. Collision 데이터 추출 (Box 기준)
        collision = link.find('collision')
        c_pose, c_size = "0 0 0 0 0 0", "1 1 1"
        if collision is not None:
            c_pose = get_pose(collision)
            box = collision.find('geometry/box')
            if box is not None: c_size = box.get('size', '1 1 1')

        # 4. Visual 데이터 추출
        visual = link.find('visual')
        v_pose = get_pose(visual)

        return {
            "mass": mass_val,
            "i_pose": i_pose,
            "inertia": {"ixx": ixx, "ixy": ixy, "ixz": ixz, "iyy": iyy, "iyz": iyz, "izz": izz},
            "c_pose": c_pose,
            "c_size": c_size,
            "v_pose": v_pose
        }, None
    except Exception as e:
        return None, f"파일 분석 오류: {str(e)}"

def create_integrated_gazebo_model():
    root_gui = Tk()
    root_gui.withdraw()

    # 1. 모델 이름 및 파일 선택
    model_name = simpledialog.askstring("모델 이름", "생성할 가제보 모델 이름을 입력하세요:", initialvalue="body_weight")
    if not model_name: return

    urdf_path = filedialog.askopenfilename(title="URDF 파일 선택", filetypes=[("URDF files", "*.urdf")])
    if not urdf_path: return

    dae_path = filedialog.askopenfilename(title="DAE(Mesh) 파일 선택", filetypes=[("DAE files", "*.dae")])
    if not dae_path: return

    image_paths = filedialog.askopenfilenames(title="이미지 파일 선택 (meshes 폴더로 복사)", filetypes=[("Images", "*.png *.jpg *.jpeg")])

    # 2. URDF 수치 추출 수행
    data, error = parse_urdf_values(urdf_path)

    # [CRITICAL] data가 None인지 명확히 체크하여 에러 방지
    if error or data is None:
        messagebox.showerror("오류", f"URDF 분석 중 에러 발생: {error}")
        return

    # 3. 폴더 구조 생성 (현재 폴더/3d_model/이름/meshes)
    current_dir = Path(os.getcwd())
    base_dir = current_dir / "3d_model" / model_name
    mesh_dir = base_dir / "meshes"
    mesh_dir.mkdir(parents=True, exist_ok=True)

    # 4. 파일 복사
    dae_filename = os.path.basename(dae_path)
    shutil.copy2(dae_path, mesh_dir / dae_filename)
    for img in image_paths:
        shutil.copy2(img, mesh_dir / os.path.basename(img))

    # 5. model.config 생성
    with open(base_dir / "model.config", "w", encoding='utf-8') as f:
        f.write(f'<?xml version="1.0"?>\n<model>\n  <name>{model_name}</name>\n  <version>1.0</version>\n  <sdf version="1.6">model.sdf</sdf>\n  <author><name>Gemini_Auto_Builder</name></author>\n</model>')

    # 6. model.sdf 생성 (추출된 수치 동적 적용)
    sdf_content = f'''<?xml version="1.0" ?>
<sdf version="1.6">
  <model name="{model_name}">
    <link name="base_link">
      <inertial>
        <pose>{data['i_pose']}</pose>
        <mass>{data['mass']}</mass>
        <inertia>
          <ixx>{data['inertia']['ixx']}</ixx>
          <ixy>{data['inertia']['ixy']}</ixy>
          <ixz>{data['inertia']['ixz']}</ixz>
          <iyy>{data['inertia']['iyy']}</iyy>
          <iyz>{data['inertia']['iyz']}</iyz>
          <izz>{data['inertia']['izz']}</izz>
        </inertia>
      </inertial>
      <collision name="collision">
        <pose>{data['c_pose']}</pose>
        <geometry>
          <box><size>{data['c_size']}</size></box>
        </geometry>
      </collision>
      <visual name="visual">
        <pose>{data['v_pose']}</pose>
        <geometry>
          <mesh><uri>model://{model_name}/meshes/{dae_filename}</uri></mesh>
        </geometry>
      </visual>
    </link>
  </model>
</sdf>'''

    with open(base_dir / "model.sdf", "w", encoding='utf-8') as f:
        f.write(sdf_content)

    messagebox.showinfo("완료", f"'{model_name}' 모델 생성 완료!\n경로: {base_dir.absolute()}")

if __name__ == "__main__":
    create_integrated_gazebo_model()