import tkinter as tk
from tkinter import messagebox, ttk
from floor_events import FloorEventsMixin
from floor_project import FloorProjectMixin

class FloorGeneratorApp(FloorEventsMixin, FloorProjectMixin):
    def __init__(self, root):
        self.root = root
        self.root.title("Gazebo SDF Floor Master v1.4 - by D.W Lee")
        self.root.geometry("900x980")

        # 변수 초기화
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
        self.material_var = tk.StringVar(value="Custom Image")

        materials = ["Gazebo/Wood", "Gazebo/CeilingTiled", "Gazebo/Grey", "Gazebo/Bricks", "Gazebo/Grass", "Gazebo/Asphalt", "Custom Image"]
        self.mat_combo = ttk.Combobox(right_btn_frame, textvariable=self.material_var, values=materials, state="readonly", width=18)
        self.mat_combo.pack(side=tk.LEFT, padx=(0, 5))

        help_text = "좌 클릭: 바닥 생성  |  우 클릭: 삭제  |  휠: 줌  |  휠 클릭(드래그): 이동"
        tk.Label(top_frame, text=help_text, fg="#818181", font=("Arial", 10, "bold")).pack()

        # 캔버스 바인딩 (이벤트는 FloorEventsMixin 에서 상속받음)
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

        # 하단 제어부 (로직은 FloorProjectMixin 에서 상속받음)
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