import math
from datetime import datetime

import flet as ft

import weather_api


def _sky_icon(sky_code: str) -> str:
    # 기상청 SKY: 맑음(1) 구름많음(3) 흐림(4)
    return {"1": "☀️", "3": "⛅", "4": "☁️"}.get(str(sky_code), "🌫️")


def _sky_label(sky_code: str) -> str:
    return {"1": "맑음", "3": "구름많음", "4": "흐림"}.get(str(sky_code), "알수없음")


def _fmt_time(fcst_time: str) -> str:
    # "HHMM" -> "H AM/PM" 느낌으로 맞추려면 더 손봐도 되지만, 우선 스크린샷처럼 간결하게.
    hh = int(fcst_time[:2])
    return "Now" if hh == datetime.now().hour else f"{hh}시"


def _apparent_temp_c(t_c: float, rh: int) -> float:
    """
    간단 체감온도 근사(정확한 풍속/복사 고려 불가).
    - Steadman 계열 근사식 기반으로 너무 과하게 튀지 않도록 제한.
    """
    try:
        e = (rh / 100.0) * 6.105 * math.exp((17.27 * t_c) / (237.7 + t_c))
        at = t_c + 0.33 * e - 0.70 * 0.0 - 4.0  # 풍속 미사용 -> 0
        return max(min(at, t_c + 5), t_c - 5)
    except Exception:
        return t_c


def _preprocess(raw_list: list[dict]) -> list[dict]:
    processed: list[dict] = []
    for item in raw_list:
        processed.append(
            {
                "date": item.get("fcst_date", ""),
                "time_raw": item.get("fcst_time", "0000"),
                "time": _fmt_time(item.get("fcst_time", "0000")),
                "temp": float(item.get("tmp", 0) or 0),
                "hum": int(item.get("hum", 0) or 0),
                "pop": int(item.get("pop", 0) or 0),
                "pcp": str(item.get("pcp", "")),
                "sky_code": str(item.get("sky", "1")),
            }
        )
    return processed


def _daily_summary(processed: list[dict]) -> list[dict]:
    by_date: dict[str, list[dict]] = {}
    for d in processed:
        by_date.setdefault(d["date"], []).append(d)

    out: list[dict] = []
    for date, items in sorted(by_date.items(), key=lambda x: x[0]):
        temps = [x["temp"] for x in items]
        sky_code = items[0]["sky_code"] if items else "1"
        out.append(
            {
                "date": date,
                "min": min(temps) if temps else 0,
                "max": max(temps) if temps else 0,
                "sky_code": sky_code,
            }
        )
    return out


def _glass_card(content: ft.Control, *, padding: int = 14) -> ft.Container:
    return ft.Container(
        content=content,
        padding=padding,
        border_radius=16,
        bgcolor=ft.Colors.with_opacity(0.25, ft.Colors.BLUE_GREY_900),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.WHITE)),
    )


