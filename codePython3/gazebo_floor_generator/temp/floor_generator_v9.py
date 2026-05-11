import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog # simpledialog 추가
import xml.etree.ElementTree as ET
import math
import re
import os

# 이미지 저장을 위해 Pillow 라이브러리가 필요합니다. (pip install Pillow)
try:
    from PIL import Image, ImageDraw
    PILLOW_AVAILABLE = True
except ImportError:
    Image = None      # type: ignore
    ImageDraw = None  # type: ignore
    PILLOW_AVAILABLE = False

class FloorGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gazebo SDF Floor Master v1.0")
        self.root.geometry("900x980")

        # 캔버스 및 뷰포트 상태
        self.canvas_w = 850
        self.canvas_h = 600
        self.scale = 40.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.last_pan_x = 0
        self.last_pan_y = 0

        self.model_cx = 0.0
        self.model_cy = 0.0

        self.original_sdf_path = ""
        self.walls_data = []

        self.start_x = None
        self.start_y = None
        self.rect_id = None

        self.confirmed_floors = []
        self.total_created_count = 0

        self.color_palette = ["#BAE1FF", "#FFB3BA", "#FFDFBA", "#FFFFBA", "#BAFFC9", "#E0BBE4", "#D4F0F0", "#FFC4E1"]
        self.color_index = 0

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

        tk.Button(left_btn_frame, text="model.sdf 불러오기", command=self.load_sdf, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(5, 5))
        tk.Button(left_btn_frame, text="초기화", command=self.reset_workspace).pack(side=tk.LEFT, padx=5)

        right_btn_frame = tk.Frame(btn_frame)
        right_btn_frame.pack(side=tk.RIGHT)

        tk.Label(right_btn_frame, text="바닥 재질:").pack(side=tk.LEFT, padx=(0, 2))
        self.material_var = tk.StringVar(value="Gazebo/Wood")
        materials = ["Gazebo/Wood", "Gazebo/CeilingTiled", "Gazebo/Grey", "Gazebo/Bricks", "Gazebo/Grass", "Gazebo/Asphalt"]
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

        self.draw_workspace()

        bottom_frame = tk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        tk.Label(bottom_frame, text="생성된 SDF 코드", font=("Arial", 10, "bold")).pack(side=tk.LEFT)

        # 버튼 배정
        tk.Button(bottom_frame, text="새 폴더에 SDF파일 저장", command=self.export_project, bg="#2196F3", fg="white", font=("Arial", 9, "bold")).pack(side=tk.RIGHT, padx=5)
        tk.Button(bottom_frame, text="코드 복사", command=self.copy_to_clipboard, bg="#4CAF50", fg="white", font=("Arial", 9)).pack(side=tk.RIGHT, padx=5)

        text_frame = tk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_output = tk.Text(text_frame, height=10, yscrollcommand=scrollbar.set, font=("Consolas", 9))
        self.text_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_output.yview)

    # (이전 버전과 동일한 좌표 변환 및 스냅 로직은 유지됩니다...)
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
                messagebox.showwarning("경고", "벽 정보를 찾을 수 없습니다.")
                return
            self.calculate_dynamic_scale()
            self.draw_workspace()
        except Exception as e: messagebox.showerror("오류", str(e))

    def parse_wall(self, link):
        try:
            p = list(map(float, link.find('pose').text.split()))
            s = list(map(float, link.find('.//box/size').text.split()))
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
        self.canvas.create_line(cx, -2000, cx, 2000, fill="#e0e0e0", dash=(4, 4))
        self.canvas.create_line(-2000, cy, 2000, cy, fill="#e0e0e0", dash=(4, 4))
        for idx, f in enumerate(self.confirmed_floors, start=1):
            sx1, sy1 = self.gz_to_screen(f[1], f[2])
            sx2, sy2 = self.gz_to_screen(f[3], f[4])
            self.canvas.create_rectangle(sx1, sy1, sx2, sy2, fill=f[5], outline="#333", tags="floor")
            self.canvas.create_text((sx1+sx2)/2, (sy1+sy2)/2, text=f"Floor_{idx}", font=("Arial", 10, "bold"), fill="#333")
        for w in self.walls_data:
            sx, sy = self.gz_to_screen(w['px'], w['py'])
            sw, sh = w['w'] * self.scale, w['h'] * self.scale
            self.canvas.create_rectangle(sx-sw/2, sy-sh/2, sx+sw/2, sy+sh/2, fill="#777", outline="black", tags="wall")

    def on_mouse_wheel(self, event):
        if event.num == 4 or event.delta > 0: self.scale *= 1.1
        elif event.num == 5 or event.delta < 0: self.scale *= 0.9
        self.draw_workspace()

    def on_pan_start(self, event):
        self.last_pan_x, self.last_pan_y = event.x, event.y

    def on_pan_drag(self, event):
        self.pan_x += event.x - self.last_pan_x
        self.pan_y += event.y - self.last_pan_y
        self.last_pan_x, self.last_pan_y = event.x, event.y
        self.draw_workspace()

    def on_mouse_down(self, event):
        gz_x, gz_y = self.screen_to_gz(event.x, event.y)
        self.snap_x, self.snap_y = self.get_snap_targets()
        self.start_x = self.snap_value(gz_x, self.snap_x)
        self.start_y = self.snap_value(gz_y, self.snap_y)
        sx, sy = self.gz_to_screen(self.start_x, self.start_y)
        if self.rect_id: self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(sx, sy, sx, sy, outline="red", width=2, dash=(4,4))

    def on_mouse_drag(self, event):
        if self.rect_id is None or self.start_x is None or self.start_y is None: return
        gz_x, gz_y = self.screen_to_gz(event.x, event.y)
        cur_x = self.snap_value(gz_x, self.snap_x)
        cur_y = self.snap_value(gz_y, self.snap_y)
        sx1, sy1 = self.gz_to_screen(self.start_x, self.start_y)
        sx2, sy2 = self.gz_to_screen(cur_x, cur_y)
        self.canvas.coords(self.rect_id, sx1, sy1, sx2, sy2)

    def on_mouse_up(self, event):
        if self.rect_id is None or self.start_x is None or self.start_y is None: return
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
        material = self.material_var.get()
        added = False
        for r in rects_to_process:
            if r[2]-r[0] > 0.2 and r[3]-r[1] > 0.2:
                self.total_created_count += 1
                self.confirmed_floors.append((self.total_created_count, r[0], r[1], r[2], r[3], color, material))
                added = True
        if added: self.color_index += 1
        else: messagebox.showinfo("알림", "영역이 너무 작거나 이미 채워져 있습니다.")
        self.canvas.delete(self.rect_id)
        self.rect_id = None
        self.draw_workspace()
        self.generate_all_sdf_code()

    def on_right_click(self, event):
        gz_x, gz_y = self.screen_to_gz(event.x, event.y)
        for i in range(len(self.confirmed_floors)-1, -1, -1):
            f = self.confirmed_floors[i]
            if f[1] <= gz_x <= f[3] and f[2] <= gz_y <= f[4]:
                del self.confirmed_floors[i]
                self.draw_workspace()
                self.generate_all_sdf_code()
                break

    def get_snap_targets(self):
        tx, ty = [], []
        for f in self.confirmed_floors: tx.extend([f[1], f[3]]); ty.extend([f[2], f[4]])
        for w in self.walls_data: tx.extend([w['px']-w['w']/2, w['px']+w['w']/2]); ty.extend([w['py']-w['h']/2, w['py']+w['h']/2])
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
        self.text_output.insert(tk.END, self.get_sdf_string().strip())

    def get_sdf_string(self):
        code = ""
        for idx, f in enumerate(self.confirmed_floors, start=1):
            _, x1, y1, x2, y2, _, material = f
            gx, gy = round((x1+x2)/2, 3), round((y1+y2)/2, 3)
            gw, gh = round(x2-x1, 3), round(y2-y1, 3)
            code += f"""    <link name='Floor_{idx}'>
      <pose>{gx} {gy} 0.001 0 0 0</pose>
      <collision name='Floor_{idx}_Col'>
        <geometry><box><size>{gw} {gh} 0.01</size></box></geometry>
      </collision>
      <visual name='Floor_{idx}_Vis'>
        <geometry><box><size>{gw} {gh} 0.01</size></box></geometry>
        <material>
          <script><uri>file://media/materials/scripts/gazebo.material</uri><name>{material}</name></script>
        </material>
      </visual>
    </link>\n\n"""
        return code

    # ---------------------------------------------------------
    # 1. 프로젝트 폴더 생성 및 저장 (2단계 분리 방식)
    # ---------------------------------------------------------
    def export_project(self):
        if not self.original_sdf_path:
            messagebox.showwarning("경고", "먼저 model.sdf 파일을 열어주세요.")
            return

        # [1단계] 상위 폴더 선택 (이미 존재하는 폴더만 선택 가능)
        base_dir = filedialog.askdirectory(
            title="프로젝트 폴더를 생성할 '상위 위치'를 선택하세요",
            parent=self.root,
            mustexist=True # 반드시 존재하는 폴더만 선택하게 하여 혼동 방지
        )
        if not base_dir: return

        # [2단계] 새 폴더 이름 입력 전용 창 띄우기
        # 이 창은 메인 창 정중앙에 나타나며, 즉시 입력 가능한 상태가 됩니다.
        project_name = simpledialog.askstring(
            "새 폴더 생성",
            f"선택한 위치: {os.path.basename(base_dir)}\n\n생성할 새 폴더 이름을 입력하세요:",
            initialvalue="My_Floor_Project",
            parent=self.root
        )

        if not project_name: # 취소 시 중단
            return

        # 최종 경로 조합 (상위 폴더 + 입력한 이름)
        full_project_path = os.path.join(base_dir, project_name)

        try:
            # 실제 폴더 생성
            if not os.path.exists(full_project_path):
                os.makedirs(full_project_path)

            # 1. SDF 파일 처리 및 저장
            sdf_save_path = os.path.join(full_project_path, "model.sdf")
            with open(self.original_sdf_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # 기존 Floor 링크 제거 및 새 코드 교체
            pattern = r"\s*<link name='Floor_\d+'>.*?</link>\s*"
            content = re.sub(pattern, "", content, flags=re.DOTALL)
            content = content.replace("</model>", self.get_sdf_string() + "\n</model>", 1)

            with open(sdf_save_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # 2. 설계 도면 이미지 저장
            self.save_image_logic(os.path.join(full_project_path, "floor_plan.png"))
            messagebox.showinfo("성공", f"새 폴더가 생성되었습니다:\n{project_name}\n\n위치: {full_project_path}")

        except Exception as e:
            messagebox.showerror("오류", f"저장 중 오류가 발생했습니다: {str(e)}")


    def save_image_logic(self, file_path):
        """캔버스 내용을 PIL 이미지를 사용하여 파일로 저장합니다."""
        # 바인딩 및 설치 여부 체크
        if not PILLOW_AVAILABLE or Image is None or ImageDraw is None:
            return

        # 💡 [해결] size 인자를 명시적으로 int 튜플로 변환하여 Literal 관련 경고 제거
        canvas_size = (int(self.canvas_w), int(self.canvas_h))

        # 캔버스 크기의 새 이미지 생성
        img = Image.new("RGB", canvas_size, "#f9f9f9") # type: ignore
        draw = ImageDraw.Draw(img)

        # 1. 바닥 그리기
        for idx, f in enumerate(self.confirmed_floors, start=1):
            sx1, sy1 = self.gz_to_screen(f[1], f[2])
            sx2, sy2 = self.gz_to_screen(f[3], f[4])
            draw.rectangle([sx1, sy1, sx2, sy2], fill=f[5], outline="#333333")
            draw.text(((sx1+sx2)/2 - 20, (sy1+sy2)/2 - 5), f"Floor_{idx}", fill="black")

        # 2. 벽 그리기
        for w in self.walls_data:
            sx, sy = self.gz_to_screen(w['px'], w['py'])
            sw, sh = w['w'] * self.scale, w['h'] * self.scale
            draw.rectangle([sx-sw/2, sy-sh/2, sx+sw/2, sy+sh/2], fill="#777777", outline="black")
        img.save(file_path)

    def copy_to_clipboard(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.text_output.get("1.0", tk.END))
        messagebox.showinfo("완료", "코드가 복사되었습니다.")

    def reset_workspace(self):
        self.original_sdf_path = ""
        self.walls_data = []
        self.confirmed_floors = []
        self.pan_x = 0; self.pan_y = 0
        self.total_created_count = 0; self.color_index = 0
        self.draw_workspace()
        self.text_output.delete("1.0", tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = FloorGeneratorApp(root)
    root.mainloop()