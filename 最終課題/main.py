print("main.py start")

from scraper_station import KeioStationScraper
print("scraper_station OK")

from scraper_time import TravelTimeScraper
print("scraper_time OK")

from database import Database
print("database OK")


station_scraper = KeioStationScraper()
time_scraper = TravelTimeScraper()
db = Database()

stations = station_scraper.scrape()

for station in stations:
    minutes = time_scraper.get_time_to_shinjuku(station["station_name"])
    station["minutes"] = minutes
    db.insert_station_with_time(station)

stations = station_scraper.scrape()
print(stations[:5])
print(len(stations))
