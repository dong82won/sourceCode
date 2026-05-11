import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import xml.etree.ElementTree as ET
import math
import re
import os

try:
    import floor_utils
except ImportError:
    print("오류: floor_utils.py 파일을 찾을 수 없습니다. 같은 폴더에 위치시켜주세요.")

try:
    from PIL import Image, ImageDraw
    PILLOW_AVAILABLE = True
except ImportError:
    Image = None      
    ImageDraw = None  
    PILLOW_AVAILABLE = False

class FloorGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gazebo SDF Floor Master v1.2")
        self.root.geometry("900x980")

        self.canvas_w, self.canvas_h = 850, 600
        self.scale, self.pan_x, self.pan_y = 40.0, 0.0, 0.0
        self.last_pan_x = self.last_pan_y = 0
        self.original_sdf_path = ""
        self.target_model_dir = ""
        self.walls_data, self.confirmed_floors = [], []
        self.color_palette = ["#BAE1FF", "#FFB3BA", "#FFDFBA", "#FFFFBA", "#BAFFC9", "#E0BBE4", "#D4F0F0", "#FFC4E1"]
        self.color_index = 0
        self.start_x = self.start_y = self.rect_id = None
        self.model_cx = self.model_cy = 0.0

        self.setup_ui()

    def setup_ui(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        top_frame = tk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 5))
        btn_frame = tk.Frame(top_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        left_btn_frame = tk.Frame(btn_frame)
        left_btn_frame.pack(side=tk.LEFT)
        tk.Button(left_btn_frame, text="모델 폴더 열기", command=self.open_model_folder, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(left_btn_frame, text="초기화", command=self.reset_workspace).pack(side=tk.LEFT, padx=5)

        right_btn_frame = tk.Frame(btn_frame)
        right_btn_frame.pack(side=tk.RIGHT)
        tk.Label(right_btn_frame, text="바닥 재질:").pack(side=tk.LEFT, padx=(0, 2))
        self.material_var = tk.StringVar(value="Gazebo/Wood")
        
        materials = ["Custom Image", "Gazebo/Wood", "Gazebo/CeilingTiled", "Gazebo/Grey", "Gazebo/Bricks", "Gazebo/Grass", "Gazebo/Asphalt"]
        self.mat_combo = ttk.Combobox(right_btn_frame, textvariable=self.material_var, values=materials, state="readonly", width=18)
        self.mat_combo.pack(side=tk.LEFT, padx=(0, 5))

        help_text = "좌 클릭: 바닥 생성  |  우 클릭: 삭제  |  휠: 줌  |  휠 클릭(드래그): 이동"
        tk.Label(top_frame, text=help_text, fg="#818181", font=("Arial", 10, "bold")).pack()

        self.canvas = tk.Canvas(main_frame, width=self.canvas_w, height=self.canvas_h, bg="#f9f9f9", relief=tk.SUNKEN, bd=2)
        self.canvas.pack(pady=5)
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<ButtonPress-3>", self.on_right_click)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)
        self.canvas.bind("<ButtonPress-2>", self.on_pan_start)
        self.canvas.bind("<B2-Motion>", self.on_pan_drag)

        bottom_frame = tk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        tk.Label(bottom_frame, text="생성된 SDF 코드", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        tk.Button(bottom_frame, text="프로젝트 업데이트 저장", command=self.export_project, bg="#2196F3", fg="white", font=("Arial", 9, "bold")).pack(side=tk.RIGHT, padx=5)
        tk.Button(bottom_frame, text="코드 복사", command=self.copy_to_clipboard, bg="#4CAF50", fg="white", font=("Arial", 9)).pack(side=tk.RIGHT, padx=5)

        text_frame = tk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_output = tk.Text(text_frame, height=10, yscrollcommand=scrollbar.set, font=("Consolas", 9))
        self.text_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_output.yview)

        self.draw_workspace()

    # --- 좌표 및 계산 ---
    def get_cx_cy(self): return self.canvas_w / 2 + self.pan_x, self.canvas_h / 2 + self.pan_y
    def gz_to_screen(self, gx, gy):
        cx, cy = self.get_cx_cy()
        return cx + (gx - self.model_cx) * self.scale, cy - (gy - self.model_cy) * self.scale
    def screen_to_gz(self, sx, sy):
        cx, cy = self.get_cx_cy()
        return (sx - cx) / self.scale + self.model_cx, self.model_cy - (sy - cy) / self.scale

    def get_snap_targets(self):
        tx = [w['px']-w['w']/2 for w in self.walls_data] + [w['px']+w['w']/2 for w in self.walls_data]
        ty = [w['py']-w['h']/2 for w in self.walls_data] + [w['py']+w['h']/2 for w in self.walls_data]
        return tx, ty

    def snap_value(self, v, targets):
        if not targets: return v
        closest = min(targets, key=lambda t: abs(v-t))
        return closest if abs(v-closest) < (20/self.scale) else v

    # --- 이벤트 핸들러 ---
    def on_mouse_down(self, event):
        gz_x, gz_y = self.screen_to_gz(event.x, event.y)
        tx, ty = self.get_snap_targets()
        self.start_x = self.snap_value(gz_x, tx)
        self.start_y = self.snap_value(gz_y, ty)
        sx, sy = self.gz_to_screen(self.start_x, self.start_y)
        if self.rect_id: self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(sx, sy, sx, sy, outline="red", width=2, dash=(4,4))

    def on_mouse_drag(self, event):
        if self.start_x is None: return
        gx, gy = self.screen_to_gz(event.x, event.y)
        tx, ty = self.get_snap_targets()
        cx, cy = self.snap_value(gx, tx), self.snap_value(gy, ty)
        sx1, sy1 = self.gz_to_screen(self.start_x, self.start_y)
        sx2, sy2 = self.gz_to_screen(cx, cy)
        self.canvas.coords(self.rect_id, sx1, sy1, sx2, sy2)

    def on_mouse_up(self, event):
        if self.start_x is None: return
        gx, gy = self.screen_to_gz(event.x, event.y)
        tx, ty = self.get_snap_targets()
        end_x, end_y = self.snap_value(gx, tx), self.snap_value(gy, ty)
        
        if abs(end_x - self.start_x) < 0.1 or abs(end_y - self.start_y) < 0.1:
            self.canvas.delete(self.rect_id); return

        new_rect = (min(self.start_x, end_x), min(self.start_y, end_y), max(self.start_x, end_x), max(self.start_y, end_y))
        
        process_list = [new_rect]
        for old in self.confirmed_floors:
            next_list = []
            for r in process_list:
                next_list.extend(floor_utils.subtract_rect(r, old[0:4]))
            process_list = next_list

        added = False
        for r in process_list:
            if (r[2]-r[0]) > 0.2 and (r[3]-r[1]) > 0.2:
                color = self.color_palette[self.color_index % len(self.color_palette)]
                self.confirmed_floors.append((r[0], r[1], r[2], r[3], color, self.material_var.get()))
                added = True
        
        if added: self.color_index += 1
        self.canvas.delete(self.rect_id)
        self.start_x = None
        self.draw_workspace()
        self.update_sdf_text()

    def on_right_click(self, event):
        gx, gy = self.screen_to_gz(event.x, event.y)
        self.confirmed_floors = [f for f in self.confirmed_floors if not (f[0]<=gx<=f[2] and f[1]<=gy<=f[3])]
        self.draw_workspace()
        self.update_sdf_text()

    def on_mouse_wheel(self, event):
        if event.num == 4 or event.delta > 0: self.scale *= 1.1
        else: self.scale *= 0.9
        self.draw_workspace()

    def on_pan_start(self, event): self.last_pan_x, self.last_pan_y = event.x, event.y
    def on_pan_drag(self, event):
        self.pan_x += event.x - self.last_pan_x
        self.pan_y += event.y - self.last_pan_y
        self.last_pan_x, self.last_pan_y = event.x, event.y
        self.draw_workspace()

    def draw_workspace(self):
        self.canvas.delete("all")
        cx, cy = self.get_cx_cy()
        self.canvas.create_line(cx, -2000, cx, 2000, fill="#e0e0e0", dash=(4, 4))
        self.canvas.create_line(-2000, cy, 2000, cy, fill="#e0e0e0", dash=(4, 4))
        
        # [옵션 A] 캔버스 상에서도 Floor_x와 image_x를 독립 카운트
        floor_idx = 1
        img_idx = 1
        for f in self.confirmed_floors:
            s1 = self.gz_to_screen(f[0], f[1])
            s2 = self.gz_to_screen(f[2], f[3])
            self.canvas.create_rectangle(s1[0], s1[1], s2[0], s2[1], fill=f[4], outline="#333")
            
            if f[5] == "Custom Image":
                label_text = f"image_{img_idx}"
                img_idx += 1
            else:
                label_text = f"Floor_{floor_idx}"
                floor_idx += 1
            
            self.canvas.create_text((s1[0]+s2[0])/2, (s1[1]+s2[1])/2, text=label_text, font=("Arial", 10, "bold"))
        
        for w in self.walls_data:
            s = self.gz_to_screen(w['px'], w['py'])
            sw, sh = w['w']*self.scale, w['h']*self.scale
            self.canvas.create_rectangle(s[0]-sw/2, s[1]-sh/2, s[0]+sw/2, s[1]+sh/2, fill="#777")

    # --- 메인 프로젝트 로직 ---
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
        
        # [옵션 A] 독립 카운트 적용
        floor_idx = 1
        img_idx = 1
        
        for f in self.confirmed_floors:
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
            code += f"        </material>\n"
            code += f"      </visual>\n"
            code += f"    </link>\n\n"
            
        self.text_output.insert(tk.END, code)

    def export_project(self):
        if not self.target_model_dir:
            messagebox.showwarning("경고", "먼저 모델 파일을 열어주세요.")
            return
            
        scripts_path = os.path.join(self.target_model_dir, "materials", "scripts")
        os.makedirs(scripts_path, exist_ok=True)
        os.makedirs(os.path.join(self.target_model_dir, "materials", "textures"), exist_ok=True)

        # 이미지 저장
        if PILLOW_AVAILABLE:
            img = Image.new("RGB", (int(self.canvas_w), int(self.canvas_h)), (249, 249, 249))
            draw = ImageDraw.Draw(img)
            
            floor_idx = 1
            img_idx = 1
            for f in self.confirmed_floors:
                s1, s2 = self.gz_to_screen(f[0], f[1]), self.gz_to_screen(f[2], f[3])
                draw.rectangle([s1[0], s1[1], s2[0], s2[1]], fill=f[4], outline="#333333")
                
                if f[5] == "Custom Image":
                    label_text = f"image_{img_idx}"
                    img_idx += 1
                else:
                    label_text = f"Floor_{floor_idx}"
                    floor_idx += 1
                    
                draw.text(((s1[0]+s2[0])/2 - 20, (s1[1]+s2[1])/2 - 5), label_text, fill="black")
                
            for w in self.walls_data:
                s = self.gz_to_screen(w['px'], w['py'])
                sw, sh = w['w']*self.scale, w['h']*self.scale
                draw.rectangle([s[0]-sw/2, s[1]-sh/2, s[0]+sw/2, s[1]+sh/2], fill="#777777", outline="black")
                
            img.save(os.path.join(self.target_model_dir, "test.png"))

        # SDF 읽기
        with open(self.original_sdf_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # [수정] Floor_x 와 image_x 링크를 모두 깔끔하게 지우기 위한 정규표현식 적용
        content = re.sub(r"\s*<link name='(?:Floor|image)_\d+'>.*?</link>\s*", "", content, flags=re.DOTALL)
        
        # Custom Image 시에만 Material 생성
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

    def copy_to_clipboard(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.text_output.get("1.0", tk.END))
        messagebox.showinfo("완료", "코드가 복사되었습니다.")

    def reset_workspace(self):
        self.walls_data, self.confirmed_floors, self.color_index = [], [], 0
        self.draw_workspace()
        self.text_output.delete("1.0", tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = FloorGeneratorApp(root)
    root.mainloop()