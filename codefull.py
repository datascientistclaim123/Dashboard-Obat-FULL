import streamlit as st
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import re

# Cache untuk membaca dataset
@st.cache_data
def load_data(file_path):
    return pd.read_excel(file_path)

# File data untuk kedua navigasi
df = load_data("Data Obat Input Billing Manual - Updated 18122024 - MIKA Removed.xlsx")  # Ganti dengan path file yang sesuai

# Pastikan kolom Qty dan Amount Bill adalah numerik
df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0)
df['Amount Bill'] = pd.to_numeric(df['Amount Bill'], errors='coerce').fillna(0)
df['Harga Satuan'] = df['Harga Satuan'].round()

# Sidebar untuk navigasi
st.sidebar.title("Navigasi")
selected_page = st.sidebar.radio("Pilih Halaman:", ["Distribusi Penggunaan Obat per Provider", "Rekomendasi Substitusi Obat"])

if selected_page == "Distribusi Penggunaan Obat per Provider":
    # Page 1: Dashboard Sebaran Obat
    st.title("Dashboard Sebaran Obat di Tiap Provider 💊")

    # st.markdown("<small>Created by: Dexcel Oswald Otniel</small>", unsafe_allow_html=True)

    # Menampilkan preview data
    st.subheader("Preview Data")
    st.dataframe(df)

    # Container untuk mengelola tabel dinamis
    tabel_container = st.container()

    # State untuk menyimpan jumlah tabel yang ditampilkan
    if "table_count" not in st.session_state:
        st.session_state.table_count = 1  # Mulai dengan 1 tabel

    df['TreatmentFinish'] = pd.to_datetime(df['TreatmentFinish'], errors='coerce')

    # Fungsi untuk menampilkan tabel berdasarkan filter
    def display_table(index):
        st.subheader(f"Tabel {index}")

        # Ambil filter dari session_state jika ada
        selected_group_providers = st.session_state.get(f"group_provider_{index}", [])
        selected_treatment_places = st.session_state.get(f"treatment_place_{index}", [])
        selected_doctors = st.session_state.get(f"doctor_name_{index}", [])
        selected_diagnosis = st.session_state.get(f"primary_diagnosis_{index}", [])
        selected_product_types = st.session_state.get(f"product_type_{index}", [])
        selected_date_range = st.session_state.get(f"date_range_{index}", [None, None])

        # Filter data berdasarkan semua pilihan saat ini
        filtered_df = df.copy()

        # Komponen filter - Pilih Group Provider
        group_provider_options = filtered_df['GroupProvider'].dropna().unique()
        selected_group_providers = st.multiselect(
            f"[Tabel {index}] Pilih Group Provider:",
            options=group_provider_options,
            default=selected_group_providers,
            key=f"group_provider_{index}"
        )

        if selected_group_providers:
            filtered_df = filtered_df[filtered_df['GroupProvider'].isin(selected_group_providers)]
        
        treatment_place_options = filtered_df['TreatmentPlace'].dropna().unique()
        selected_treatment_places = st.multiselect(
            f"[Tabel {index}] Pilih Provider:",
            options=treatment_place_options,
            default=selected_treatment_places,
            key=f"treatment_place_{index}"
        )

        if selected_treatment_places:
            filtered_df = filtered_df[filtered_df['TreatmentPlace'].isin(selected_treatment_places)]
        
        doctor_options = filtered_df['DoctorName'].dropna().unique()
        selected_doctors = st.multiselect(
            f"[Tabel {index}] Pilih Doctor Name:",
            options=doctor_options,
            default=selected_doctors,
            key=f"doctor_name_{index}"
        )

        if selected_doctors:
            filtered_df = filtered_df[filtered_df['DoctorName'].isin(selected_doctors)]
        
        diagnosis_options = filtered_df['PrimaryDiagnosis'].dropna().unique()
        selected_diagnosis = st.multiselect(
            f"[Tabel {index}] Pilih Primary Diagnosis:",
            options=diagnosis_options,
            default=selected_diagnosis,
            key=f"primary_diagnosis_{index}"
        )

        if selected_diagnosis:
            filtered_df = filtered_df[filtered_df['PrimaryDiagnosis'].isin(selected_diagnosis)]
        
        product_type_options = filtered_df['ProductType'].dropna().unique()
        selected_product_types = st.multiselect(
            f"[Tabel {index}] Pilih Product Type:",
            options=product_type_options,
            default=selected_product_types,
            key=f"product_type_{index}"
        )

        if selected_product_types:
            filtered_df = filtered_df[filtered_df['ProductType'].isin(selected_product_types)]
        
        # Fitur Timeline
        st.write("Pilih rentang tanggal:")
        min_date = pd.to_datetime(df["TreatmentFinish"].min())
        max_date = pd.to_datetime(df["TreatmentFinish"].max())

        # Periksa apakah session_state untuk date_range sudah ada, jika belum, inisialisasi
        if f"date_range_{index}" not in st.session_state:
            st.session_state[f"date_range_{index}"] = [min_date, max_date]
        
        date_range = st.date_input(f"[Tabel {index}] Rentang Tanggal:",
                                   value=(selected_date_range if all(selected_date_range) else [min_date, max_date]),
                                   min_value=min_date, max_value=max_date, key=f"date_range_{index}")

        # Hanya menyimpan kembali rentang tanggal ke session_state setelah perubahan
        if date_range != st.session_state[f"date_range_{index}"]:
            st.session_state[f"date_range_{index}"] = date_range

        # Filter data berdasarkan rentang tanggal
        if len(date_range) == 2 and all(date_range):
            start_date, end_date = pd.to_datetime(date_range)
            filtered_df = filtered_df[
                (pd.to_datetime(filtered_df['TreatmentFinish']) >= start_date) &
                (pd.to_datetime(filtered_df['TreatmentFinish']) <= end_date)]

        if filtered_df.empty:
            st.warning(f"Tidak ada data untuk filter di tabel {index}.")
        else:
            # Mengelompokkan berdasarkan "Nama Item Garda Medika"
            grouped_df = filtered_df.groupby("Nama Item Garda Medika").agg(
                Qty=('Qty', 'sum'),
                AmountBill=('Amount Bill', 'sum'),
                HargaSatuan=('Harga Satuan', 'median'),
                Golongan=('Golongan', 'first'),
                Subgolongan=('Subgolongan', 'first'),
                KomposisiZatAktif=('Komposisi Zat Aktif', 'first')
            ).reset_index()

            # Hilangkan desimal dengan pembulatan
            grouped_df['Qty'] = grouped_df['Qty'].astype(int)
            grouped_df['AmountBill'] = grouped_df['AmountBill'].astype(int)
            grouped_df['HargaSatuan'] = grouped_df['HargaSatuan'].fillna(0).round(0).astype(int)

            # Pindahkan kolom Qty, Amount Bill, dan Harga Satuan ke paling kanan
            column_order = [
                col for col in grouped_df.columns if col not in ['Qty', 'AmountBill', 'HargaSatuan']
            ] + ['Qty', 'AmountBill', 'HargaSatuan']
            grouped_df = grouped_df[column_order]

            # Menampilkan tabel yang sudah digabungkan
            st.dataframe(grouped_df, height=300)

            # Total Amount Bill
            if 'AmountBill' in grouped_df.columns:
                total_amount_bill = grouped_df['AmountBill'].sum()
                formatted_total = f"Rp {total_amount_bill:,.0f}".replace(",", ".")
                st.markdown(f"**Total Amount Bill: {formatted_total}**")
            else:
                st.warning("Kolom 'Amount Bill' tidak ditemukan di dataset.")

            # WordCloud
            st.subheader("WordCloud")
            
            # Gabungkan semua teks dari kolom 'Nama Item Garda Medika'
            wordcloud_text = " ".join(grouped_df['Nama Item Garda Medika'].dropna().astype(str))

            # Daftar kata yang ingin dihapus
            excluded_words = ["FORTE","PLUS","PLU","INFLUAN","INFUSAN","INFUS","OTSU","SP","D","S","XR","PF","FC","FORCE","B","C","P","OTU","IRPLU","NEBU","TEBOKAN","SS",
                              "N","G","ONE","VIT","O","AY","H","ETA","WIA","IV","IR","RING","WATER","SR","RL","PFS","MR","DP","NS","WIDA" ,"E","0D","BMT","MINIDOSE",
                              "Q", "TB", "TABLET", "GP", "MMR", "M", "WI", "Z", "NEO", "MIX", "GRANULE", "TT", "NA", "CL", "L", "FT", "MG", "KID", "HCL", "KIDS","DAILY",
                              "CARE", "F", "NEBULE", "NACL", "PAED", "DEWASA", "ORAL", "BABY", "LFX", "GEL", "JELLY", "STRAWBERRY", "NATRIUM", "ENEMA", "DHA", "ORAL",
                              "KA","EN","NEW","BHP","DUO","C0","CO","AL","GEL","DMP","KCL","PEN","T","INJECTION","PPD","DS","SODIUM","EXPECTORANT","JUNIOR","ANAK","SET",
                              "0DT", "MINT", "ORIGINAL", "AQUA", "KAPSUL","KOSONG", "0D","NEBULES","PLATINUM","SPINAL","DRAGEE","MINYAK","PHP","LASAL","WOUND","OD","QV",
                              "CHLORIDA","ODT","OP","COMPLEX","CENDO","VITAMIN"]

            # Gabungkan semua kata yang akan dihapus menjadi pola regex
            excluded_pattern = r'\b(?:' + '|'.join(map(re.escape, excluded_words)) + r')\b'

            # Hapus kata-kata dalam excluded_words tanpa menghapus bagian dari kata lain
            wordcloud_text = re.sub(excluded_pattern, '', wordcloud_text, flags=re.IGNORECASE)

            # Buat WordCloud
            wordcloud = WordCloud(width=800, height=400, background_color="white").generate(wordcloud_text)
            
            # Tampilkan WordCloud
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wordcloud, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)

    # Menampilkan tabel dinamis
    for i in range(1, st.session_state.table_count + 1):
        with tabel_container:
            display_table(i)

    # Tombol untuk menambah tabel baru
    if st.button("Insert Tabel Baru"):
        st.session_state.table_count += 1

