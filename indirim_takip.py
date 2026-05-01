import requests
from datetime import datetime

# === AYARLAR ===
TELEGRAM_TOKEN = "8741153666:AAEty0sS3akctSQzzoAQ-TNx6daIpS-mo8k"
CHAT_ID = "7010024755"
INDIRIM_ESIGI = 30

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=data, timeout=10)
        print(f"Telegram gönderildi: {r.status_code}")
    except Exception as e:
        print(f"Telegram hatası: {e}")

def proteinocean_kontrol():
    print("ProteinOcean kontrol ediliyor...")
    bulunan = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        urls = [
            "https://proteinocean.com/api/products?limit=250&page=1",
            "https://proteinocean.com/products.json?limit=250",
        ]
        for url in urls:
            try:
                r = requests.get(url, headers=headers, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    urunler = data.get("products", data.get("data", []))
                    for urun in urunler:
                        ad = urun.get("name") or urun.get("title", "")
                        normal = float(urun.get("compare_at_price") or urun.get("original_price") or 0)
                        indirimli = float(urun.get("price") or urun.get("discounted_price") or 0)
                        if normal > 0 and indirimli > 0 and normal > indirimli:
                            indirim = round((1 - indirimli/normal) * 100, 1)
                            if indirim >= INDIRIM_ESIGI:
                                bulunan.append({
                                    "site": "ProteinOcean",
                                    "ad": ad,
                                    "normal": normal,
                                    "indirimli": indirimli,
                                    "indirim": indirim,
                                    "link": f"https://proteinocean.com/products/{urun.get('slug', urun.get('handle', ''))}"
                                })
                    if urunler:
                        break
            except:
                continue
    except Exception as e:
        print(f"ProteinOcean hatası: {e}")
    return bulunan

def takehiq_kontrol():
    print("HIQ Nutrition kontrol ediliyor...")
    bulunan = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        }
        r = requests.get("https://takehiq.com/products.json?limit=250", headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            for urun in data.get("products", []):
                for variant in urun.get("variants", []):
                    normal = float(variant.get("compare_at_price") or 0)
                    indirimli = float(variant.get("price") or 0)
                    if normal > 0 and indirimli > 0 and normal > indirimli:
                        indirim = round((1 - indirimli/normal) * 100, 1)
                        if indirim >= INDIRIM_ESIGI:
                            bulunan.append({
                                "site": "HIQ Nutrition",
                                "ad": urun["title"],
                                "normal": normal,
                                "indirimli": indirimli,
                                "indirim": indirim,
                                "link": f"https://takehiq.com/products/{urun['handle']}"
                            })
    except Exception as e:
        print(f"HIQ hatası: {e}")
    return bulunan

def main():
    print(f"Kontrol başlıyor: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    
    tum_indirimler = []
    tum_indirimler += proteinocean_kontrol()
    tum_indirimler += takehiq_kontrol()
    
    if tum_indirimler:
        for u in tum_indirimler:
            mesaj = (
                f"🚨 <b>İNDİRİM ALARMI!</b>\n\n"
                f"🏪 <b>Site:</b> {u['site']}\n"
                f"🛍 <b>Ürün:</b> {u['ad']}\n"
                f"💰 <b>Normal:</b> {u['normal']} TL\n"
                f"🔥 <b>İndirimli:</b> {u['indirimli']} TL\n"
                f"📉 <b>İndirim:</b> %{u['indirim']}\n"
                f"🔗 {u['link']}"
            )
            telegram_gonder(mesaj)
        print(f"{len(tum_indirimler)} indirim bulundu ve gönderildi!")
    else:
        print("Şu an %30+ indirim yok.")

if __name__ == "__main__":
    main()
