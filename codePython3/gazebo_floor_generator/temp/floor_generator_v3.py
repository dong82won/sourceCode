import tkinter as tk
from tkinter import filedialog, messagebox
import xml.etree.ElementTree as ET
import math

class FloorGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("가제보 SDF 바닥 자동 생성기 (색상 구분 & 레이아웃 정렬)")
        self.root.geometry("850x900")

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
        
        # 바닥 영역 데이터 저장 (x1, y1, x2, y2, color)
        self.confirmed_floors = [] 
        
        # [추가] 영역 구분을 위한 파스텔톤 색상 팔레트
        self.color_palette = ["#BAE1FF", "#FFB3BA", "#FFDFBA", "#FFFFBA", "#BAFFC9", "#E0BBE4", "#D4F0F0", "#FFC4E1"]
        self.color_index = 0

        self.setup_ui()

    def setup_ui(self):
        # [핵심 수정] 모든 요소를 동일한 너비로 맞추기 위한 메인 컨테이너 프레임
        main_frame = tk.Frame(self.root)
        main_frame.pack(padx=25, pady=10, fill=tk.BOTH, expand=True)

        # 1. 상단 버튼 및 안내 영역
        top_frame = tk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 5))

        btn_frame = tk.Frame(top_frame)
        btn_frame.pack(pady=5)
        
        load_btn = tk.Button(btn_frame, text="1. model.sdf 파일 열기", command=self.load_sdf, font=("Arial", 11, "bold"))
        load_btn.pack(side=tk.LEFT, padx=5)

        reset_btn = tk.Button(btn_frame, text="초기화", command=self.reset_canvas)
        reset_btn.pack(side=tk.LEFT, padx=5)

        info_label = tk.Label(top_frame, text="2. 드래그하여 바닥 생성 (기존 벽/바닥 근처에 놓으면 자동으로 자석처럼 붙습니다)", fg="blue")
        info_label.pack()

        # 2. 도면 표시 캔버스 (크기 고정)
        self.canvas = tk.Canvas(main_frame, width=self.canvas_w, height=self.canvas_h, bg="white", relief=tk.SUNKEN, bd=2)
        # 캔버스를 고정 크기로 띄우되 중앙 정렬
        self.canvas.pack(pady=5)
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        self.draw_grid()

        # 3. 하단 출력 및 복사 버튼 영역 (캔버스와 폭 맞춤)
        bottom_frame = tk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(5, 0))

        tk.Label(bottom_frame, text="3. 생성된 누적 SDF 코드", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        copy_btn = tk.Button(bottom_frame, text="📋 전체 코드 복사하기", command=self.copy_to_clipboard, bg="#4CAF50", fg="white", font=("Arial", 9, "bold"))
        copy_btn.pack(side=tk.RIGHT)

        # 텍스트 박스와 스크롤바 묶음
        text_frame = tk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # width를 지정하지 않고 fill=tk.BOTH로 프레임 너비에 강제 맞춤
        self.text_output = tk.Text(text_frame, height=10, yscrollcommand=scrollbar.set)
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
        filepath = filedialog.askopenfilename(filetypes=[("SDF Files", "*.sdf"), ("All Files", "*.*")])
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
        except Exception as e:
            messagebox.showerror("오류", f"파일을 읽는 중 오류가 발생했습니다:\n{e}")

    def parse_wall(self, link):
        try:
            pose_elem = link.find('pose')
            size_elem = link.find('.//box/size')
            px, py, pz, r, p, yaw = map(float, pose_elem.text.split())
            sx, sy, sz = map(float, size_elem.text.split())
            yaw_deg = abs(math.degrees(yaw)) % 180
            w, h = (sy, sx) if 80 < yaw_deg < 100 else (sx, sy)
            return {'px': px, 'py': py, 'w': w, 'h': h}
        except: return None

    def calculate_dynamic_scale(self, walls):
        min_x = min(w['px'] - w['w']/2 for w in walls)
        max_x = max(w['px'] + w['w']/2 for w in walls)
        min_y = min(w['py'] - w['h']/2 for w in walls)
        max_y = max(w['py'] + w['h']/2 for w in walls)

        gazebo_w = max_x - min_x
        gazebo_h = max_y - min_y
        self.model_cx = (min_x + max_x) / 2
        self.model_cy = (min_y + max_y) / 2

        scale_x = (self.canvas_w - 100) / gazebo_w if gazebo_w > 0 else 40.0
        scale_y = (self.canvas_h - 100) / gazebo_h if gazebo_h > 0 else 40.0
        self.scale = min(scale_x, scale_y)
        self.canvas.delete("all")
        self.draw_grid()

    def draw_wall(self, w):
        cx = self.canvas_cx + (w['px'] - self.model_cx) * self.scale
        cy = self.canvas_cy - (w['py'] - self.model_cy) * self.scale
        cw, ch = w['w'] * self.scale, w['h'] * self.scale
        self.canvas.create_rectangle(cx - cw/2, cy - ch/2, cx + cw/2, cy + ch/2, fill="darkgray", outline="black", tags="wall")

    def on_mouse_down(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect_id: self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red", width=2, dash=(4, 4))

    def on_mouse_drag(self, event):
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def get_snapped_coord(self, val, targets, threshold=15):
        closest_t = None
        min_dist = threshold
        for t in targets:
            dist = abs(val - t)
            if dist < min_dist:
                min_dist = dist
                closest_t = t
        return closest_t if closest_t is not None else val

    def on_mouse_up(self, event):
        if abs(event.x - self.start_x) < 10 or abs(event.y - self.start_y) < 10: 
            if self.rect_id: self.canvas.delete(self.rect_id)
            return

        snap_x = []
        snap_y = []
        for r in self.confirmed_floors:
            snap_x.extend([r[0], r[2]])
            snap_y.extend([r[1], r[3]])
            
        for item in self.canvas.find_withtag("wall"):
            coords = self.canvas.coords(item)
            if len(coords) == 4:
                snap_x.extend([coords[0], coords[2]])
                snap_y.extend([coords[1], coords[3]])

        x1 = self.get_snapped_coord(min(self.start_x, event.x), snap_x)
        y1 = self.get_snapped_coord(min(self.start_y, event.y), snap_y)
        x2 = self.get_snapped_coord(max(self.start_x, event.x), snap_x)
        y2 = self.get_snapped_coord(max(self.start_y, event.y), snap_y)

        new_rect = (x1, y1, x2, y2)

        rects_to_process = [new_rect]
        for old_data in self.confirmed_floors:
            old_rect = old_data[:4] # 색상 데이터를 제외한 좌표만 추출
            next_rects = []
            for r in rects_to_process:
                next_rects.extend(self.subtract_rect(r, old_rect))
            rects_to_process = next_rects

        # [수정] 새로 추가될 조각들에 현재 순서의 색상을 부여
        current_color = self.color_palette[self.color_index % len(self.color_palette)]
        added_new_piece = False
        
        for r in rects_to_process:
            if r[2] - r[0] > 1 and r[3] - r[1] > 1:
                self.confirmed_floors.append((r[0], r[1], r[2], r[3], current_color))
                added_new_piece = True

        # 유효한 영역이 하나라도 추가되었다면 다음 드래그를 위해 색상 인덱스 증가
        if added_new_piece:
            self.color_index += 1

        if self.rect_id: self.canvas.delete(self.rect_id)
        
        self.redraw_floors()
        self.generate_all_sdf_code()

    def subtract_rect(self, r1, r2):
        ix1, iy1 = max(r1[0], r2[0]), max(r1[1], r2[1])
        ix2, iy2 = min(r1[2], r2[2]), min(r1[3], r2[3])

        if ix1 >= ix2 or iy1 >= iy2: return [r1]

        result = []
        if r1[0] < ix1: result.append((r1[0], r1[1], ix1, r1[3])) 
        if ix2 < r1[2]: result.append((ix2, r1[1], r1[2], r1[3])) 
        if r1[1] < iy1: result.append((ix1, r1[1], ix2, iy1))     
        if iy2 < r1[3]: result.append((ix1, iy2, ix2, r1[3]))     
        return result

    def redraw_floors(self):
        self.canvas.delete("floor")
        for r in self.confirmed_floors:
            # r[4]에 저장된 개별 색상 값을 불러와 채우기
            self.canvas.create_rectangle(r[0], r[1], r[2], r[3], fill=r[4], outline="#555555", tags="floor")
        self.canvas.tag_raise("wall")

    def generate_all_sdf_code(self):
        self.text_output.delete(1.0, tk.END)
        all_code = ""
        for idx, r in enumerate(self.confirmed_floors):
            cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
            pw, ph = r[2] - r[0], r[3] - r[1]

            gazebo_x = (cx - self.canvas_cx) / self.scale + self.model_cx
            gazebo_y = self.model_cy - (cy - self.canvas_cy) / self.scale 
            gazebo_w, gazebo_h = pw / self.scale, ph / self.scale

            floor_name = f"Custom_Floor_{idx + 1}"
            sdf_template = f"""    <link name='{floor_name}'>
      <pose>{round(gazebo_x, 3)} {round(gazebo_y, 3)} 0.001 0 0 0</pose>
      <collision name='{floor_name}_Collision'>
        <geometry><box><size>{round(gazebo_w, 3)} {round(gazebo_h, 3)} 0.01</size></box></geometry>
        <surface>
          <friction><ode><mu>1.0</mu><mu2>1.0</mu2></ode></friction>
          <contact><ode><kp>1e6</kp><kd>1.0</kd><min_depth>0.001</min_depth></ode></contact>
        </surface>
      </collision>
      <visual name='{floor_name}_Visual'>
        <geometry><box><size>{round(gazebo_w, 3)} {round(gazebo_h, 3)} 0.01</size></box></geometry>
        <material>
          <script><uri>file://media/materials/scripts/gazebo.material</uri><name>Gazebo/Wood</name></script>
          <ambient>0.435 0.796 0.674 1</ambient>
          <diffuse>0.435 0.796 0.674 1</diffuse>
        </material>
      </visual>
    </link>"""
            all_code += sdf_template + "\n\n"
        self.text_output.insert(tk.END, all_code.strip())

    def copy_to_clipboard(self):
        text_to_copy = self.text_output.get(1.0, tk.END).strip()
        if text_to_copy:
            self.root.clipboard_clear()
            self.root.clipboard_append(text_to_copy)
            messagebox.showinfo("복사 완료", f"총 {len(self.confirmed_floors)}개의 바닥 코드가 복사되었습니다!")
        else:
            messagebox.showwarning("경고", "복사할 코드가 없습니다.")

    def reset_canvas(self):
        self.canvas.delete("all")
        self.model_cx = 0.0
        self.model_cy = 0.0
        self.confirmed_floors.clear()
        self.color_index = 0 # 색상 인덱스도 초기화
        self.draw_grid()
        self.text_output.delete(1.0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = FloorGeneratorApp(root)
    root.mainloop()