elif selected_page == "Rekomendasi Substitusi Obat":
    # Title
    st.title("Dashboard Rekomendasi Substitusi Obat 💊")

    # Input untuk filter range tanggal
    st.sidebar.header("Filter")
    date_range = st.sidebar.date_input(
        "Pilih Rentang Tanggal:",
        value=[df['TreatmentFinish'].min(), df['TreatmentFinish'].max()],
        min_value=df['TreatmentFinish'].min(),
        max_value=df['TreatmentFinish'].max(),
        key="date_range"
    )

    # Mendefinisikan filtered_df terlebih dahulu dengan dataset asli df
    filtered_df = df.copy()

    # Pastikan date_range valid (rentang tanggal tidak kosong)
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[(filtered_df['TreatmentFinish'] >= pd.Timestamp(start_date)) &
                                (filtered_df['TreatmentFinish'] <= pd.Timestamp(end_date))]
    else:
        st.error("Silakan pilih rentang tanggal yang valid.")

    # Dropdown filter lainnya
    nama_obat = st.sidebar.selectbox("Pilih Nama Item Obat:", df['Nama Item Garda Medika'].unique())
    treatment_place = st.sidebar.selectbox("Pilih TreatmentPlace (RS/Klinik):", df['TreatmentPlace'].unique())

    # Filter data berdasarkan input
    filtered_df_input = filtered_df[(filtered_df['Nama Item Garda Medika'] == nama_obat) & 
                                    (filtered_df['TreatmentPlace'] == treatment_place)]

    if not filtered_df_input.empty:
        # Statistik obat
        total_qty = filtered_df_input['Qty'].sum()
        total_amount_bill = filtered_df_input['Amount Bill'].sum()
        median_harga_satuan = filtered_df_input['Harga Satuan'].median()

        st.subheader("Statistik Obat yang Dipilih")
        st.write(f"**Total Qty:** {int(total_qty)}")
        st.write(f"**Total Amount Bill:** Rp {int(total_amount_bill):,}")
        st.write(f"**Harga Satuan:** Rp {int(median_harga_satuan):,}")

        # Filter rekomendasi obat
        komposisi_zat_aktif = filtered_df_input['Komposisi Zat Aktif'].iloc[0]
        rekomendasi_df = filtered_df[(filtered_df['Komposisi Zat Aktif'] == komposisi_zat_aktif) & (filtered_df['Nama Item Garda Medika'] != nama_obat)]

        # Agregasi untuk rekomendasi
        def aggregate_data(data):
            grouped = data.groupby(['Nama Item Garda Medika', 'TreatmentPlace']).agg(
                GroupProvider=('GroupProvider', 'first'),
                Golongan=('Golongan', 'first'),
                Subgolongan=('Subgolongan', 'first'),
                KomposisiZatAktif=('Komposisi Zat Aktif', 'first'),
                TotalQty=('Qty', 'sum'),
                TotalAmountBill=('Amount Bill', 'sum'),
                HargaSatuan=('Harga Satuan', 'median')
            ).reset_index()
            return grouped
        
        # Fungsi untuk membulatkan kolom angka dan memperbaiki format
        def format_columns(df):
            df['TotalQty'] = df['TotalQty'].round(0).astype(int)
            df['TotalAmountBill'] = df['TotalAmountBill'].round(0).astype(int)
            df['HargaSatuan'] = df['HargaSatuan'].round(0).astype(int)
            if 'Cost Saving (%)' in df.columns:
                df['Cost Saving (%)'] = df['Cost Saving (%)'].round(2)
            return df
        
        # Fungsi untuk memberi warna berdasarkan nilai
        def colorize(val):
            color = 'green' if val < 0 else 'red'  # Hijau untuk negatif, merah untuk positif
            return f'background-color: {color}; color: white;'  # Menambahkan warna latar belakang dan teks

        # Rekomendasi di RS sama
        rekomendasi_same_rs = rekomendasi_df[rekomendasi_df['TreatmentPlace'] == treatment_place]
        if not rekomendasi_same_rs.empty:
            rekomendasi_same_rs_grouped = aggregate_data(rekomendasi_same_rs)
            rekomendasi_same_rs_grouped['Cost Saving per Satuan'] = (
                rekomendasi_same_rs_grouped['HargaSatuan'] - median_harga_satuan
            )
            rekomendasi_same_rs_grouped['Cost Saving Amount'] = (
                (rekomendasi_same_rs_grouped['HargaSatuan'] - median_harga_satuan) * total_qty
            )
            rekomendasi_same_rs_grouped['Cost Saving (%)'] = (
                (rekomendasi_same_rs_grouped['HargaSatuan'] - median_harga_satuan) / median_harga_satuan * 100
            )

            # Format Kolom Angka & Styler Cost Saving
            rekomendasi_same_rs_grouped = format_columns(rekomendasi_same_rs_grouped).style.applymap(colorize, subset=["Cost Saving per Satuan", "Cost Saving Amount", "Cost Saving (%)"])

            # Format angka di kolom "Cost Saving (%)"
            rekomendasi_same_rs_grouped = rekomendasi_same_rs_grouped.format({
                'Cost Saving (%)': "{:+.2f}%", # Format dua angka belakang koma
                'Cost Saving per Satuan': "{:+,.0f}", # Format pemisah ribuan
                'Cost Saving Amount': "{:+,.0f}", # Format pemisah ribuan
                'TotalAmountBill': "{:,.0f}", # Format pemisah ribuan
                'HargaSatuan': "{:,.0f}" # Format pemisah ribuan
            })

            st.subheader("Rekomendasi Obat Substitusi (RS Sama)")
            st.dataframe(rekomendasi_same_rs_grouped)
        else:
            st.write("Tidak ada rekomendasi substitusi di RS yang sama.")

        # Rekomendasi di RS lain (semua RS lain tanpa pembatasan)
        rekomendasi_other_rs = rekomendasi_df[rekomendasi_df['TreatmentPlace'] != treatment_place]
        if not rekomendasi_other_rs.empty:
            rekomendasi_other_rs_grouped = aggregate_data(rekomendasi_other_rs)
            rekomendasi_other_rs_grouped['Cost Saving per Satuan'] = (
                rekomendasi_other_rs_grouped['HargaSatuan'] - median_harga_satuan
            )
            rekomendasi_other_rs_grouped['Cost Saving Amount'] = (
                (rekomendasi_other_rs_grouped['HargaSatuan'] - median_harga_satuan) * total_qty
            )
            rekomendasi_other_rs_grouped['Cost Saving (%)'] = (
                (rekomendasi_other_rs_grouped['HargaSatuan'] - median_harga_satuan) / median_harga_satuan * 100
            )
        
            # Sort by Nama Item Obat and TreatmentPlace
            rekomendasi_other_rs_grouped = rekomendasi_other_rs_grouped.sort_values(
                by=['TreatmentPlace', 'Nama Item Garda Medika'], 
                ascending=[True, True]
            )

            # Format Kolom Angka & Styler Cost Saving
            rekomendasi_other_rs_grouped = format_columns(rekomendasi_other_rs_grouped).style.applymap(colorize, subset=["Cost Saving per Satuan", "Cost Saving Amount", "Cost Saving (%)"])

            # Format angka di kolom "Cost Saving (%)"
            rekomendasi_other_rs_grouped = rekomendasi_other_rs_grouped.format({
                'Cost Saving (%)': "{:+.2f}%", # Format dua angka belakang koma
                'Cost Saving per Satuan': "{:+,.0f}", # Format pemisah ribuan
                'Cost Saving Amount': "{:+,.0f}", # Format pemisah ribuan
                'TotalAmountBill': "{:,.0f}", # Format pemisah ribuan
                'HargaSatuan': "{:,.0f}" # Format pemisah ribuan
            })
        
            st.subheader("Rekomendasi Obat Substitusi (RS Lain)")
            st.dataframe(rekomendasi_other_rs_grouped)
        else:
            st.write("Tidak ada rekomendasi substitusi di RS lain.")
    else:
        st.write("Tidak ada data yang sesuai dengan filter.")
