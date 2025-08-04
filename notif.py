import requests
import json
import time
from datetime import datetime

# --- Konfigurasi Telegram ---
TELEGRAM_BOT_TOKEN = "8330025895:AAFdd4OMdX3GNpWqaGB9GODMOduGJZ9xNW8"

# KONFIGURASI CHAT ID TELEGRAM
# =============================
# Untuk 1 ID saja:
# TELEGRAM_CHAT_ID = ["7398809677"]
#
# Untuk multiple ID (lebih dari 1):
# TELEGRAM_CHAT_ID = ["7398809677", "1234567890", "9876543210"]
#
# Cara mendapatkan Chat ID:
# 1. Chat dengan bot @userinfobot
# 2. Atau gunakan @RawDataBot
# 3. Atau buat bot sendiri dan cek update webhook
TELEGRAM_CHAT_ID = ["7398809677", "1737464807"]
# Waktu tunggu antara setiap request (dalam detik). Sesuaikan sesuai kebutuhan.
WAIT_TIME_SECONDS = 5  # Contoh: 5 menit (300 detik)

# URL untuk mengirim pesan ke Telegram
telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# --- Konfigurasi Request HTTP ---
url = "https://smsbower.org/activations/getMailRestsByService?serviceId=195"

headers = {
    "Host": "smsbower.org",
    "Cookie": "smsbower_net_session=eyJpdiI6Iit2eHVUMjRteGt4anVKNGlxczV1VVE9PSIsInZhbHVlIjoiaStER25sZXFMS1FyZ1RCQWE0SkNsdFJjRHoxMzhkYjJlVFVQSVlMVnEvN0ZRclJITFpQdW1wZjdaSktvODVEN1pITUlCcCtlRzlTMTRkWVhYTUZwWnJoVnNJWm5DZWhicEtmcHBmdW9NZ25McEE0VXlQZys5RTZVYWhQVnhKeVgiLCJtYWMiOiI1ZTk3MzAyZDQ2ZDEyNDBlODg1ZjlhZmZiYjFkNjQzZjY1ZGJlMmY0YjU1YTZkMjA4NWMzYmY5NjBlZDNlMjk5IiwidGFnIjoiIn0%3D; _gcl_au=1.1.661281141.1754289081; _ga_KQLPHL7RJF=GS2.1.s1754289080$o1$g0$t1754289080$j60$l0$h0; _ga=GA1.1.2111220209.1754289081; _clck=1ue1o6j%7C2%7Cfy6%7C0%7C2042; _ym_uid=1754289082627140093; _ym_d=1754289082; _ym_isad=2; _clsk=ezmmdu%7C1754289099324%7C1%7C1%7Ce.clarity.ms%2Fcollect",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "application/json, text/plain, */*",
    "Sec-Ch-Ua": '"Not)A;Brand";v="8", "Chromium";v="138"',
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://smsbower.org/temporaryMail",
    "Accept-Encoding": "gzip, deflate, br"
}

def send_telegram_notification(message):
    """Fungsi untuk mengirim pesan ke Telegram"""
    if TELEGRAM_BOT_TOKEN == "GANTI_DENGAN_TOKEN_BOT_KAMU":
        print("⚠️  PERINGATAN: Token Telegram belum dikonfigurasi!")
        print("   Silakan ganti TELEGRAM_BOT_TOKEN di file ini")
        return
    
    for chat_id in TELEGRAM_CHAT_ID:
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            response = requests.post(telegram_url, data=payload)
            if response.status_code == 200:
                print(f"✅ Notifikasi Telegram ke {chat_id} berhasil dikirim")
            else:
                print(f"❌ Gagal mengirim notifikasi Telegram ke {chat_id}: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error mengirim notifikasi Telegram ke {chat_id}: {e}")

def log_response_data(data):
    """Fungsi untuk mencatat data response"""
    try:
        if 'mails' in data and '195' in data['mails']:
            rests = data['mails']['195']['rests']
            
            # Cari data Gmail saja
            gmail_data = None
            for item in rests:
                if item['domain']['name'] == 'gmail.com':
                    gmail_data = item
                    break
            
            if gmail_data:
                count = gmail_data['count']
                price = gmail_data['price']
                print(f"\n📊 Data stok Gmail Apple:")
                print(f"   • gmail.com: {count} stok (₽{price})")
            else:
                print("\n📊 Data stok Gmail Apple:")
                print("   • gmail.com: 0 stok (tidak ditemukan)")
        else:
            print("⚠️  Struktur data tidak sesuai yang diharapkan")
            print(f"   Data yang diterima: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"❌ Error saat memproses data: {e}")

# Fungsi utama yang akan dijalankan PM2
def main():
    print(f"\n🔄 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Memeriksa stok email...")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"📡 Status Response: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Request berhasil")
            data = response.json()
            
            # Log semua data untuk debugging
            log_response_data(data)
            
            # Cari stok Gmail
            gmail_count = 0
            gmail_price = "0"
            if 'mails' in data and '195' in data['mails']:
                rests = data['mails']['195']['rests']
                for item in rests:
                    if item['domain']['name'] == 'gmail.com':
                        gmail_count = item['count']
                        gmail_price = item['price']
                        break
                        
                if gmail_count > 0:
                    message = f"**🍎 Notifikasi Stok Gmail Apple!**\n\n📧 Domain: `gmail.com`\n📦 Stok: *{gmail_count}*\n💰 Harga: ₽{gmail_price}\n⏰ Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    print(f"🎉 Stok Gmail ditemukan: {gmail_count}")
                    send_telegram_notification(message)
                else:
                    print("😔 Stok Gmail masih 0. Tidak ada notifikasi yang dikirim.")
            else:
                print("⚠️  Data tidak mengandung informasi mails yang diharapkan")
                print(f"   Response data: {json.dumps(data, indent=2)[:500]}...")
                
        elif response.status_code == 401:
            print("❌ Unauthorized - Cookie mungkin expired")
            print("   Silakan update cookie di headers")
        elif response.status_code == 403:
            print("❌ Forbidden - Akses ditolak")
        elif response.status_code == 429:
            print("❌ Too Many Requests - Rate limit terlampaui")
            print("   Tunggu beberapa saat sebelum mencoba lagi")
        else:
            print(f"❌ Request gagal dengan status code: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
    except requests.exceptions.Timeout:
        print("❌ Timeout - Request terlalu lama")
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error - Tidak bisa terhubung ke server")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error koneksi: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        print(f"   Response text: {response.text[:200]}...")
    except KeyError as e:
        print(f"❌ Error mengakses data: {e}")
    except Exception as e:
        print(f"❌ Error tidak terduga: {e}")
        import traceback
        traceback.print_exc()

# Jalankan dalam loop
if __name__ == "__main__":
    print("🚀 Bot notifikasi stok email dimulai...")
    print("⚠️  Pastikan TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID sudah dikonfigurasi!")
    print(f"📱 Jumlah chat ID yang dikonfigurasi: {len(TELEGRAM_CHAT_ID)}")
    
    # Kirim notifikasi bot started
    start_message = f"**🤖 Bot Gmail Monitor Started!**\n\n📱 Status: *Online*\n⏰ Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n🔄 Interval: {WAIT_TIME_SECONDS} detik\n🎯 Target: Gmail Apple\n👥 Chat ID: {len(TELEGRAM_CHAT_ID)} recipient(s)"
    send_telegram_notification(start_message)
    
    while True:
        main()
        print(f"⏰ Menunggu {WAIT_TIME_SECONDS} detik sebelum pengecekan berikutnya...")
        time.sleep(WAIT_TIME_SECONDS)
