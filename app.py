import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os
import pytz # Library zona waktu

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="SOUL: Remembrance Engine", page_icon="🕊️")
st.markdown("<style>footer {visibility: hidden;}</style>", unsafe_allow_html=True)

# --- SETUP API KEY ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Key mati/kosong!")
    st.stop()

# --- AUTO-DETECT MODEL (Supaya tidak Error 404) ---
# Kode ini otomatis mencari model yang tersedia di akunmu
active_model_name = "models/gemini-pro" # Default
try:
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)
    
    # Cari yang terbaik dari daftar yang ada
    priority = ["models/gemini-1.5-flash", "models/gemini-1.0-pro", "models/gemini-pro"]
    for p in priority:
        if p in available_models:
            active_model_name = p
            break
except:
    pass # Kalau gagal deteksi, pakai default gemini-pro

# --- FUNGSI DATABASE (HYBRID + WIB) ---
def save_to_sheet(nama_user, nama_almarhum, hubungan, pesan_terakhir):
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        # 1. CEK APAKAH DI CLOUD (SECRETS)
        if "gcp_service_account" in st.secrets:
            # Ubah format TOML Streamlit jadi Dictionary Python
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            
        # 2. CEK APAKAH DI LAPTOP (FILE JSON)
        elif os.path.exists('credentials.json'):
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
            
        else:
            st.error("❌ Kunci Database Tidak Ditemukan!")
            return False

        # 3. KONEKSI & BUKA SHEET
        client_sheets = gspread.authorize(creds)
        sheet = client_sheets.open("SOUL_User_Database").sheet1
        
        # 4. AMBIL WAKTU WIB (JAKARTA)
        zona_waktu = pytz.timezone("Asia/Jakarta")
        waktu_sekarang = datetime.now(zona_waktu)
        waktu_teks = waktu_sekarang.strftime("%Y-%m-%d %H:%M:%S")
        
        # 5. TULIS KE SHEET
        sheet.append_row([waktu_teks, nama_user, nama_almarhum, hubungan, pesan_terakhir])
        return True
        
    except Exception as e:
        st.error(f"Gagal Simpan: {e}")
        return False

# --- UI VISUAL ---
st.title("🕊️ SOUL | Remembrance Engine")
st.caption(f"Connected to: `{active_model_name}`")

# --- SIDEBAR KONFIGURASI ---
with st.sidebar:
    st.header("⚙️ Konfigurasi")
    soul_name = st.text_input("Nama", "Ayah")
    relationship = st.selectbox("Hubungan", ["Ayah", "Ibu", "Pasangan", "Anak"])
    sample_chat = st.text_area("Gaya Bicara", "Nak, makan ya. Ayah sayang kamu.", height=100)
    
    if st.button("💾 Simpan Chat"):
        if "messages" in st.session_state and st.session_state.messages:
            with st.spinner("Menyimpan ke Database..."):
                if save_to_sheet("User Demo", soul_name, relationship, st.session_state.messages[-1]['content']):
                    st.toast("Tersimpan! (Cek Google Sheet)", icon="✅")
    
    if st.button("Reset"):
        st.session_state.messages = []
        st.rerun()

# --- LOGIKA AI ---
system_prompt = f"Peran: {soul_name}. Hubungan: {relationship}. Gaya: {sample_chat}. Jangan jadi hantu."
model = genai.GenerativeModel(active_model_name)

# --- CHAT ENGINE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ketik pesan..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            full_text = f"SYSTEM: {system_prompt}\n\n"
            for m in st.session_state.messages:
                full_text += f"{m['role']}: {m['content']}\n"
            full_text += "assistant: "
            
            response = model.generate_content(full_text)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error("Koneksi Error.")
            st.info("Kemungkinan kuota habis atau sinyal buruk.")