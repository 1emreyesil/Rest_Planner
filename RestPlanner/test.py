import streamlit as st
import pandas as pd
from datetime import datetime, time
from timezonefinder import TimezoneFinder
from pytz import timezone, utc
from astral.sun import sun
from astral import LocationInfo
import pytz
from PIL import Image


# Başlık
st.set_page_config(page_title="Kabin Memuru Zaman Planlayıcısı", page_icon="🛫")
st.title("🛬 Kabin Memuru Zaman Planlayıcısı")
st.caption("Varış & Dönüş zamanına göre kalış süresi ve gündüz/gece hesaplaması")

# Havalimanı veritabanı
@st.cache_data
def load_airports():
    df = pd.read_csv("RestPlanner/airport-codes.csv")
    return df[df["iata_code"].notna()]

airports = load_airports()

selected_airport = None
airport_lat, airport_lon = None, None

# Havalimanı arama inputunu al
query = st.text_input("Havalimanı Ara (Kod / Şehir / Ad)", max_chars=30).upper()

# Havalimanı arama için boşluk yoksa işlemi başlat
if query:
    # 1. Havaalanı koduna göre arama
    airport_row = airports[airports['iata_code'] == query]

    # 2. Şehir adına veya havaalanı adına göre arama
    if airport_row.empty:
        airport_row = airports[airports['municipality'].str.upper().str.contains(query)]
    
    if airport_row.empty:
        airport_row = airports[airports['name'].str.upper().str.contains(query)]
    
    # Havaalanı bulunduysa
    if not airport_row.empty:
        selected_airport = airport_row.iloc[0]
        st.write(f"**Seçilen Havaalanı:** {query}")
        st.write(f"**İsim:** {selected_airport['name']}")
        st.write(f"**Ülke:** {selected_airport['iso_country']}")

        # Koordinatlar
        coords = selected_airport['coordinates'].split(", ")
        airport_lat = float(coords[1])  # Enlem
        airport_lon = float(coords[0])  # Boylam
        st.write(f"**Enlem:** {airport_lat}, **Boylam:** {airport_lon}")
    else:
        # Geçersiz giriş için hata mesajı
        st.error("Geçersiz havaalanı kodu veya şehir adı! Lütfen geçerli bir kod veya şehir girin.")

# Zaman seçimi
if selected_airport is not None:
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
            city = LocationInfo(name=selected_airport['name'], region="", timezone=tz_name,
                                latitude=airport_lat, longitude=airport_lon)
            s = sun(city.observer, date=local_arrival.date(), tzinfo=local_tz)
            sunrise = s["sunrise"]
            sunset = s["sunset"]

            if sunrise is not None and sunset is not None:
                if sunrise <= local_arrival <= sunset:
                    st.info(f"🌞 Varışta gündüz! (Güneş: {sunrise.strftime('%H:%M')} - {sunset.strftime('%H:%M')})")
                else:
                    st.info(f"🌙 Varışta gece. (Güneş: {sunrise.strftime('%H:%M')} - {sunset.strftime('%H:%M')})")
            else:
                st.warning("Gündüz/gece verisi bulunamadı.")

        except Exception as e:
            st.error(f"Hata oluştu: {e}")
            
        # ... sonuçlar gösterildikten sonra
        st.markdown("### ✨ Yatı süren hazır! ✈️")
        
        # Eğer yerel bir GIF kullanıyorsan:
        gif = Image.open("RestPlanner/tenor.gif")
        st.image(gif, caption="Şimdiden iyi istirhatler sevgilim, kendine iyi bak❤️", use_container_width=True)
