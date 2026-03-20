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


# 공학용 계산 버튼
@ft.control
class EnginerringWhiteButtoon(CalcButton):
    bgcolor: ft.Colors = ft.Colors.with_opacity(0.15, ft.Colors.WHITE)
    color: ft.Colors = ft.Colors.WHITE


@ft.control
class CalculatorApp(ft.Container):
    # 전환 용 생성자?
    def __init__(self, switch_callback):
        super().__init__()
        self.switch_callback = switch_callback

        # def init(self):
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
        self.open_parens = 0  # 열린 괄호 개수
        self.last_answer = (
            "0"  # 결과값 저장변수----------------------------------------
        )

        self.content = ft.Column(
            controls=[
                ft.Row(
                    controls=[self.mode_text, self.result],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Row(
                    controls=[
                        EngineeringChangeButton(   # 백스페이스 버튼 추가
                            icon=ft.Icons.BACKSPACE,
                            on_click=self.backspace_clicked
                        ),
                        EngineeringChangeButton(
                            icon=ft.Icons.AUTORENEW, on_click=self.switch_callback
                        )  # 버튼 수정
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
                ft.Row(
                    controls=[
                        EnginerringWhiteButtoon(
                            content="ANS", on_click=self.button_clicked
                        ),
                        EnginerringWhiteButtoon(
                            content="R/D", on_click=self.button_clicked
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

    """def close_pending_function(self):
        if self.pending_function is not None:
            self.eval_expression += ")"
            self.pending_function = None"""

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
            # 수정 괄호
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
                self.current_input += data  # if self.current_input != "0" else data

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
            if (
                self.open_parens > 0
                and self.expression
                and (
                    self.expression[-1].isdigit()
                    or self.expression[-1] == ")"
                    or self.expression[-1] == "."
                )
            ):
                self.expression += ")"
                self.eval_expression += ")"
                self.open_parens -= 1
                self.result.value = self.expression
                self.new_operand = True

            else:
                # 숫자나 닫는 괄호 뒤에 여는 괄호가 오면 곱셈 처리
                if self.expression and (
                    self.expression[-1].isdigit()
                    or self.expression[-1] == ")"
                    or self.expression[-1] == "."
                ):
                    self.expression += "*"
                    self.eval_expression += "*"

                self.expression += "("
                self.eval_expression += "("
                self.open_parens += 1
                self.result.value = self.expression
                self.new_operand = True

        # 라디안/디그리 전환 버튼 기능 추가
        elif data == "R/D":
            if self.angle_mode == "DEG":
                self.angle_mode = "RAD"
            else:
                self.angle_mode = "DEG"
            self.mode_text.value = self.angle_mode

        # 수정 사칙연산
        elif data in ("sin", "cos", "tan", "log", "ln"):
            if self.just_calculated:
                self.expression = self.result.value
                self.eval_expression = self.result.value
                self.just_calculated = False
                self.current_input = self.result.value

            if self.expression and (
                self.expression[-1].isdigit()
                or self.expression[-1] == "."
                or self.expression[-1] == ")"
                or self.expression[-1] == "π"
                or self.expression[-1] == "e"
            ):
                self.expression += "*"
                self.eval_expression += "*"

            self.expression += f"{data}("
            if data in ("sin", "cos", "tan"):
                self.eval_expression += f"{data}_fn("
            else:
                self.eval_expression += f"{data}("

            self.current_input = "0"
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
                    "abs": abs,
                    "exp": math.exp,
                }

                calc_result = eval(eval_expr, calc_env, {})
                calc_result = self.format_number(calc_result)

                self.last_answer = str(calc_result)  # "="입력시 결과값 자동 저장
                self.result.value = str(calc_result)
                self.expression = str(calc_result)
                self.eval_expression = str(calc_result)
                self.current_input = str(calc_result)
                self.new_operand = True
                self.just_calculated = True
                # 괄호
                self.open_parens = 0
                # self.pending_function = None

            except:
                self.result.value = "Error"
                self.expression = ""
                self.eval_expression = ""
                self.current_input = "0"
                self.just_calculated = False
                # 괄호
                self.open_parens = 0
                # self.pending_function = None
                self.reset()

        # 수정 사칙연산
        elif data == "%":
            try:
                if self.eval_expression:
                    # self.close_pending_function()
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
                        "abs": abs,
                        "exp": math.exp,
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
                # self.pending_function = None

            except:
                self.result.value = "Error"
                self.expression = ""
                self.eval_expression = ""
                self.current_input = "0"
                self.just_calculated = False
                # self.pending_function = None
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

        elif data == "√":
            if self.just_calculated:
                self.expression = self.result.value
                self.eval_expression = self.result.value
                self.just_calculated = False
                self.current_input = self.result.value

            if self.expression and (
                self.expression[-1].isdigit()
                or self.expression[-1] == ")"
                or self.expression[-1] == "."
                or self.expression[-1] == "π"
                or self.expression[-1] == "e"
            ):
                self.expression += "*"
                self.eval_expression += "*"

            self.expression += "√("
            self.eval_expression += "sqrt("
            self.open_parens += 1
            self.result.value = self.expression
            self.new_operand = True

        elif data == "eˣ":
            if self.just_calculated:
                self.expression = self.result.value
                self.eval_expression = self.result.value
                self.just_calculated = False
                self.current_input = self.result.value

            # 숫자 뒤면 자동 곱하기
            if self.expression and (
                self.expression[-1].isdigit()
                or self.expression[-1] == ")"
                or self.expression[-1] == "."
                or self.expression[-1] == "π"
                or self.expression[-1] == "e"
            ):
                self.expression += "*"
                self.eval_expression += "*"

            self.expression += "e^("
            self.eval_expression += "exp("
            self.open_parens += 1
            self.result.value = self.expression
            self.current_input = "0"
            self.new_operand = True

        elif data == "x²":
            if not self.expression:
                self.update()
                return

            if self.expression[-1] in ("+", "-", "*", "/", "(", "."):
                self.update()
                return

            if self.expression:
                # self.close_pending_function()
                self.expression += "²"
                self.eval_expression += "**2"
                self.result.value = self.expression

        elif data == "xʸ":
            if self.just_calculated:
                self.expression = self.result.value
                self.eval_expression = self.result.value
                self.just_calculated = False
                self.current_input = self.result.value

            # 숫자나 닫는 괄호 뒤면 바로 붙이기 가능
            if not self.expression:
                return

            self.expression += "^("
            self.eval_expression += "**("
            self.open_parens += 1
            self.result.value = self.expression
            self.current_input = "0"
            self.new_operand = True

        elif data == "1/x":
            if self.just_calculated:
                self.expression = self.result.value
                self.eval_expression = self.result.value
                self.just_calculated = False
                self.current_input = self.result.value

            # 숫자, 닫는 괄호, 소수점 뒤에 오면 곱하기 추가
            if self.expression and (
                self.expression[-1].isdigit()
                or self.expression[-1] == ")"
                or self.expression[-1] == "."
                or self.expression[-1] == "π"
                or self.expression[-1] == "e"
            ):
                self.expression += "*"
                self.eval_expression += "*"

            self.expression += "1/("
            self.eval_expression += "1/("
            self.open_parens += 1
            self.result.value = self.expression
            self.current_input = "0"
            self.new_operand = True

        elif data == "|x|":
            if self.just_calculated:
                self.expression = ""
                self.eval_expression = ""
                self.current_input = "0"
                self.just_calculated = False
                self.open_parens = 0

            # 숫자, 닫는 괄호, 상수 뒤면 자동 곱하기
            if self.expression and (
                self.expression[-1].isdigit()
                or self.expression[-1] == ")"
                or self.expression[-1] == "."
                or self.expression[-1] == "π"
                or self.expression[-1] == "e"
            ):
                self.expression += "*"
                self.eval_expression += "*"

            self.expression += "abs("
            self.eval_expression += "abs("
            self.open_parens += 1
            self.result.value = self.expression
            self.current_input = "0"
            self.new_operand = True

        elif data == "e":
            if self.just_calculated:
                self.expression = ""
                self.eval_expression = ""
                self.current_input = "0"
                self.just_calculated = False
                self.open_parens = 0

            # 숫자 뒤면 자동 곱하기
            if self.expression and (
                self.expression[-1].isdigit()
                or self.expression[-1] == ")"
                or self.expression[-1] == "."
                or self.expression[-1] == "π"
                or self.expression[-1] == "e"
            ):
                self.expression += "*"
                self.eval_expression += "*"

            self.expression += "e"
            self.eval_expression += "e"
            self.result.value = self.expression
            self.current_input = "e"
            self.new_operand = True

        elif data == "π":
            if self.just_calculated:
                self.expression = ""
                self.eval_expression = ""
                self.just_calculated = False

            if self.expression and (
                self.expression[-1].isdigit()
                or self.expression[-1] == "."
                or self.expression[-1] == "π"
            ):
                self.expression += "*"
                self.eval_expression += "*"

            self.expression += "π"
            self.eval_expression += "pi"
            self.result.value = self.expression

        elif data == "ANS":
            if self.just_calculated:
                self.expression = ""
                self.eval_expression = ""
                self.current_input = "0"
                self.just_calculated = False

            if self.expression and (
                self.expression[-1].isdigit()
                or self.expression[-1] == "."
                or self.expression[-1] == ")"
                or self.expression[-1] == "π"
                or self.expression[-1] == "e"
            ):
                self.expression += "*"
                self.eval_expression += "*"

            self.expression += "ANS"
            self.eval_expression += str(self.last_answer)
            self.current_input = str(self.last_answer)
            self.result.value = self.expression
            self.new_operand = False

        self.update()
    def backspace_clicked(self, e):
        if not self.expression:
            return

        # 함수 시작 토큰 통째로 삭제
        if self.expression.endswith("sin(") and self.eval_expression.endswith("sin_fn("):
            self.expression = self.expression[:-4]
            self.eval_expression = self.eval_expression[:-7]
            self.open_parens -= 1

        elif self.expression.endswith("cos(") and self.eval_expression.endswith("cos_fn("):
            self.expression = self.expression[:-4]
            self.eval_expression = self.eval_expression[:-7]
            self.open_parens -= 1

        elif self.expression.endswith("tan(") and self.eval_expression.endswith("tan_fn("):
            self.expression = self.expression[:-4]
            self.eval_expression = self.eval_expression[:-7]
            self.open_parens -= 1

        elif self.expression.endswith("log(") and self.eval_expression.endswith("log("):
            self.expression = self.expression[:-4]
            self.eval_expression = self.eval_expression[:-4]
            self.open_parens -= 1

        elif self.expression.endswith("ln(") and self.eval_expression.endswith("ln("):
            self.expression = self.expression[:-3]
            self.eval_expression = self.eval_expression[:-3]
            self.open_parens -= 1

        elif self.expression.endswith("abs(") and self.eval_expression.endswith("abs("):
            self.expression = self.expression[:-4]
            self.eval_expression = self.eval_expression[:-4]
            self.open_parens -= 1

        elif self.expression.endswith("e^(") and self.eval_expression.endswith("exp("):
            self.expression = self.expression[:-3]
            self.eval_expression = self.eval_expression[:-4]
            self.open_parens -= 1

        elif self.expression.endswith("^(") and self.eval_expression.endswith("**("):
            self.expression = self.expression[:-2]
            self.eval_expression = self.eval_expression[:-3]
            self.open_parens -= 1

        else:
            # 일반 한 글자 삭제
            last_expr = self.expression[-1]
            last_eval = self.eval_expression[-1] if self.eval_expression else ""

            self.expression = self.expression[:-1]
            self.eval_expression = self.eval_expression[:-1]

            if last_expr == "(":
                self.open_parens -= 1
            elif last_expr == ")":
                self.open_parens += 1

        self.result.value = self.expression if self.expression else "0"
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

    ## 사용하지 않음
    # def calculate(self, operand1, operand2, operator):
    #     if operator == "+":
    #         return self.format_number(operand1 + operand2)

    #     elif operator == "-":
    #         return self.format_number(operand1 - operand2)

    #     elif operator == "*":
    #         return self.format_number(operand1 * operand2)

    #     elif operator == "/":
    #         if operand2 == 0:
    #             return "Error"
    #         else:
    #             return self.format_number(operand1 / operand2)

    def reset(self):
        self.operator = "+"
        self.operand1 = 0
        self.new_operand = True


## 다른 main 파일이 진행
# def main(page: ft.Page):
#     page.title = "Calc App"
#     calc = CalculatorApp()
#     page.add(calc)


# ft.run(main)
