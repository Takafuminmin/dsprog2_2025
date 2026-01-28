from database import Database
from scraper_station import KeioStationScraper
from scraper_time import KeioTimeScraper

def main():
    print("main.py start")

    db = Database()
    db.create_tables()
    print("database OK")

    station_scraper = KeioStationScraper()
    time_scraper = KeioTimeScraper()

    stations = station_scraper.scrape()
    print(f"stations scraped: {len(stations)}")

    for station in stations:
        minutes = time_scraper.get_minutes(station["station_name"])
        station["minutes"] = minutes
        db.insert_station_with_time(station)

    print("ALL DONE")

if __name__ == "__main__":
    main()
