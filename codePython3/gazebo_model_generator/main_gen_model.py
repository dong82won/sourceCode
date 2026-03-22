import os
import shutil
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

# content.py 파일에서 함수 임포트
from content import generate_config_content, generate_sdf_content

def get_files_path():
    """파일 선택 창을 통해 DAE와 텍스처 이미지 경로를 가져옵니다."""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    # 1. DAE 파일 (필수)
    dae_path = filedialog.askopenfilename(
        title="1. Select .dae file (Required)",
        filetypes=(("Collada files", "*.dae"), ("All files", "*.*"))
    )
    if not dae_path:
        root.destroy()
        return None, None

    # 2. 텍스처 파일 (선택 사항: 취소 시 빈 튜플 반환)
    texture_paths = filedialog.askopenfilenames(
        title="2. Select Texture files (Optional - Press Cancel if none)",
        filetypes=(("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*"))
    )
    root.destroy()
    return dae_path, texture_paths

def create_gazebo_model(parent_dir, model_name, dae_file_path, texture_paths):
    #1 경로 설정
    model_root = os.path.join(os.getcwd(), parent_dir, model_name)
    mesh_dir = os.path.join(model_root, "meshes")
    texture_dir = os.path.join(model_root, "materials", "textures")

    if os.path.exists(model_root):
        print(f"❌ 오류: '{model_name}' 폴더가 이미 존재합니다.")
        return False

    # 2. 폴더 생성
    os.makedirs(mesh_dir, exist_ok=True)
    os.makedirs(texture_dir, exist_ok=True)

    # 3. 파일 복사 (DAE & Textures)
    try:
        # DAE 복사
        shutil.copy(dae_file_path, os.path.join(mesh_dir, "model.dae"))
        
        # 텍스처 파일이 있을 때만 복사 수행
        if texture_paths:
            for t_path in texture_paths:
                shutil.copy(t_path, os.path.join(texture_dir, os.path.basename(t_path)))
            print(f"📂 리소스 복사 완료 (이미지 {len(texture_paths)}개)")
        else:
            print("ℹ️ 텍스처 파일이 선택되지 않아 건너뜁니다.")
            
    except Exception as e:
        print(f"❌ 복사 중 오류: {e}")
        return False

    # 4. 설정 파일(SDF, Config) 생성 - dae_file_path(원본 경로) 전달
    try:
        config_data = generate_config_content(model_name, os.path.basename(dae_file_path))
        # 수정: 원본 DAE 경로를 함께 전달하여 사이즈를 분석함
        sdf_data = generate_sdf_content(model_name, dae_file_path)

        with open(os.path.join(model_root, "model.config"), "w", encoding="utf-8") as f:
            f.write(config_data)
        with open(os.path.join(model_root, "model.sdf"), "w", encoding="utf-8") as f:
            f.write(sdf_data)
        print(f"📄 설정 파일 생성 완료")
    except Exception as e:
        print(f"❌ 파일 쓰기 오류: {e}")
        return False

    print(f"\n✅ '{model_name}' 생성 성공!")
    return True


if __name__ == "__main__":
    TARGET_DIR = "my_gazebo_models"

    model_name_input = input("생성할 모델의 이름을 입력하세요: ").strip()
    if not model_name_input:
        print("이름이 입력되지 않았습니다.")
        sys.exit()

    dae_file, textures = get_files_path()

    if dae_file:
        create_gazebo_model(TARGET_DIR, model_name_input, dae_file, textures)
    else:
        print("파일 선택이 취소되었습니다.")
