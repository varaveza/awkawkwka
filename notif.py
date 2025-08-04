import requests
import json
import time
from datetime import datetime

# --- Konfigurasi Telegram ---
TELEGRAM_BOT_TOKEN = "8330025895:AAFdd4OMdX3GNpWqaGB9GODMOduGJZ9xNW8"
TELEGRAM_CHAT_ID = ["7398809677", "1737464807"]

# Waktu tunggu antara setiap request (dalam detik).
WAIT_TIME_SECONDS = 3 

# URL untuk mengirim pesan ke Telegram
telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# Nama file untuk menyimpan state (jumlah stok terakhir)
STATE_FILE = "stock_state.json"

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

# --- Fungsi Baru untuk State Management ---

def read_last_stock():
    """Membaca jumlah stok terakhir dari file JSON."""
    try:
        with open(STATE_FILE, 'r') as f:
            data = json.load(f)
            # Mengembalikan nilai 'last_gmail_stock' atau -1 jika tidak ada
            return data.get('last_gmail_stock', -1)
    except (FileNotFoundError, json.JSONDecodeError):
        # Jika file tidak ada atau error, anggap belum ada data sebelumnya
        return -1

def write_current_stock(count):
    """Menyimpan jumlah stok saat ini ke file JSON."""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump({'last_gmail_stock': count}, f, indent=4)
        print(f"💾 State berhasil disimpan: {count} stok.")
    except Exception as e:
        print(f"❌ Gagal menyimpan state ke file: {e}")

# --- Fungsi yang sudah ada ---

def send_telegram_notification(message):
    """Fungsi untuk mengirim pesan ke Telegram"""
    if TELEGRAM_BOT_TOKEN == "GANTI_DENGAN_TOKEN_BOT_KAMU":
        print("⚠️  PERINGATAN: Token Telegram belum dikonfigurasi!")
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
                print(f"❌ Gagal mengirim notifikasi Telegram ke {chat_id}: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error mengirim notifikasi Telegram ke {chat_id}: {e}")

def log_response_data(data):
    """Fungsi untuk mencatat data response"""
    try:
        if 'mails' in data and '195' in data['mails']:
            rests = data['mails']['195']['rests']
            gmail_data = next((item for item in rests if item['domain']['name'] == 'gmail.com'), None)

            print("\n📊 Data stok Gmail Apple:")
            if gmail_data:
                print(f"   • gmail.com: {gmail_data['count']} stok (₽{gmail_data['price']})")
            else:
                print("   • gmail.com: 0 stok (tidak ditemukan)")
        else:
            print("⚠️  Struktur data tidak sesuai yang diharapkan")
    except Exception as e:
        print(f"❌ Error saat memproses data log: {e}")

# --- Fungsi Utama yang Dimodifikasi ---

def main():
    print(f"\n🔄 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Memeriksa stok email...")

    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"📡 Status Response: {response.status_code}")

        if response.status_code == 200:
            print("✅ Request berhasil")
            data = response.json()
            log_response_data(data)

            # Ekstrak stok Gmail saat ini
            gmail_count = 0
            gmail_price = "0"
            if 'mails' in data and '195' in data['mails']:
                rests = data['mails']['195']['rests']
                gmail_data = next((item for item in rests if item['domain']['name'] == 'gmail.com'), None)
                if gmail_data:
                    gmail_count = gmail_data['count']
                    gmail_price = gmail_data['price']

            # Baca stok terakhir dari file
            last_known_stock = read_last_stock()
            print(f"📦 Stok saat ini: {gmail_count}")

            # **LOGIKA UTAMA: Kirim notifikasi HANYA jika stok berubah dan lebih dari 0**
            if gmail_count > 0 and gmail_count != last_known_stock:
                message = (
                    f"**🍎 Notifikasi Stok Gmail Apple!**\n\n"
                    f"📧 Domain: `gmail.com`\n"
                    f"📦 Stok: *{gmail_count}* (Sebelumnya: {last_known_stock if last_known_stock != -1 else 'N/A'})\n"
                    f"💰 Harga: ₽{gmail_price}\n"
                    f"⏰ Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                print(f"🎉 Stok Gmail berubah dan tersedia! Mengirim notifikasi...")
                send_telegram_notification(message)
            elif gmail_count == last_known_stock:
                print(f"⚖️ Stok tidak berubah ({gmail_count}). Tidak ada notifikasi yang dikirim.")
            else: # Termasuk jika stok menjadi 0
                print("😔 Stok Gmail kosong atau tidak berubah. Tidak ada notifikasi yang dikirim.")
            
            # Selalu update file state dengan jumlah stok terbaru setelah pengecekan berhasil
            write_current_stock(gmail_count)

        # ... (error handling lainnya tetap sama) ...
        elif response.status_code == 401:
            print("❌ Unauthorized - Cookie mungkin expired. Silakan update cookie di headers.")
        else:
            print(f"❌ Request gagal dengan status code: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")

    except requests.exceptions.Timeout:
        print("❌ Timeout - Request terlalu lama")
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error - Tidak bisa terhubung ke server")
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        print(f"   Response text: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Error tidak terduga: {e}")
        import traceback
        traceback.print_exc()

# --- Loop Utama ---
if __name__ == "__main__":
    print("🚀 Bot notifikasi stok email dimulai...")
    print("⚠️  Pastikan TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID sudah dikonfigurasi!")

    start_message = (
        f"**🤖 Bot Gmail Monitor Started!**\n\n"
        f"📱 Status: *Online*\n"
        f"⏰ Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"🔄 Interval: {WAIT_TIME_SECONDS} detik"
    )
    send_telegram_notification(start_message)

    while True:
        main()
        print(f"⏰ Menunggu {WAIT_TIME_SECONDS} detik sebelum pengecekan berikutnya...")
        time.sleep(WAIT_TIME_SECONDS)
