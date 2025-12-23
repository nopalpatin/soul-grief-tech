import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os
import pytz
import traceback # <--- Alat bedah error

# --- KONFIGURASI ---
st.set_page_config(page_title="SOUL: Debug Mode", page_icon="VX")

# --- JUDUL ---
st.title("🛠️ SOUL | DEBUG MODE")
st.warning("Mode ini akan menampilkan error secara kasar. Jangan panik.")

# --- 1. CEK API KEY ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        st.success(f"✅ API Key terdeteksi (Depan: {api_key[:5]}...)")
    else:
        st.error("❌ API Key TIDAK DITEMUKAN di Secrets!")
        st.stop()
except Exception as e:
    st.error(f"❌ Error saat Configure API Key: {e}")
    st.code(traceback.format_exc())
    st.stop()

# --- 2. CEK MODEL YANG TERSEDIA (PENTING) ---
st.subheader("1. Pengecekan Model")
active_model = None
try:
    with st.spinner("Mengecek daftar model di akunmu..."):
        # Kita paksa list semua model
        available = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available.append(m.name)
        
        st.write(f"Model yang diizinkan Google untuk akunmu: `{available}`")
        
        # Prioritas model (Kita coba Flash dulu karena paling hemat)
        targets = ["models/gemini-1.5-flash", "models/gemini-pro", "models/gemini-1.0-pro"]
        
        for t in targets:
            if t in available:
                active_model = t
                break
        
        # Jika tidak ada di prioritas, ambil sembarang
        if not active_model and available:
            active_model = available[0]
            
        if active_model:
            st.success(f"✅ Target Model: {active_model}")
        else:
            st.error("❌ TIDAK ADA MODEL YANG BISA DIPAKAI (Daftar Kosong). API Key kamu mungkin tidak valid atau belum mengaktifkan layanan Generative AI.")
            st.stop()

except Exception as e:
    st.error("❌ Gagal mengambil daftar model (Kemungkinan Error 400/403)")
    st.code(traceback.format_exc())
    st.stop()

# --- 3. TEST GENERATE SEDERHANA ---
st.subheader("2. Test Otak AI")
if st.button("Uji Coba Chat (Ping)"):
    try:
        model = genai.GenerativeModel(active_model)
        response = model.generate_content("Jawab 'Hadir' jika kamu hidup.")
        st.info(f"🤖 Balasan AI: {response.text}")
        st.success("✅ AI BERFUNGSI!")
    except Exception as e:
        st.error("❌ AI GAGAL MENJAWAB")
        # INI YANG SAYA BUTUHKAN:
        st.code(traceback.format_exc()) 

# --- 4. CEK DATABASE ---
st.subheader("3. Test Database")
if st.button("Uji Coba Simpan ke Sheet"):
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            st.write("✅ Menggunakan Kunci dari Secrets (Cloud)")
        elif os.path.exists('credentials.json'):
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
            st.write("✅ Menggunakan File credentials.json (Local)")
        else:
            st.error("❌ Kunci Database Hilang!")
            st.stop()

        client = gspread.authorize(creds)
        sheet = client.open("SOUL_User_Database").sheet1
        
        zona = pytz.timezone("Asia/Jakarta")
        waktu = datetime.now(zona).strftime("%Y-%m-%d %H:%M:%S")
        
        sheet.append_row([waktu, "DEBUG", "TEST", "CHECK", "SYSTEM OK"])
        st.success("✅ BERHASIL MENULIS KE SHEET! Cek Google Sheet kamu.")
        
    except Exception as e:
        st.error("❌ DATABASE ERROR")
        st.code(traceback.format_exc())