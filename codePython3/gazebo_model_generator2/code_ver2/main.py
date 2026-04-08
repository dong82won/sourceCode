import os
from tkinter import Tk, filedialog, messagebox, simpledialog
from ver2.urdf_parser import parse_urdf_values
from ver2.model_definition_generator import generate_sdf_content, generate_config_content, generate_material_content
from ver2.file_manager import setup_folders, copy_resources

def run():
    root = Tk()
    root.withdraw()

    start_dir = os.getcwd()

    # 1. 입력 및 파일 선택
    model_name = simpledialog.askstring("모델 이름", "모델 이름을 입력하세요:", initialvalue="Default_Model_Name")
    if not model_name: return

    urdf_path = filedialog.askopenfilename(
        title="URDF 파일 선택",
        initialdir=start_dir,
        filetypes=[("URDF", "*.urdf")]
    )

    dae_path = filedialog.askopenfilename(
        title="DAE 파일 선택",
        initialdir=start_dir,
        filetypes=[("DAE", "*.dae")]
    )

    image_paths = filedialog.askopenfilenames(
        title="이미지 선택",
        initialdir=start_dir,
        filetypes=[("Images", "*.png *.jpg *.jpeg")]
    )

    if not urdf_path or not dae_path: return

    # 2. 분석 및 데이터 생성
    data, error = parse_urdf_values(urdf_path)
    if error:
        messagebox.showerror("오류", error)
        return

    # 3. 폴더 준비 및 파일 복사 (스크립트 및 텍스처 폴더 추가)
    base_dir, mesh_dir, scripts_dir, textures_dir = setup_folders(model_name)
    copy_resources(dae_path, image_paths, mesh_dir, textures_dir)

    # 첫 번째 이미지 이름을 가져옴 (단일 텍스처 매핑용)
    image_filename = os.path.basename(image_paths[0]) if image_paths else None
    dae_name = os.path.basename(dae_path)

    # 4. 파일 쓰기 (.material, .config, .sdf)
    if image_filename:
        # .material 스크립트 파일 생성
        with open(scripts_dir / f"{model_name}.material", "w", encoding='utf-8') as f:
            f.write(generate_material_content(model_name, image_filename))

    with open(base_dir / "model.config", "w", encoding='utf-8') as f:
        f.write(generate_config_content(model_name))

    with open(base_dir / "model.sdf", "w", encoding='utf-8') as f:
        # SDF 생성 시 image_filename을 넘겨 material 태그를 구성하도록 함
        f.write(generate_sdf_content(model_name, dae_name, data, image_filename))

    messagebox.showinfo("완료", f"'{model_name}'이(가) My_Gazebo_Model 폴더 내에 성공적으로 생성되었습니다.")

if __name__ == "__main__":
    run()