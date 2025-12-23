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

# --- 2. AUTO-DETECT MODEL (LOGIKA DEBUG) ---
# Kita pakai cara yang terbukti berhasil tadi
active_model_name = "models/gemini-1.5-flash" # Default fallback
try:
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)
    
    # Cari prioritas (Flash biasanya paling aman & cepat buat demo)
    priorities = ["models/gemini-1.5-flash", "models/gemini-pro", "models/gemini-1.0-pro"]
    for p in priorities:
        if p in available_models:
            active_model_name = p
            break
except:
    pass # Silent fail, pakai default

# --- 3. FUNGSI DATABASE (HYBRID + WIB) ---
def save_to_sheet(nama_user, nama_almarhum, hubungan, pesan_terakhir):
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        # Cek Cloud (Secrets) dulu
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        # Cek Laptop (File) kemudian
        elif os.path.exists('credentials.json'):
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        else:
            return False

        client_sheets = gspread.authorize(creds)
        sheet = client_sheets.open("SOUL_User_Database").sheet1
        
        # Waktu WIB
        zona_waktu = pytz.timezone("Asia/Jakarta")
        waktu_sekarang = datetime.now(zona_waktu).strftime("%Y-%m-%d %H:%M:%S")
        
        sheet.append_row([waktu_sekarang, nama_user, nama_almarhum, hubungan, pesan_terakhir])
        return True
    except Exception as e:
        st.error(f"Gagal Simpan: {e}")
        return False

# --- 4. UI VISUAL (CANTIK) ---
st.title("🕊️ SOUL | Remembrance Engine")
st.caption(f"System Status: Online | Model: `{active_model_name}`")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Identitas")
    soul_name = st.text_input("Nama Almarhum/ah", "Ayah")
    relationship = st.selectbox("Hubungan", ["Ayah", "Ibu", "Pasangan", "Sahabat", "Anak"])
    
    st.header("🎭 Kepribadian")
    sample_chat = st.text_area("Contoh Gaya Bicara (Penting!)", 
                               "Nak, jangan lupa makan ya. Ayah bangga sama kamu. Sholat jangan ditinggal.", 
                               height=150,
                               help="AI akan meniru gaya bicara ini. Masukkan kalimat khas beliau.")
    
    st.divider()
    
    if st.button("💾 Simpan Percakapan", type="primary"):
        if "messages" in st.session_state and len(st.session_state.messages) > 0:
            last_msg = st.session_state.messages[-1]
            # Kita simpan pesan terakhir (entah itu user atau AI)
            msg_content = f"[{last_msg['role']}] {last_msg['content']}"
            
            with st.spinner("Menyimpan ke memori abadi..."):
                if save_to_sheet("Demo User", soul_name, relationship, msg_content):
                    st.toast("✅ Tersimpan di Database!", icon="🕊️")
                else:
                    st.toast("❌ Gagal menyimpan.", icon="⚠️")
        else:
            st.warning("Belum ada percakapan untuk disimpan.")
    
    if st.button("Hapus Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 5. LOGIKA AI ---
system_prompt = f"""
Kamu adalah simulasi digital dari {soul_name}, seorang {relationship} bagi pengguna ini. 
Tugasmu adalah memberikan kenyamanan dan mendengarkan keluh kesah pengguna.
Gunakan gaya bahasa yang sangat mirip dengan contoh ini: "{sample_chat}".
Jawablah dengan singkat, hangat, dan penuh empati. Jangan pernah mengaku sebagai AI.
"""

model = genai.GenerativeModel(active_model_name)

# --- 6. CHAT ENGINE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Tampilkan chat lama
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input user
if prompt := st.chat_input(f"Sampaikan rindu pada {soul_name}..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Balasan AI
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            # Bangun konteks
            full_text = f"SYSTEM: {system_prompt}\n\n"
            # Sertakan 5 chat terakhir saja biar hemat token & fokus
            recent_msgs = st.session_state.messages[-5:] 
            for m in recent_msgs:
                full_text += f"{m['role']}: {m['content']}\n"
            full_text += "assistant: "
            
            # Generate
            response = model.generate_content(full_text)
            response_text = response.text
            
            message_placeholder.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            
        except Exception as e:
            message_placeholder.error(f"⚠️ ERROR ASLI DARI GOOGLE: {e}")