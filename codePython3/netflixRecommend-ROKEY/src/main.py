import flet as ft
import sqlite3
from db import init_db, make_db, search_db

DATA_DB_PATH = "src/assets/data.db"

init_db()
make_db()


# genre 목록 가져오는 함수
def load_genres(conn):
    cur = conn.cursor()
    cur.execute("SELECT genre FROM genre")

    genres = ["All"]
    genres.extend([row[0] for row in cur.fetchall()])

    return genres


def main(page: ft.Page):
    page.title = "Netflix Recommend"

    # 기본 창 크기 설정 # custom_ui
    page.window_width = 1500
    page.window_height = 950

    # 페이지 전체 테마를 다크 모드로 변경 # custom_ui
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ft.Colors.BLACK

    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO

    # genre 종류 받아오기
    conn = sqlite3.connect(DATA_DB_PATH)
    genres = load_genres(conn)

    # 작품 상세 페이지 dialog
    dialog = ft.AlertDialog(title=ft.Text(""))
    page.overlay.append(dialog)

    # 작품 상세 페이지 팝업 창 띄우기
    def show_detail(e):
        movie = e.control.data
        print("show_detail!")

        dialog.title = ft.Container(
            # bgcolor=ft.Colors.GREEN_200,
            content=ft.Row(
                [
                    ft.Text(""),  # 보기 좋은 정렬을 위해 추가
                    ft.Text(
                        f"      {movie['title']}",  # 보기 좋은 정렬을 위해 공백 추가
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.IconButton(icon=ft.Icons.CLOSE, on_click=close_dialog),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )

        dialog.content = ft.Column(
            [
                ft.Image(src=movie["image_path"], width=270),
                ft.Text(f"⭐ {movie['rating']}"),
                ft.Text(f"{movie.get('release_year','')} • {movie.get('type','')}"),
                ft.Container(
                    width=450,
                    content=ft.Text(
                        movie["description"], text_align=ft.TextAlign.START
                    ),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
            tight=True,
        )

        dialog.open = True
        page.update()

    # 작품 상세 페이지 팝업 창 닫기
    def close_dialog(e):
        dialog.open = False
        page.update()

    # 검색 옵션
    title_field = ft.TextField(label="Title", width=180)

    rating_field = ft.TextField(label="Rating ≥", width=120)

    year_field = ft.TextField(label="Year", width=120)

    # 드롭 다운 기본 값을 All로 지정 # custom_ui
    # 아무것도 선택하지 않으면 전체 검색이 되도록
    type_dropdown = ft.Dropdown(
        label="Type",
        width=150,
        value="All",
        options=[
            ft.dropdown.Option("All"),
            ft.dropdown.Option("Movie"),
            ft.dropdown.Option("TV Show"),
        ],
    )

    genre_dropdown = ft.Dropdown(
        label="Genre",
        width=160,
        value="All",
        options=[ft.dropdown.Option(genre) for genre in genres],
    )

    # 오류 메시지 출력을 위한 텍스트 추가 # custom_ui
    message_text = ft.Text("", color=ft.Colors.RED_300)

    # 포스터 Grid 살짝 증가 # custom_ui
    # 세로형 포스터에 맞게 세로가 긴 Grid로 설정
    grid = ft.GridView(
        expand=True, spacing=15, run_spacing=15, max_extent=200, child_aspect_ratio=0.58
    )

    # 첫 화면 (Top 5) Top Rated 제목 아래 설명 문구 추가 # custom_ui
    top_column = ft.Column(
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=30,
        controls=[
            ft.Text(
                "Top Rated", size=40, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE
            ),
            ft.Text("평점이 높은 넷플릭스 콘텐츠", size=16, color=ft.Colors.GREY_400),
        ],
    )

    result = search_db(conn, {"rating": 0, "ascending": False})

    for movie in result[:5]:
        # Top 5 카드에 배경색, 여백, 글자색 추가 # custom_ui
        top_column.controls.append(
            ft.Container(
                bgcolor=ft.Colors.GREY_900,
                padding=15,
                margin=5,
                data=movie,  # 상페 페이지에 표시할 정보를 위해 저장
                on_click=show_detail,  # 클릭 시 상세페이지 open
                content=ft.Column(
                    [
                        ft.Image(
                            src=movie["image_path"],
                            width=300,
                            height=450,
                            fit=ft.BoxFit.CONTAIN,
                        ),
                        ft.Text(
                            movie["title"],
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(f"⭐ {movie['rating']}", color=ft.Colors.AMBER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
            )
        )

    # content area (화면 교체용) padding 추가 # custom_ui
    content_area = ft.Container(content=top_column, padding=10)

    # 검색 함수에 숫자 입력 예외 처리 추가 # custom_ui
    def search(e):
        options = {}
        message_text.value = ""

        try:
            if title_field.value:
                options["title"] = title_field.value

            if type_dropdown.value and type_dropdown.value != "All":
                options["type"] = type_dropdown.value

            if rating_field.value:
                options["rating"] = float(rating_field.value)

            if year_field.value:
                options["release_year"] = int(year_field.value)

            if genre_dropdown.value and genre_dropdown.value != "All":
                options["genre"] = genre_dropdown.value

        except ValueError:
            message_text.value = "Rating은 숫자, Year는 정수로 입력해주세요."
            page.update()
            return

        result = search_db(conn, options)  # 검색 결과

        grid.controls.clear()  # grid 안의 내용 초기화

        # 검색 결과가 없을 때 해당 메시지를 표시
        if len(result) == 0:
            grid.controls.append(
                ft.Container(
                    padding=20,
                    content=ft.Text(
                        "검색 결과가 없습니다.", size=18, color=ft.Colors.GREY_400
                    ),
                )
            )
        else:
            # 검색 결과 카드에 제목/평점 표시 추가 # custom_ui
            # container 크기 조정 및 이미지 크기 축소
            for movie in result:
                grid.controls.append(
                    ft.Container(
                        width=200,
                        height=320,
                        bgcolor=ft.Colors.GREY_900,
                        padding=8,
                        data=movie,  # 상세 페이지에 표시할 정보 저장
                        on_click=show_detail,  # 클릭 시 상세 페이지 오픈
                        content=ft.Column(
                            [
                                ft.Image(
                                    src=movie["image_path"],
                                    width=180,
                                    height=230,
                                    fit=ft.BoxFit.COVER,
                                ),
                                ft.Text(
                                    movie["title"],
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Text(
                                    f"⭐ {movie['rating']}",
                                    size=12,
                                    color=ft.Colors.AMBER,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=6,
                        ),
                    )
                )
        # 검색 결과 화면에 제목 추가 # custom_ui
        content_area.content = ft.Column(
            [
                ft.Text(
                    "Search Results",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                ),
                grid,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        )

        page.update()

    # Home 버튼 추가 # custom_ui
    def show_home(e):
        # 검색창 초기화
        title_field.value = ""
        rating_field.value = ""
        year_field.value = ""
        type_dropdown.value = "All"
        genre_dropdown.value = "All"

        content_area.content = top_column
        message_text.value = ""
        page.update()

    search_button = ft.Button(content="Search", icon=ft.Icons.SEARCH, on_click=search)

    # Home 버튼 추가 # custom_ui
    home_button = ft.Button(content="Home", icon=ft.Icons.HOME, on_click=show_home)

    # 가로 중앙정렬 옵션 Row
    search_row = ft.Container(
        content=ft.Row(
            [
                title_field,
                type_dropdown,
                rating_field,
                year_field,
                genre_dropdown,
                search_button,
                home_button,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
        ),
        margin=10,
    )

    page.appbar = ft.AppBar(
        title=ft.Text("Netflix Contents Recommend", weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.SURFACE_CONTAINER,
        actions=[search_row],
        toolbar_height=90,
    )

    # 페이지에 message_text 표시 추가
    page.add(ft.Container(height=30), message_text, content_area)


ft.run(main)
