import flet as ft
import requests
from datetime import datetime
import sqlite3

AREA_URL = "https://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"
DB_NAME = "weather_forecast.db"

# 天気アイコンのマッピング
WEATHER_ICONS = {
    "晴": "☀️", "曇": "☁️", "雨": "🌧️", "雪": "❄️",
    "晴時々曇": "🌤️", "晴後曇": "🌤️", "曇時々晴": "⛅",
    "曇後晴": "⛅", "晴時々雨": "🌦️", "曇時々雨": "🌧️",
    "雨時々曇": "🌧️",
}


def init_database():
    """データベースを初期化"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 地域センター情報テーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS centers (
            center_code TEXT PRIMARY KEY,
            center_name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    # 地域オフィス情報テーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS offices (
            office_code TEXT PRIMARY KEY,
            office_name TEXT NOT NULL,
            center_code TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (center_code) REFERENCES centers(center_code)
        )
    """)
    
    # 天気予報テーブル（正規化）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            office_code TEXT NOT NULL,
            forecast_date TEXT NOT NULL,
            weather TEXT NOT NULL,
            temp_min TEXT,
            temp_max TEXT,
            report_datetime TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            FOREIGN KEY (office_code) REFERENCES offices(office_code),
            UNIQUE(office_code, forecast_date, report_datetime)
        )
    """)
    
    # インデックス作成（検索高速化）
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_forecasts_office 
        ON forecasts(office_code, report_datetime DESC)
    """)
    
    conn.commit()
    conn.close()


def save_area_to_db(area_json):
    """エリア情報をDBに保存"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    created_at = datetime.now().isoformat()
    
    # センター情報を保存
    for center_code, center_data in area_json["centers"].items():
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO centers (center_code, center_name, created_at)
                VALUES (?, ?, ?)
            """, (center_code, center_data["name"], created_at))
        except Exception as e:
            print(f"Center保存エラー: {e}")
    
    # オフィス情報を保存
    for office_code, office_data in area_json["offices"].items():
        # このオフィスが属するセンターを見つける
        parent_center = None
        for center_code, center_data in area_json["centers"].items():
            if office_code in center_data.get("children", []):
                parent_center = center_code
                break
        
        if parent_center:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO offices (office_code, office_name, center_code, created_at)
                    VALUES (?, ?, ?, ?)
                """, (office_code, office_data["name"], parent_center, created_at))
            except Exception as e:
                print(f"Office保存エラー: {e}")
    
    conn.commit()
    conn.close()


def load_area_from_db():
    """DBからエリア情報を取得"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # センター情報取得
    cursor.execute("SELECT center_code, center_name FROM centers")
    centers = {row[0]: {"name": row[1], "children": []} for row in cursor.fetchall()}
    
    # オフィス情報取得
    cursor.execute("SELECT office_code, office_name, center_code FROM offices")
    offices = {}
    for row in cursor.fetchall():
        office_code, office_name, center_code = row
        offices[office_code] = {"name": office_name}
        if center_code in centers:
            centers[center_code]["children"].append(office_code)
    
    conn.close()
    
    return {"centers": centers, "offices": offices} if centers else None


def save_forecast_to_db(area_code, forecast_list, temps_min, temps_max, report_datetime):
    """天気予報データをデータベースに保存"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    fetched_at = datetime.now().isoformat()
    
    for i, (date_str, weather) in enumerate(forecast_list):
        temp_min = temps_min[i] if i < len(temps_min) else None
        temp_max = temps_max[i] if i < len(temps_max) else None
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO forecasts 
                (office_code, forecast_date, weather, temp_min, temp_max, report_datetime, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (area_code, date_str, weather, temp_min, temp_max, report_datetime, fetched_at))
        except Exception as e:
            print(f"DB保存エラー: {e}")
    
    conn.commit()
    conn.close()


def load_forecast_from_db(area_code, report_datetime=None):
    """データベースから天気予報データを取得"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    if report_datetime:
        # 特定の発表時刻のデータを取得
        cursor.execute("""
            SELECT forecast_date, weather, temp_min, temp_max, report_datetime
            FROM forecasts
            WHERE office_code = ? AND report_datetime = ?
            ORDER BY forecast_date ASC
        """, (area_code, report_datetime))
    else:
        # 最新のデータを取得
        cursor.execute("""
            SELECT forecast_date, weather, temp_min, temp_max, report_datetime
            FROM forecasts
            WHERE office_code = ? AND report_datetime = (
                SELECT report_datetime FROM forecasts 
                WHERE office_code = ? 
                ORDER BY report_datetime DESC LIMIT 1
            )
            ORDER BY forecast_date ASC
        """, (area_code, area_code))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return None, None, None, None
    
    forecast_list = [(row[0], row[1]) for row in rows]
    temps_min = [row[2] for row in rows]
    temps_max = [row[3] for row in rows]
    report_datetime = rows[0][4] if rows else None
    
    return forecast_list, temps_min, temps_max, report_datetime


