from scraper_station import KeioStationScraper
from scraper_time import TravelTimeScraper
from database import Database

station_scraper = KeioStationScraper()
time_scraper = TravelTimeScraper()
db = Database()

stations = station_scraper.scrape()

for station in stations:
    minutes = time_scraper.get_time_to_shinjuku(station["station_name"])
    station["minutes"] = minutes
    db.insert_station(station)
