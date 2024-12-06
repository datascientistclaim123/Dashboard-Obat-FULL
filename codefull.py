# Masukin filter di Page 2
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
file_path_1 = "Data Obat Input Billing Manual - Updated 05122024.xlsx"  # Ganti dengan path file yang sesuai
file_path_2 = "Data Obat Input Billing Manual Revisi.xlsx"  # Ganti dengan path file yang sesuai

# Sidebar untuk navigasi
st.sidebar.title("Navigasi")
selected_page = st.sidebar.radio("Pilih Halaman:", ["Distribusi Penggunaan Obat per Provider", "Distribusi Provider Berdasarkan Obat"])

if selected_page == "Distribusi Penggunaan Obat per Provider":
    # Distribusi Penggunaan Obat per Provider
    st.title("Distribusi Penggunaan Obat per Provider 💊")

    df = load_data(file_path_1)

    # Pastikan kolom Qty dan Amount Bill adalah numerik
    df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0)
    df['Amount Bill'] = pd.to_numeric(df['Amount Bill'], errors='coerce').fillna(0)
    df['Harga Satuan'] = df['Harga Satuan'].round()

    # Menampilkan preview data
    st.subheader("Preview Data")
    preview_df = df.copy()

    # Format kolom 'Amount Bill' dan 'Harga Satuan' untuk Preview Data
    preview_df['Amount Bill'] = preview_df['Amount Bill'].apply(lambda x: f"{x:,.0f}".replace(",", "."))
    preview_df['Qty'] = preview_df['Qty'].astype(int).apply(lambda x: f"{x:,}".replace(",", "."))
    preview_df['Harga Satuan'] = preview_df['Harga Satuan'].apply(lambda x: f"{x:,.0f}".replace(",", "."))

    st.dataframe(preview_df)

    # State untuk menyimpan jumlah tabel yang ditampilkan
    if "table_count" not in st.session_state:
        st.session_state.table_count = 1  # Mulai dengan 1 tabel

    def display_table(index):
        st.subheader(f"Tabel {index}")
        filtered_df = df.copy()

        # Filter berdasarkan "Provider", "TreatmentPlace", "Doctor Name", "Primary Diagnosis", "Product Type"
        provider_options = filtered_df['GroupProvider'].dropna().unique()
        selected_provider = st.multiselect(f"[Tabel {index}] Pilih Provider:", provider_options, key=f"provider_{index}")
        if selected_provider:
            filtered_df = filtered_df[filtered_df['GroupProvider'].isin(selected_provider)]

        # Filter berdasarkan "TreatmentPlace"
        treatment_place_options = filtered_df['TreatmentPlace'].dropna().unique()
        selected_treatment_place = st.multiselect(f"[Tabel {index}] Pilih Treatment Place:", treatment_place_options, key=f"treatment_place_{index}")
        if selected_treatment_place:
            filtered_df = filtered_df[filtered_df['TreatmentPlace'].isin(selected_treatment_place)]

        # Filter berdasarkan "Doctor Name"
        doctor_options = filtered_df['DoctorName'].dropna().unique()
        selected_doctor = st.multiselect(f"[Tabel {index}] Pilih Doctor Name:", doctor_options, key=f"doctor_{index}")
        if selected_doctor:
            filtered_df = filtered_df[filtered_df['DoctorName'].isin(selected_doctor)]

        # Filter berdasarkan "Primary Diagnosis"
        diagnosis_options = filtered_df['PrimaryDiagnosis'].dropna().unique()
        selected_diagnosis = st.multiselect(f"[Tabel {index}] Pilih Primary Diagnosis:", diagnosis_options, key=f"diagnosis_{index}")
        if selected_diagnosis:
            filtered_df = filtered_df[filtered_df['PrimaryDiagnosis'].isin(selected_diagnosis)]

        # Filter berdasarkan "Product Type"
        product_options = filtered_df['ProductType'].dropna().unique()
        selected_product = st.multiselect(f"[Tabel {index}] Pilih Product Type:", product_options, key=f"product_{index}")
        if selected_product:
            filtered_df = filtered_df[filtered_df['ProductType'].isin(selected_product)]

        # Filter rentang tanggal
        st.write("Pilih rentang tanggal:")
        min_date = pd.to_datetime(df["TreatmentFinish"].min())
        max_date = pd.to_datetime(df["TreatmentFinish"].max())
        date_range = st.date_input(f"[Tabel {index}] Rentang Tanggal:", value=(min_date, max_date), min_value=min_date, max_value=max_date, key=f"date_range_{index}")
        if len(date_range) == 2:
            start_date, end_date = pd.to_datetime(date_range)
            filtered_df = filtered_df[(pd.to_datetime(filtered_df['TreatmentFinish']) >= start_date) & (pd.to_datetime(filtered_df['TreatmentFinish']) <= end_date)]

        if filtered_df.empty:
            st.warning(f"Tidak ada data untuk filter di tabel {index}.")
        else:
            grouped_df = filtered_df.groupby("Nama Item Garda Medika").agg(
                Qty=('Qty', 'sum'),
                AmountBill=('Amount Bill', 'sum'),
                HargaSatuan=('Harga Satuan', 'median')
            ).reset_index()
            grouped_df['Qty'] = grouped_df['Qty'].astype(int)
            grouped_df['AmountBill'] = grouped_df['AmountBill'].astype(int)

            # Format kolom 'Amount Bill' dan 'Harga Satuan' untuk Tabel
            grouped_df['AmountBill'] = grouped_df['AmountBill'].apply(lambda x: f"{x:,.0f}".replace(",", "."))
            grouped_df['HargaSatuan'] = grouped_df['HargaSatuan'].apply(lambda x: f"{x:,.0f}".replace(",", "."))

            st.dataframe(grouped_df, height=300)

            # WordCloud
            st.subheader("WordCloud")

            # Gabungkan semua teks dari kolom 'Nama Item Garda Medika'
            wordcloud_text = " ".join(grouped_df['Nama Item Garda Medika'].dropna().astype(str))

            # Daftar kata yang ingin dihapus
            excluded_words = ["FORTE", "PLUS", "PLU", "INFLUAN", "INFUSAN", "INFUS", "OTSU", ...]  # Tambahkan daftar lengkap kata di sini

            excluded_pattern = r'\b(?:' + '|'.join(map(re.escape, excluded_words)) + r')\b'
            wordcloud_text = re.sub(excluded_pattern, '', wordcloud_text, flags=re.IGNORECASE)

            wordcloud = WordCloud(width=800, height=400, background_color="white").generate(wordcloud_text)
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wordcloud, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)

    for i in range(1, st.session_state.table_count + 1):
        display_table(i)

    if st.button("Insert Tabel Baru"):
        st.session_state.table_count += 1

