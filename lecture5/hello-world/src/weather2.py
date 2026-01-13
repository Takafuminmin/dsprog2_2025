import flet as ft
import requests
from datetime import datetime
import sqlite3
import json
import os

AREA_URL = "http://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"
DB_NAME = "weather_forecast.db"

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


def init_database():
    """データベースを初期化"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 天気予報テーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_code TEXT NOT NULL,
            area_name TEXT NOT NULL,
            forecast_date TEXT NOT NULL,
            weather TEXT NOT NULL,
            temp_min TEXT,
            temp_max TEXT,
            report_datetime TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(area_code, forecast_date, report_datetime)
        )
    """)
    
    # お気に入り地域テーブル（オプション）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorite_areas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_code TEXT UNIQUE NOT NULL,
            area_name TEXT NOT NULL,
            added_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()


def save_forecast_to_db(area_code, area_name, forecast_list, temps_min, temps_max, report_datetime):
    """天気予報データをデータベースに保存"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    created_at = datetime.now().isoformat()
    
    for i, (date_str, weather) in enumerate(forecast_list):
        temp_min = temps_min[i] if i < len(temps_min) else None
        temp_max = temps_max[i] if i < len(temps_max) else None
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO forecasts 
                (area_code, area_name, forecast_date, weather, temp_min, temp_max, report_datetime, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (area_code, area_name, date_str, weather, temp_min, temp_max, report_datetime, created_at))
        except Exception as e:
            print(f"DB保存エラー: {e}")
    
    conn.commit()
    conn.close()


def load_forecast_from_db(area_code):
    """データベースから天気予報データを取得"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT forecast_date, weather, temp_min, temp_max, report_datetime
        FROM forecasts
        WHERE area_code = ?
        ORDER BY forecast_date ASC
    """, (area_code,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return None, None, None, None
    
    forecast_list = [(row[0], row[1]) for row in rows]
    temps_min = [row[2] for row in rows]
    temps_max = [row[3] for row in rows]
    report_datetime = rows[0][4] if rows else None
    
    return forecast_list, temps_min, temps_max, report_datetime


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
    page.title = "天気予報アプリ（改良版）"
    page.window_width = 1200
    page.window_height = 600
    page.bgcolor = "#263238"
    page.padding = 0

    # データベース初期化
    init_database()

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
    
    data_source_text = ft.Text(
        "",
        size=11,
        color="#FFD700",
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

    def load_forecast(area_code, area_name, use_cache=False):
        """天気予報を読み込み（DBキャッシュ対応）"""
        try:
            selected_area_text.value = f" {area_name} - 読み込み中..."
            update_time_text.value = ""
            data_source_text.value = ""
            forecast_cards.controls.clear()
            page.update()
            
            forecast_list = None
            temps_min = None
            temps_max = None
            report_datetime = None
            
            # キャッシュ使用モードの場合はDBから取得を試みる
            if use_cache:
                forecast_list, temps_min, temps_max, report_datetime = load_forecast_from_db(area_code)
                if forecast_list:
                    data_source_text.value = "💾 データベースから取得"
            
            # DBにデータがないか、最新データ取得モードの場合はAPIから取得
            if not forecast_list:
                forecast_json = fetch_forecast(area_code)
                forecast_list, temps_min, temps_max, report_datetime = parse_forecast(forecast_json)
                
                # データベースに保存
                save_forecast_to_db(area_code, area_name, forecast_list, temps_min, temps_max, report_datetime)
                data_source_text.value = "🌐 気象庁APIから取得（DBに保存済み）"

            selected_area_text.value = f" {area_name}"
            
            if report_datetime:
                try:
                    dt = datetime.fromisoformat(report_datetime.replace("Z", "+00:00"))
                    update_time_text.value = f"発表: {dt.strftime('%Y年%m月%d日 %H:%M')}"
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
            data_source_text.value = ""
            page.update()

    def on_area_click(e):
        area_code = e.control.data
        area_name = e.control.title.value
        current_area_code[0] = area_code
        current_area_name[0] = area_name
        load_forecast(area_code, area_name, use_cache=True)  # 初回はキャッシュ優先

    def on_refresh_click(e):
        """最新データを取得"""
        if current_area_code[0]:
            load_forecast(current_area_code[0], current_area_name[0], use_cache=False)

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
                                "天気予報（改良版）",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color="white",
                            ),
                            ft.Container(expand=True),
                            ft.TextButton(
                                "🔄 最新情報に更新",
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
                            data_source_text,
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