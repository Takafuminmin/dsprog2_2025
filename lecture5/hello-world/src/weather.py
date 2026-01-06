import flet as ft
import requests
from datetime import datetime

AREA_URL = "http://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"

# 天気アイコンのマッピング
WEATHER_ICONS = {
    "晴": "☀️",
    "曇": "☁️",
    "雨": "🌧️",
    "雪": "❄️",
    "晴時々曇": "🌤️",
    "晴後曇": "🌤️",
    "曇時々晴": "⛅",
    "曇後晴": "⛅",
    "晴時々雨": "🌦️",
    "曇時々雨": "🌧️",
    "雨時々曇": "🌧️",
}


def get_weather_icon(weather_text):
    """天気テキストから適切なアイコンを取得"""
    for key, icon in WEATHER_ICONS.items():
        if key in weather_text:
            return icon
    return "☀️"


def fetch_area():
    return requests.get(AREA_URL).json()


def fetch_forecast(area_code):
    url = FORECAST_URL.format(area_code)
    return requests.get(url).json()


def parse_forecast(data):
    """天気予報データを解析"""
    ts = data[0]["timeSeries"][0]
    dates = ts["timeDefines"]
    weathers = ts["areas"][0]["weathers"]
    
    # 気温データを取得（存在する場合）
    temps_min = []
    temps_max = []
    
    try:
        if len(data[0]["timeSeries"]) > 2:
            temp_ts = data[0]["timeSeries"][2]
            if "areas" in temp_ts and len(temp_ts["areas"]) > 0:
                temp_data = temp_ts["areas"][0]
                if "tempsMin" in temp_data:
                    temps_min = temp_data["tempsMin"]
                if "tempsMax" in temp_data:
                    temps_max = temp_data["tempsMax"]
    except:
        pass
    
    # 発表時刻を取得
    report_datetime = data[0].get("reportDatetime", "")
    
    return list(zip(dates, weathers)), temps_min, temps_max, report_datetime


def create_forecast_card(date_str, weather, temp_min=None, temp_max=None):
    """天気予報カードを作成"""
    try:
        date = datetime.fromisoformat(date_str.replace("Z", "+0000"))
        weekdays = ["月", "火", "水", "木", "金", "土", "日"]
        date_display = f"{date.month}/{date.day}({weekdays[date.weekday()]})"
    except:
        date_display = date_str[:10]
    
    icon = get_weather_icon(weather)
    
    # 気温表示
    temp_row = ft.Row(
        [
            ft.Text(
                f"{temp_min}°" if temp_min and temp_min != "" else "--",
                size=14,
                color="#81D4FA",
                weight=ft.FontWeight.BOLD,
            ),
            ft.Text("/", size=14, color="#B0BEC5"),
            ft.Text(
                f"{temp_max}°" if temp_max and temp_max != "" else "--",
                size=14,
                color="#EF5350",
                weight=ft.FontWeight.BOLD,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=5,
    )
    
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    date_display,
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color="white",
                ),
                ft.Container(height=5),
                ft.Text(icon, size=48),
                ft.Container(height=5),
                ft.Text(
                    weather,
                    size=11,
                    text_align=ft.TextAlign.CENTER,
                    color="#B0BEC5",
                    max_lines=2,
                ),
                ft.Container(height=5),
                temp_row,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        width=140,
        height=200,
        bgcolor="#4DFFFFFF",
        border_radius=10,
        padding=12,
        border=ft.border.all(1, "#33FFFFFF"),
    )


def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.window_width = 1200
    page.window_height = 600
    page.bgcolor = "#263238"
    page.padding = 0

    selected_area_text = ft.Text(
        "地域を選択してください",
        size=20,
        weight=ft.FontWeight.BOLD,
        color="white",
    )
    
    update_time_text = ft.Text(
        "",
        size=12,
        color="#B0BEC5",
        italic=True,
    )
    
    forecast_cards = ft.Row(
        wrap=True,
        spacing=15,
        run_spacing=15,
        scroll=ft.ScrollMode.AUTO,
    )
    
    current_area_code = [None]
    current_area_name = [""]

    def load_forecast(area_code, area_name):
        """天気予報を読み込み"""
        try:
            selected_area_text.value = f"📍 {area_name} - 読み込み中..."
            update_time_text.value = ""
            forecast_cards.controls.clear()
            page.update()
            
            forecast_json = fetch_forecast(area_code)
            forecast_list, temps_min, temps_max, report_datetime = parse_forecast(forecast_json)

            selected_area_text.value = f"📍 {area_name}"
            
            if report_datetime:
                try:
                    dt = datetime.fromisoformat(report_datetime.replace("Z", "+00:00"))
                    update_time_text.value = f"発表: {dt.strftime('%Y年%m月%d日 %H:%M')} (気象庁)"
                except:
                    update_time_text.value = f"発表: {report_datetime}"
            
            forecast_cards.controls.clear()

            for i, (date_str, weather) in enumerate(forecast_list):
                temp_min = temps_min[i] if i < len(temps_min) else None
                temp_max = temps_max[i] if i < len(temps_max) else None
                
                card = create_forecast_card(date_str, weather, temp_min, temp_max)
                forecast_cards.controls.append(card)

            page.update()
        except Exception as ex:
            selected_area_text.value = f"エラー: {str(ex)}"
            update_time_text.value = ""
            page.update()

    def on_area_click(e):
        area_code = e.control.data
        area_name = e.control.title.value
        current_area_code[0] = area_code
        current_area_name[0] = area_name
        load_forecast(area_code, area_name)

    def on_refresh_click(e):
        if current_area_code[0]:
            load_forecast(current_area_code[0], current_area_name[0])

    area_json = fetch_area()

    tiles = []
    for center in area_json["centers"].values():
        children = []
        for code in center["children"]:
            office = area_json["offices"][code]
            children.append(
                ft.ListTile(
                    title=ft.Text(office["name"], color="white"),
                    data=code,
                    on_click=on_area_click,
                    hover_color="#1AFFFFFF",
                )
            )

        tiles.append(
            ft.ExpansionTile(
                title=ft.Text(
                    center["name"],
                    color="white",
                    weight=ft.FontWeight.BOLD,
                ),
                controls=children,
                text_color="white",
                collapsed_text_color="#B0BEC5",
                bgcolor="transparent",
            )
        )

    sidebar = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text("📍", size=24),
                            ft.Text(
                                "地域選択",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color="white",
                            ),
                        ],
                    ),
                    padding=15,
                    bgcolor="#37474F",
                ),
                ft.Container(
                    content=ft.Column(tiles, scroll=ft.ScrollMode.AUTO),
                    expand=True,
                    padding=5,
                ),
            ],
        ),
        width=300,
        bgcolor="#455A64",
    )

    main_content = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text("☀️", size=32),
                            ft.Text(
                                "天気予報",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color="white",
                            ),
                            ft.Container(expand=True),
                            ft.TextButton(
                                "🔄 更新",
                                on_click=on_refresh_click,
                                style=ft.ButtonStyle(color="white"),
                            ),
                        ],
                    ),
                    bgcolor="#283593",
                    padding=15,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            selected_area_text,
                            update_time_text,
                        ],
                        spacing=5,
                    ),
                    padding=20,
                ),
                ft.Container(
                    content=forecast_cards,
                    padding=ft.padding.only(left=20, right=20, bottom=20),
                    expand=True,
                ),
            ],
        ),
        expand=True,
        bgcolor="#263238",
    )

    page.add(
        ft.Row(
            [
                sidebar,
                main_content,
            ],
            expand=True,
            spacing=0,
        )
    )


ft.app(target=main)