import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

conn = sqlite3.connect("keio.db")

df = pd.read_sql("""
SELECT s.station_name, s.limited_express, t.minutes
FROM Station s
JOIN TravelTime t ON s.station_id = t.station_id
""", conn)

print(df)

# 平均比較
avg = df.groupby("limited_express")["minutes"].mean()
print("Average travel time:", avg)

# 箱ひげ図
df.boxplot(column="minutes", by="limited_express",
           grid=False)
plt.title("所要時間の分布")
plt.suptitle("")
plt.xlabel("特急停車 (1=Yes, 0=No)")
plt.ylabel("新宿までの所要時間（分）")
plt.show()
