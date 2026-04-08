import os
from tkinter import Tk, filedialog, messagebox, simpledialog
from urdf_parser import parse_urdf_values
from dae_parser import extract_material_info
from model_definition_generator import (
    generate_sdf_content, 
    generate_config_content, 
    generate_material_content
)
from file_manager import setup_folders, copy_resources

def run():
    root = Tk()
    root.withdraw() 

    model_name = simpledialog.askstring("모델 생성", "모델 이름을 입력하세요:", initialvalue="wooden_pallet")
    if not model_name: return 

    urdf_p = filedialog.askopenfilename(title="URDF 파일 선택", filetypes=[("URDF", "*.urdf")])
    if not urdf_p: return

    dae_p = filedialog.askopenfilename(title="DAE 파일 선택", filetypes=[("DAE", "*.dae")])
    if not dae_p: return

    # 이미지는 선택 안 해도 진행 가능
    img_ps = filedialog.askopenfilenames(title="이미지 선택 (선택 사항)", filetypes=[("Images", "*.png *.jpg")])

    data, err = parse_urdf_values(urdf_p)
    if err: return messagebox.showerror("URDF 파싱 오류", err)

    mat_info = extract_material_info(dae_p)

    base, mesh, scripts, textures = setup_folders(model_name)
    copy_resources(dae_p, img_ps, mesh, textures)

    # 이미지가 없을 경우 none 처리
    img_n = os.path.basename(img_ps[0]) if img_ps else "none"
    dae_n = os.path.basename(dae_p)

    try:
        with open(scripts / f"{model_name}.material", "w", encoding='utf-8') as f:
            f.write(generate_material_content(mat_info, img_n))

        with open(base / "model.sdf", "w", encoding='utf-8') as f:
            f.write(generate_sdf_content(model_name, dae_n, data))

        with open(base / "model.config", "w", encoding='utf-8') as f:
            f.write(generate_config_content(model_name))

        messagebox.showinfo("성공", f"'{model_name}' 모델이 성공적으로 생성되었습니다.\n위치: {base}")

    except Exception as e:
        messagebox.showerror("파일 저장 오류", f"파일 생성 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    run()