def get_forecast_history(area_code):
    """特定地域の過去の予報発表時刻一覧を取得"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT report_datetime, fetched_at
        FROM forecasts
        WHERE office_code = ?
        ORDER BY report_datetime DESC
    """, (area_code,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return rows


def get_weather_icon(weather_text):
    """天気テキストから適切なアイコンを取得"""
    for key, icon in WEATHER_ICONS.items():
        if key in weather_text:
            return icon
    return "☀️"


def fetch_area():
    """エリア情報を取得（DBにキャッシュ）"""
    # まずDBから取得を試みる
    area_data = load_area_from_db()
    if area_data:
        return area_data, "DB"
    
    # DBになければAPIから取得してDBに保存
    area_data = requests.get(AREA_URL).json()
    save_area_to_db(area_data)
    return area_data, "API"


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
                ft.Text(date_display, size=14, weight=ft.FontWeight.BOLD, color="white"),
                ft.Container(height=5),
                ft.Text(icon, size=48),
                ft.Container(height=5),
                ft.Text(weather, size=11, text_align=ft.TextAlign.CENTER, color="#B0BEC5", max_lines=2),
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

    selected_area_text = ft.Text("地域を選択してください", size=20, weight=ft.FontWeight.BOLD, color="white")
    update_time_text = ft.Text("", size=12, color="#B0BEC5", italic=True)
    data_source_text = ft.Text("", size=11, color="#FFD700", italic=True)
    
    forecast_cards = ft.Row(wrap=True, spacing=15, run_spacing=15, scroll=ft.ScrollMode.AUTO)
    
    current_area_code = [None]
    current_area_name = [""]
    
    # 履歴選択ドロップダウン
    history_dropdown = ft.Dropdown(
        label="過去の予報を表示",
        width=300,
        bgcolor="white",
        visible=False,
    )

    def load_forecast(area_code, area_name, force_update=False, specific_datetime=None):
        """天気予報を読み込み（完全DB対応）"""
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
            
            # 特定の日時が指定されている場合
            if specific_datetime:
                forecast_list, temps_min, temps_max, report_datetime = load_forecast_from_db(area_code, specific_datetime)
                if forecast_list:
                    data_source_text.value = "データベースから過去予報を取得"
            
            # 強制更新でない場合はDBから最新を取得
            elif not force_update:
                forecast_list, temps_min, temps_max, report_datetime = load_forecast_from_db(area_code)
                if forecast_list:
                    data_source_text.value = "データベースから最新予報を取得"
            
            # DBにデータがないか、強制更新の場合はAPIから取得
            if not forecast_list:
                forecast_json = fetch_forecast(area_code)
                forecast_list, temps_min, temps_max, report_datetime = parse_forecast(forecast_json)
                
                # データベースに保存
                save_forecast_to_db(area_code, forecast_list, temps_min, temps_max, report_datetime)
                data_source_text.value = "気象庁APIから取得（DBに保存済み）"
            
            # 過去予報履歴を更新
            history_list = get_forecast_history(area_code)
            if history_list:
                history_dropdown.visible = True
                history_dropdown.options = [
                    ft.dropdown.Option(
                        key=dt,
                        text=f"{datetime.fromisoformat(dt.replace('Z', '+00:00')).strftime('%Y/%m/%d %H:%M')} 発表"
                    )
                    for dt, _ in history_list
                ]
                history_dropdown.value = specific_datetime if specific_datetime else (history_list[0][0] if history_list else None)
            else:
                history_dropdown.visible = False

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
        load_forecast(area_code, area_name, force_update=False)

    def on_refresh_click(e):
        """最新データを強制取得"""
        if current_area_code[0]:
            load_forecast(current_area_code[0], current_area_name[0], force_update=True)

    def on_history_change(e):
        """過去の予報を表示"""
        if current_area_code[0] and history_dropdown.value:
            load_forecast(current_area_code[0], current_area_name[0], specific_datetime=history_dropdown.value)

    history_dropdown.on_change = on_history_change

    # エリア情報を取得（DBから優先）
    area_json, area_source = fetch_area()
    print(f"エリア情報: {area_source}から取得")

    tiles = []
    for center in area_json["centers"].values():
        children = []
        for code in center["children"]:
            if code in area_json["offices"]:
                office = area_json["offices"][code]
                children.append(
                    ft.ListTile(
                        title=ft.Text(office["name"], color="white"),
                        data=code,
                        on_click=on_area_click,
                        hover_color="#1AFFFFFF",
                    )
                )

        if children:
            tiles.append(
                ft.ExpansionTile(
                    title=ft.Text(center["name"], color="white", weight=ft.FontWeight.BOLD),
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
                    content=ft.Row([
                        ft.Text("地域選択", size=18, weight=ft.FontWeight.BOLD, color="white"),
                    ]),
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
                    content=ft.Row([
                        ft.Text("☀️", size=32),
                        ft.Text("天気予報（改良版）", size=24, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Container(expand=True),
                        ft.TextButton("🔄 最新情報に更新", on_click=on_refresh_click, style=ft.ButtonStyle(color="white")),
                    ]),
                    bgcolor="#283593",
                    padding=15,
                ),
                ft.Container(
                    content=ft.Column([
                        selected_area_text,
                        update_time_text,
                        data_source_text,
                        history_dropdown,
                    ], spacing=5),
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

    page.add(ft.Row([sidebar, main_content], expand=True, spacing=0))


ft.app(target=main)