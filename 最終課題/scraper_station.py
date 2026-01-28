import requests
from bs4 import BeautifulSoup
import time

class KeioStationScraper:
    def __init__(self):
        self.base_url = "https://www.keio.co.jp/train/station/"

    def scrape(self):
        response = requests.get(self.base_url)
        soup = BeautifulSoup(response.text, "html.parser")

        stations = []

        # 駅リンク（aタグ）を取得
        for a in soup.select("a[href^='/train/station/']"):
            station_name = a.text.strip()

            # 空文字・重複除外
            if not station_name or "駅" not in station_name:
                continue

            stations.append({
                "station_name": station_name.replace("駅", ""),
                "limited_express": None  # ← まずは仮
            })

            time.sleep(0.5)

        return stations
