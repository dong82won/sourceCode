import os
from tkinter import Tk, filedialog, messagebox, simpledialog
from urdf_parser import parse_urdf_values
from model_definition_generator import generate_sdf_content, generate_config_content
from file_manager import setup_folders, copy_resources

def run():
    root = Tk()
    root.withdraw()

    # 특정 시작 폴더 설정 (예: 현재 실행 중인 스크립트의 경로)
    start_dir = os.getcwd()
    # 또는 특정 절대 경로: start_dir = "/home/user/meshes"

    # 1. 입력 및 파일 선택
    model_name = simpledialog.askstring("모델 이름", "모델 이름을 입력하세요:", initialvalue="Default_Model_Name")
    if not model_name: return

    # initialdir 매개변수를 추가합니다.
    urdf_path = filedialog.askopenfilename(
        title="URDF 파일 선택",
        initialdir=start_dir, # 여기서 시작 폴더를 지정
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
        filetypes=[("Images", "*.png *.jpg")]
    )

    # # 1. 입력 및 파일 선택
    # model_name = simpledialog.askstring("모델 이름", "모델 이름을 입력하세요:", initialvalue="Default_Model_Name")
    # if not model_name: return

    # urdf_path = filedialog.askopenfilename(title="URDF 파일 선택", filetypes=[("URDF", "*.urdf")])
    # dae_path = filedialog.askopenfilename(title="DAE 파일 선택", filetypes=[("DAE", "*.dae")])
    # image_paths = filedialog.askopenfilenames(title="이미지 선택", filetypes=[("Images", "*.png *.jpg")])

    if not urdf_path or not dae_path: return

    # 2. 분석 및 데이터 생성
    data, error = parse_urdf_values(urdf_path)
    if error:
        messagebox.showerror("오류", error)
        return

    # 3. 폴더 준비 및 파일 복사
    base_dir, mesh_dir = setup_folders(model_name)
    copy_resources(dae_path, image_paths, mesh_dir)

    # 4. SDF 및 Config 파일 쓰기
    dae_name = os.path.basename(dae_path)
    with open(base_dir / "model.config", "w", encoding='utf-8') as f:
        f.write(generate_config_content(model_name))

    with open(base_dir / "model.sdf", "w", encoding='utf-8') as f:
        f.write(generate_sdf_content(model_name, dae_name, data))

    messagebox.showinfo("완료", f"'{model_name}'이 My_Gazebo_Model 폴더 내에 생성되었습니다.")

if __name__ == "__main__":
    run()