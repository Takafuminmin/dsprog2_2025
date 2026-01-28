import requests
from bs4 import BeautifulSoup
import time

class TravelTimeScraper:
    def __init__(self):
        self.base_url = "https://transit.yahoo.co.jp/search/result"

    def get_time_to_shinjuku(self, station_name):
        params = {
            "from": station_name,
            "to": "新宿"
        }

        response = requests.get(self.base_url, params=params)
        soup = BeautifulSoup(response.text, "html.parser")

        time_text = soup.select_one("所要時間セレクタ").text
        minutes = int(time_text.replace("分", ""))

        time.sleep(1)
        return minutes
