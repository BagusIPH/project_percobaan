import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime


# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="MDMS - CV Amal Mulia", layout="wide", page_icon="🏭")

# --- 2. FUNGSI DATABASE ---
def get_connection():
    """Membuat koneksi ke database SQLite."""
    return sqlite3.connect('makloon.db', check_same_thread=False)

def init_db():
    """Membuat tabel dan user default jika belum ada."""
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
                    tanggal_masuk TEXT)''')
        # Tabel Users
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT,
                    role TEXT)''')
        
        # Cek dan Isi Data Default
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

# Jalankan Inisialisasi
init_db()

# --- 3. SISTEM LOGIN ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Login MDMS - CV Amal Mulia")
    col_l1, col_l2, col_l3 = st.columns([1,2,1])
    with col_l2:
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

# --- 4. SIDEBAR ---
st.sidebar.title(f"👤 {st.session_state.username}")
st.sidebar.info(f"Role: {st.session_state.role.upper()}")
if st.sidebar.button("🚪 Keluar"):
    st.session_state.authenticated = False
    st.rerun()

# --- 5. DASHBOARD BERDASARKAN ROLE ---
role = st.session_state.role

if role == "pabrik":
    st.title("🏭 Dashboard Admin Pabrik")
    t1, t2, t3 = st.tabs(["📊 Stok Barang", "📦 Pesanan Makloon", "➕ Tambah Produk"])
    
    # TAB 1: STOK BARANG
    with t1:
        st.subheader("Inventory Real-time")
        df_stok = get_df("SELECT id, nama, stok, harga_jual FROM produk")
        if not df_stok.empty:
            st.dataframe(df_stok, use_container_width=True, hide_index=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Belum ada data produk.")

    # TAB 2: PESANAN MAKLOON
    with t2:
        st.subheader("Input Pesanan Makloon Baru")
        with st.form("add_order", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                k_name = st.text_input("Nama Klien").strip()
                p_name = st.text_input("Nama Produk").strip()
            with col_b:
                qty = st.number_input("Jumlah", min_value=1, step=1)
                tgl_now = datetime.now().strftime("%d/%m/%Y %H:%M")
            
            if st.form_submit_button("Simpan Pesanan"):
                if k_name and p_name:
                    try:
                        run_query("INSERT INTO pesanan_makloon (klien, produk, jumlah, status, tanggal_masuk) VALUES (?,?,?,?,?)",
                                  (k_name, p_name, qty, "Proses Produksi", tgl_now))
                        st.success(f"Berhasil mencatat pesanan {k_name}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal simpan: {e}")
                else:
                    st.warning("Lengkapi data klien dan produk!")
        
        st.divider()
        st.subheader("Daftar Pesanan")
        df_orders = get_df("SELECT * FROM pesanan_makloon")
        st.dataframe(df_orders, use_container_width=True, hide_index=True)

    # TAB 3: TAMBAH PRODUK
    with t3:
        st.subheader("Registrasi Produk Baru")
        with st.form("new_product", clear_on_submit=True):
            np = st.text_input("Nama Produk Baru").strip()
            sp = st.number_input("Stok Awal", min_value=0, step=1)
            hp = st.number_input("Harga Jual", min_value=0, step=1000)
            
            if st.form_submit_button("Tambah ke Database"):
                if np:
                    try:
                        run_query("INSERT INTO produk (nama, stok, harga_jual) VALUES (?,?,?)", (np, sp, hp))
                        st.success(f"Produk '{np}' berhasil didaftarkan!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Gagal! Nama produk sudah ada.")
                    except Exception as e:
                        st.error(f"Kesalahan: {e}")
                else:
                    st.warning("Nama produk tidak boleh kosong!")

elif role == "distributor":
    st.title("🏪 Portal Distributor")
    st.subheader("Cek Ketersediaan Stok di Pabrik")
    df_dist = get_df("SELECT nama, stok, harga_jual FROM produk")
    if not df_dist.empty:
        st.dataframe(df_dist, use_container_width=True, hide_index=True)
    else:
        st.info("Data produk belum tersedia.")

elif role == "klien":
    st.title("🤝 Monitoring Produksi Klien")
    user_klien = st.session_state.username
    df_k = get_df("SELECT produk, jumlah, status, tanggal_masuk FROM pesanan_makloon WHERE klien=?", (user_klien,))
    
    if df_k.empty:
        st.info(f"Halo {user_klien}, saat ini tidak ada pesanan aktif atas nama Anda.")
    else:
        st.subheader(f"Status Pesanan: {user_klien}")
        st.dataframe(df_k, use_container_width=True, hide_index=True)
