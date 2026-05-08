import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime


# --- Konfigurasi Halaman ---
st.set_page_config(page_title="MDMS - CV Amal Mulia", layout="wide", page_icon="🏭")

# --- Fungsi Database ---
def get_connection():
    """Membuat koneksi ke SQLite dengan dukungan multi-threading."""
    return sqlite3.connect('makloon.db', check_same_thread=False)

def init_db():
    """Inisialisasi tabel dan data awal pengguna."""
    with get_connection() as conn:
        c = conn.cursor()
        # Tabel Produk
        c.execute('''CREATE TABLE IF NOT EXISTS produk (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nama TEXT UNIQUE,
                    stok INTEGER,
                    harga_jual INTEGER)''')
        # Tabel Pesanan
        c.execute('''CREATE TABLE IF NOT EXISTS pesanan_makloon (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    klien TEXT,
                    produk TEXT,
                    jumlah INTEGER,
                    status TEXT,
                    tanggal_masuk TEXT,
                    target_selesai TEXT)''')
        # Tabel Users
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT,
                    role TEXT)''')
        
        # Data Default jika kosong
        c.execute("SELECT COUNT(*) FROM users")
        if c.fetchone()[0] == 0:
            users_data = [
                ('pabrik', 'pabrik123', 'pabrik'),
                ('distributor', 'dist123', 'distributor'),
                ('klien', 'klien123', 'klien')
            ]
            c.executemany("INSERT INTO users VALUES (?,?,?)", users_data)
            
            c.executemany("INSERT INTO produk (nama, stok, harga_jual) VALUES (?,?,?)", 
                         [('Saus Sambal', 500, 15000), ('Sirup Markisa', 300, 25000)])
        conn.commit()

def run_query(query, params=()):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()

def get_df(query, params=()):
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)

# --- Jalankan Inisialisasi Database ---
init_db()

# --- Sistem Login ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Login MDMS - CV Amal Mulia")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("login_form"):
            u = st.text_input("Username").strip()
            p = st.text_input("Password", type="password").strip()
            if st.form_submit_button("Masuk"):
                res = get_df("SELECT role FROM users WHERE username=? AND password=?", (u, p))
                if not res.empty:
                    st.session_state.authenticated = True
                    st.session_state.username = u
                    st.session_state.role = res.iloc[0]['role']
                    st.rerun()
                else:
                    st.error("Username atau password salah!")
    st.stop()

# --- Sidebar ---
st.sidebar.title(f"👤 {st.session_state.username}")
st.sidebar.info(f"Role: {st.session_state.role.upper()}")
if st.sidebar.button("🚪 Keluar"):
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.rerun()

# --- Navigasi Berdasarkan Role ---
role = st.session_state.role

if role == "pabrik":
    st.title("🏭 Dashboard Admin Pabrik")
    t1, t2, t3 = st.tabs(["📊 Stok Barang", "📦 Pesanan Makloon", "➕ Tambah Produk"])
    
   with t1:
        st.subheader("📊 Inventory Real-time")
        df_stok = get_df("SELECT id, nama, stok, harga_jual FROM produk")
        
        if not df_stok.empty:
            # Menampilkan tabel dengan gaya yang bersih
            st.dataframe(
                df_stok, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "harga_jual": st.column_config.NumberColumn("Harga (Rp)", format="Rp %d")
                }
            )
            
            # Grafik Stok
            fig = px.bar(
                df_stok, 
                x="nama", 
                y="stok", 
                title="Grafik Ketersediaan Stok",
                color="stok",
                color_continuous_scale="Viridis"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("💡 Belum ada data produk di gudang. Silakan tambah produk di Tab 'Tambah Produk'.")

    with t2:
        st.subheader("Input Pesanan Makloon")
        with st.form("add_order"):
            k_name = st.text_input("Nama Klien")
            p_name = st.text_input("Nama Produk")
            qty = st.number_input("Jumlah", min_value=1, step=1)
            if st.form_submit_button("Simpan Pesanan"):
                if k_name and p_name:
                    run_query("INSERT INTO pesanan_makloon (klien, produk, jumlah, status, tanggal_masuk) VALUES (?,?,?,?,?)",
                              (k_name, p_name, qty, "Dalam Proses", datetime.now().strftime("%d/%m/%Y")))
                    st.success(f"Pesanan untuk {k_name} berhasil dicatat!")
                    st.rerun()
                else:
                    st.error("Mohon isi nama klien dan produk.")
        
        st.subheader("Daftar Pesanan Aktif")
        df_orders = get_df("SELECT * FROM pesanan_makloon")
        st.dataframe(df_orders, use_container_width=True, hide_index=True)

    with t3:
        st.subheader("Registrasi Produk Baru")
        with st.form("new_product"):
            np = st.text_input("Nama Produk")
            sp = st.number_input("Stok Awal", min_value=0, step=1)
            hp = st.number_input("Harga Jual", min_value=0, step=1000)
            if st.form_submit_button("Tambah Ke Sistem"):
                if np:
                    try:
                        run_query("INSERT INTO produk (nama, stok, harga_jual) VALUES (?,?,?)", (np, sp, hp))
                        st.success(f"Produk {np} berhasil ditambahkan!")
                        st.rerun()
                    except:
                        st.error("Gagal! Nama produk sudah ada dalam sistem.")
                else:
                    st.error("Nama produk tidak boleh kosong.")

elif role == "distributor":
    st.title("🏪 Portal Distributor")
    st.subheader("Cek Stok Pabrik")
    df_dist = get_df("SELECT nama, stok, harga_jual FROM produk")
    if not df_dist.empty:
        st.dataframe(df_dist, use_container_width=True, hide_index=True)
    else:
        st.info("Tidak ada data produk tersedia.")
    st.info("💡 Hubungi pihak pabrik untuk melakukan pengadaan barang.")

elif role == "klien":
    st.title("🤝 Monitoring Klien Makloon")
    user_klien = st.session_state.username
    # Filter data berdasarkan nama klien
    df_k = get_df("SELECT produk, jumlah, status, tanggal_masuk FROM pesanan_makloon WHERE klien=?", (user_klien,))
    
    if df_k.empty:
        st.info(f"Halo {user_klien}, Anda belum memiliki pesanan aktif.")
    else:
        st.subheader(f"Status Produksi Pesanan: {user_klien}")
        st.dataframe(df_k, use_container_width=True, hide_index=True)
