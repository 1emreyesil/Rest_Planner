# %%
import streamlit as st
import pandas as pd
from datetime import datetime, time
from timezonefinder import TimezoneFinder
from pytz import timezone, utc
from astral.sun import sun
from astral import LocationInfo
import pytz

# Başlık
st.set_page_config(page_title="Kabin Memuru Zaman Planlayıcısı", page_icon="🛫")
st.title("🛬 Kabin Memuru Zaman Planlayıcısı")
st.caption("Varış & Dönüş zamanına göre kalış süresi ve gündüz/gece hesaplaması")

# Havalimanı veritabanı
@st.cache_data
def load_airports():
    df = pd.read_csv(r"D:\İndirilenler\python\RestPlanner\airport-codes.csv")
    return df[df["iata_code"].notna()]

airports = load_airports()

# Havalimanı arama
query = st.text_input("Havalimanı Ara (Kod / Şehir / Ad)", max_chars=30).upper()

selected_airport = None
airport_lat, airport_lon = None, None

if len(query) >= 2:
    matches = airports[
        airports["iata_code"].str.contains(query, na=False) |
        airports["municipality"].str.upper().str.contains(query, na=False) |
        airports["name"].str.upper().str.contains(query, na=False)
    ]

    options = [
        f"{row['iata_code']} - {row['municipality']} ({row['name']})"
        for _, row in matches.iterrows()
    ]

    if options:
        selected_option = st.selectbox("Havalimanını Seç", options)
        selected_airport = selected_option.split(" - ")[0]
        selected_row = matches[matches["iata_code"] == selected_airport].iloc[0]
        airport_lat = selected_row["latitude_deg"]
        airport_lon = selected_row["longitude_deg"]
    else:
        st.warning("Eşleşen havalimanı bulunamadı.")
else:
    st.info("Lütfen en az 2 harf girin.")

# Zaman seçimi
if selected_airport:
    st.markdown("### 🕓 Varış & Dönüş Bilgileri (GMT+0)")

    col1, col2 = st.columns(2)
    with col1:
        arrival_date = st.date_input("Varış Tarihi")
        arrival_hour = st.number_input("Varış Saati", 0, 23, 12)
        arrival_minute = st.number_input("Varış Dakikası", 0, 59, 0)
    with col2:
        departure_date = st.date_input("Dönüş Tarihi")
        departure_hour = st.number_input("Dönüş Saati", 0, 23, 12)
        departure_minute = st.number_input("Dönüş Dakikası", 0, 59, 0)

    if st.button("✈️ Hesapla"):
        try:
            # GMT+0 saatlerini oluştur
            arrival_utc = datetime.combine(arrival_date, time(arrival_hour, arrival_minute))
            departure_utc = datetime.combine(departure_date, time(departure_hour, departure_minute))

            # Timezone bul
            tf = TimezoneFinder()
            tz_name = tf.timezone_at(lng=airport_lon, lat=airport_lat)
            local_tz = timezone(tz_name)

            # Yerel saatlere çevir
            local_arrival = utc.localize(arrival_utc).astimezone(local_tz)
            local_departure = utc.localize(departure_utc).astimezone(local_tz)

            # Süre hesapla
            duration = local_departure - local_arrival
            hours = duration.total_seconds() // 3600
            minutes = (duration.total_seconds() % 3600) // 60

            st.success(f"🕰️ Toplam Kalış Süresi: {int(hours)} saat {int(minutes)} dakika")

            # Gündüz/gece kontrolü (Astral)
            city = LocationInfo(name=selected_airport, region="", timezone=tz_name,
                                latitude=airport_lat, longitude=airport_lon)
            s = sun(city.observer, date=local_arrival.date(), tzinfo=local_tz)
            sunrise = s["sunrise"]
            sunset = s["sunset"]

            if sunrise <= local_arrival <= sunset:
                st.info(f"🌞 Varışta gündüz! (Güneş: {sunrise.strftime('%H:%M')} - {sunset.strftime('%H:%M')})")
            else:
                st.info(f"🌙 Varışta gece. (Güneş: {sunrise.strftime('%H:%M')} - {sunset.strftime('%H:%M')})")

        except Exception as e:
            st.error(f"Hata oluştu: {e}")

# %%



