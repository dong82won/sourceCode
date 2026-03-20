import flet as ft
from basic_calc import CalculatorApp as BasicCalculator
from engineering_calc import CalculatorApp as EngineeringCalculator


def main(page: ft.Page):

    page.window.resizable = False

    def show_basic(e=None):
        page.controls.clear()

        # 일반 계산기 창 크기
        page.window.width = 380
        page.window.height = 380

        page.add(BasicCalculator(show_engineering))
        page.update()

    def show_engineering(e=None):
        page.controls.clear()

        # 공학용 계산기 창 크기
        page.window.width = 680
        page.window.height = 380

        page.add(EngineeringCalculator(show_basic))
        page.update()

    show_basic()


ft.app(target=main)