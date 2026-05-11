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

        self.content = ft.Column(  # 버튼 위치 정하기
            controls=[
                ft.Row(
                    controls=[self.result],
                    alignment=ft.MainAxisAlignment.END,
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
                        # 공학용
                        EnginerringWhiteButtoon(
                            content="Rad", on_click=self.button_clicked
                        ),
                        EnginerringWhiteButtoon(
                            content="Rad", on_click=self.button_clicked
                        ),
                        EnginerringWhiteButtoon(
                            content="√", on_click=self.button_clicked
                        ),
                        # 기본
                        ExtraActionButton(content="AC", on_click=self.button_clicked),
                        ExtraActionButton(content="()", on_click=self.button_clicked),
                        ExtraActionButton(content="%", on_click=self.button_clicked),
                        ActionButton(content="/", on_click=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        # 공학용
                        EnginerringWhiteButtoon(
                            content="sin", on_click=self.button_clicked
                        ),
                        EnginerringWhiteButtoon(
                            content="cos", on_click=self.button_clicked
                        ),
                        EnginerringWhiteButtoon(
                            content="tan", on_click=self.button_clicked
                        ),
                        # 기본
                        DigitButton(content="7", on_click=self.button_clicked),
                        DigitButton(content="8", on_click=self.button_clicked),
                        DigitButton(content="9", on_click=self.button_clicked),
                        ActionButton(content="*", on_click=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        # 공학용
                        EnginerringWhiteButtoon(
                            content="ln", on_click=self.button_clicked
                        ),
                        EnginerringWhiteButtoon(
                            content="log", on_click=self.button_clicked
                        ),
                        EnginerringWhiteButtoon(
                            content="1/x", on_click=self.button_clicked
                        ),
                        # 기본
                        DigitButton(content="4", on_click=self.button_clicked),
                        DigitButton(content="5", on_click=self.button_clicked),
                        DigitButton(content="6", on_click=self.button_clicked),
                        ActionButton(content="-", on_click=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        # 공학용
                        EnginerringWhiteButtoon(
                            content="eˣ", on_click=self.button_clicked
                        ),
                        EnginerringWhiteButtoon(
                            content="x²", on_click=self.button_clicked
                        ),
                        EnginerringWhiteButtoon(
                            content="xʸ", on_click=self.button_clicked
                        ),
                        # 기본
                        DigitButton(content="1", on_click=self.button_clicked),
                        DigitButton(content="2", on_click=self.button_clicked),
                        DigitButton(content="3", on_click=self.button_clicked),
                        ActionButton(content="+", on_click=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        # 공학용
                        EnginerringWhiteButtoon(
                            content="|x|", on_click=self.button_clicked
                        ),
                        EnginerringWhiteButtoon(
                            content="π", on_click=self.button_clicked
                        ),
                        EnginerringWhiteButtoon(
                            content="e", on_click=self.button_clicked
                        ),
                        # 기본
                        ExtraActionButton(content="+/-", on_click=self.button_clicked),
                        DigitButton(content="0", on_click=self.button_clicked),
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
            self.reset()

        elif data in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "."):
            if self.result.value == "0" or self.new_operand:
                self.result.value = data
                self.new_operand = False
            else:
                self.result.value = self.result.value + data

        elif data in ("+", "-", "*", "/"):
            self.result.value = self.calculate(
                self.operand1, float(self.result.value), self.operator
            )
            self.operator = data
            if self.result.value == "Error":
                self.operand1 = "0"
            else:
                self.operand1 = float(self.result.value)
            self.new_operand = True

        elif data in ("="):
            self.result.value = self.calculate(
                self.operand1, float(self.result.value), self.operator
            )
            self.reset()

        elif data in ("%"):
            self.result.value = float(self.result.value) / 100
            self.reset()

        elif data in ("+/-"):
            if float(self.result.value) > 0:
                self.result.value = "-" + str(self.result.value)

            elif float(self.result.value) < 0:
                self.result.value = str(
                    self.format_number(abs(float(self.result.value)))
                )
        # log =====================================================================
        elif data in ("log"):
            value = float(self.result.value)
            if value <= 0:
                self.result.value = "Error"
            else:
                result = round(self.format_number(math.log10(value)), 10)
                self.result.value = str(result)
            self.new_operand = True

        elif data in ("ln"):
            value = float(self.result.value)
            if value <= 0:
                self.result.value = "Error"
            else:
                result = round(self.format_number(math.log(value)), 10)
                self.result.value = str(result)
            self.new_operand = True
        # ================================================================
        self.update()

    def format_number(self, num):
        if num % 1 == 0:
            return int(num)
        else:
            return num

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
    # create application instance
    calc = CalculatorApp()

    # add application's root control to the page
    page.add(calc)


ft.run(main)
