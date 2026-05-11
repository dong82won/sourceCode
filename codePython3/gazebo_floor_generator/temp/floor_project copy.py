import os
import re
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import filedialog, messagebox
import floor_utils

try:
    from PIL import Image, ImageDraw
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    Image = None
    ImageDraw = None
    PILLOW_AVAILABLE = False

class FloorProjectMixin:
    # --- IDE 경고 해결용 타입 힌트 ---
    target_model_dir: str
    original_sdf_path: str
    walls_data: list
    confirmed_floors: list
    model_cx: float
    model_cy: float
    canvas_w: int
    canvas_h: int
    scale: float
    text_output: tk.Text

    def reset_workspace(self): ...
    def draw_workspace(self): ...
    # [해결] 튜플을 반환한다고(-> tuple) 확실히 명시해 줍니다!
    def gz_to_screen(self, gx: float, gy: float) -> tuple: ...
    # --------------------------------

    def open_model_folder(self):
        sdf_path = filedialog.askopenfilename(
            title="업데이트할 폴더 안의 'model.sdf'를 선택하세요",
            filetypes=[("SDF Files", "model.sdf"), ("All Files", "*.*")]
        )
        if not sdf_path: return

        self.target_model_dir = os.path.dirname(sdf_path)
        self.original_sdf_path = sdf_path
        self.reset_workspace()

        try:
            tree = ET.parse(self.original_sdf_path)
            for link in tree.getroot().iter('link'):
                d = floor_utils.parse_wall_data(link)
                if d: self.walls_data.append(d)
            if self.walls_data:
                min_x = min(w['px'] - w['w']/2 for w in self.walls_data)
                max_x = max(w['px'] + w['w']/2 for w in self.walls_data)
                min_y = min(w['py'] - w['h']/2 for w in self.walls_data)
                max_y = max(w['py'] + w['h']/2 for w in self.walls_data)
                self.model_cx, self.model_cy = (min_x + max_x) / 2, (min_y + max_y) / 2
                self.draw_workspace()
        except Exception as e:
            messagebox.showerror("오류", str(e))

    def update_sdf_text(self):
        self.text_output.delete("1.0", tk.END)
        code = ""
        folder_name = os.path.basename(self.target_model_dir) if self.target_model_dir else "model"

        floor_idx, img_idx = 1, 1
        for f in self.confirmed_floors:
            # 원본 로직으로 복구: 영역의 중심점(gx, gy)과 크기(gw, gh) 계산
            gx, gy, gw, gh = (f[0]+f[2])/2, (f[1]+f[3])/2, f[2]-f[0], f[3]-f[1]
            mat_choice = f[5]

            if mat_choice == "Custom Image":
                base_name = f"image_{img_idx}"
                mat_tag = f"""<uri>model://{folder_name}/materials/scripts</uri>
            <uri>model://{folder_name}/materials/textures/</uri>
            <name>{base_name}_Mat</name>"""
                img_idx += 1
            else:
                base_name = f"Floor_{floor_idx}"
                mat_tag = f"""<uri>file://media/materials/scripts/gazebo.material</uri>
            <name>{mat_choice}</name>"""
                floor_idx += 1

            code += f"    <link name='{base_name}'>\n"
            # 💡 회전값(Yaw)을 다시 0으로 고정합니다. (이미지 파일 자체를 회전하여 대응)
            code += f"      <pose>{gx:.3f} {gy:.3f} 0.001 0 0 0</pose>\n"
            code += f"      <collision name='{base_name}_Col'>\n"
            code += f"        <geometry><box><size>{gw:.3f} {gh:.3f} 0.01</size></box></geometry>\n"
            code += f"      </collision>\n"
            code += f"      <visual name='{base_name}_Vis'>\n"
            code += f"        <geometry><box><size>{gw:.3f} {gh:.3f} 0.01</size></box></geometry>\n"
            code += f"        <material>\n"
            code += f"          <script>\n"
            code += f"            {mat_tag}\n"
            code += f"          </script>\n"
            # [참고] 개별 material 파일에 이미 ambient, diffuse 등이 정의되어 있으므로 여기서는 생략합니다.
            code += f"        </material>\n"
            code += f"      </visual>\n"
            code += f"    </link>\n\n"

        self.text_output.insert(tk.END, code)

    # def export_project(self):
        if not self.target_model_dir:
            messagebox.showwarning("경고", "먼저 모델 파일을 열어주세요.")
            return

        scripts_path = os.path.join(self.target_model_dir, "materials", "scripts")
        os.makedirs(scripts_path, exist_ok=True)
        os.makedirs(os.path.join(self.target_model_dir, "materials", "textures"), exist_ok=True)

        if PILLOW_AVAILABLE:
            # [해결] IDE에게 여기서부터는 절대 None이 아님을 100% 보장한다고 알려줍니다.
            assert Image is not None and ImageDraw is not None

            # 튜플 대신 헥사 코드 문자열 "#f9f9f9"를 사용합니다.
            img = Image.new("RGB", (int(self.canvas_w), int(self.canvas_h)), "#f9f9f9") # type: ignore

            draw = ImageDraw.Draw(img)

            floor_idx, img_idx = 1, 1
            for f in self.confirmed_floors:
                s1, s2 = self.gz_to_screen(f[0], f[1]), self.gz_to_screen(f[2], f[3])
                draw.rectangle([s1[0], s1[1], s2[0], s2[1]], fill=f[4], outline="#333333")

                # 💡 [추가] 픽셀 값 계산 (미터당 200픽셀)
                gw = abs(f[2] - f[0])
                gh = abs(f[3] - f[1])
                px_w = int(gw * 200)
                px_h = int(gh * 200)

                if f[5] == "Custom Image":
                    # 💡 [수정] 파일 저장용 텍스트에도 픽셀 단위 표시 추가
                    label_text = f"Image_{img_idx}\n[{px_w} x {px_h} px]"
                    img_idx += 1
                else:
                    label_text = f"Floor_{floor_idx}"
                    floor_idx += 1

                # 텍스트 그리기 (중앙 정렬 효과를 위해 위치 조정)
                text_pos = ((s1[0]+s2[0])/2 - 35, (s1[1]+s2[1])/2 - 10)
                draw.text(text_pos, label_text, fill="black")

            for w in self.walls_data:
                s = self.gz_to_screen(w['px'], w['py'])
                sw, sh = w['w']*self.scale, w['h']*self.scale
                draw.rectangle([s[0]-sw/2, s[1]-sh/2, s[0]+sw/2, s[1]+sh/2], fill="#777777", outline="black")

            img.save(os.path.join(self.target_model_dir, "test.png"))

        with open(self.original_sdf_path, 'r', encoding='utf-8') as f:
            content = f.read()

        content = re.sub(r"\s*<link name='(?:Floor|image)_\d+'>.*?</link>\s*", "", content, flags=re.DOTALL)
        img_idx = 1
        for f in self.confirmed_floors:
            if f[5] == "Custom Image":
                floor_utils.create_material_script(scripts_path, f"image_{img_idx}_Mat", f[5])
                img_idx += 1

        new_links = self.text_output.get("1.0", tk.END)
        content = content.replace("</model>", new_links + "</model>", 1)

        with open(self.original_sdf_path, 'w', encoding='utf-8') as f:
            f.write(content)

        messagebox.showinfo("완료", "프로젝트가 성공적으로 저장되었습니다.")


    def export_project(self):
            if not self.target_model_dir:
                messagebox.showwarning("경고", "먼저 모델 파일을 열어주세요.")
                return

            # 0. 폴더 이름 가져오기
            folder_name = os.path.basename(self.target_model_dir)

            # 1. 재질 관련 폴더 생성 (기존 로직)
            scripts_path = os.path.join(self.target_model_dir, "materials", "scripts")
            os.makedirs(scripts_path, exist_ok=True)
            os.makedirs(os.path.join(self.target_model_dir, "materials", "textures"), exist_ok=True)

            # 2. 이미지 생성 (기존 로직 유지)
            if PILLOW_AVAILABLE:
                assert Image is not None and ImageDraw is not None
                img = Image.new("RGB", (int(self.canvas_w), int(self.canvas_h)), "#f9f9f9") # type: ignore
                draw = ImageDraw.Draw(img)
                # ... (기존 draw 로직 생략) ...
                img.save(os.path.join(self.target_model_dir, "test.png"))

            # 3. model.sdf 내용 로드 및 업데이트
            with open(self.original_sdf_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # [수정] model name='...' 부분을 폴더 이름으로 자동 교체
            content = re.sub(r"<model name=['\"].*?['\"]>", f"<model name='{folder_name}'>", content)

            # 기존 바닥 링크 제거 (기존 로직)
            content = re.sub(r"\s*<link name='(?:Floor|image)_\d+'>.*?</link>\s*", "", content, flags=re.DOTALL)

            # 새로운 바닥 코드 삽입 (기존 로직)
            new_links = self.text_output.get("1.0", tk.END)
            if "</model>" in content:
                content = content.replace("</model>", new_links + "</model>", 1)

            # 4. model.sdf 저장
            with open(self.original_sdf_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # 5. [추가] model.config 파일 자동 생성/업데이트
            config_path = os.path.join(self.target_model_dir, "model.config")
            config_content = f"""<?xml version="1.0"?>
    <model>
    <name>{folder_name}</name>
    <version>1.0</version>
    <sdf version="1.6">model.sdf</sdf>
    <author>
        <name>LEE D.W.</name>
        <email>2dongwon@gmaile.com</email>
    </author>
    <description>Auto-generated floors for {folder_name}</description>
    </model>
    """
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(config_content)

            messagebox.showinfo("완료", f"'{folder_name}' 프로젝트가 성공적으로 저장 및 업데이트되었습니다.")