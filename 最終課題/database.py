import sqlite3

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("keio.db")

    def insert_station(self, station):
        sql = """
        INSERT INTO Station(station_name, limited_express)
        VALUES (?, ?)
        """
        self.conn.execute(sql, (
            station["station_name"],
            station["limited_express"]
        ))
        self.conn.commit()
