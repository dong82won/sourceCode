import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import xml.etree.ElementTree as ET
import math
import re
import shutil

class FloorGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gazebo SDF Floor Master (Zoom, Pan, Auto-Save)")
        self.root.geometry("900x950")

        # 캔버스 및 뷰포트 상태
        self.canvas_w = 850
        self.canvas_h = 600
        self.scale = 40.0
        self.pan_x = 0.0 # 화면 이동(Pan) X 오프셋
        self.pan_y = 0.0 # 화면 이동(Pan) Y 오프셋
        self.last_pan_x = 0
        self.last_pan_y = 0

        self.model_cx = 0.0
        self.model_cy = 0.0

        self.original_sdf_path = ""
        self.walls_data = [] # 파싱된 벽 데이터 저장

        self.start_x = None
        self.start_y = None
        self.rect_id = None

        # 바닥 리스트 (id, x1, y1, x2, y2, color, material)
        self.confirmed_floors = []
        self.total_created_count = 0

        self.color_palette = ["#BAE1FF", "#FFB3BA", "#FFDFBA", "#FFFFBA", "#BAFFC9", "#E0BBE4", "#D4F0F0", "#FFC4E1"]
        self.color_index = 0

        self.setup_ui()

    def setup_ui(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        # 1. 상단 컨트롤 영역
        top_frame = tk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 5))
        
        btn_frame = tk.Frame(top_frame)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="📁 1. model.sdf 열기", command=self.load_sdf, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        # [기능 1] 재질 선택 드롭다운 추가
        tk.Label(btn_frame, text="바닥 재질:").pack(side=tk.LEFT, padx=(15, 2))
        self.material_var = tk.StringVar(value="Gazebo/Wood")
        materials = ["Gazebo/Wood", "Gazebo/CeilingTiled", "Gazebo/Grey", "Gazebo/Bricks", "Gazebo/Grass", "Gazebo/Asphalt"]
        self.mat_combo = ttk.Combobox(btn_frame, textvariable=self.material_var, values=materials, state="readonly", width=18)
        self.mat_combo.pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="초기화", command=self.reset_workspace).pack(side=tk.LEFT, padx=(15, 5))

        # 조작법 안내
        help_text = "🖱️ 좌클릭: 바닥 생성  |  🖱️ 우클릭: 조각 삭제  |  ⚙️ 휠: 줌(확대/축소)  |  🖱️ 휠클릭(드래그): 화면 이동"
        tk.Label(top_frame, text=help_text, fg="#d32f2f", font=("Arial", 10, "bold")).pack()

        # 2. 캔버스 영역
        self.canvas = tk.Canvas(main_frame, width=self.canvas_w, height=self.canvas_h, bg="#f9f9f9", relief=tk.SUNKEN, bd=2)
        self.canvas.pack(pady=5)
        
        # 이벤트 바인딩
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)   
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)       
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)   
        self.canvas.bind("<ButtonPress-3>", self.on_right_click)  # 우클릭 (삭제)
        
        # [기능 4] 화면 줌(Zoom) & 이동(Pan) 바인딩
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)     # Windows/Mac 줌
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)       # Linux 줌 in
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)       # Linux 줌 out
        self.canvas.bind("<ButtonPress-2>", self.on_pan_start)    # 휠 클릭 (이동 시작)
        self.canvas.bind("<B2-Motion>", self.on_pan_drag)         # 휠 드래그 (이동)

        self.draw_workspace()

        # 3. 하단 텍스트 및 저장 영역
        bottom_frame = tk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        tk.Label(bottom_frame, text="3. 생성된 SDF 코드", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
        # [기능 3] 파일 직접 덮어쓰기 버튼 추가
        tk.Button(bottom_frame, text="💾 SDF 파일에 바로 저장 (추천)", command=self.save_to_file, bg="#2196F3", fg="white", font=("Arial", 9, "bold")).pack(side=tk.RIGHT, padx=5)
        tk.Button(bottom_frame, text="📋 코드 복사", command=self.copy_to_clipboard, bg="#4CAF50", fg="white", font=("Arial", 9)).pack(side=tk.RIGHT)

        text_frame = tk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_output = tk.Text(text_frame, height=10, yscrollcommand=scrollbar.set, font=("Consolas", 9))
        self.text_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_output.yview)

    # ================= 좌표 변환 핵심 로직 =================
    def get_cx_cy(self):
        return self.canvas_w / 2 + self.pan_x, self.canvas_h / 2 + self.pan_y

    def gz_to_screen(self, gx, gy):
        cx, cy = self.get_cx_cy()
        sx = cx + (gx - self.model_cx) * self.scale
        sy = cy - (gy - self.model_cy) * self.scale
        return sx, sy

    def screen_to_gz(self, sx, sy):
        cx, cy = self.get_cx_cy()
        gx = (sx - cx) / self.scale + self.model_cx
        gy = self.model_cy - (sy - cy) / self.scale
        return gx, gy
    # ======================================================

    def load_sdf(self):
        filepath = filedialog.askopenfilename(filetypes=[("SDF Files", "*.sdf")])
        if not filepath: return
        self.reset_workspace()
        self.original_sdf_path = filepath
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            for link in root.iter('link'):
                wall_data = self.parse_wall(link)
                if wall_data: self.walls_data.append(wall_data)
            
            if not self.walls_data:
                messagebox.showwarning("경고", "벽(높이 0.5m 이상의 장애물)을 찾을 수 없습니다.")
                return
            self.calculate_dynamic_scale()
            self.draw_workspace()
        except Exception as e: messagebox.showerror("오류", str(e))

    # [기능 2] 범용 벽 인식 로직 (이름 무관, 높이 기반)
    def parse_wall(self, link):
        try:
            p = list(map(float, link.find('pose').text.split()))
            s = list(map(float, link.find('.//box/size').text.split()))
            # 높이(Z)가 0.5m 이상인 경우에만 벽으로 취급
            if s[2] < 0.5: return None 
            
            yaw = abs(math.degrees(p[5])) % 180
            w, h = (s[1], s[0]) if 80 < yaw < 100 else (s[0], s[1])
            return {'px': p[0], 'py': p[1], 'w': w, 'h': h}
        except: return None

    def calculate_dynamic_scale(self):
        min_x = min(w['px'] - w['w']/2 for w in self.walls_data)
        max_x = max(w['px'] + w['w']/2 for w in self.walls_data)
        min_y = min(w['py'] - w['h']/2 for w in self.walls_data)
        max_y = max(w['py'] + w['h']/2 for w in self.walls_data)
        self.model_cx, self.model_cy = (min_x + max_x) / 2, (min_y + max_y) / 2
        self.scale = min((self.canvas_w-150)/(max_x-min_x), (self.canvas_h-150)/(max_y-min_y))

    def draw_workspace(self):
        self.canvas.delete("all")
        cx, cy = self.get_cx_cy()
        
        # 그리드
        self.canvas.create_line(cx, -2000, cx, 2000, fill="#e0e0e0", dash=(4, 4))
        self.canvas.create_line(-2000, cy, 2000, cy, fill="#e0e0e0", dash=(4, 4))
        
        # 바닥
        for f in self.confirmed_floors:
            sx1, sy1 = self.gz_to_screen(f[1], f[2])
            sx2, sy2 = self.gz_to_screen(f[3], f[4])
            self.canvas.create_rectangle(sx1, sy1, sx2, sy2, fill=f[5], outline="#333", tags="floor")
            
        # 벽
        for w in self.walls_data:
            sx, sy = self.gz_to_screen(w['px'], w['py'])
            sw, sh = w['w'] * self.scale, w['h'] * self.scale
            self.canvas.create_rectangle(sx-sw/2, sy-sh/2, sx+sw/2, sy+sh/2, fill="#777", outline="black", tags="wall")

    # [기능 4] 줌 & 팬 이벤트 핸들러
    def on_mouse_wheel(self, event):
        if event.num == 4 or event.delta > 0: self.scale *= 1.1 # 줌 인
        elif event.num == 5 or event.delta < 0: self.scale *= 0.9 # 줌 아웃
        self.draw_workspace()

    def on_pan_start(self, event):
        self.last_pan_x, self.last_pan_y = event.x, event.y

    def on_pan_drag(self, event):
        self.pan_x += event.x - self.last_pan_x
        self.pan_y += event.y - self.last_pan_y
        self.last_pan_x, self.last_pan_y = event.x, event.y
        self.draw_workspace()

    # 드래그 스냅 로직
    def on_mouse_down(self, event):
        gz_x, gz_y = self.screen_to_gz(event.x, event.y)
        self.snap_x, self.snap_y = self.get_snap_targets()

        self.start_x = self.snap_value(gz_x, self.snap_x)
        self.start_y = self.snap_value(gz_y, self.snap_y)

        sx, sy = self.gz_to_screen(self.start_x, self.start_y)
        if self.rect_id: self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(sx, sy, sx, sy, outline="red", width=2, dash=(4,4))

    def on_mouse_drag(self, event):
        # [타입 에러 방지] 변수들이 None이면 실행하지 않음
        if self.rect_id is None or self.start_x is None or self.start_y is None:
            return

        gz_x, gz_y = self.screen_to_gz(event.x, event.y)
        cur_x = self.snap_value(gz_x, self.snap_x)
        cur_y = self.snap_value(gz_y, self.snap_y)

        sx1, sy1 = self.gz_to_screen(self.start_x, self.start_y)
        sx2, sy2 = self.gz_to_screen(cur_x, cur_y)
        self.canvas.coords(self.rect_id, sx1, sy1, sx2, sy2)

    def on_mouse_up(self, event):
        # [타입 에러 방지] 변수들이 None이면 실행하지 않음
        if self.rect_id is None or self.start_x is None or self.start_y is None:
            return

        gz_x, gz_y = self.screen_to_gz(event.x, event.y)
        cur_x = self.snap_value(gz_x, self.snap_x)
        cur_y = self.snap_value(gz_y, self.snap_y)

        if abs(cur_x - self.start_x) < 0.1 or abs(cur_y - self.start_y) < 0.1:
            self.canvas.delete(self.rect_id); return

        new_rect = (min(self.start_x, cur_x), min(self.start_y, cur_y), max(self.start_x, cur_x), max(self.start_y, cur_y))
        rects_to_process = [new_rect]
        for old in self.confirmed_floors:
            next_rects = []
            for r in rects_to_process: next_rects.extend(self.subtract_rect(r, old[1:5]))
            rects_to_process = next_rects

        color = self.color_palette[self.color_index % len(self.color_palette)]
        material = self.material_var.get() # 현재 선택된 재질 가져오기
        added = False

        for r in rects_to_process:
            if r[2]-r[0] > 0.05 and r[3]-r[1] > 0.05: # 최소 5cm 이상의 조각만 허용
                self.total_created_count += 1
                self.confirmed_floors.append((self.total_created_count, r[0], r[1], r[2], r[3], color, material))
                added = True

        if added: self.color_index += 1
        self.canvas.delete(self.rect_id)
        self.draw_workspace()
        self.generate_all_sdf_code()

    def on_right_click(self, event):
        gz_x, gz_y = self.screen_to_gz(event.x, event.y)
        found = False
        for i in range(len(self.confirmed_floors)-1, -1, -1):
            f = self.confirmed_floors[i]
            if f[1] <= gz_x <= f[3] and f[2] <= gz_y <= f[4]:
                del self.confirmed_floors[i]
                found = True
                break
        if found:
            self.draw_workspace()
            self.generate_all_sdf_code()

    def get_snap_targets(self):
        tx, ty = [], []
        for f in self.confirmed_floors:
            tx.extend([f[1], f[3]]); ty.extend([f[2], f[4]])
        for w in self.walls_data:
            tx.extend([w['px']-w['w']/2, w['px']+w['w']/2])
            ty.extend([w['py']-w['h']/2, w['py']+w['h']/2])
        return tx, ty

    def snap_value(self, val, targets):
        closest = min(targets, key=lambda t: abs(val-t)) if targets else val
        return closest if abs(val-closest) < (15/self.scale) else val

    def subtract_rect(self, r1, r2):
        ix1, iy1, ix2, iy2 = max(r1[0], r2[0]), max(r1[1], r2[1]), min(r1[2], r2[2]), min(r1[3], r2[3])
        if ix1 >= ix2 or iy1 >= iy2: return [r1]
        res = []
        if r1[0] < ix1: res.append((r1[0], r1[1], ix1, r1[3]))
        if ix2 < r1[2]: res.append((ix2, r1[1], r1[2], r1[3]))
        if r1[1] < iy1: res.append((ix1, r1[1], ix2, iy1))
        if iy2 < r1[3]: res.append((ix1, iy2, ix2, r1[3]))
        return res

    def generate_all_sdf_code(self):
        self.text_output.delete("1.0", tk.END)
        code = self.get_sdf_string()
        self.text_output.insert(tk.END, code.strip())

    def get_sdf_string(self):
        code = ""
        for f in self.confirmed_floors:
            fid, x1, y1, x2, y2, _, material = f
            gx, gy = round((x1+x2)/2, 3), round((y1+y2)/2, 3)
            gw, gh = round(x2-x1, 3), round(y2-y1, 3)
            code += f"""    <link name='Floor_{fid}'>
      <pose>{gx} {gy} 0.001 0 0 0</pose>
      <collision name='Floor_{fid}_Col'>
        <geometry><box><size>{gw} {gh} 0.01</size></box></geometry>
        <surface>
          <friction><ode><mu>1.0</mu><mu2>1.0</mu2></ode></friction>
          <contact><ode><kp>1e6</kp><kd>1.0</kd><min_depth>0.001</min_depth></ode></contact>
        </surface>
      </collision>
      <visual name='Floor_{fid}_Vis'>
        <geometry><box><size>{gw} {gh} 0.01</size></box></geometry>
        <material>
          <script><uri>file://media/materials/scripts/gazebo.material</uri><name>{material}</name></script>
          <ambient>0.435 0.796 0.674 1</ambient>
        </material>
      </visual>
    </link>\n\n"""
        return code
    

    def save_to_file(self):
        if not self.original_sdf_path:
            messagebox.showwarning("경고", "먼저 SDF 파일을 열어주세요.")
            return

        generated_code = self.get_sdf_string()

        if not generated_code:
            messagebox.showinfo("알림", "저장할 바닥 코드가 없습니다.")
            return

        try:
            # 💡 [개선] 원본 파일 덮어쓰기 전 안전을 위해 백업 파일 생성
            backup_path = self.original_sdf_path + ".bak"
            shutil.copy2(self.original_sdf_path, backup_path)

            # 기존 파일 읽기
            with open(self.original_sdf_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 기존에 생성된 Floor 링크 제거
            pattern = r"\s*<link name='Floor_\d+'>.*?</link>\s*"
            content = re.sub(pattern, "", content, flags=re.DOTALL)

            # </model> 태그 앞에 새 바닥 코드 삽입
            if "</model>" not in content:
                messagebox.showerror("오류", "</model> 태그를 찾을 수 없습니다.")
                return

            # 💡 [개선] 혹시 모를 중복 교체를 방지하기 위해 1회만 교체되도록 설정 (count=1)
            content = content.replace(
                "</model>",
                generated_code + "\n</model>",
                1
            )

            # 파일 저장
            with open(self.original_sdf_path, 'w', encoding='utf-8') as f:
                f.write(content)

            messagebox.showinfo("완료", "SDF 파일 저장 완료\n(원본 파일은 .bak로 백업되었습니다.)")

        except Exception as e:
            messagebox.showerror("오류", str(e))


    def copy_to_clipboard(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.text_output.get("1.0", tk.END))
        messagebox.showinfo("완료", "코드가 복사되었습니다.")

    def reset_workspace(self):
        self.original_sdf_path = ""
        self.walls_data = []
        self.confirmed_floors = []
        self.pan_x = 0
        self.pan_y = 0
        self.total_created_count = 0
        self.color_index = 0
        self.canvas.delete("all")
        self.text_output.delete("1.0", tk.END)

# =====================================================================
# 프로그램 실행을 위한 메인 블록 (파일의 맨 마지막 부분)
# =====================================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = FloorGeneratorApp(root)
    root.mainloop()