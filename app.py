import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os
import pytz

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="SOUL: Remembrance Engine", page_icon="🕊️")
st.markdown("<style>footer {visibility: hidden;}</style>", unsafe_allow_html=True)

# --- 1. SETUP API KEY ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("API Key mati/kosong!")
        st.stop()
except Exception as e:
    st.error(f"Error Konfigurasi AI: {e}")
    st.stop()

# --- 2. SETTING MODEL (KITA PAKSA YANG PASTI ADA) ---
# Jangan pakai 1.5-flash, akunmu belum support. Kita pakai classic pro.
active_model_name = "models/gemini-pro" 

# --- 3. FUNGSI DATABASE ---
def save_to_sheet(nama_user, nama_almarhum, hubungan, pesan_terakhir):
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        elif os.path.exists('credentials.json'):
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        else:
            return False

        client_sheets = gspread.authorize(creds)
        sheet = client_sheets.open("SOUL_User_Database").sheet1
        zona_waktu = pytz.timezone("Asia/Jakarta")
        waktu_sekarang = datetime.now(zona_waktu).strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([waktu_sekarang, nama_user, nama_almarhum, hubungan, pesan_terakhir])
        return True
    except Exception as e:
        st.error(f"Gagal Simpan Database: {e}")
        return False

# --- 4. UI VISUAL ---
st.title("🕊️ SOUL | Remembrance Engine")
st.caption(f"System Status: Online | Model: `{active_model_name}`")

with st.sidebar:
    st.header("⚙️ Identitas")
    soul_name = st.text_input("Nama Almarhum/ah", "Ayah")
    relationship = st.selectbox("Hubungan", ["Ayah", "Ibu", "Pasangan", "Sahabat", "Anak"])
    st.header("🎭 Kepribadian")
    sample_chat = st.text_area("Contoh Gaya Bicara", "Nak, jangan lupa makan ya. Ayah bangga sama kamu.", height=150)
    
    if st.button("💾 Simpan Percakapan", type="primary"):
        if "messages" in st.session_state and len(st.session_state.messages) > 0:
            last_msg = st.session_state.messages[-1]
            msg_content = f"[{last_msg['role']}] {last_msg['content']}"
            with st.spinner("Menyimpan..."):
                if save_to_sheet("Demo User", soul_name, relationship, msg_content):
                    st.toast("✅ Tersimpan!", icon="🕊️")
    
    if st.button("Hapus Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 5. LOGIKA AI ---
system_prompt = f"""
Kamu adalah simulasi digital dari {soul_name}, seorang {relationship}. 
Tiru gaya bicara: "{sample_chat}". 
Jawab singkat, hangat, dan empati.
"""

# Inisialisasi Model (Pindah ke sini biar aman)
try:
    model = genai.GenerativeModel(active_model_name)
except Exception as e:
    st.error(f"Gagal memuat model {active_model_name}. Error: {e}")
    st.stop()

# --- 6. CHAT ENGINE ---
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
        message_placeholder = st.empty()
        try:
            full_text = f"SYSTEM: {system_prompt}\n\n"
            for m in st.session_state.messages[-5:]: 
                full_text += f"{m['role']}: {m['content']}\n"
            full_text += "assistant: "
            
            response = model.generate_content(full_text)
            message_placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            # Tampilkan Error Asli jika masih gagal
            message_placeholder.error(f"⚠️ ERROR: {e}")