import streamlit as st
import google.generativeai as genai
import os

st.set_page_config(page_title="🔍 Model Scanner")
st.title("🔍 MODEL SCANNER")
st.write("Sedang memeriksa isi 'Gudang' Google AI Studio kamu...")

# 1. SETUP API KEY
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        st.success("✅ API Key Terbaca")
    else:
        st.error("❌ API Key Hilang dari Secrets")
        st.stop()
except Exception as e:
    st.error(f"❌ Error Config: {e}")
    st.stop()

# 2. LIST MODELS
st.divider()
st.subheader("DAFTAR MODEL YANG TERSEDIA:")

try:
    # Kita minta semua daftar
    all_models = list(genai.list_models())
    
    count = 0
    for m in all_models:
        # Kita cari yang bisa chat (generateContent)
        if 'generateContent' in m.supported_generation_methods:
            st.code(f"{m.name}")
            count += 1
            
    if count == 0:
        st.error("❌ DAFTAR KOSONG! Akun ini tidak punya akses ke model apapun.")
        st.info("Solusi: Cek Billing di Google Cloud Console atau Buat Akun Baru.")
    else:
        st.success(f"✅ Ditemukan {count} model yang bisa dipakai.")
        st.write("👆 Copy salah satu nama di atas (yang diawali 'models/') dan kirim ke chat.")

except Exception as e:
    st.error(f"❌ GAGAL SCANNING: {e}")
    st.write("Ini biasanya karena API Key salah, atau Project di Google Cloud kena suspend.")