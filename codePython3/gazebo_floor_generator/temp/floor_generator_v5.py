import tkinter as tk
from tkinter import filedialog, messagebox
import xml.etree.ElementTree as ET
import math

class FloorGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("가제보 SDF 바닥 생성기 (삭제 버그 수정판)")
        self.root.geometry("850x950")

        self.canvas_w = 800
        self.canvas_h = 600
        self.canvas_cx = self.canvas_w / 2
        self.canvas_cy = self.canvas_h / 2

        self.scale = 40.0
        self.model_cx = 0.0 
        self.model_cy = 0.0 
        
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        
        # [수정] 고유 ID를 포함한 바닥 리스트 (id, x1, y1, x2, y2, color)
        self.confirmed_floors = [] 
        self.total_created_count = 0 # 고유 번호 생성을 위한 카운터
        
        self.color_palette = ["#BAE1FF", "#FFB3BA", "#FFDFBA", "#FFFFBA", "#BAFFC9", "#E0BBE4", "#D4F0F0", "#FFC4E1"]
        self.color_index = 0
        self.snap_x_targets = []
        self.snap_y_targets = []

        self.setup_ui()

    def setup_ui(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(padx=25, pady=10, fill=tk.BOTH, expand=True)

        # 1. 상단 컨트롤 영역
        top_frame = tk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 5))
        btn_frame = tk.Frame(top_frame)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="1. model.sdf 열기", command=self.load_sdf, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="초기화", command=self.reset_canvas).pack(side=tk.LEFT, padx=5)

        tk.Label(top_frame, text="좌클릭 드래그: 생성  |  우클릭: 해당 조각 삭제", fg="red", font=("Arial", 10, "bold")).pack()

        # 2. 캔버스 영역
        self.canvas = tk.Canvas(main_frame, width=self.canvas_w, height=self.canvas_h, bg="white", relief=tk.SUNKEN, bd=2)
        self.canvas.pack(pady=5)
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<ButtonPress-3>", self.on_right_click) # Win/Linux
        self.canvas.bind("<ButtonPress-2>", self.on_right_click) # Mac

        self.draw_grid()

        # 3. 하단 텍스트 및 복사 영역
        bottom_frame = tk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        tk.Label(bottom_frame, text="3. 생성된 SDF 코드 (자동 갱신)", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        tk.Button(bottom_frame, text="📋 전체 코드 복사", command=self.copy_to_clipboard, bg="#4CAF50", fg="white", font=("Arial", 9, "bold")).pack(side=tk.RIGHT)

        text_frame = tk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_output = tk.Text(text_frame, height=12, yscrollcommand=scrollbar.set, font=("Consolas", 9))
        self.text_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_output.yview)

    def draw_grid(self):
        self.canvas.create_line(self.canvas_cx, 0, self.canvas_cx, self.canvas_h, fill="#f0f0f0", dash=(4, 4))
        self.canvas.create_line(0, self.canvas_cy, self.canvas_w, self.canvas_cy, fill="#f0f0f0", dash=(4, 4))
        origin_x = self.canvas_cx + (0 - self.model_cx) * self.scale
        origin_y = self.canvas_cy - (0 - self.model_cy) * self.scale
        self.canvas.create_line(origin_x, 0, origin_x, self.canvas_h, fill="#cccccc", dash=(2, 2))
        self.canvas.create_line(0, origin_y, self.canvas_w, origin_y, fill="#cccccc", dash=(2, 2))

    def load_sdf(self):
        filepath = filedialog.askopenfilename(filetypes=[("SDF Files", "*.sdf")])
        if not filepath: return
        self.reset_canvas()
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            walls = []
            for link in root.iter('link'):
                if 'Wall' in link.attrib.get('name', ''):
                    wall_data = self.parse_wall(link)
                    if wall_data: walls.append(wall_data)
            if not walls: return
            self.calculate_dynamic_scale(walls)
            for w in walls: self.draw_wall(w)
            self.canvas.tag_raise("wall")
        except Exception as e: messagebox.showerror("오류", str(e))

    def parse_wall(self, link):
        try:
            p = list(map(float, link.find('pose').text.split()))
            s = list(map(float, link.find('.//box/size').text.split()))
            yaw = abs(math.degrees(p[5])) % 180
            w, h = (s[1], s[0]) if 80 < yaw < 100 else (s[0], s[1])
            return {'px': p[0], 'py': p[1], 'w': w, 'h': h}
        except: return None

    def calculate_dynamic_scale(self, walls):
        min_x = min(w['px'] - w['w']/2 for w in walls)
        max_x = max(w['px'] + w['w']/2 for w in walls)
        min_y = min(w['py'] - w['h']/2 for w in walls)
        max_y = max(w['py'] + w['h']/2 for w in walls)
        self.model_cx, self.model_cy = (min_x + max_x) / 2, (min_y + max_y) / 2
        self.scale = min((self.canvas_w-100)/(max_x-min_x), (self.canvas_h-100)/(max_y-min_y))
        self.canvas.delete("all"); self.draw_grid()

    def draw_wall(self, w):
        cx, cy = self.canvas_cx + (w['px']-self.model_cx)*self.scale, self.canvas_cy - (w['py']-self.model_cy)*self.scale
        cw, ch = w['w']*self.scale, w['h']*self.scale
        self.canvas.create_rectangle(cx-cw/2, cy-ch/2, cx+cw/2, cy+ch/2, fill="#555", tags="wall")

    def on_mouse_down(self, event):
        self.snap_x_targets = []
        self.snap_y_targets = []
        for r in self.confirmed_floors: self.snap_x_targets.extend([r[1], r[3]]); self.snap_y_targets.extend([r[2], r[4]])
        for item in self.canvas.find_withtag("wall"):
            c = self.canvas.coords(item)
            self.snap_x_targets.extend([c[0], c[2]]); self.snap_y_targets.extend([c[1], c[3]])
        self.start_x = self.get_snapped_coord(event.x, self.snap_x_targets)
        self.start_y = self.get_snapped_coord(event.y, self.snap_y_targets)
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red", width=2)

    def on_mouse_drag(self, event):
        cur_x, cur_y = self.get_snapped_coord(event.x, self.snap_x_targets), self.get_snapped_coord(event.y, self.snap_y_targets)
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)

    def get_snapped_coord(self, val, targets):
        closest = min(targets, key=lambda t: abs(val-t)) if targets else val
        return closest if abs(val-closest) < 15 else val

    def on_mouse_up(self, event):
        cur_x, cur_y = self.get_snapped_coord(event.x, self.snap_x_targets), self.get_snapped_coord(event.y, self.snap_y_targets)
        if abs(cur_x - self.start_x) < 5 or abs(cur_y - self.start_y) < 5:
            self.canvas.delete(self.rect_id); return
        
        new_rect = (min(self.start_x, cur_x), min(self.start_y, cur_y), max(self.start_x, cur_x), max(self.start_y, cur_y))
        rects_to_process = [new_rect]
        for old in self.confirmed_floors:
            next_rects = []
            for r in rects_to_process: next_rects.extend(self.subtract_rect(r, old[1:5]))
            rects_to_process = next_rects

        color = self.color_palette[self.color_index % len(self.color_palette)]
        added = False
        for r in rects_to_process:
            if r[2]-r[0] > 2 and r[3]-r[1] > 2:
                self.total_created_count += 1
                self.confirmed_floors.append((self.total_created_count, r[0], r[1], r[2], r[3], color))
                added = True
        if added: self.color_index += 1
        self.canvas.delete(self.rect_id); self.redraw_floors(); self.generate_all_sdf_code()

    # [수정] 우클릭 삭제 로직 강화
    def on_right_click(self, event):
        found = False
        for i in range(len(self.confirmed_floors)-1, -1, -1):
            f = self.confirmed_floors[i]
            if f[1] <= event.x <= f[3] and f[2] <= event.y <= f[4]:
                del self.confirmed_floors[i]
                found = True
                break
        if found:
            self.redraw_floors()
            self.generate_all_sdf_code() # 코드 즉시 갱신

    def subtract_rect(self, r1, r2):
        ix1, iy1, ix2, iy2 = max(r1[0], r2[0]), max(r1[1], r2[1]), min(r1[2], r2[2]), min(r1[3], r2[3])
        if ix1 >= ix2 or iy1 >= iy2: return [r1]
        res = []
        if r1[0] < ix1: res.append((r1[0], r1[1], ix1, r1[3]))
        if ix2 < r1[2]: res.append((ix2, r1[1], r1[2], r1[3]))
        if r1[1] < iy1: res.append((ix1, r1[1], ix2, iy1))
        if iy2 < r1[3]: res.append((ix1, iy2, ix2, r1[3]))
        return res

    def redraw_floors(self):
        self.canvas.delete("floor")
        for f in self.confirmed_floors:
            self.canvas.create_rectangle(f[1], f[2], f[3], f[4], fill=f[5], outline="#333", tags="floor")
        self.canvas.tag_raise("wall")

    def generate_all_sdf_code(self):
        self.text_output.delete("1.0", tk.END) # 텍스트 박스 완전 초기화
        code = ""
        for f in self.confirmed_floors:
            fid, x1, y1, x2, y2, _ = f
            gx = round(((x1+x2)/2 - self.canvas_cx)/self.scale + self.model_cx, 3)
            gy = round(self.model_cy - ((y1+y2)/2 - self.canvas_cy)/self.scale, 3)
            gw, gh = round((x2-x1)/self.scale, 3), round((y2-y1)/self.scale, 3)
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
          <script><uri>file://media/materials/scripts/gazebo.material</uri><name>Gazebo/Wood</name></script>
          <ambient>0.435 0.796 0.674 1</ambient>
        </material>
      </visual>
    </link>\n\n"""
        self.text_output.insert(tk.END, code.strip())

    def copy_to_clipboard(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.text_output.get("1.0", tk.END))
        messagebox.showinfo("완료", "코드가 복사되었습니다.")

    def reset_canvas(self):
        self.canvas.delete("all"); self.confirmed_floors = []; self.total_created_count = 0
        self.color_index = 0; self.draw_grid(); self.text_output.delete("1.0", tk.END)

if __name__ == "__main__":
    root = tk.Tk(); app = FloorGeneratorApp(root); root.mainloop()