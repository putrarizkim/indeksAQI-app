import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# --- Konfigurasi Halaman ---
st.set_page_config(layout="wide", page_title="AQI Calculator: Advanced 🌬️📊")

# --- Header Aplikasi (Di bagian utama) ---
st.title("🌬️📊 Kalkulator Indeks Kualitas Udara (AQI) Interaktif")
st.markdown("## Analisis Kualitas Udara Lebih Mendalam")
st.write("Aplikasi ini memungkinkan Anda untuk mensimulasikan, menghitung, dan memahami Indeks Kualitas Udara (AQI) dengan lebih detail.")

st.markdown("---")

# --- Data Simulasi Lokasi ---
SIMULATED_LOCATION_DATA = {
    "Jakarta (Pagi Sibuk)": {
        "pm25": 75.0, "o3": 50.0, "co": 8.0, "so2": 30.0, "no2": 60.0
    },
    "Pegunungan (Bersih)": {
        "pm25": 8.0, "o3": 40.0, "co": 0.5, "so2": 2.0, "no2": 5.0
    },
    "Area Industri (Malam)": {
        "pm25": 120.0, "o3": 30.0, "co": 10.0, "so2": 80.0, "no2": 90.0
    },
    "Pilihan Manual": {
        "pm25": 15.0, "o3": 70.0, "co": 2.0, "so2": 10.0, "no2": 20.0
    }
}

# --- Fungsi Perhitungan AQI (Inti "Model") ---
def calculate_sub_aqi(concentration, breakpoints, aqi_values):
    if concentration < breakpoints[0][0]:
        return aqi_values[0][0]

    for i in range(len(breakpoints)):
        c_low, c_high = breakpoints[i]
        aqi_low, aqi_high = aqi_values[i]

        if c_low <= concentration <= c_high:
            if c_high == c_low:
                return aqi_low
            aqi = ((concentration - c_low) / (c_high - c_low)) * (aqi_high - aqi_low) + aqi_low
            return round(aqi)
        elif concentration > c_high and i == len(breakpoints) - 1:
            return aqi_high
    return 0

def get_aqi_category(aqi_value):
    if 0 <= aqi_value <= 50:
        return "Baik", "Kualitas udara memuaskan, risiko kesehatan sedikit atau tidak ada.", "green"
    elif 51 <= aqi_value <= 100:
        return "Sedang", "Kualitas udara dapat diterima; namun, untuk beberapa polutan mungkin ada kekhawatiran kesehatan moderat bagi sejumlah kecil orang yang sangat sensitif terhadap polusi udara.", "gold"
    elif 101 <= aqi_value <= 150:
        return "Tidak Sehat untuk Kelompok Sensitif", "Anggota kelompok sensitif mungkin mengalami efek kesehatan. Masyarakat umum cenderung tidak terpengaruh.", "orange"
    elif 151 <= aqi_value <= 200:
        return "Tidak Sehat", "Setiap orang mungkin mulai mengalami efek kesehatan; anggota kelompok sensitif mungkin mengalami efek yang lebih serius.", "red"
    elif 201 <= aqi_value <= 300:
        return "Sangat Tidak Sehat", "Peringatan kesehatan: setiap orang mungkin mengalami efek kesehatan yang lebih serius.", "rebeccapurple"
    else:
        return "Berbahaya", "Peringatan kesehatan serius: setiap orang mungkin mengalami efek kesehatan darurat.", "darkred"

def calculate_overall_aqi_and_sub_aqi(pm25, o3, co, so2, no2):
    pm25_bp = [(0.0, 12.0), (12.1, 35.4), (35.5, 55.4), (55.5, 150.4), (150.5, 250.4), (250.5, 500.4)]
    pm25_aqi_val = [(0, 50), (51, 100), (101, 150), (151, 200), (201, 300), (301, 500)]
    o3_bp = [(0.0, 54), (55, 70), (71, 85), (86, 105), (106, 200)]
    o3_aqi_val = [(0, 50), (51, 100), (101, 150), (151, 200), (201, 300)]
    co_bp = [(0.0, 4.4), (4.5, 9.4), (9.5, 12.4), (12.5, 15.4)]
    co_aqi_val = [(0, 50), (51, 100), (101, 150), (151, 200)]
    so2_bp = [(0.0, 35), (36, 75), (76, 185), (186, 304)]
    so2_aqi_val = [(0, 50), (51, 100), (101, 150), (151, 200)]
    no2_bp = [(0.0, 53), (54, 100), (101, 360), (361, 649)]
    no2_aqi_val = [(0, 50), (51, 100), (101, 150), (151, 200)]

    sub_aqi_values = {
        "PM2.5": calculate_sub_aqi(pm25, pm25_bp, pm25_aqi_val),
        "O3": calculate_sub_aqi(o3, o3_bp, o3_aqi_val),
        "CO": calculate_sub_aqi(co, co_bp, co_aqi_val),
        "SO2": calculate_sub_aqi(so2, so2_bp, so2_aqi_val),
        "NO2": calculate_sub_aqi(no2, no2_bp, no2_aqi_val)
    }

    overall_aqi = max(sub_aqi_values.values())
    return overall_aqi, sub_aqi_values

