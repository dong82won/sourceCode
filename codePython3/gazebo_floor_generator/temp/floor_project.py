import os
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

    def open_model_folder(self):
        sdf_path = filedialog.askopenfilename(
            title="업데이트할 폴더 안의 'model.sdf'를 선택하세요",
            filetypes=[("SDF Files", "model.sdf"), ("All Files", "*.*")]
        )
        if not sdf_path: return

        self.target_model_dir = os.path.dirname(sdf_path)
        self.original_sdf_path = sdf_path
        self.reset_workspace()
        
        # [최적화] 맵 초기화 시 스냅 타겟 캐시도 초기화
        self._cached_tx = None
        self._cached_ty = None
        
        try:
            tree = ET.parse(self.original_sdf_path)
            for link in tree.getroot().iter('link'):
                d = floor_utils.parse_wall_data(link)
                if d: self.walls_data.append(d)

            if self.walls_data:
                # 맵 중심점 계산
                min_x = min(w['px'] - w['w']/2 for w in self.walls_data)
                max_x = max(w['px'] + w['w']/2 for w in self.walls_data)
                min_y = min(w['py'] - w['h']/2 for w in self.walls_data)
                max_y = max(w['py'] + w['h']/2 for w in self.walls_data)
                self.model_cx, self.model_cy = (min_x + max_x) / 2, (min_y + max_y) / 2

                # 스케일 자동 계산
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

        for f in self.confirmed_floors:
            gx = (f[0] + f[2]) / 2
            gy = (f[1] + f[3]) / 2
            gw = f[2] - f[0]
            gh = f[3] - f[1]

            mat_choice = f[5]
            f_id = f[6] if len(f) > 6 else 1 # 💡 고유 ID 가져오기

            mass = max(1.0, round(gw * gh * 1.5, 2))
            thickness = 0.01

            # 관성 모멘트 계산
            ixx = round((1.0 / 12.0) * mass * (gh**2 + thickness**2), 4)
            iyy = round((1.0 / 12.0) * mass * (gw**2 + thickness**2), 4)
            izz = round((1.0 / 12.0) * mass * (gw**2 + gh**2), 4)

            if mat_choice == "Custom Image":
                base_name = f"image_{f_id}" # 💡 고유 ID 적용
                mat_tag = f"""<uri>model://{folder_name}/materials/scripts</uri>
                <uri>model://{folder_name}/materials/textures/</uri>
                <name>{base_name}_Mat</name>"""
                mu_val = 1.0
            else:
                base_name = f"Floor_{f_id}" # 💡 고유 ID 적용
                mat_tag = f"""<uri>file://media/materials/scripts/gazebo.material</uri>
                <name>{mat_choice}</name>"""
                mu_val = 1.0

            code += f"\n    <link name='{base_name}'>\n"
            # 💡 회전 제거 (0 0 0) - test.png와 방향 일치
            code += f"      <pose>{gx:.3f} {gy:.3f} 0.001 0 0 0</pose>\n"

            code += f"      <inertial>\n"
            code += f"        <mass>{mass}</mass>\n"
            code += f"        <inertia>\n"
            code += f"          <ixx>{ixx}</ixx> <ixy>0.0</ixy> <ixz>0.0</ixz>\n"
            code += f"          <iyy>{iyy}</iyy> <iyz>0.0</iyz>\n"
            code += f"          <izz>{izz}</izz>\n"
            code += f"        </inertia>\n"
            code += f"      </inertial>\n"

            code += f"      <collision name='{base_name}_Col'>\n"
            code += f"        <geometry><box><size>{gw:.3f} {gh:.3f} {thickness}</size></box></geometry>\n"
            code += f"        <surface>\n          <friction><ode><mu>{mu_val}</mu><mu2>{mu_val}</mu2></ode></friction>\n"
            code += f"          <contact><ode><kp>10000000.0</kp><kd>1.0</kd></ode></contact>\n"
            code += f"        </surface>\n      </collision>\n"

            code += f"      <visual name='{base_name}_Vis'>\n"
            code += f"        <geometry><box><size>{gw:.3f} {gh:.3f} {thickness}</size></box></geometry>\n"
            code += f"        <material><script>{mat_tag}</script></material>\n"
            code += f"      </visual>\n    </link>\n"

        self.text_output.insert(tk.END, code)
    

    def export_project(self):
        if not self.target_model_dir:
            messagebox.showwarning("경고", "먼저 모델 폴더를 열어주세요.")
            return

        scripts_path = os.path.join(self.target_model_dir, "materials", "scripts")
        os.makedirs(scripts_path, exist_ok=True)
        os.makedirs(os.path.join(self.target_model_dir, "materials", "textures"), exist_ok=True)

        for f in self.confirmed_floors:
            if f[5] == "Custom Image":
                f_id = f[6] if len(f) > 6 else 1
                mat_name = f"image_{f_id}_Mat" # 💡 생성 시 고유 ID 유지
                floor_utils.create_material_script(scripts_path, mat_name, "test.png")

        if PILLOW_AVAILABLE and Image and ImageDraw:
            def png_gz_to_screen(gx, gy):
                cx, cy = self.canvas_w / 2, self.canvas_h / 2
                return cx + (gx - self.model_cx) * self.scale, cy - (gy - self.model_cy) * self.scale

            img = Image.new("RGB", (int(self.canvas_w), int(self.canvas_h)), "#f9f9f9") # type: ignore

            draw = ImageDraw.Draw(img)

            for f in self.confirmed_floors:
                s1 = png_gz_to_screen(f[0], f[1])
                s2 = png_gz_to_screen(f[2], f[3])
                draw.rectangle([s1[0], s1[1], s2[0], s2[1]], fill=f[4], outline="#333333")

                gw, gh = abs(f[2] - f[0]), abs(f[3] - f[1])
                px_w, px_h = int(gw * 200), int(gh * 200)
                f_id = f[6] if len(f) > 6 else "?"

                # 💡 이미지에 라벨링 할 때도 고유 ID 사용
                label = f"image_{f_id}\n[{px_w}x{px_h}]" if f[5] == "Custom Image" else f"Floor_{f_id}"
                draw.text(((s1[0]+s2[0])/2 - 30, (s1[1]+s2[1])/2 - 10), label, fill="black")

            for w in self.walls_data:
                s = png_gz_to_screen(w['px'], w['py'])
                sw, sh = w['w'] * self.scale, w['h'] * self.scale
                draw.rectangle([s[0]-sw/2, s[1]-sh/2, s[0]+sw/2, s[1]+sh/2], fill="#777777", outline="black") 

            # 💡 [최적화 & 방향 일치] 90도 회전을 없애고 캔버스 뷰 그대로 저장
            img.save(os.path.join(self.target_model_dir, "test.png"))

        # 💡 [최적화] 정규표현식 대신 안전한 ElementTree 파싱으로 SDF 업데이트
        folder_name = os.path.basename(self.target_model_dir)
        try:
            tree = ET.parse(self.original_sdf_path)
            root = tree.getroot()
            model_elem = root.find('model')
            
            if model_elem is not None:
                # 1. 모델 이름 동기화
                model_elem.set('name', folder_name)
                
                # 2. 기존 바닥 및 이미지 링크 삭제
                links_to_remove = []
                for link in model_elem.findall('link'):
                    name = link.get('name', '')
                    if name.startswith('Floor_') or name.startswith('image_'):
                        links_to_remove.append(link)
                for link in links_to_remove:
                    model_elem.remove(link)
                
                # 3. 새 코드 파싱 후 삽입
                new_links_str = self.text_output.get("1.0", tk.END).strip()
                if new_links_str:
                    wrapped_links = f"<dummy>{new_links_str}</dummy>"
                    new_links_tree = ET.fromstring(wrapped_links)
                    for new_link in new_links_tree:
                        model_elem.append(new_link)
                
                # 들여쓰기 정렬 지원 (Python 3.9+)
                if hasattr(ET, 'indent'):
                    ET.indent(tree, space="  ", level=0)

            tree.write(self.original_sdf_path, encoding='utf-8', xml_declaration=True)

        except Exception as e:
            messagebox.showerror("오류", f"SDF 파일 저장/파싱 중 오류: {str(e)}")
            return

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