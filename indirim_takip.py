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
    
    # Kontrol edilecek tüm sayfalar
    sayfalar = [
        "https://proteinocean.com",
        "https://proteinocean.com/lansman",
        "https://proteinocean.com/paketler",
        "https://proteinocean.com/firsatlar",
        "https://proteinocean.com/indirimli-urunler",
        "https://proteinocean.com/kampanya",
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/html"
    }
    
    # ikas GraphQL API - tüm ürünleri çek
    try:
        graphql_url = "https://proteinocean.com/api/catalog/search"
        payload = {
            "query": "",
            "filters": {},
            "pagination": {"page": 1, "perPage": 100},
            "sort": {"field": "DISCOUNT", "order": "DESC"}
        }
        r = requests.post(graphql_url, json=payload, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            urunler = data.get("data", data.get("products", data.get("items", [])))
            for urun in urunler:
                _kontrol_urun(urun, "ProteinOcean", bulunan)
            if urunler:
                print(f"ProteinOcean API'den {len(urunler)} ürün alındı")
                return bulunan
    except Exception as e:
        print(f"ProteinOcean API hatası: {e}")
    
    # HTML sayfalarını tara
    for sayfa_url in sayfalar:
        try:
            r = requests.get(sayfa_url, headers=headers, timeout=15)
            if r.status_code == 200:
                html = r.text
                # JSON-LD veya script içindeki ürün verilerini bul
                import re
                import json
                
                # __NEXT_DATA__ içindeki verileri çek
                match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
                if match:
                    try:
                        next_data = json.loads(match.group(1))
                        # Ürünleri bul
                        _ara_urunler(next_data, "ProteinOcean", bulunan)
                    except:
                        pass
                
                # window.__data__ veya benzeri
                patterns = [
                    r'window\.__data__\s*=\s*({.*?});',
                    r'"products":\s*(\[.*?\])',
                    r'"items":\s*(\[.*?\])',
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, html, re.DOTALL)
                    for m in matches:
                        try:
                            data = json.loads(m)
                            if isinstance(data, list):
                                for urun in data:
                                    _kontrol_urun(urun, "ProteinOcean", bulunan)
                        except:
                            pass
                            
        except Exception as e:
            print(f"Sayfa hatası {sayfa_url}: {e}")
    
    return bulunan

def _ara_urunler(data, site, bulunan, depth=0):
    """Recursive olarak JSON içinde ürün ara"""
    if depth > 10:
        return
    if isinstance(data, dict):
        # Ürün benzeri yapı mı?
        if any(k in data for k in ["price", "salePrice", "comparePrice", "originalPrice"]):
            _kontrol_urun(data, site, bulunan)
        for v in data.values():
            _ara_urunler(v, site, bulunan, depth+1)
    elif isinstance(data, list):
        for item in data:
            _ara_urunler(item, site, bulunan, depth+1)

def _kontrol_urun(urun, site, bulunan):
    """Tek bir ürünü kontrol et"""
    try:
        ad = (urun.get("name") or urun.get("title") or 
              urun.get("displayName") or urun.get("productName") or "")
        if not ad:
            return
            
        # Farklı fiyat alanları
        normal = float(urun.get("compareAtPrice") or urun.get("compare_at_price") or 
                      urun.get("originalPrice") or urun.get("comparePrice") or
                      urun.get("basePrice") or 0)
        indirimli = float(urun.get("price") or urun.get("salePrice") or 
                         urun.get("discountedPrice") or urun.get("currentPrice") or 0)
        
        # Direkt indirim yüzdesi
        indirim_pct = float(urun.get("discountPercentage") or urun.get("discount") or 
                           urun.get("discountRate") or 0)
        
        if indirim_pct == 0 and normal > 0 and indirimli > 0 and normal > indirimli:
            indirim_pct = round((1 - indirimli/normal) * 100, 1)
        
        if indirim_pct >= INDIRIM_ESIGI:
            link = urun.get("url") or urun.get("href") or urun.get("slug") or ""
            if link and not link.startswith("http"):
                link = f"https://proteinocean.com{link}"
            
            anahtar = f"{site}_{ad}_{indirim_pct}"
            if not any(b["ad"] == ad for b in bulunan):
                bulunan.append({
                    "site": site,
                    "ad": ad,
                    "normal": normal,
                    "indirimli": indirimli,
                    "indirim": indirim_pct,
                    "link": link or f"https://proteinocean.com"
                })
                print(f"🔥 {site}: {ad} - %{indirim_pct} indirim!")
    except Exception as e:
        pass

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
                            if not any(b["ad"] == urun["title"] for b in bulunan):
                                bulunan.append({
                                    "site": "HIQ Nutrition",
                                    "ad": urun["title"],
                                    "normal": normal,
                                    "indirimli": indirimli,
                                    "indirim": indirim,
                                    "link": f"https://takehiq.com/products/{urun['handle']}"
                                })
                                print(f"🔥 HIQ: {urun['title']} - %{indirim} indirim!")
    except Exception as e:
        print(f"HIQ hatası: {e}")
    return bulunan

def main():
    print(f"\n{'='*40}")
    print(f"Kontrol başlıyor: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    
    tum_indirimler = []
    tum_indirimler += proteinocean_kontrol()
    tum_indirimler += takehiq_kontrol()
    
    if tum_indirimler:
        for u in tum_indirimler:
            normal_str = f"{u['normal']} TL" if u['normal'] > 0 else "?"
            indirimli_str = f"{u['indirimli']} TL" if u['indirimli'] > 0 else "?"
            mesaj = (
                f"🚨 <b>İNDİRİM ALARMI!</b>\n\n"
                f"🏪 <b>Site:</b> {u['site']}\n"
                f"🛍 <b>Ürün:</b> {u['ad']}\n"
                f"💰 <b>Normal:</b> {normal_str}\n"
                f"🔥 <b>İndirimli:</b> {indirimli_str}\n"
                f"📉 <b>İndirim:</b> %{u['indirim']}\n"
                f"🔗 {u['link']}"
            )
            telegram_gonder(mesaj)
        print(f"\n✅ {len(tum_indirimler)} indirim bulundu ve gönderildi!")
    else:
        print(f"❌ Şu an %{INDIRIM_ESIGI}+ indirim yok.")

if __name__ == "__main__":
    main()
