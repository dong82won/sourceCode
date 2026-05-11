import tkinter as tk
from tkinter import filedialog, messagebox
import xml.etree.ElementTree as ET
import math # 각도 계산을 위해 추가

class FloorGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("가제보 SDF 바닥 자동 생성기")
        self.root.geometry("850x850") # 창 크기를 늘림

        # 변수 초기화
        self.scale = 40.0  # 1미터를 40픽셀로 매핑
        self.center_x = 425
        self.center_y = 350
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.floor_count = 1

        self.setup_ui()

    def setup_ui(self):
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        load_btn = tk.Button(btn_frame, text="1. model.sdf 파일 열기", command=self.load_sdf, font=("Arial", 12, "bold"))
        load_btn.pack(side=tk.LEFT, padx=10)

        reset_btn = tk.Button(btn_frame, text="초기화", command=self.reset_canvas)
        reset_btn.pack(side=tk.LEFT, padx=10)

        info_label = tk.Label(self.root, text="2. 캔버스 위에서 마우스로 드래그하여 바닥을 깔 공간을 선택하세요.", fg="blue")
        info_label.pack()

        # 도면 표시 캔버스 (높이를 400에서 600으로 늘려 잘림 현상 해결)
        self.canvas = tk.Canvas(self.root, width=800, height=600, bg="white", relief=tk.SUNKEN, bd=2)
        self.canvas.pack(pady=10)
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        self.draw_grid()

        tk.Label(self.root, text="3. 생성된 SDF 코드 (복사하여 model.sdf에 붙여넣기)").pack()
        self.text_output = tk.Text(self.root, height=10, width=95)
        self.text_output.pack(pady=5)

    def draw_grid(self):
        self.canvas.create_line(self.center_x, 0, self.center_x, 700, fill="#e0e0e0", dash=(4, 4))
        self.canvas.create_line(0, self.center_y, 850, self.center_y, fill="#e0e0e0", dash=(4, 4))

    def load_sdf(self):
        filepath = filedialog.askopenfilename(filetypes=[("SDF Files", "*.sdf"), ("All Files", "*.*")])
        if not filepath:
            return

        self.reset_canvas()
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            for link in root.iter('link'):
                name = link.attrib.get('name', '')
                if 'Wall' in name:
                    self.draw_wall(link)
            messagebox.showinfo("성공", "SDF 파일을 성공적으로 불러왔습니다. 드래그하여 바닥을 생성하세요!")
        except Exception as e:
            messagebox.showerror("오류", f"파일을 읽는 중 오류가 발생했습니다:\n{e}")

    def draw_wall(self, link):
        try:
            # Pose 추출 (방어적 코드 적용)
            pose_elem = link.find('pose')
            if pose_elem is None: return
            px, py, pz, r, p, yaw = map(float, pose_elem.text.split())

            # Size 추출
            size_elem = link.find('.//box/size')
            if size_elem is None: return
            sx, sy, sz = map(float, size_elem.text.split())

            # [핵심 수정] 수학적으로 정확한 회전(Yaw) 판단
            yaw_deg = abs(math.degrees(yaw)) % 180
            if 80 < yaw_deg < 100:  # 90도 부근 (수직으로 세워진 벽)
                w, h = sy, sx
            else:                   # 0도, 180도 부근 (수평으로 누운 벽)
                w, h = sx, sy

            # 화면 픽셀 좌표로 변환
            cx = self.center_x + (px * self.scale)
            cy = self.center_y - (py * self.scale)
            cw = w * self.scale
            ch = h * self.scale

            self.canvas.create_rectangle(
                cx - cw/2, cy - ch/2, 
                cx + cw/2, cy + ch/2, 
                fill="darkgray", outline="black"
            )
        except Exception as e:
            print(f"벽 파싱 중 오류: {e}") # 오류 시 터미널에 원인 출력

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

        center_pixel_x = (self.start_x + event.x) / 2
        center_pixel_y = (self.start_y + event.y) / 2

        gazebo_x = (center_pixel_x - self.center_x) / self.scale
        gazebo_y = (self.center_y - center_pixel_y) / self.scale 
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

    def reset_canvas(self):
        self.canvas.delete("all")
        self.draw_grid()
        self.text_output.delete(1.0, tk.END)
        self.floor_count = 1

if __name__ == "__main__":
    root = tk.Tk()
    app = FloorGeneratorApp(root)
    root.mainloop()