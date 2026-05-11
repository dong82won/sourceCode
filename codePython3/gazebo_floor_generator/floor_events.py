import floor_utils
import tkinter as tk

class FloorEventsMixin:
    # --- IDE(정적 분석기) 경고 해결을 위한 타입 힌트 선언부 ---
    # 실제 값은 main.py의 FloorGeneratorApp에서 할당됩니다.
    canvas_w: int
    canvas_h: int
    scale: float
    pan_x: float
    pan_y: float
    last_pan_x: float
    last_pan_y: float
    model_cx: float
    model_cy: float
    walls_data: list
    confirmed_floors: list
    color_palette: list
    color_index: int
    start_x: float | None
    start_y: float | None
    rect_id: int | None
    canvas: tk.Canvas
    material_var: tk.StringVar

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
        # 1. start_x와 start_y가 None인지 확실히 검사
        if self.start_x is None or self.start_y is None:
            return
        
        # 2. 에디터가 확실히 float로 인식하도록 지역 변수로 복사
        sx, sy = float(self.start_x), float(self.start_y)
        
        gx, gy = self.screen_to_gz(event.x, event.y)
        tx, ty = self.get_snap_targets()
        cx, cy = self.snap_value(gx, tx), self.snap_value(gy, ty)
        
        sx1, sy1 = self.gz_to_screen(sx, sy)
        sx2, sy2 = self.gz_to_screen(cx, cy)
        # [해결] rect_id가 확실히 존재할 때만 캔버스 좌표를 업데이트하도록 방어 로직 추가
        if self.rect_id is not None:
          self.canvas.coords(self.rect_id, sx1, sy1, sx2, sy2)

    def on_mouse_up(self, event):
        # 1. 여기서도 확실하게 None 검사
        if self.start_x is None or self.start_y is None: 
            return
            
        # 2. IDE 경고를 없애기 위해 지역 변수로 안전하게 할당
        sx, sy = float(self.start_x), float(self.start_y)
        
        gx, gy = self.screen_to_gz(event.x, event.y)
        tx, ty = self.get_snap_targets()
        end_x, end_y = float(self.snap_value(gx, tx)), float(self.snap_value(gy, ty))
        
        # 3. self.start_x 대신 sx, sy 사용
        if abs(end_x - sx) < 0.1 or abs(end_y - sy) < 0.1:
            if self.rect_id: self.canvas.delete(self.rect_id)
            self.start_x = self.start_y = None
            return

        # 4. min, max에도 sx, sy 사용 (이제 에러가 사라집니다!)
        new_rect = (min(sx, end_x), min(sy, end_y), max(sx, end_x), max(sy, end_y))
        
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
        
        if self.rect_id: self.canvas.delete(self.rect_id)
        self.start_x = self.start_y = None
        
        self.draw_workspace()
        self.update_sdf_text()# type: ignore

    def on_right_click(self, event):
        gx, gy = self.screen_to_gz(event.x, event.y)
        self.confirmed_floors = [f for f in self.confirmed_floors if not (f[0]<=gx<=f[2] and f[1]<=gy<=f[3])]
        self.draw_workspace()
        self.update_sdf_text()# type: ignore

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

        floor_idx, img_idx = 1, 1
        for f in self.confirmed_floors:
            s1 = self.gz_to_screen(f[0], f[1])
            s2 = self.gz_to_screen(f[2], f[3])
            self.canvas.create_rectangle(s1[0], s1[1], s2[0], s2[1], fill=f[4], outline="#333")

            # 실제 가로(gw), 세로(gh) 미터 값 계산
            gw = abs(f[2] - f[0])
            gh = abs(f[3] - f[1])

            # 💡 [수정] 미터당 200픽셀을 곱해 추천 해상도를 정수로 계산
            px_w = int(gw * 200)
            px_h = int(gh * 200)

            if f[5] == "Custom Image":
                # 💡 [수정] 비율 대신 픽셀(px) 단위로 표시 (예: 1200 x 770 px)
                label_text = f"image_{img_idx}\n[{px_w} x {px_h} px]"
                img_idx += 1
            else:
                label_text = f"Floor_{floor_idx}"
                floor_idx += 1

            # self.canvas.create_text((s1[0]+s2[0])/2, (s1[1]+s2[1])/2, ㅏtext=label_text, font=("Arial", 10, "bold"))
            self.canvas.create_text((s1[0]+s2[0])/2, (s1[1]+s2[1])/2, text=label_text, font=("Arial", 10, "bold"), justify="center")
            

        for w in self.walls_data:
            s = self.gz_to_screen(w['px'], w['py'])
            sw, sh = w['w']*self.scale, w['h']*self.scale
            self.canvas.create_rectangle(s[0]-sw/2, s[1]-sh/2, s[0]+sw/2, s[1]+sh/2, fill="#777")