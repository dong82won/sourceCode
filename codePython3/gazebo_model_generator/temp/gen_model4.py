import os
import shutil
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

def get_dae_file_path():
    """파일 선택 창을 띄워 .dae 파일 경로를 반환합니다."""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    file_path = filedialog.askopenfilename(
        initialdir=os.getcwd(),
        title="가제보 모델로 사용할 .dae 파일을 선택하세요",
        filetypes=(("Collada files", "*.dae"), ("All files", "*.*"))
    )
    root.destroy()
    return file_path

def create_gazebo_model(parent_dir, model_name, dae_file_path):
    # 1. 경로 설정
    current_working_dir = os.getcwd()
    model_root = os.path.join(current_working_dir, parent_dir, model_name)

    # [추가] 중복 폴더 체크 로직
    if os.path.exists(model_root):
        print(f"\n❌ 오류: '{parent_dir}' 폴더 안에 이미 '{model_name}' 폴더가 존재합니다.")
        # 팝업 알림 (선택 사항)
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("중복 오류", f"이미 존재하는 모델 이름입니다: {model_name}")
        root.destroy()
        return False # 생성 실패 반환

    mesh_dir = os.path.join(model_root, "meshes")

    # 2. 계층형 폴더 생성
    try:
        os.makedirs(mesh_dir)
        print(f"\n[1/3] 디렉토리 생성 완료: {model_root}")
    except Exception as e:
        print(f"❌ 폴더 생성 실패: {e}")
        return False

    # 3. DAE 파일 복사
    dest_dae_path = os.path.join(mesh_dir, "model.dae")
    try:
        shutil.copy(dae_file_path, dest_dae_path)
        print(f"[2/3] 파일 복사 완료: {dest_dae_path}")
    except Exception as e:
        print(f"❌ 파일 복사 오류: {e}")
        return False

    # 4. model.config & 5. model.sdf 작성
    config_content = f"""<?xml version="1.0"?>
<model>
  <name>{model_name}</name>
  <version>1.0</version>
  <sdf version="1.6">model.sdf</sdf>
  <author><name>Gemini_Auto_Gen</name><email>2dongwon@gmail.com</email></author>
  <description>Auto-generated from {os.path.basename(dae_file_path)}</description>
</model>"""

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

    print(f"[3/3] 설정 파일 작성 완료")
    print(f"\n✅ 성공: '{model_name}' 모델 생성이 완료되었습니다.")
    return True

# --- 실행부 ---
if __name__ == "__main__":
    p_dir = "my_models" # 부모 폴더 이름 ex)my_gazebo_collection
    m_name = input("생성할 모델의 이름을 입력하세요: ").strip()

    if not m_name:
        print("이름이 입력되지 않아 종료합니다.")
        sys.exit()

    # 파일 선택 전 중복 체크를 한 번 더 수행 (빠른 종료를 위해)
    if os.path.exists(os.path.join(os.getcwd(), p_dir, m_name)):
        print(f"❌ '{m_name}'은(는) 이미 존재하는 폴더입니다. 다른 이름을 사용하세요.")
        sys.exit()

    selected_path = get_dae_file_path()

    if selected_path:
        create_gazebo_model(p_dir, m_name, selected_path)
    else:
        print("파일 선택이 취소되었습니다.")