elif selected_page == "Distribusi Provider Berdasarkan Obat":
    # Distribusi Provider Berdasarkan Obat
    st.title("Distribusi Provider Berdasarkan Obat")
    st.title("Distribusi Provider Berdasarkan Obat ")

    df = load_data(file_path_2)
    # Menampilkan preview data
    st.subheader("Preview Data")
    preview_df = df.copy()
    # Format angka di Preview Data (bulatkan angka dan koma → titik)
    preview_df['Amount Bill'] = preview_df['Amount Bill'].fillna(0).round().apply(lambda x: f"{x:,}".replace(",", "."))
    preview_df['Qty'] = preview_df['Qty'].fillna(0).astype(int).apply(lambda x: f"{x:,}".replace(",", "."))
    preview_df['Harga Satuan'] = preview_df['Harga Satuan'].fillna(0).apply(lambda x: round(x, 0)).astype(float).apply(lambda x: f"{x:,.0f}".replace(",", "."))
    st.dataframe(df)

    st.dataframe(preview_df)
    # Filter dropdown untuk Nama Item, Golongan, Subgolongan, dan Komposisi Zat Aktif
    # Filter dropdown (logika sama seperti navigasi pertama)
    st.subheader("Filter Data")
    # Filter Nama Item Garda Medika
    item_options = df['Nama Item Garda Medika'].dropna().unique()
    selected_items = st.multiselect("Pilih Nama Item Garda Medika:", item_options, key="item_filter")
    # Filter Golongan
    golongan_options = df['Golongan'].dropna().unique()
    selected_golongan = st.multiselect("Pilih Golongan:", golongan_options, key="golongan_filter")
    # Filter Subgolongan
    subgolongan_options = df['Subgolongan'].dropna().unique()
    selected_subgolongan = st.multiselect("Pilih Subgolongan:", subgolongan_options, key="subgolongan_filter")
    # Filter Komposisi Zat Aktif
    composition_options = df['Komposisi'].dropna().unique()
    selected_compositions = st.multiselect("Pilih Komposisi Zat Aktif:", composition_options, key="composition_filter")
    # Terapkan filter
    filtered_df = df.copy()
    if selected_items:
        filtered_df = filtered_df[filtered_df['Nama Item Garda Medika'].isin(selected_items)]
    if selected_golongan:
        filtered_df = filtered_df[filtered_df['Golongan'].isin(selected_golongan)]
    if selected_subgolongan:
        filtered_df = filtered_df[filtered_df['Subgolongan'].isin(selected_subgolongan)]
    if selected_compositions:
        filtered_df = filtered_df[filtered_df['Komposisi'].isin(selected_compositions)]

    # Dropdown untuk filter
    selected_items = st.multiselect("Pilih Nama Item Garda Medika:", item_options, default=item_options)
    selected_golongan = st.multiselect("Pilih Golongan:", golongan_options, default=golongan_options)
    selected_subgolongan = st.multiselect("Pilih Subgolongan:", subgolongan_options, default=subgolongan_options)
    selected_compositions = st.multiselect("Pilih Komposisi Zat Aktif:", composition_options, default=composition_options)
    # Terapkan filter berdasarkan pilihan
    filtered_df = df[
        (df['Nama Item Garda Medika'].isin(selected_items)) &
        (df['Golongan'].isin(selected_golongan)) &
        (df['Subgolongan'].isin(selected_subgolongan)) &
        (df['Komposisi'].isin(selected_compositions))
    ]
    # Menampilkan data hasil filter
    if filtered_df.empty:
        st.warning("Tidak ada data yang sesuai dengan filter yang dipilih.")
    else:
        # Menampilkan data hasil filter
        st.subheader("Data Hasil Filter")
        grouped_df = filtered_df.groupby(["Provider", "Nama Item Garda Medika"]).agg(
            Qty=('Qty', 'sum'),
            AmountBill=('Amount Bill', 'sum'),
            HargaSatuan=('Harga Satuan', 'median')
        ).reset_index()
        grouped_df['Qty'] = grouped_df['Qty'].astype(int)
        grouped_df['AmountBill'] = grouped_df['AmountBill'].apply(lambda x: f"{x:,.0f}".replace(",", "."))
        grouped_df['HargaSatuan'] = grouped_df['HargaSatuan'].apply(lambda x: f"{x:,.0f}".replace(",", "."))
        st.dataframe(grouped_df, height=300)
        
        # Kolom yang ditampilkan
        display_columns = [
            "Group Provider", "TreatmentPlace", "Nama Item Garda Medika",
            "Golongan", "Subgolongan", "Komposisi", "Qty", "Amount Bill", "Harga Satuan"
        ]
        # Format angka di tabel hasil filter
        filtered_df['Qty'] = filtered_df['Qty'].astype(int)
        filtered_df['Amount Bill'] = filtered_df['Amount Bill'].apply(lambda x: f"{x:,.0f}".replace(",", "."))
        filtered_df['Harga Satuan'] = filtered_df['Harga Satuan'].apply(lambda x: f"{x:,.0f}".replace(",", "."))
        # Tampilkan data yang difilter
        st.dataframe(filtered_df[display_columns], height=300)
