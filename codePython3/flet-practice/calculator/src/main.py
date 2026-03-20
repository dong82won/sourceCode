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
class EngineeringChangeButton(ft.Button):
    bgcolor: ft.Colors = ft.Colors.WHITE
    color: ft.Colors = ft.Colors.BLACK
    width: int = 40
    height: int = 40
    border_radius: int = 999


# 공학용 계산 버튼
@ft.control
class EnginerringWhiteButtoon(CalcButton):
    bgcolor: ft.Colors = ft.Colors.with_opacity(0.15, ft.Colors.WHITE)
    color: ft.Colors = ft.Colors.WHITE


@ft.control
class CalculatorApp(ft.Container):
    def init(self):
        self.reset()
        self.width = 700
        self.bgcolor = ft.Colors.BLACK
        self.border_radius = ft.BorderRadius.all(20)
        self.padding = 20
        self.result = ft.Text(value="0", color=ft.Colors.WHITE, size=20)
        self.mode_text = ft.Text(value="DEG", color=ft.Colors.WHITE, size=14)
        self.angle_mode = "DEG"

        # 수정 사칙연산
        self.expression = ""  # 화면 표시용 수식
        self.eval_expression = ""  # 실제 eval 계산용 수식
        self.current_input = "0"  # 현재 입력 중인 숫자
        self.just_calculated = False  # = 직후 여부
        self.pending_function = None  # sin, cos, tan 대기 상태

        self.content = ft.Column(
            controls=[
                ft.Row(
                    controls=[self.mode_text, self.result],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Row(
                    controls=[
                        EngineeringChangeButton(
                            icon=ft.Icons.AUTORENEW, on_click=self.button_clicked
                        )
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
                ft.Row(
                    controls=[
                        EnginerringWhiteButtoon(
                            content="temp", on_click=self.button_clicked
                        ),
                        EnginerringWhiteButtoon(
                            content="Rad", on_click=self.button_clicked
                        ),
                        EnginerringWhiteButtoon(
                            content="√", on_click=self.button_clicked
                        ),
                        ExtraActionButton(content="AC", on_click=self.button_clicked),
                        ExtraActionButton(content="()", on_click=self.button_clicked),
                        ExtraActionButton(content="%", on_click=self.button_clicked),
                        ActionButton(content="/", on_click=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        EnginerringWhiteButtoon(
                            content="sin", on_click=self.button_clicked
                        ),
                        EnginerringWhiteButtoon(
                            content="cos", on_click=self.button_clicked
                        ),
                        EnginerringWhiteButtoon(
                            content="tan", on_click=self.button_clicked
                        ),
                        DigitButton(content="7", on_click=self.button_clicked),
                        DigitButton(content="8", on_click=self.button_clicked),
                        DigitButton(content="9", on_click=self.button_clicked),
                        ActionButton(content="*", on_click=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        EnginerringWhiteButtoon(
                            content="ln", on_click=self.button_clicked
                        ),
                        EnginerringWhiteButtoon(
                            content="log", on_click=self.button_clicked
                        ),
                        EnginerringWhiteButtoon(
                            content="1/x", on_click=self.button_clicked
                        ),
                        DigitButton(content="4", on_click=self.button_clicked),
                        DigitButton(content="5", on_click=self.button_clicked),
                        DigitButton(content="6", on_click=self.button_clicked),
                        ActionButton(content="-", on_click=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        EnginerringWhiteButtoon(
                            content="eˣ", on_click=self.button_clicked
                        ),
                        EnginerringWhiteButtoon(
                            content="x²", on_click=self.button_clicked
                        ),
                        EnginerringWhiteButtoon(
                            content="xʸ", on_click=self.button_clicked
                        ),
                        DigitButton(content="1", on_click=self.button_clicked),
                        DigitButton(content="2", on_click=self.button_clicked),
                        DigitButton(content="3", on_click=self.button_clicked),
                        ActionButton(content="+", on_click=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        EnginerringWhiteButtoon(
                            content="|x|", on_click=self.button_clicked
                        ),
                        EnginerringWhiteButtoon(
                            content="π", on_click=self.button_clicked
                        ),
                        EnginerringWhiteButtoon(
                            content="e", on_click=self.button_clicked
                        ),
                        ExtraActionButton(content="+/-", on_click=self.button_clicked),
                        DigitButton(content="0", on_click=self.button_clicked),
                        DigitButton(content=".", on_click=self.button_clicked),
                        ActionButton(content="=", on_click=self.button_clicked),
                    ]
                ),
            ]
        )

    # 수정 사칙연산
    def close_pending_function(self):
        if self.pending_function is not None:
            self.eval_expression += ")"
            self.pending_function = None

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
            self.pending_function = None

        # 수정 사칙연산
        elif data in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "."):
            if self.just_calculated:
                self.expression = ""
                self.eval_expression = ""
                self.current_input = "0"
                self.just_calculated = False
                self.pending_function = None

            if self.current_input == "0" and data != ".":
                self.current_input = data
            else:
                if data == "." and "." in self.current_input:
                    self.update()
                    return
                self.current_input += data if self.current_input != "0" else data

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

            self.close_pending_function()

            if self.expression and self.expression[-1] in ("+", "-", "*", "/"):
                self.expression = self.expression[:-1] + data
                self.eval_expression = self.eval_expression[:-1] + data
            else:
                self.expression += data
                self.eval_expression += data

            self.current_input = "0"
            self.new_operand = True
            self.result.value = self.expression

        # 라디안/디그리 전환 버튼 기능 추가
        elif data == "Rad":
            if self.angle_mode == "DEG":
                self.angle_mode = "RAD"
            else:
                self.angle_mode = "DEG"
            self.mode_text.value = self.angle_mode

        # 수정 사칙연산
        elif data in ("sin", "cos", "tan"):
            if self.just_calculated:
                self.expression = ""
                self.eval_expression = ""
                self.current_input = "0"
                self.just_calculated = False
                self.pending_function = None

            if self.expression and (
                self.expression[-1].isdigit() or self.expression[-1] == "."
            ):
                self.expression += "*"
                self.eval_expression += "*"

            self.expression += f"{data} "
            self.eval_expression += f"{data}_fn("
            self.current_input = "0"
            self.pending_function = data
            self.result.value = self.expression

        # 수정 사칙연산
        elif data == "=":
            try:
                if not self.eval_expression:
                    self.update()
                    return

                self.close_pending_function()

                calc_env = {
                    "__builtins__": None,
                    "sin_fn": self.calc_sin,
                    "cos_fn": self.calc_cos,
                    "tan_fn": self.calc_tan,
                    "sqrt": math.sqrt,
                    "log": math.log10,
                    "ln": math.log,
                    "pi": math.pi,
                    "e": math.e,
                }

                calc_result = eval(self.eval_expression, calc_env, {})
                calc_result = self.format_number(calc_result)

                self.result.value = str(calc_result)
                self.expression = str(calc_result)
                self.eval_expression = str(calc_result)
                self.current_input = str(calc_result)
                self.new_operand = True
                self.just_calculated = True
                self.pending_function = None

            except:
                self.result.value = "Error"
                self.expression = ""
                self.eval_expression = ""
                self.current_input = "0"
                self.just_calculated = False
                self.pending_function = None
                self.reset()

        # 수정 사칙연산
        elif data == "%":
            try:
                if self.eval_expression:
                    self.close_pending_function()
                    calc_env = {
                        "__builtins__": None,
                        "sin_fn": self.calc_sin,
                        "cos_fn": self.calc_cos,
                        "tan_fn": self.calc_tan,
                        "sqrt": math.sqrt,
                        "log": math.log10,
                        "ln": math.log,
                        "pi": math.pi,
                        "e": math.e,
                    }
                    calc_result = eval(self.eval_expression, calc_env, {}) / 100
                else:
                    calc_result = float(self.current_input) / 100

                calc_result = self.format_number(calc_result)
                self.result.value = str(calc_result)
                self.expression = str(calc_result)
                self.eval_expression = str(calc_result)
                self.current_input = str(calc_result)
                self.new_operand = True
                self.just_calculated = True
                self.pending_function = None

            except:
                self.result.value = "Error"
                self.expression = ""
                self.eval_expression = ""
                self.current_input = "0"
                self.just_calculated = False
                self.pending_function = None
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
                self.expression = (
                    self.expression[: -len(self.current_input)] + new_input
                )
                self.eval_expression = (
                    self.eval_expression[: -len(self.current_input)] + new_input
                )
                self.current_input = new_input
                self.result.value = self.expression

        self.update()

    # 수정 사칙연산
    def calc_sin(self, x):
        if self.angle_mode == "DEG":
            x = math.radians(x)
        return math.sin(x)

    # 수정 사칙연산
    def calc_cos(self, x):
        if self.angle_mode == "DEG":
            x = math.radians(x)
        return math.cos(x)

    # 수정 사칙연산
    def calc_tan(self, x):
        if self.angle_mode == "DEG":
            x = math.radians(x)
        return math.tan(x)

    def format_number(self, num):
        try:
            num = float(num)
            if num.is_integer():
                return int(num)
            return round(num, 10)
        except:
            return "Error"

    def calculate(self, operand1, operand2, operator):
        if operator == "+":
            return self.format_number(operand1 + operand2)

        elif operator == "-":
            return self.format_number(operand1 - operand2)

        elif operator == "*":
            return self.format_number(operand1 * operand2)

        elif operator == "/":
            if operand2 == 0:
                return "Error"
            else:
                return self.format_number(operand1 / operand2)

    def reset(self):
        self.operator = "+"
        self.operand1 = 0
        self.new_operand = True


def main(page: ft.Page):
    page.title = "Calc App"
    calc = CalculatorApp()
    page.add(calc)


ft.run(main)
