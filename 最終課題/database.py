class Database:
    def __init__(self):
        self.conn = sqlite3.connect("keio.db")

    def insert_station_with_time(self, station):
        # ① Station に挿入
        cur = self.conn.cursor()
        cur.execute("""
        INSERT INTO Station(station_name, limited_express)
        VALUES (?, ?)
        """, (
            station["station_name"],
            station["limited_express"]
        ))

        station_id = cur.lastrowid  # ← 超重要

        # ② TravelTime に挿入
        cur.execute("""
        INSERT INTO TravelTime(station_id, minutes)
        VALUES (?, ?)
        """, (
            station_id,
            station["minutes"]
        ))

        self.conn.commit()
