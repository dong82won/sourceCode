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
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO

    # genre 종류 받아오기
    conn = sqlite3.connect(DATA_DB_PATH)
    genres = load_genres(conn)

    # 검색 옵션
    title_field = ft.TextField(label="Title", width=180)

    rating_field = ft.TextField(label="Rating ≥", width=120)

    year_field = ft.TextField(label="Year", width=120)

    type_dropdown = ft.Dropdown(
        label="Type",
        width=150,
        options=[
            ft.dropdown.Option("All"),
            ft.dropdown.Option("Movie"),
            ft.dropdown.Option("TV Show"),
        ],
    )

    genre_dropdown = ft.Dropdown(
        label="Genre",
        width=160,
        options=[ft.dropdown.Option(genre) for genre in genres],
    )

    # 포스터 Grid
    grid = ft.GridView(expand=True, spacing=10, run_spacing=10, max_extent=200)

    # 첫 화면 (Top 5)
    top_column = ft.Column(
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=30,
        controls=[ft.Text("Top Rated", size=40, weight=ft.FontWeight.BOLD)],
    )

    result = search_db(conn, {"rating": 0, "ascending": False})
    print(len(result))

    for movie in result[:5]:

        top_column.controls.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Image(
                            src=movie["image_path"],
                            width=300,
                            height=450,
                            fit=ft.BoxFit.CONTAIN,
                        ),
                        ft.Text(movie["title"], size=20, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            f"⭐ {movie['rating']}",
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=10,
            )
        )

    # content area (화면 교체용)
    content_area = ft.Container(content=top_column)

    # 검색 함수
    def search(e):

        options = {}

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

        result = search_db(conn, options)

        grid.controls.clear()

        for movie in result:
            grid.controls.append(
                ft.Container(
                    content=ft.Image(
                        src=movie["image_path"],
                        width=200,
                        height=500,
                        fit=ft.BoxFit.COVER,
                    ),
                    padding=5,
                )
            )

        content_area.content = grid

        page.update()

    search_button = ft.Button(content="Search", icon=ft.Icons.SEARCH, on_click=search)

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
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
        ),
        margin=10,
    )

    page.appbar = ft.AppBar(
        title=ft.Text("Netflix Contents Recommend"),
        bgcolor=ft.Colors.SURFACE_CONTAINER,
        actions=[search_row],
        toolbar_height=90,
    )

    page.add(ft.Container(height=30), content_area)


ft.run(main)
