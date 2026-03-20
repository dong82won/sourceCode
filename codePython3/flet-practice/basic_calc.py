from dataclasses import field

import flet as ft
import math

@ft.control
class CalcButton(ft.Button):
    expand: int = field(default_factory=lambda: 1)


@ft.control
class DigitButton(CalcButton):
    bgcolor: ft.Colors = ft.Colors.WHITE_24
    color: ft.Colors = ft.Colors.WHITE


@ft.control
class ActionButton(CalcButton):
    bgcolor: ft.Colors = ft.Colors.ORANGE
    color: ft.Colors = ft.Colors.WHITE


@ft.control
class ExtraActionButton(CalcButton):
    bgcolor: ft.Colors = ft.Colors.BLUE_GREY_100
    color: ft.Colors = ft.Colors.BLACK


# 버튼 정의 (모양 색)
# 동글한 버튼
@ft.control
class EngineeringChangeButton(ft.IconButton):
    icon_color: ft.Colors = ft.Colors.BLACK
    bgcolor: ft.Colors = ft.Colors.WHITE
    width: int = 40
    height: int = 40




@ft.control
class CalculatorApp(ft.Container):
    # 전환 용 생성자?
    def __init__(self, switch_callback):
        super().__init__()
        self.switch_callback = switch_callback
        self.reset()
        self.width = 350
        self.bgcolor = ft.Colors.BLACK
        self.border_radius = ft.BorderRadius.all(20)
        self.padding = 20
        self.result = ft.Text(value="0", color=ft.Colors.WHITE, size=20)
        self.mode_text = ft.Text(value="DEG", color=ft.Colors.WHITE, size=14)
        self.angle_mode = "DEG"

        # 수정 사칙연산
        self.expression = ""          # 화면 표시용 수식
        self.eval_expression = ""     # 실제 eval 계산용 수식
        self.current_input = "0"      # 현재 입력 중인 숫자
        self.just_calculated = False  # = 직후 여부
        # self.pending_function = None  # sin, cos, tan 대기 상태
        self.open_parens = 0   # 열린 괄호 개수
        
        self.content = ft.Column(
            controls=[
                ft.Row(
                    controls=[self.result],
                    alignment=ft.MainAxisAlignment.END,
                ),
                ft.Row(
                    controls=[
                        EngineeringChangeButton(   # 백스페이스 버튼 추가
                            icon=ft.Icons.BACKSPACE,
                            on_click=self.backspace_clicked
                        ),
                        EngineeringChangeButton(
                            icon=ft.Icons.AUTORENEW,
                            on_click=self.switch_callback
                        )
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
                ft.Row(
                    controls=[                        
                        ExtraActionButton(content="AC", on_click=self.button_clicked),
                        ExtraActionButton(content="()", on_click=self.button_clicked),
                        ExtraActionButton(content="%", on_click=self.button_clicked),
                        ActionButton(content="/", on_click=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[                        
                        DigitButton(content="7", on_click=self.button_clicked),
                        DigitButton(content="8", on_click=self.button_clicked),
                        DigitButton(content="9", on_click=self.button_clicked),
                        ActionButton(content="*", on_click=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[                        
                        DigitButton(content="4", on_click=self.button_clicked),
                        DigitButton(content="5", on_click=self.button_clicked),
                        DigitButton(content="6", on_click=self.button_clicked),
                        ActionButton(content="-", on_click=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[                        
                        DigitButton(content="1", on_click=self.button_clicked),
                        DigitButton(content="2", on_click=self.button_clicked),
                        DigitButton(content="3", on_click=self.button_clicked),
                        ActionButton(content="+", on_click=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[                        
                        DigitButton(content="0", expand=2, on_click=self.button_clicked),
                        DigitButton(content=".", on_click=self.button_clicked),
                        ActionButton(content="=", on_click=self.button_clicked),
                    ]
                ),
            ]
        )


    def button_clicked(self, e):
        data = e.control.content
        print(f"Button clicked with data = {data}")

        if self.result.value == "Error" or data == "AC":
            self.result.value = "0"
            self.mode_text.value = self.angle_mode
            self.reset()

            # 수정 사칙연산
            self.expression = ""
            self.eval_expression = ""
            self.current_input = "0"
            self.just_calculated = False
            # self.pending_function = None
            self.open_parens = 0
        # 수정 사칙연산
        elif data in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "."):
            if self.just_calculated:
                self.expression = ""
                self.eval_expression = ""
                self.current_input = "0"
                self.just_calculated = False
                # self.pending_function = None
                
            # π 뒤에 숫자 누르면 자동 곱하기
            if self.expression and self.expression[-1] == "π":
                self.expression += "*"
                self.eval_expression += "*"

            if self.current_input == "0" and data != ".":
                self.current_input = data
            else:
                if data == "." and "." in self.current_input:
                    self.update()
                    return
                self.current_input += data # if self.current_input != "0" else data 

            self.expression += data
            self.eval_expression += data
            self.result.value = self.expression if self.expression else "0"
            self.new_operand = False

        # 수정 사칙연산
        elif data in ("+", "-", "*", "/"):
            if self.just_calculated:
                self.expression = self.result.value
                self.eval_expression = self.result.value
                self.just_calculated = False
                self.current_input = self.result.value

            if not self.expression:
                if data == "-":
                    self.expression = "-"
                    self.eval_expression = "-"
                    self.current_input = "-"
                    self.result.value = self.expression
                self.update()
                return

            # self.close_pending_function()

            if self.expression and self.expression[-1] in ("+", "-", "*", "/"):
                self.expression = self.expression[:-1] + data
                self.eval_expression = self.eval_expression[:-1] + data
            else:
                self.expression += data
                self.eval_expression += data

            self.current_input = "0"
            self.new_operand = True
            self.result.value = self.expression
            
        # 수정 사칙연산
        elif data == "()":
            if self.just_calculated:
                self.expression = self.result.value
                self.eval_expression = self.result.value
                self.current_input = self.result.value
                self.just_calculated = False

            # 닫는 괄호를 넣을 수 있는 경우
            if self.open_parens > 0 and self.expression and (
                self.expression[-1].isdigit() or self.expression[-1] == ")" or self.expression[-1] == "."
            ):
                self.expression += ")"
                self.eval_expression += ")"
                self.open_parens -= 1
                self.result.value = self.expression
                self.new_operand = True

            else:
                # 숫자나 닫는 괄호 뒤에 여는 괄호가 오면 곱셈 처리
                if self.expression and (
                    self.expression[-1].isdigit() or self.expression[-1] == ")" or self.expression[-1] == "."
                ):
                    self.expression += "*"
                    self.eval_expression += "*"

                self.expression += "("
                self.eval_expression += "("
                self.open_parens += 1
                self.result.value = self.expression
                self.new_operand = True

        # 수정 사칙연산
        elif data == "=":
            try:
                if not self.eval_expression:
                    self.update()
                    return

                eval_expr = self.eval_expression + (")" * self.open_parens)

      

                calc_result = eval(eval_expr,  {})
                calc_result = self.format_number(calc_result)

                self.result.value = str(calc_result)
                self.expression = str(calc_result)
                self.eval_expression = str(calc_result)
                self.current_input = str(calc_result)
                self.new_operand = True
                self.just_calculated = True
                self.open_parens = 0   # 추가
                #self.pending_function = None
                
            except:
                self.result.value = "Error"
                self.expression = ""
                self.eval_expression = ""
                self.current_input = "0"
                self.just_calculated = False
                #self.pending_function = None
                self.open_parens = 0   # 추가
                self.reset()

        # 수정 사칙연산
        elif data == "%":
            try:
                if self.eval_expression:
                    eval_expr = self.eval_expression + (")" * self.open_parens)
                    calc_result = eval(eval_expr, {}) / 100
                else:
                    calc_result = float(self.current_input) / 100

                calc_result = self.format_number(calc_result)
                self.result.value = str(calc_result)
                self.expression = str(calc_result)
                self.eval_expression = str(calc_result)
                self.current_input = str(calc_result)
                self.new_operand = True
                self.just_calculated = True
                self.open_parens = 0   # 추가
                #self.pending_function = None

            except:
                self.result.value = "Error"
                self.expression = ""
                self.eval_expression = ""
                self.current_input = "0"
                self.just_calculated = False
                self.open_parens = 0   # 추가
                #self.pending_function = None
                self.reset()

        # 수정 사칙연산
        elif data == "+/-":
            if self.just_calculated:
                self.expression = self.result.value
                self.eval_expression = self.result.value
                self.current_input = self.result.value
                self.just_calculated = False

            if self.current_input.startswith("-"):
                new_input = self.current_input[1:]
            else:
                new_input = "-" + self.current_input

            if self.expression.endswith(self.current_input):
                self.expression = self.expression[:-len(self.current_input)] + new_input
                self.eval_expression = self.eval_expression[:-len(self.current_input)] + new_input
                self.current_input = new_input
                self.result.value = self.expression


        self.update()
    def backspace_clicked(self, e):
        if not self.expression:
            return

        last = self.expression[-1]

        self.expression = self.expression[:-1]
        self.eval_expression = self.eval_expression[:-1]

        if last == "(":
            self.open_parens = max(0, self.open_parens - 1)
        elif last == ")":
            self.open_parens += 1

        self.result.value = self.expression if self.expression else "0"
        self.update()

    def format_number(self, num):
        try:
            num = float(num)
            if num.is_integer():
                return int(num)
            return round(num, 10)
        except:
            return "Error"
    


    def reset(self):
        self.operator = "+"
        self.operand1 = 0
        self.new_operand = True
