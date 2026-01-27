import requests
from bs4 import BeautifulSoup
import time

class KeioStationScraper:
    def __init__(self):
        self.base_url = "（京王電鉄 駅一覧ページURL）"

    def scrape(self):
        response = requests.get(self.base_url)
        soup = BeautifulSoup(response.text, "html.parser")

        stations = []

        for row in soup.select("駅情報の行セレクタ"):
            station_name = row.select_one("駅名セレクタ").text.strip()

            # 特急停車の有無（アイコンや文字で判定）
            is_limited_express = "特急" in row.text

            stations.append({
                "station_name": station_name,
                "limited_express": is_limited_express
            })

            time.sleep(1)

        return stations
