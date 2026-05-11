import tkinter as tk
from tkinter import filedialog, messagebox
import xml.etree.ElementTree as ET
import math

class FloorGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("가제보 SDF 바닥 자동 생성기 (자동 스케일 & 복사 기능)")
        self.root.geometry("850x900") # 복사 버튼을 위해 높이 약간 증가

        # 캔버스 고정 크기
        self.canvas_w = 800
        self.canvas_h = 600
        self.canvas_cx = self.canvas_w / 2
        self.canvas_cy = self.canvas_h / 2

        # 동적 스케일링을 위한 변수
        self.scale = 40.0
        self.model_cx = 0.0 # Gazebo 맵의 실제 중앙 X
        self.model_cy = 0.0 # Gazebo 맵의 실제 중앙 Y
        
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.floor_count = 1

        self.setup_ui()

    def setup_ui(self):
        # 1. 상단 버튼 영역
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        load_btn = tk.Button(btn_frame, text="1. model.sdf 파일 열기", command=self.load_sdf, font=("Arial", 12, "bold"))
        load_btn.pack(side=tk.LEFT, padx=10)

        reset_btn = tk.Button(btn_frame, text="초기화", command=self.reset_canvas)
        reset_btn.pack(side=tk.LEFT, padx=10)

        info_label = tk.Label(self.root, text="2. 캔버스 위에서 마우스로 드래그하여 바닥을 깔 공간을 선택하세요.", fg="blue")
        info_label.pack()

        # 2. 도면 표시 캔버스 (크기 고정)
        self.canvas = tk.Canvas(self.root, width=self.canvas_w, height=self.canvas_h, bg="white", relief=tk.SUNKEN, bd=2)
        self.canvas.pack(pady=10)
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        self.draw_grid()

        # 3. 하단 출력 및 복사 버튼 영역
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=25)

        tk.Label(bottom_frame, text="3. 생성된 SDF 코드").pack(side=tk.LEFT)
        
        copy_btn = tk.Button(bottom_frame, text="📋 코드 복사하기", command=self.copy_to_clipboard, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        copy_btn.pack(side=tk.RIGHT)

        self.text_output = tk.Text(self.root, height=10, width=95)
        self.text_output.pack(pady=5)

    def draw_grid(self):
        # 캔버스 정중앙을 가로지르는 십자선 (화면 기준)
        self.canvas.create_line(self.canvas_cx, 0, self.canvas_cx, self.canvas_h, fill="#f0f0f0", dash=(4, 4))
        self.canvas.create_line(0, self.canvas_cy, self.canvas_w, self.canvas_cy, fill="#f0f0f0", dash=(4, 4))

        # 가제보의 실제 원점(0, 0) 위치 표시 (스케일링 적용)
        origin_x = self.canvas_cx + (0 - self.model_cx) * self.scale
        origin_y = self.canvas_cy - (0 - self.model_cy) * self.scale
        
        self.canvas.create_line(origin_x, 0, origin_x, self.canvas_h, fill="#cccccc", dash=(2, 2))
        self.canvas.create_line(0, origin_y, self.canvas_w, origin_y, fill="#cccccc", dash=(2, 2))

    def load_sdf(self):
        filepath = filedialog.askopenfilename(filetypes=[("SDF Files", "*.sdf"), ("All Files", "*.*")])
        if not filepath:
            return

        self.reset_canvas()
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            walls = []
            # 1단계: 모든 벽의 데이터를 파싱하여 리스트에 저장
            for link in root.iter('link'):
                name = link.attrib.get('name', '')
                if 'Wall' in name:
                    wall_data = self.parse_wall(link)
                    if wall_data:
                        walls.append(wall_data)
            
            if not walls:
                messagebox.showwarning("경고", "SDF 파일에서 벽(Wall) 데이터를 찾을 수 없습니다.")
                return

            # 2단계: 맵의 전체 크기(Bounding Box) 계산하여 스케일 설정
            self.calculate_dynamic_scale(walls)

            # 3단계: 계산된 스케일에 맞춰 벽 그리기
            for w in walls:
                self.draw_wall(w)
                
            messagebox.showinfo("성공", "SDF 맵을 화면에 맞게 불러왔습니다. 드래그하여 바닥을 생성하세요!")
        except Exception as e:
            messagebox.showerror("오류", f"파일을 읽는 중 오류가 발생했습니다:\n{e}")

    def parse_wall(self, link):
        try:
            pose_elem = link.find('pose')
            if pose_elem is None: return None
            px, py, pz, r, p, yaw = map(float, pose_elem.text.split())

            size_elem = link.find('.//box/size')
            if size_elem is None: return None
            sx, sy, sz = map(float, size_elem.text.split())

            yaw_deg = abs(math.degrees(yaw)) % 180
            if 80 < yaw_deg < 100:  
                w, h = sy, sx
            else:                   
                w, h = sx, sy
                
            return {'px': px, 'py': py, 'w': w, 'h': h}
        except:
            return None

    def calculate_dynamic_scale(self, walls):
        # 모든 벽의 최소/최대 x, y 좌표 찾기
        min_x = min(w['px'] - w['w']/2 for w in walls)
        max_x = max(w['px'] + w['w']/2 for w in walls)
        min_y = min(w['py'] - w['h']/2 for w in walls)
        max_y = max(w['py'] + w['h']/2 for w in walls)

        # 맵의 실제 넓이와 중심점
        gazebo_w = max_x - min_x
        gazebo_h = max_y - min_y
        self.model_cx = (min_x + max_x) / 2
        self.model_cy = (min_y + max_y) / 2

        # 캔버스 여백(Padding) 설정
        padding = 100
        eff_w = self.canvas_w - padding
        eff_h = self.canvas_h - padding

        # 화면에 꽉 차도록 비율 계산 (0으로 나누기 방지)
        scale_x = eff_w / gazebo_w if gazebo_w > 0 else 40.0
        scale_y = eff_h / gazebo_h if gazebo_h > 0 else 40.0
        
        # 가로/세로 중 더 타이트한 비율을 선택하여 맵이 잘리지 않게 함
        self.scale = min(scale_x, scale_y)
        
        # 맵이 불러와졌으므로 그리드 다시 그리기 (원점 재조정)
        self.canvas.delete("all")
        self.draw_grid()

    def draw_wall(self, w):
        # 가제보 좌표를 캔버스 픽셀 좌표로 변환 (중앙 정렬 및 스케일 적용)
        cx = self.canvas_cx + (w['px'] - self.model_cx) * self.scale
        cy = self.canvas_cy - (w['py'] - self.model_cy) * self.scale # Y축은 반전
        cw = w['w'] * self.scale
        ch = w['h'] * self.scale

        self.canvas.create_rectangle(
            cx - cw/2, cy - ch/2, 
            cx + cw/2, cy + ch/2, 
            fill="darkgray", outline="black"
        )

    def on_mouse_down(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red", width=2, dash=(4, 4))

    def on_mouse_drag(self, event):
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def on_mouse_up(self, event):
        pixel_w = abs(event.x - self.start_x)
        pixel_h = abs(event.y - self.start_y)
        
        if pixel_w < 10 or pixel_h < 10: 
            if self.rect_id: self.canvas.delete(self.rect_id)
            return

        # 드래그한 중심의 픽셀 좌표
        center_pixel_x = (self.start_x + event.x) / 2
        center_pixel_y = (self.start_y + event.y) / 2

        # 픽셀을 다시 가제보 미터(m) 단위 좌표로 변환 (중앙 보정 포함)
        gazebo_x = (center_pixel_x - self.canvas_cx) / self.scale + self.model_cx
        gazebo_y = self.model_cy - (center_pixel_y - self.canvas_cy) / self.scale 
        gazebo_w = pixel_w / self.scale
        gazebo_h = pixel_h / self.scale

        self.generate_sdf_code(round(gazebo_x, 3), round(gazebo_y, 3), round(gazebo_w, 3), round(gazebo_h, 3))

    def generate_sdf_code(self, px, py, w, h):
        floor_name = f"Custom_Floor_{self.floor_count}"
        self.floor_count += 1

        sdf_template = f"""    <link name='{floor_name}'>
      <pose>{px} {py} 0.001 0 0 0</pose>
      <collision name='{floor_name}_Collision'>
        <geometry><box><size>{w} {h} 0.01</size></box></geometry>
        <surface>
          <friction><ode><mu>1.0</mu><mu2>1.0</mu2></ode></friction>
          <contact><ode><kp>1e6</kp><kd>1.0</kd><min_depth>0.001</min_depth></ode></contact>
        </surface>
      </collision>
      <visual name='{floor_name}_Visual'>
        <geometry><box><size>{w} {h} 0.01</size></box></geometry>
        <material>
          <script><uri>file://media/materials/scripts/gazebo.material</uri><name>Gazebo/Wood</name></script>
          <ambient>0.435 0.796 0.674 1</ambient>
          <diffuse>0.435 0.796 0.674 1</diffuse>
        </material>
      </visual>
    </link>"""
        self.text_output.delete(1.0, tk.END)
        self.text_output.insert(tk.END, sdf_template)

    def copy_to_clipboard(self):
        text_to_copy = self.text_output.get(1.0, tk.END).strip()
        if text_to_copy:
            self.root.clipboard_clear()
            self.root.clipboard_append(text_to_copy)
            messagebox.showinfo("복사 완료", "SDF 코드가 클립보드에 복사되었습니다!\nmodel.sdf 파일에 바로 붙여넣기(Ctrl+V) 하세요.")
        else:
            messagebox.showwarning("경고", "복사할 코드가 없습니다. 먼저 도면을 드래그하여 코드를 생성하세요.")

    def reset_canvas(self):
        self.canvas.delete("all")
        self.model_cx = 0.0
        self.model_cy = 0.0
        self.draw_grid()
        self.text_output.delete(1.0, tk.END)
        self.floor_count = 1

if __name__ == "__main__":
    root = tk.Tk()
    app = FloorGeneratorApp(root)
    root.mainloop()