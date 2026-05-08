import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="MDMS - CV Amal Mulia", layout="wide")

# --- Inisialisasi Database SQLite ---
def init_db():
    conn = sqlite3.connect('makloon.db')
    c = conn.cursor()
    # Tabel untuk stok produk jadi
    c.execute('''CREATE TABLE IF NOT EXISTS produk (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT UNIQUE,
                stok INTEGER,
                harga_jual INTEGER)''')
    # Tabel untuk pesanan makloon
    c.execute('''CREATE TABLE IF NOT EXISTS pesanan_makloon (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                klien TEXT,
                produk TEXT,
                jumlah INTEGER,
                status TEXT,
                tanggal_masuk TEXT,
                target_selesai TEXT)''')
    # Tabel untuk user login
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT,
                role TEXT)''')
    
    # Insert data awal jika belum ada
    c.execute("SELECT * FROM produk WHERE nama='Saus Sambal'")
    if not c.fetchone():
        c.execute("INSERT INTO produk (nama, stok, harga_jual) VALUES ('Saus Sambal', 500, 15000)")
        c.execute("INSERT INTO produk (nama, stok, harga_jual) VALUES ('Sirup Markisa', 300, 25000)")
        c.execute("INSERT INTO produk (nama, stok, harga_jual) VALUES ('Minyak Kelapa', 200, 45000)")
        
    c.execute("SELECT * FROM users WHERE username='pabrik'")
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES ('pabrik', 'pabrik123', 'pabrik')")
        c.execute("INSERT INTO users VALUES ('distributor', 'dist123', 'distributor')")
        c.execute("INSERT INTO users VALUES ('klien', 'klien123', 'klien')")
    conn.commit()
    conn.close()

init_db()

# --- Helper Functions untuk Database ---
def get_connection():
    return sqlite3.connect('makloon.db')

def get_data(query, params=()):
    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)
    return df

def run_query(query, params=()):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()

# --- Sistem Autentikasi ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.session_state.role = ""

    if not st.session_state.authenticated:
        st.title("🔐 Selamat Datang di MDMS")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            if submit:
                conn = get_connection()
                c = conn.cursor()
                c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
                result = c.fetchone()
                conn.close()
                if result:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.role = result[0]
                    st.rerun()
                else:
                    st.error("Username atau password salah.")
        return False
    return True

# --- Logout ---
def logout():
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.rerun()

# --- MAIN APP ---
if check_password():
    logout()
    st.sidebar.title(f"Halo, **{st.session_state.username}**")
    st.sidebar.markdown(f"**Role:** {st.session_state.role.capitalize()}")
    st.sidebar.markdown("---")
    
    # 1. TAMPILAN UNTUK PABRIK
    if st.session_state.role == "pabrik":
        st.title("🏭 Dashboard Pabrik CV Amal Mulia")
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview & Stok", "📦 Kelola Pesanan Makloon", "📈 Pantau Distributor", "➕ Tambah Produk"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📦 Stok Produk Jadi Saat Ini")
                df_produk = get_data("SELECT id, nama, stok, harga_jual FROM produk")
                
                # Highlight stok menipis (Updated to map)
                def highlight_stok(val):
                    if val < 50: return 'background-color: #ffcccc'
                    elif val < 150: return 'background-color: #ffffcc'
                    return ''
                
                st.dataframe(df_produk.style.map(highlight_stok, subset=['stok']), 
                             use_container_width=True, hide_index=True)
            
            with col2:
                st.subheader("📊 Grafik Stok")
                fig = px.bar(df_produk, x='nama', y='stok', color='stok', text='stok', 
                             color_continuous_scale='RdYlGn')
                st.plotly_chart(fig, use_container_width=True)

            st.subheader("📋 Daftar Pesanan Makloon Aktif")
            df_pesanan = get_data("SELECT klien, produk, jumlah, status, target_selesai FROM pesanan_makloon")
            st.dataframe(df_pesanan, use_container_width=True, hide_index=True)

        with tab2:
            st.subheader("➕ Buat Pesanan Makloon Baru")
            with st.form("form_makloon"):
                col1, col2 = st.columns(2)
                with col1:
                    klien_input = st.text_input("Nama Klien")
                    produk_input = st.text_input("Nama Produk")
                with col2:
                    jumlah_input = st.number_input("Jumlah (pcs)", min_value=1, step=1)
                    target_input = st.date_input("Target Selesai")
                
                if st.form_submit_button("Tambah Pesanan"):
                    if klien_input and produk_input:
                        run_query("INSERT INTO pesanan_makloon (klien, produk, jumlah, status, tanggal_masuk, target_selesai) VALUES (?,?,?,?,?,?)",
                                  (klien_input, produk_input, jumlah_input, "Proses", datetime.now().strftime("%Y-%m-%d"), target_input.strftime("%Y-%m-%d")))
                        st.success("Pesanan makloon berhasil ditambahkan!")
                        st.rerun()

            st.subheader("✏️ Update Status Pesanan")
            df_pesanan_update = get_data("SELECT id, klien, produk, status FROM pesanan_makloon")
            if not df_pesanan_update.empty:
                # Perbaikan lambda function untuk seleksi ID
                options = df_pesanan_update['id'].tolist()
                def get_label(id_val):
                    row = df_pesanan_update[df_pesanan_update['id'] == id_val].iloc[0]
                    return f"{id_val} - {row['klien']} ({row['produk']})"
                
                selected_id = st.selectbox("Pilih Pesanan", options, format_func=get_label)
                new_status = st.selectbox("Update Status", ["Proses", "Quality Control", "Siap Kirim"])
                
                if st.button("Update Status"):
                    run_query("UPDATE pesanan_makloon SET status=? WHERE id=?", (new_status, selected_id))
                    st.success("Status berhasil diupdate!")
                    st.rerun()

        with tab3:
            st.subheader("📡 Pantau Stok di Distributor")
            data_distributor = {
                "Distributor": ["UD Makmur Jaya", "Toko Sumber Rezeki", "Agen Sentosa"],
                "Saus Sambal": [120, 30, 80],
                "Sirup Markisa": [45, 10, 60],
                "Minyak Kelapa": [15, 5, 40]
            }
            df_dist = pd.DataFrame(data_distributor)
            st.dataframe(df_dist, use_container_width=True, hide_index=True)
            
            df_dist_melt = df_dist.melt(id_vars=["Distributor"], var_name="Produk", value_name="Stok")
            fig_dist = px.bar(df_dist_melt, x="Distributor", y="Stok", color="Produk", barmode="group")
            st.plotly_chart(fig_dist, use_container_width=True)

        with tab4:
            st.subheader("➕ Tambah Produk Baru")
            with st.form("tambah_produk"):
                nama_p = st.text_input("Nama Produk")
                stok_p = st.number_input("Stok Awal", min_value=0, step=10)
                harga_p = st.number_input("Harga (Rp)", min_value=1000, step=1000)
                if st.form_submit_button("Simpan Produk"):
                    if nama_p:
                        try:
                            run_query("INSERT INTO produk (nama, stok, harga_jual) VALUES (?,?,?)", (nama_p, stok_p, harga_p))
                            st.success(f"Produk '{nama_p}' ditambahkan!")
                            st.rerun()
                        except:
                            st.error("Gagal menambahkan produk (cek apakah nama sudah ada).")

    # 2. TAMPILAN DISTRIBUTOR
    elif st.session_state.role == "distributor":
        st.title("🏪 Dashboard Distributor")
        df_pabrik = get_data("SELECT nama, stok as stok_pabrik, harga_jual FROM produk")
        st.subheader("📊 Stok Real-time di Pabrik")
        st.table(df_pabrik)
        
        with st.expander("📝 Laporkan Stok Gudang Anda"):
            for _, row in df_pabrik.iterrows():
                st.number_input(f"Stok {row['nama']}", min_value=0, key=f"dist_{row['nama']}")
            if st.button("Kirim Laporan"):
                st.success("Laporan terkirim!")

    # 3. TAMPILAN KLIEN
    elif st.session_state.role == "klien":
        st.title("👥 Portal Klien Makloon")
        # Simulasi: Klien hanya melihat datanya sendiri
        df_orders = get_data("SELECT produk, jumlah, status, target_selesai FROM pesanan_makloon WHERE klien='klien' OR klien='Client A'")
        if df_orders.empty:
            st.info("Belum ada pesanan.")
        else:
            st.subheader("Status Pesanan Anda")
            st.dataframe(df_orders, use_container_width=True)
