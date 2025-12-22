import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="SOUL: Remembrance Engine", page_icon="🕊️")
st.markdown("<style>footer {visibility: hidden;}</style>", unsafe_allow_html=True)

# --- SETUP API KEY ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Key mati/kosong!")
    st.stop()

# --- BAGIAN KRUSIAL: BRUTE FORCE MODEL TESTER ---
# Kita tidak akan menebak. Kita akan mencoba chat "Ping" ke semua model.
# Model pertama yang menjawab, itulah yang kita pakai.

@st.cache_resource # Cache supaya tidak ngetes terus tiap kali klik tombol
def find_working_model():
    print("--- MEMULAI PENCARIAN MODEL HIDUP ---")
    candidates = []
    try:
        # Ambil semua model yang bisa chat
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                candidates.append(m.name)
        
        # Urutkan: Prioritaskan Flash (biasanya gratis & cepat), hindari 'latest' yang sering jebakan
        # Kita taruh model spesifik di depan
        priority_order = [
            "models/gemini-1.5-flash", 
            "models/gemini-1.5-flash-001",
            "models/gemini-1.5-flash-002",
            "models/gemini-1.0-pro",
            "models/gemini-pro"
        ]
        
        # Gabungkan prioritas dengan sisa kandidat
        final_list = priority_order + [c for c in candidates if c not in priority_order]
        
        for model_name in final_list:
            try:
                print(f"Testing: {model_name} ...", end=" ")
                tester = genai.GenerativeModel(model_name)
                # Tes kirim 1 token
                response = tester.generate_content("Tes")
                if response.text:
                    print("BERHASIL! ✅")
                    return model_name
            except Exception as e:
                print(f"GAGAL ({e}) ❌")
                continue
                
    except Exception as e:
        print(f"Error fatal saat listing: {e}")
    
    return None

# Jalankan pencari model
active_model_name = find_working_model()

if not active_model_name:
    st.error("SEMUA MODEL MATI / LIMIT HABIS. Ganti API Key baru dari Google AI Studio.")
    st.stop()

# --- UI VISUAL ---
st.title("🕊️ SOUL | Remembrance Engine")
st.caption(f"Connected to: `{active_model_name}` (Status: Online)")

# --- FUNGSI DATABASE ---
def save_to_sheet(nama_user, nama_almarhum, hubungan, pesan_terakhir):
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        if not os.path.exists('credentials.json'):
            return False
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client_sheets = gspread.authorize(creds)
        sheet = client_sheets.open("SOUL_User_Database").sheet1
        waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([waktu, nama_user, nama_almarhum, hubungan, pesan_terakhir])
        return True
    except:
        return False

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Konfigurasi")
    soul_name = st.text_input("Nama", "Ayah")
    relationship = st.selectbox("Hubungan", ["Ayah", "Ibu", "Pasangan", "Anak"])
    sample_chat = st.text_area("Gaya Bicara", "Nak, makan ya. Ayah sayang kamu.", height=100)
    
    if st.button("💾 Simpan Chat"):
        if "messages" in st.session_state and st.session_state.messages:
            save_to_sheet("Demo User", soul_name, relationship, st.session_state.messages[-1]['content'])
            st.toast("Tersimpan!", icon="✅")
    
    if st.button("Reset"):
        st.session_state.messages = []
        st.rerun()

# --- SYSTEM LOGIC ---
system_prompt = f"Peran: {soul_name}. Hubungan: {relationship}. Gaya: {sample_chat}. Jangan jadi hantu."
model = genai.GenerativeModel(active_model_name)

# --- CHAT ---
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
            # Manual Context Construction
            full_text = f"SYSTEM: {system_prompt}\n\n"
            for m in st.session_state.messages:
                full_text += f"{m['role']}: {m['content']}\n"
            full_text += "assistant: "
            
            response = model.generate_content(full_text)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error("Koneksi Error. Coba refresh.")
            st.code(e)