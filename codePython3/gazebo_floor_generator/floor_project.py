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

class FloorProjectMixin:
    # --- 타입 힌트 (에러 방지용) ---
    target_model_dir: str
    original_sdf_path: str
    walls_data: list
    confirmed_floors: list
    model_cx: float
    model_cy: float
    canvas_w: int
    canvas_h: int
    scale: float
    pan_x: float
    pan_y: float
    text_output: tk.Text

    def reset_workspace(self): ...
    def draw_workspace(self): ...
    def gz_to_screen(self, gx: float, gy: float) -> tuple: ...
    def calculate_dynamic_scale(self): ... # main이나 events에 있는 scale 계산 함수

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
                # 1. 맵 중심점 계산
                min_x = min(w['px'] - w['w']/2 for w in self.walls_data)
                max_x = max(w['px'] + w['w']/2 for w in self.walls_data)
                min_y = min(w['py'] - w['h']/2 for w in self.walls_data)
                max_y = max(w['py'] + w['h']/2 for w in self.walls_data)
                self.model_cx, self.model_cy = (min_x + max_x) / 2, (min_y + max_y) / 2

                # 💡 [중요] 스케일 계산 추가 (이미지가 캔버스 밖으로 나가는 것 방지)
                dist_x = max_x - min_x if max_x != min_x else 1.0
                dist_y = max_y - min_y if max_y != min_y else 1.0
                self.scale = min((self.canvas_w - 100) / dist_x, (self.canvas_h - 100) / dist_y)

                self.draw_workspace()
        except Exception as e:
            messagebox.showerror("오류", f"SDF 로딩 중 오류: {str(e)}")

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

            code += f"\n"
            code += f"    <link name='{base_name}'>\n"
            code += f"      <pose>{gx:.3f} {gy:.3f} 0.001 0 0 0</pose>\n"
            code += f"      <collision name='{base_name}_Col'>\n"
            code += f"        <geometry><box><size>{gw:.3f} {gh:.3f} 0.01</size></box></geometry>\n"
            code += f"      </collision>\n"
            code += f"      <visual name='{base_name}_Vis'>\n"
            code += f"        <geometry><box><size>{gw:.3f} {gh:.3f} 0.01</size></box></geometry>\n"
            code += f"        <material>\n"
            code += f"          <script>\n            {mat_tag}\n          </script>\n"
            code += f"        </material>\n"
            code += f"      </visual>\n"
            code += f"    </link>\n\n"
        self.text_output.insert(tk.END, code)

    def export_project(self):
        if not self.target_model_dir:
            messagebox.showwarning("경고", "먼저 모델 폴더를 열어주세요.")
            return

        scripts_path = os.path.join(self.target_model_dir, "materials", "scripts")
        os.makedirs(scripts_path, exist_ok=True)
        os.makedirs(os.path.join(self.target_model_dir, "materials", "textures"), exist_ok=True)

        if PILLOW_AVAILABLE and Image and ImageDraw:
            # 💡 PNG 저장용 별도 좌표 변환 (Pan 무시하고 중앙 정렬)
            def png_gz_to_screen(gx, gy):
                cx, cy = self.canvas_w / 2, self.canvas_h / 2
                return cx + (gx - self.model_cx) * self.scale, cy - (gy - self.model_cy) * self.scale

            img = Image.new("RGB", (int(self.canvas_w), int(self.canvas_h)), "#f9f9f9") #type: ignore
            draw = ImageDraw.Draw(img)

            # 바닥 그리기
            floor_idx, img_idx = 1, 1
            for f in self.confirmed_floors:
                s1 = png_gz_to_screen(f[0], f[1])
                s2 = png_gz_to_screen(f[2], f[3])
                draw.rectangle([s1[0], s1[1], s2[0], s2[1]], fill=f[4], outline="#333333")

                gw, gh = abs(f[2] - f[0]), abs(f[3] - f[1])
                px_w, px_h = int(gw * 200), int(gh * 200)

                label = f"image_{img_idx}\n[{px_w}x{px_h}]" if f[5] == "Custom Image" else f"Floor_{floor_idx}"
                if f[5] == "Custom Image": img_idx += 1
                else: floor_idx += 1

                draw.text(((s1[0]+s2[0])/2 - 30, (s1[1]+s2[1])/2 - 10), label, fill="black")

            # 벽 그리기
            for w in self.walls_data:
                s = png_gz_to_screen(w['px'], w['py'])
                sw, sh = w['w'] * self.scale, w['h'] * self.scale
                draw.rectangle([s[0]-sw/2, s[1]-sh/2, s[0]+sw/2, s[1]+sh/2], fill="#777777", outline="black")

            img.save(os.path.join(self.target_model_dir, "test.png"))

        # model.sdf 업데이트 (model name 자동 변경 포함)
        folder_name = os.path.basename(self.target_model_dir)
        with open(self.original_sdf_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 모델 이름 동기화
        content = re.sub(r"<model name=['\"].*?['\"]>", f"<model name='{folder_name}'>", content)
        # 기존 바닥 제거
        content = re.sub(r"\s*<link name='(?:Floor|image)_\d+'>.*?</link>\s*", "", content, flags=re.DOTALL)
        # 새 코드 삽입
        new_links = self.text_output.get("1.0", tk.END)
        content = content.replace("</model>", new_links + "</model>", 1)

        with open(self.original_sdf_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # model.config 생성/업데이트
        config_path = os.path.join(self.target_model_dir, "model.config")
        config_content = f"""<?xml version="1.0"?>
<model>
    <name>{folder_name}</name>
    <version>1.0</version>
    <sdf version="1.7">model.sdf</sdf>
    <author>
        <name>LEE D.W.</name>
        <email>2dongwon@gmail.com</email>
    </author>
    <description>Auto-generated floors for {folder_name}</description>
</model>
"""
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)

        messagebox.showinfo("완료", "프로젝트 및 이미지 저장 완료")