import sqlite3

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("keio.db")

    def create_tables(self):
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Station (
            station_id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_name TEXT,
            limited_express INTEGER
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS TravelTime (
            time_id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id INTEGER,
            minutes INTEGER,
            FOREIGN KEY(station_id) REFERENCES Station(station_id)
        )
        """)
        self.conn.commit()

    def insert_station_with_time(self, station):
        cur = self.conn.cursor()
        cur.execute("""
        INSERT INTO Station(station_name, limited_express)
        VALUES (?, ?)
        """, (station["station_name"], station["limited_express"]))

        station_id = cur.lastrowid

        cur.execute("""
        INSERT INTO TravelTime(station_id, minutes)
        VALUES (?, ?)
        """, (station_id, station["minutes"]))

        self.conn.commit()
