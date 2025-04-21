import streamlit as st
import pandas as pd
from datetime import datetime, time
from timezonefinder import TimezoneFinder
from pytz import timezone, utc
from astral.sun import sun
from astral import LocationInfo
import pytz
from PIL import Image


# Header
st.set_page_config(page_title="🛬 Yatı Süresi Hesaplama?")

# Displaying the welcoming message
st.markdown("### Hoş geldin sevgilim 💖")  # Sweet and warm greeting

# Creating two columns to display GIFs side by side with some space
col1, col2 = st.columns([1, 1])  # Adjust the ratio for space between the GIFs

with col1:
    st.image("https://media1.tenor.com/m/estHtymljV0AAAAd/hello-hi.gif", width=300)

with col2:
    st.image("https://media1.tenor.com/m/NJMkAoGOGrkAAAAd/rohee.gif", width=300)





# Definition
st.title("Esma'nın yatısı ne kadar? 🤔")
st.caption("Varış & Dönüş zamanınıza göre yatınızdaki kalış süresi ve gündüz/gece hesaplaması yapılacak.")

# Airport Dataset
@st.cache_data
def load_airports():
    df = pd.read_csv("RestPlanner/airport-codes.csv")
    return df[df["iata_code"].notna()]

airports = load_airports()

selected_airport = None
airport_lat, airport_lon = None, None

# Input for airtport searching
query = st.text_input("Havalimanı Kodunu Giriniz (örn: IST, JFK)", max_chars=10).upper()

if query:
    # Search wwith only IATA Code
    airport_row = airports[airports['iata_code'] == query]

    if not airport_row.empty:
        selected_airport = airport_row.iloc[0]
        st.write(f"**Gideceğiniz Havaalanı Kodu:** {query}")
        st.write(f"**Gideceğiniz Havaalanı İsim:** {selected_airport['name']}")
        st.write(f"**Gideceğiniz Ülke Kodu:** {selected_airport['iso_country']}")

        # Coords
        coords = selected_airport['coordinates'].split(", ")
        airport_lat = float(coords[1])  # Enlem
        airport_lon = float(coords[0])  # Boylam
    else:
        # Hatalı kod girildiğinde gif + uyarı
        st.error("Hatalı havaalanı kodu girdin birtanem. Lütfen geçerli bir IATA kodu yaz! 🛑")

        col1, col2 = st.columns(2)

        with col1:
            st.image("https://media1.tenor.com/m/QQSmZAKIu4cAAAAd/korean-baby-scratch-head.gif", width=300)

        with col2:
            st.image("https://media1.tenor.com/m/kuG6V2W-8qAAAAAd/coreaninha-by-ch-saab.gif", width=300)



# Time Selection
if selected_airport is not None:
    st.markdown("### 🕓 Varış & Dönüş Bilgilerinizi Girin (GMT+0 olarak tabiki (: )")

    col1, col2 = st.columns(2)
    with col1:
        arrival_date = st.date_input("Varış Tarihi")
        arrival_hour = st.number_input("Varış Saati", 0, 23, 12)
        arrival_minute = st.number_input("Varış Dakikası", 0, 59, 0)
    with col2:
        departure_date = st.date_input("Dönüş Tarihi")
        departure_hour = st.number_input("Dönüş Saati", 0, 23, 12)
        departure_minute = st.number_input("Dönüş Dakikası", 0, 59, 0)

    if st.button("✨ Wingardium Leviosa ✈️"):
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
            
            # ... sonuçlar gösterildikten sonra
            st.markdown("### ✨ Yatı süren hazır sevgilim! ✈️")
            st.success(f"🕰️ Toplam Kalış Süren: {int(hours)} saat {int(minutes)} dakika")

            # Gündüz/gece kontrolü (Astral)
            city = LocationInfo(name=selected_airport['name'], region="", timezone=tz_name,
                                latitude=airport_lat, longitude=airport_lon)
            s = sun(city.observer, date=local_arrival.date(), tzinfo=local_tz)
            sunrise = s["sunrise"]
            sunset = s["sunset"]

            if sunrise is not None and sunset is not None:
                if sunrise <= local_arrival <= sunset:
                    st.info(f"🌞 Varışta gündüz! (Gün Doğumu&Batışı: {sunrise.strftime('%H:%M')} - {sunset.strftime('%H:%M')})")
                else:
                    st.info(f"🌙 Varışta gece. (Gün Doğumu&Batışı: {sunrise.strftime('%H:%M')} - {sunset.strftime('%H:%M')})")
            else:
                st.warning("Gündüz/gece verisi bulunamadı.")

        except Exception as e:
            st.error(f"Hata oluştu: {e}")
            

        


        st.caption("Şimdiden iyi istirhatler sevgilim, kendine iyi bak ❤️")

        col1, col2 = st.columns(2)

        with col1:
            st.image("https://media1.tenor.com/m/zZGprKYALQEAAAAd/bhibatsam-cute-kid.gif", width=300)

        with col2:
            st.image("https://media1.tenor.com/m/LOOM5x-oRsUAAAAd/baby.gif", width=300)

