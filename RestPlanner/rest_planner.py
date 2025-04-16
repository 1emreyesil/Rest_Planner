import streamlit as st
from datetime import datetime
import pandas as pd
import pytz
from timezonefinder import TimezoneFinder
from astral.sun import sun
from astral import LocationInfo

# Veritabanı CSV'yi oku (önceden indirilmiş olması gerekiyor)
df = pd.read_csv("airports.csv")

st.title("Yatıda ne kadar zamanım var? 🤔")
# INPUT
airport_code = st.text_input("Havalimanı Kodu (IATA - örn: JFK, CDG)").upper()
arrival_str = st.text_input("Varış tarihi ve saati (GMT+0 - örn: 2025-04-16 13:00)")
departure_str = st.text_input("Dönüş tarihi ve saati (GMT+0 - örn: 2025-04-19 22:00)")

if st.button("✈️ Hesapla"):
    try:
        # 1. Havalimanı detaylarını bul
        airport = df[df['iata_code'] == airport_code].iloc[0]
        lat, lon = airport['latitude_deg'], airport['longitude_deg']
        municipality = airport['municipality'] or "Unknown"
        country = airport['iso_country']
        
        # 2. Saat dilimini bul
        tf = TimezoneFinder()
        tz_str = tf.timezone_at(lat=lat, lng=lon)
        tz = pytz.timezone(tz_str)

        # 3. Tarihleri UTC olarak al ve yerel saate çevir
        arrival_utc = pytz.utc.localize(datetime.strptime(arrival_str, "%Y-%m-%d %H:%M"))
        departure_utc = pytz.utc.localize(datetime.strptime(departure_str, "%Y-%m-%d %H:%M"))
        arrival_local = arrival_utc.astimezone(tz)
        departure_local = departure_utc.astimezone(tz)

        # 4. Gündüz/gece hesapları
        city = LocationInfo(name=municipality, region=country, timezone=tz_str, latitude=lat, longitude=lon)
        total_daylight = 0
        total_night = 0

        current_day = arrival_local.date()
        end_day = departure_local.date()

        while current_day <= end_day:
            s = sun(city.observer, date=current_day, tzinfo=tz)
            sunrise, sunset = s['sunrise'], s['sunset']
            day_start = max(arrival_local, sunrise)
            day_end = min(departure_local, sunset)

            if day_start < day_end:
                daylight = (day_end - day_start).total_seconds() / 3600
                total_daylight += daylight

            total_time = 24 if current_day not in [arrival_local.date(), departure_local.date()] else \
                         (departure_local - arrival_local).total_seconds() / 3600
            total_night += max(total_time - daylight, 0)

            current_day += pd.Timedelta(days=1)

        # 5. Sonuçları göster
        st.success(f"📍 {municipality}, {country} ({airport_code})")
        st.write(f"🕓 Saat Dilimi: {tz_str}")
        st.write(f"🧳 Kalış süresi: {(departure_local - arrival_local)}")
        st.write(f"☀️ Toplam Gündüz: {total_daylight:.2f} saat")
        st.write(f"🌙 Toplam Gece: {total_night:.2f} saat")

    except Exception as e:
        st.error(f"Bir hata oluştu: {e}")
