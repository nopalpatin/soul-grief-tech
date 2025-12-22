import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

print("--- MULAI DIAGNOSA DATABASE ---")

# 1. CEK FILE KUNCI
if not os.path.exists('credentials.json'):
    print("❌ GAGAL TOTAL: File credentials.json TIDAK DITEMUKAN di folder ini!")
    exit()
else:
    print("✅ File credentials.json ditemukan.")

# 2. CEK EMAIL ROBOT
try:
    with open('credentials.json') as f:
        data = json.load(f)
        email_robot = data.get('client_email')
        print(f"🤖 Email Robot kamu adalah:\n   {email_robot}")
        print("(Pastikan email ini sudah dijadikan EDITOR di Google Sheet!)")
except Exception as e:
    print(f"❌ File JSON rusak: {e}")
    exit()

# 3. COBA KONEK
try:
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    print("✅ Login berhasil.")
except Exception as e:
    print(f"❌ Gagal Login: {e}")
    exit()

# 4. COBA BUKA SHEET
NAMA_SHEET = "SOUL_User_Database" # <--- INI HARUS SAMA PERSIS
try:
    sheet = client.open(NAMA_SHEET).sheet1
    print(f"✅ Berhasil membuka sheet: {NAMA_SHEET}")
except Exception as e:
    print(f"❌ GAGAL MEMBUKA SHEET '{NAMA_SHEET}'")
    print(f"Penyebab: {e}")
    print("SOLUSI: Cek apakah nama file di Google Sheets sudah BENAR-BENAR sama?")
    exit()

# 5. COBA TULIS
try:
    sheet.append_row(["TES", "DIAGNOSA", "BERHASIL", "MASUK", "DATABASE"])
    print("✅ SUKSES! Data berhasil ditulis ke baris baru.")
    print("Coba cek Google Sheet kamu sekarang.")
except Exception as e:
    print(f"❌ Gagal Menulis: {e}")