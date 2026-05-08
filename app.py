import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime


# --- Konfigurasi Halaman ---
st.set_page_config(page_title="MDMS - CV Amal Mulia", layout="wide", page_icon="🏭")

# --- Fungsi Database (Ditingkatkan) ---
def get_connection():
    """Membuat koneksi ke database SQLite."""
    return sqlite3.connect('makloon.db', check_same_thread=False)

def init_db():
    """Inisialisasi tabel dan data awal."""
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
        # Tabel User
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT,
                    role TEXT)''')
        
        # Data Default Produk
        c.execute("SELECT COUNT(*) FROM produk")
        if c.fetchone()[0] == 0:
            data_produk = [
                ('Saus Sambal', 500, 15000),
                ('Sirup Markisa', 300, 25000),
                ('Minyak Kelapa', 200, 45000)
            ]
            c.executemany("INSERT INTO produk (nama, stok, harga_jual) VALUES (?,?,?)", data_produk)
            
        # Data Default Users
        c.execute("SELECT COUNT(*) FROM users")
        if c.fetchone()[0] == 0:
            data_users = [
                ('pabrik', 'pabrik123', 'pabrik'),
                ('distributor', 'dist123', 'distributor'),
                ('klien', 'klien123', 'klien')
            ]
            c.executemany("INSERT INTO users VALUES (?,?,?)", data_users)
        conn.commit()

# --- Helper Data ---
def run_query(query, params=()):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()

def get_df(query, params=()):
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)

# --- Logika Autentikasi ---
def login_ui():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔐 Login MDMS - CV Amal Mulia")
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            with st.form("login_form"):
                user = st.text_input("Username")
                pw = st.text_input("Password", type="password")
                if st.form_submit_button("Masuk"):
                    res = get_df("SELECT role FROM users WHERE username=? AND password=?", (user, pw))
                    if not res.empty:
                        st.session_state.authenticated = True
                        st.session_state.username = user
                        st.session_state.role = res.iloc[0]['role']
                        st.rerun()
                    else:
                        st.error("Username atau password salah!")
        return False
    return True

# --- Jalankan Inisialisasi ---
init_db()

# --- APLIKASI UTAMA ---
if login_ui():
    # Sidebar
    st.sidebar.title(f"👤 {st.session_state.username}")
    st.sidebar.info(f"Role: **{st.session_state.role.upper()}**")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.rerun()

    # --- 1. DASHBOARD PABRIK ---
    if st.session_state.role == "pabrik":
        st.title("🏭 Control Center Pabrik")
        t1, t2, t3 = st.tabs(["📊 Inventory", "📦 Produksi & Makloon", "➕ Tambah Produk"])

        with t1:
            df_stok = get_df("SELECT * FROM produk")
            c1, c2 = st.columns([3, 2])
            with c1:
                st.subheader("Stok Produk Jadi")
                # Styling stok rendah
                def style_stok(row):
                    color = 'background-color: #ff4b4b; color: white' if row.stok < 100 else ''
                    return [color] * len(row)
                st.dataframe(df_stok.style.apply(style_stok, axis=1), use_container_width=True, hide_index=True)
            with c2:
     elif role = "klien":
    st.title("🤝 Portal Klien")
    # Perbaikan: Filter data berdasarkan username yang login
    # Jika di tabel pesanan nama kliennya adalah 'klien', maka data akan muncul
    df_k = get_df("SELECT produk, jumlah, status FROM pesanan_makloon WHERE klien=?", (st.session_state.username,))
    
    if df_k.empty:
        st.info(f"Halo {st.session_state.username}, saat ini belum ada pesanan atas nama Anda.")
    else:
        st.subheader("Status Pesanan Anda")
        st.dataframe(df_k, use_container_width=True, hide_index=True)
        with t2:
            st.subheader("Kelola Pesanan Makloon")
            with st.expander("📝 Input Pesanan Baru"):
                with st.form("new_order"):
                    k = st.text_input("Nama Klien")
                    p = st.selectbox("Pilih Produk", df_stok['nama'].tolist())
                    j = st.number_input("Jumlah Pesanan", min_value=1)
                    d = st.date_input("Deadline")
                    if st.form_submit_button("Submit"):
                        run_query("INSERT INTO pesanan_makloon (klien, produk, jumlah, status, tanggal_masuk, target_selesai) VALUES (?,?,?,?,?,?)",
                                 (k, p, j, "Antrean", datetime.now().strftime("%Y-%m-%d"), str(d)))
                        st.success("Pesanan dicatat!")
                        st.rerun()
            
            df_p = get_df("SELECT * FROM pesanan_makloon")
            st.table(df_p)

        with t3:
            st.subheader("Registrasi Produk Baru")
            with st.form("add_p"):
                np = st.text_input("Nama Produk Baru")
                sp = st.number_input("Stok Awal", min_value=0)
                hp = st.number_input("Harga Satuan", min_value=0)
                if st.form_submit_button("Simpan"):
                    try:
                        run_query("INSERT INTO produk (nama, stok, harga_jual) VALUES (?,?,?)", (np, sp, hp))
                        st.success("Produk berhasil didaftarkan!")
                    except:
                        st.error("Gagal! Nama produk mungkin sudah ada.")

    # --- 2. DASHBOARD DISTRIBUTOR ---
    elif st.session_state.role == "distributor":
        st.title("🏪 Portal Distributor")
        st.subheader("Ketersediaan Barang di Pabrik")
        df_p = get_df("SELECT nama, stok, harga_jual FROM produk")
        st.dataframe(df_p, use_container_width=True)
        
        st.info("💡 Hubungi Admin Pabrik untuk melakukan pemesanan restock.")

    # --- 3. DASHBOARD KLIEN ---
    elif st.session_state.role == "klien":
        st.title("🤝 Monitoring Produksi Makloon")
        # Simulasi filter berdasarkan klien yang login
        df_k = get_df("SELECT produk, jumlah, status, target_selesai FROM pesanan_makloon")
        if df_k.empty:
            st.warning("Anda belum memiliki riwayat pesanan.")
        else:
            st.subheader("Status Pesanan Anda")
            st.dataframe(df_k, use_container_width=True)
