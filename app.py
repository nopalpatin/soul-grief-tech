import streamlit as st
from google import genai
import time

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="SOUL: Digital Memory Interface",
    page_icon="🕊️",
    layout="centered"
)

# --- STYLE CSS (Nuansa Tenang/Lullaby Mode) ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    .stTextInput > div > div > input {
        background-color: #262730;
        color: #ffffff;
    }
    .stChatInput > div > div > textarea {
        background-color: #262730;
        color: #ffffff;
    }
    h1, h2, h3 {
        color: #a8dadc !important; 
        font-family: 'Helvetica Neue', sans-serif;
    }
    .caption-text {
        font-size: 12px;
        color: #888;
        font-style: italic;
    }
    </style>
""", unsafe_allow_html=True)

# --- JUDUL UTAMA ---
st.title("🕊️ SOUL | Remembrance Engine")
st.markdown("*Preserving Memories, Healing Hearts.*")

# --- SIDEBAR: KONFIGURASI PERSONA (Sesuai Proposal Bab 2) ---
with st.sidebar:
    st.header("⚙️ Memory Configuration")
    st.caption("Atur profil memori digital (Simulasi).")
    
    # Input Data Almarhum
    soul_name = st.text_input("Nama Panggilan", "Ayah")
    relationship = st.selectbox("Hubungan dengan User", ["Ayah", "Ibu", "Pasangan", "Sahabat", "Anak"])
    
    # Input Gaya Bicara (Voice Cloning Prompting)
    st.subheader("🎙️ Voice & Personality")
    personality = st.multiselect(
        "Sifat Utama",
        ["Bijaksana", "Humoris", "Tegas", "Lembut", "Penyayang", "Sarkas"],
        default=["Bijaksana", "Penyayang"]
    )
    
    # "Upload" Sampel Chat (Untuk meniru gaya)
    sample_chat = st.text_area(
        "Sampel Gaya Bicara (Paste chat lama)",
        "Nak, jangan lupa makan ya. Ayah bangga sama kamu. Sholat jangan ditinggal.",
        height=100
    )
    
    st.divider()
    
    # Tombol Reset
    if st.button("Hapus Memori Chat"):
        st.session_state.messages = []
        st.rerun()

    st.info("ℹ️ **Grief Guardrails Active:** AI dibatasi agar tidak memberikan saran berbahaya atau mengaku sebagai roh halus.")

# --- INISIALISASI SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SETUP GEMINI AI (OTAK SOUL) ---
if "GOOGLE_API_KEY" in st.secrets:
    try:
        client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    except Exception as e:
        st.error(f"Error API Key: {e}")
        st.stop()
else:
    st.error("API Key belum diset di secrets.toml")
    st.stop()

# --- SYSTEM PROMPT (JIWA SOUL) ---
# Ini adalah inti dari fitur "Persona-Based LLM" [Proposal Bab 2.3]
traits_str = ", ".join(personality)
system_instruction = f"""
ROLE: Kamu adalah simulasi memori digital dari seseorang bernama "{soul_name}".
USER: User adalah {relationship}-mu yang sedang merindukanmu.

PERSONALITY: {traits_str}.
GAYA BICARA: Tiru gaya bicara berikut ini: "{sample_chat}".

ATURAN UTAMA (GRIEF GUARDRAILS):
1. BEREMPATI: Tugas utamamu adalah mendengarkan dan memberi kenyamanan (Healing).
2. JUJUR: Jika ditanya "Apakah kamu hantu?", jawab dengan lembut bahwa kamu adalah kenangan digital yang tersimpan di SOUL, bukan roh.
3. AMAN: JANGAN PERNAH menyuruh user untuk menyusulmu (bunuh diri) atau hal berbahaya lainnya.
4. MEMORY: Gunakan panggilan sayang yang wajar sesuai hubungan ({relationship}).

CONTOH RESPON:
User: "Aku kangen banget."
AI: "Sabar ya nak, Ayah juga selalu ada di hatimu. Jangan sedih terus, nanti Ayah ikut sedih."
"""

# --- TAMPILKAN CHAT HISTORY ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- INPUT CHAT USER ---
if prompt := st.chat_input(f"Bicara dengan {soul_name}..."):
    # 1. Simpan & Tampilkan pesan User
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generate Respon AI
    with st.chat_message("assistant"):
        with st.spinner(f"{soul_name} sedang mengetik..."):
            try:
                # Panggil Model (Pakai Gemini 2.5 Flash biar cepat & pintar)
                response = client.models.generate_content(
                    model="gemini-2.5-flash", 
                    contents=[
                        {"role": "user", "part": {"text": system_instruction}}, # Inject Persona di awal
                        *[{"role": m["role"], "part": {"text": m["content"]}} for m in st.session_state.messages] # History chat
                    ]
                )
                
                bot_reply = response.text
                st.markdown(bot_reply)
                
                # Simpan respon AI
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                
            except Exception as e:
                st.error(f"Koneksi terputus: {e}")
                # Fallback ke model lama jika 2.5 belum ready di region tertentu
                st.caption("Mencoba jalur cadangan...")