# --- Inisialisasi Session State ---
if 'last_aqi_data' not in st.session_state:
    st.session_state.last_aqi_data = {
        "pm25": 15.0, "o3": 70.0, "co": 2.0, "so2": 10.0, "no2": 20.0, "aqi": 0, "category": "", "implication": ""
    }
if 'calculation_done' not in st.session_state:
    st.session_state.calculation_done = False

# --- Bagian Input & Kontrol (Sekarang di Sidebar!) ---
with st.sidebar: # Semua yang ada di sini akan masuk ke sidebar
    st.header("⚙️ Input Kondisi Udara")
    st.info("Atur parameter polutan atau pilih skenario di sini.")

    scenario_option = st.selectbox(
        "Pilih Skenario Lokasi/Kondisi:",
        list(SIMULATED_LOCATION_DATA.keys()),
        index=3, # Default to "Pilihan Manual"
        help="Pilih skenario prasetel atau 'Pilihan Manual' untuk mengatur sendiri konsentrasi polutan."
    )

    current_data = SIMULATED_LOCATION_DATA[scenario_option]

    # Sliders untuk polutan
    st.markdown("---")
    st.subheader("Konsentrasi Polutan")
    pm25 = st.slider("PM2.5 (µg/m³)", min_value=0.0, max_value=200.0, value=float(current_data["pm25"]), step=0.1, key="sidebar_pm25")
    o3 = st.slider("O3 (ppb)", min_value=0.0, max_value=200.0, value=float(current_data["o3"]), step=0.1, key="sidebar_o3")
    co = st.slider("CO (ppm)", min_value=0.0, max_value=15.0, value=float(current_data["co"]), step=0.1, key="sidebar_co")
    so2 = st.slider("SO2 (ppb)", min_value=0.0, max_value=100.0, value=float(current_data["so2"]), step=0.1, key="sidebar_so2")
    no2 = st.slider("NO2 (ppb)", min_value=0.0, max_value=100.0, value=float(current_data["no2"]), step=0.1, key="sidebar_no2")

    st.markdown("---")
    if scenario_option != "Pilihan Manual":
        st.info(f"Nilai slider sudah disesuaikan untuk skenario: **{scenario_option}**")
    st.caption("Geser slider di atas untuk menyesuaikan nilai.")


# --- Bagian Utama Aplikasi (Konten setelah sidebar) ---
tab1, tab2 = st.tabs(["📊 Hasil Analisis", "📚 Tentang AQI"])

with tab1:
    st.header("1. Hasil Analisis Kualitas Udara")
    st.write("Klik tombol di bawah untuk menganalisis AQI berdasarkan input dari sidebar.")

    if st.button("Hitung & Analisis AQI", type="primary"):
        aqi_result, sub_aqi_values = calculate_overall_aqi_and_sub_aqi(pm25, o3, co, so2, no2)
        category, implication, color_code = get_aqi_category(aqi_result)

        st.session_state.last_aqi_data = {
            "pm25": pm25, "o3": o3, "co": co, "so2": so2, "no2": no2,
            "aqi": aqi_result, "category": category, "implication": implication, "color": color_code,
            "sub_aqi": sub_aqi_values
        }
        st.session_state.calculation_done = True
        # st.rerun() # Tidak perlu rerun jika tombol di main content memicu ini

    if st.session_state.calculation_done:
        current_aqi_data = st.session_state.last_aqi_data

        col_res_aqi, col_res_impact = st.columns([0.4, 0.6])

        with col_res_aqi:
            st.metric(label="Indeks Kualitas Udara (AQI) Saat Ini", value=current_aqi_data["aqi"])
            st.markdown(f"**<span style='color:{current_aqi_data['color']}; font-size: 24px;'>Kategori: {current_aqi_data['category']}</span>**", unsafe_allow_html=True)

            st.subheader("Rekomendasi Aksi:")
            if current_aqi_data["category"] == "Baik":
                st.success("✅ Kualitas udara sangat baik. Nikmati aktivitas luar ruangan Anda tanpa batasan.")
            elif current_aqi_data["category"] == "Sedang":
                st.warning("🟡 Kualitas udara moderat. Untuk kelompok sangat sensitif (anak-anak, lansia, penderita asma), pertimbangkan untuk mengurangi aktivitas luar ruangan yang berat.")
            elif current_aqi_data["category"] == "Tidak Sehat untuk Kelompok Sensitif":
                st.error("🟠 Tidak sehat untuk kelompok sensitif. Individu dengan penyakit jantung/paru-paru, anak-anak, dan lansia harus membatasi aktivitas fisik di luar ruangan.")
                st.write("➡️ Disarankan menggunakan masker saat di luar ruangan.")
            elif current_aqi_data["category"] == "Tidak Sehat":
                st.error("🔴 Udara tidak sehat untuk semua orang. Batasi aktivitas luar ruangan yang berkepanjangan atau berat. Kelompok sensitif harus menghindari semua aktivitas fisik di luar ruangan.")
                st.write("➡️ Gunakan masker N95/KN95 jika harus keluar. Pertimbangkan untuk menutup jendela.")
            elif current_aqi_data["category"] == "Sangat Tidak Sehat":
                st.error("🟣 Udara sangat tidak sehat. Semua orang harus menghindari aktivitas fisik di luar ruangan. Tetap di dalam ruangan dan tutup jendela/pintu.")
                st.write("➡️ Pertimbangkan penggunaan pembersih udara (air purifier).")
            else: # Berbahaya
                st.error("🟤 Kondisi udara berbahaya. Tetap di dalam ruangan. Semua aktivitas fisik di luar ruangan harus dihindari. Siapkan rencana darurat.")
                st.write("➡️ Cari tempat berlindung di dalam ruangan dengan ventilasi yang baik atau fasilitas pembersih udara.")

        with col_res_impact:
            st.subheader("Implikasi Kesehatan Umum:")
            st.write(current_aqi_data["implication"])

            st.subheader("Kontribusi Polutan Terhadap AQI:")
            sub_aqi_df = pd.DataFrame(st.session_state.last_aqi_data['sub_aqi'].items(), columns=['Polutan', 'Sub-AQI'])
            sub_aqi_df = sub_aqi_df.sort_values(by='Sub-AQI', ascending=False)

            fig, ax = plt.subplots(figsize=(8, 4))
            sns.barplot(x='Sub-AQI', y='Polutan', data=sub_aqi_df, palette='viridis', ax=ax)
            ax.set_title('Kontribusi Sub-AQI per Polutan')
            ax.set_xlabel('Nilai Sub-AQI')
            ax.set_ylabel('Polutan')
            ax.set_xlim(0, max(sub_aqi_df['Sub-AQI']) * 1.1)
            st.pyplot(fig)

        st.markdown("---")

        st.subheader("Perbandingan AQI (Simulasi)")
        avg_aqi_sim = np.random.randint(50, 150)
        st.info(f"""
        AQI Rata-rata/Sebelumnya di area serupa (simulasi): **{avg_aqi_sim}**
        * **AQI Saat Ini:** **{current_aqi_data['aqi']}**
        * **Perbedaan:** {current_aqi_data['aqi'] - avg_aqi_sim}
        """)
        st.caption("Perbandingan ini hanya simulasi untuk tujuan demonstrasi fitur.")
    else:
        st.info("Klik 'Hitung & Analisis AQI' untuk menampilkan hasil di sini.")