def main(page: ft.Page):
    page.title = "Weather Dashboard"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 16
    page.bgcolor = ft.Colors.BLACK

    bg_gradient = ft.LinearGradient(
        begin=ft.Alignment(-1, -1),
        end=ft.Alignment(1, 1),
        colors=[
            ft.Colors.with_opacity(0.85, ft.Colors.BLUE_GREY_900),
            ft.Colors.with_opacity(0.85, ft.Colors.BLUE_GREY_800),
            ft.Colors.with_opacity(0.85, ft.Colors.BLUE_GREY_700),
        ],
    )

    selected_region = ft.Text("서울", size=42, weight=ft.FontWeight.W_600)
    selected_sky = ft.Text("--", size=14, color=ft.Colors.WHITE70)
    selected_temp = ft.Text("--°", size=64, weight=ft.FontWeight.BOLD)
    selected_feels = ft.Text("Feels Like: --°", size=14, color=ft.Colors.WHITE70)
    selected_hilo = ft.Text("H: --°  L: --°", size=14, color=ft.Colors.WHITE70)

    # 좌측: 검색 + 지역 리스트
    search = ft.TextField(
        hint_text="Search",
        height=44,
        border_radius=14,
        filled=True,
        bgcolor=ft.Colors.with_opacity(0.25, ft.Colors.BLUE_GREY_900),
        border=ft.InputBorder.NONE,
        text_size=14,
        content_padding=ft.Padding(left=14, right=14, top=12, bottom=12),
    )

    region_list = ft.ListView(spacing=10, expand=True, auto_scroll=False)

    hourly_row = ft.Row(spacing=18, wrap=False, scroll=ft.ScrollMode.HIDDEN)
    ten_day_col = ft.Column(spacing=10)

    def _toast_error(message: str):
        page.snack_bar = ft.SnackBar(content=ft.Text(message))
        page.snack_bar.open = True
        page.update()

    def load_region(region_name: str):
        try:
            raw = weather_api.forecast(region_name)
            processed = _preprocess(raw["data"])
            if not processed:
                raise RuntimeError("예보 데이터가 비어있습니다.")

            now = processed[0]
            temps = [x["temp"] for x in processed]
            feels = _apparent_temp_c(now["temp"], now["hum"])

            # 배경: 날씨(하늘상태)에 따라 변경
            sky = str(now.get("sky_code", "1"))
            if sky == "1":  # 맑음
                bg_gradient.colors = [
                    ft.Colors.with_opacity(0.88, ft.Colors.LIGHT_BLUE_400),
                    ft.Colors.with_opacity(0.88, ft.Colors.LIGHT_BLUE_700),
                    ft.Colors.with_opacity(0.88, ft.Colors.BLUE_900),
                ]
            elif sky == "3":  # 구름많음
                bg_gradient.colors = [
                    ft.Colors.with_opacity(0.86, ft.Colors.BLUE_GREY_700),
                    ft.Colors.with_opacity(0.86, ft.Colors.BLUE_GREY_800),
                    ft.Colors.with_opacity(0.86, ft.Colors.BLUE_GREY_900),
                ]
            else:  # 흐림(4) 포함
                bg_gradient.colors = [
                    ft.Colors.with_opacity(0.88, ft.Colors.GREY_900),
                    ft.Colors.with_opacity(0.88, ft.Colors.BLUE_GREY_900),
                    ft.Colors.with_opacity(0.88, ft.Colors.BLACK),
                ]

            selected_region.value = raw["region"]
            selected_sky.value = f"{_sky_icon(now['sky_code'])}  {_sky_label(now['sky_code'])}  ·  습도 {now['hum']}%  ·  강수확률 {now['pop']}%"
            selected_temp.value = f"{round(now['temp'])}°"
            selected_feels.value = f"Feels Like: {round(feels)}°"
            selected_hilo.value = f"H: {round(max(temps))}°  L: {round(min(temps))}°"

            # 시간별(스크린샷처럼 길게)
            hourly_row.controls.clear()
            for d in processed[:12]:
                hourly_row.controls.append(
                    ft.Column(
                        spacing=6,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(d["time"], size=12, color=ft.Colors.WHITE70),
                            ft.Text(_sky_icon(d["sky_code"]), size=18),
                            ft.Text(f"{round(d['temp'])}°", size=12, weight=ft.FontWeight.W_600),
                        ],
                    )
                )

            # 일별 요약(현재 API는 24시간이라 실제로는 1~2일만 나옴)
            ten_day_col.controls.clear()
            for daily in _daily_summary(processed)[:7]:
                date = daily["date"]
                label = date[4:6] + "/" + date[6:8] if len(date) == 8 else date
                ten_day_col.controls.append(
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(label, size=12, color=ft.Colors.WHITE70),
                            ft.Text(_sky_icon(daily["sky_code"]), size=14),
                            ft.Text(f"{round(daily['min'])}°", size=12, color=ft.Colors.WHITE70),
                            ft.Container(
                                width=90,
                                height=6,
                                border_radius=99,
                                bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                            ),
                            ft.Text(f"{round(daily['max'])}°", size=12, color=ft.Colors.WHITE),
                        ],
                    )
                )

            page.update()
        except Exception as ex:
            _toast_error(f"오류: {ex}")

    def on_search_submit(e: ft.ControlEvent):
        v = (search.value or "").strip()
        if not v:
            return
        load_region(v)

    search.on_submit = on_search_submit

    def region_tile(name: str, temp: str = "", subtitle: str = "") -> ft.Control:
        return ft.Container(
            on_click=lambda e: load_region(name),
            border_radius=16,
            padding=12,
            bgcolor=ft.Colors.with_opacity(0.22, ft.Colors.BLUE_GREY_900),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text(name, size=14, weight=ft.FontWeight.W_600),
                            ft.Text(subtitle or "Cloudy", size=11, color=ft.Colors.WHITE54),
                        ],
                    ),
                    ft.Text(temp or "", size=16, weight=ft.FontWeight.BOLD),
                ],
            ),
        )

    # 기본 지역 채우기
    for r in list(weather_api.REGION_MAP.keys()):
        region_list.controls.append(region_tile(r))

    left_panel = ft.Container(
        width=290,
        padding=14,
        border_radius=24,
        bgcolor=ft.Colors.with_opacity(0.20, ft.Colors.BLUE_GREY_900),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)),
        content=ft.Column(
            spacing=12,
            controls=[
                search,
                ft.Container(height=8),
                ft.Text("My Location", size=12, color=ft.Colors.WHITE70),
                region_tile("서울", "", "My Location  •  Home"),
                ft.Container(height=6),
                ft.Text("Locations", size=12, color=ft.Colors.WHITE70),
                region_list,
            ],
        ),
    )

    header = ft.Column(
        spacing=2,
        controls=[
            selected_region,
            selected_sky,
            ft.Row(
                spacing=10,
                controls=[
                    selected_temp,
                    ft.Column(spacing=4, controls=[selected_feels, selected_hilo]),
                ],
            ),
        ],
    )

    hourly_card = _glass_card(
        ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("HOURLY FORECAST", size=11, color=ft.Colors.WHITE70),
                        ft.Icon(ft.Icons.SCHEDULE, size=16, color=ft.Colors.WHITE70),
                    ],
                ),
                ft.Container(
                    height=92,
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                expand=True,
                                content=ft.Row(
                                    spacing=0,
                                    controls=[
                                        ft.Container(
                                            expand=True,
                                            content=ft.Row(
                                                controls=[hourly_row],
                                                scroll=ft.ScrollMode.AUTO,
                                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                            ),
                                        )
                                    ],
                                ),
                            ),
                        ]
                    ),
                ),
            ],
        ),
        padding=14,
    )

    ten_day_card = _glass_card(
        ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("10-DAY FORECAST", size=11, color=ft.Colors.WHITE70),
                        ft.Icon(ft.Icons.CALENDAR_MONTH, size=16, color=ft.Colors.WHITE70),
                    ],
                ),
                ten_day_col,
                ft.Text(
                    "참고: 현재 API는 24시간 예보라 10일치가 아닌 1~2일만 표시됩니다.",
                    size=10,
                    color=ft.Colors.WHITE54,
                ),
            ],
        )
    )

    dashboard = ft.Column(
        spacing=14,
        expand=True,
        controls=[
            header,
            hourly_card,
            ten_day_card,
        ],
    )

    background = ft.Container(
        expand=True,
        border_radius=26,
        padding=18,
        gradient=bg_gradient,
        content=dashboard,
    )

    page.add(
        ft.Row(
            spacing=14,
            expand=True,
            controls=[
                left_panel,
                background,
            ],
        )
    )

    # 초기 로딩: 지원 지역 중 서울이 있으면 로드
    default_region = "서울" if "서울" in weather_api.REGION_MAP else next(iter(weather_api.REGION_MAP.keys()))
    load_region(default_region)


if __name__ == "__main__":
    ft.run(main)