# --- Tab "Tentang AQI" ---
with tab2:
    st.header("📚 Tentang Indeks Kualitas Udara (AQI)")
    st.markdown("""
    Indeks Kualitas Udara (AQI) adalah alat yang digunakan untuk mengomunikasikan seberapa kotor atau bersih udara.
    AQI memberitahu Anda tentang dampak kesehatan yang mungkin Anda alami dalam beberapa jam atau hari setelah menghirup udara.

    #### Kategori AQI (Sederhana):
    -   **0-50 (Baik):** Kualitas udara memuaskan.
    -   **51-100 (Sedang):** Kualitas udara dapat diterima; kelompok sensitif mungkin terdampak.
    -   **101-150 (Tidak Sehat untuk Kelompok Sensitif):** Orang dengan penyakit paru-paru atau jantung, anak-anak, lansia, mungkin terdampak.
    -   **151-200 (Tidak Sehat):** Semua orang mungkin mulai merasakan efek kesehatan.
    -   **201-300 (Sangat Tidak Sehat):** Peringatan kesehatan.
    -   **301+ (Berbahaya):** Kondisi darurat.

    #### Polutan Utama yang Diukur AQI:
    1.  **Particulate Matter (PM2.5 dan PM10):** Partikel sangat kecil di udara.
    2.  **Ozon (O3):** Gas yang terbentuk ketika polutan bereaksi di bawah sinar matahari.
    3.  **Karbon Monoksida (CO):** Gas dari pembakaran tidak sempurna.
    4.  **Sulfur Dioksida (SO2):** Gas dari pembakaran bahan bakar fosil.
    5.  **Nitrogen Dioksida (NO2):** Gas dari pembakaran bahan bakar dan industri.

    #### Bagaimana AQI Dihitung (Konsep Umum):
    AQI dihitung secara individual untuk setiap polutan. Nilai AQI tertinggi dari semua polutan pada waktu tertentu menjadi AQI keseluruhan. Hal ini karena polutan yang memiliki dampak terbesar pada kesehatan pada suatu waktu tertentu adalah yang paling relevan.

    #### Disclaimer Penting:
    Aplikasi ini menyediakan **simulasi dan perhitungan AQI yang disederhanakan** untuk tujuan edukasi dan demonstrasi. Angka dan rekomendasi yang diberikan mungkin **tidak cocok** dengan data AQI real-time resmi dari badan pemerintah atau organisasi pemantau kualitas udara di wilayah Anda. Selalu rujuk sumber data kualitas udara resmi untuk informasi yang akurat dan saran kesehatan.
    """)

st.markdown("---")
st.caption("Dibuat dengan Streamlit. Sumber data AQI disederhanakan dari standar umum.")