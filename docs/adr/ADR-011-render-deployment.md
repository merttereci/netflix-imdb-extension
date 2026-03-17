# ADR-011: Deployment Platformunun Railway'den Render'a Tasinmasi

## Tarih
17 Mart 2026

## Durum
Kabul Edildi

## Baglam
Projenin Faz 6 asamasinda backend API (FastAPI) Railway platformu uzerinde barindirilmaya baslanmisti (bkz. ADR-010). Ancak Railway'in "Free Trial" (500 saat veya 5$ kredi) hakki sona erdigi icin API servis disi kalmistir. 

Projenin egitim ve kisisel portfolyo (CV) amaci tasimasi nedeniyle; altyapi maliyeti olusturmayacak, sonsuz ucretsiz tier'i (free tier) bulunan alternatif bir barindirma platformuna gecilmesine karar verilmistir. OGRENME_NOTLARI.md icinde Koyeb, Render, Hugging Face ve Vercel gibi secenekler degerlendirilmis olup en zahmetsiz (kredi karti gerektirmeyen) cozumlerden biri olan Render secilmistir.

## Karar
Backend API'nin barindirma platformu Railway'den Render'a (render.com) tasinacaktir.

## Sonuclar

### Olumlu:
1. **0 Maliyet:** Render'in Free Web Service plani kredi kartsiz ve suresiz olarak kullanilabilir.
2. **Kolay Entegrasyon:** Proje zaten `requirements.txt` ile standart bir Python yapisina sahip oldugu icin Render uzerinde direk calisabilmektedir.
3. **GitHub Continuous Deployment (CD):** Mevcut repo uzerinden yeni commit'ler geldikce otomatik degisiklik uygulanacaktir.

### Olumsuz:
1. **Cold Start Gecikmesi:** Render'in ucretsiz planindaki sunucular, 15 dakika boyunca HTTP istegi almadiginda uyku moduna (sleep) gecerler. Uyuyan sunucuya yapilan ilk istek (cold start) yaklasik 30-60 saniye boyunca yanitsiz kalir veya bekletir.
2. **Extension Deneyimi:** Eger eklenti 15 dakikadan uzun sure kullanilmazsa, kullanici anasayfayi veya bir filmin modalini actiginda, badge'lerin (rating) yuklenmesi icin yaklasik 1 dakika beklemesi gerekecektir.

### Implementasyon Detaylari:
- **Build Command:** `pip install -r backend/requirements.txt`
- **Start Command:** `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT` (Dizin ve port ayari Render kurallari cercevesinde revize edilecektir, alternatif `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT` da olabilir)
- **Cevre Degiskenleri (Environment Variables):** Pydantic ayarlari icindeki `DATABASE_URL` (Supabase) ve `REDIS_URL` (Upstash) aynen Render Environment Variables kisminda set edilecektir.
- **Root Directory:** Eger Render root directory destekliyorsa `backend` klasoru secilmelidir, desteklemiyorsa komutlarda pathler uydurulmalidir.

## Alternatifler
Eger Render'daki cold start suresi ileride gercekten rahatsiz edici bulunursa, ucretsiz ancak uyku modu olmayan `Koyeb` dusunulebilir (Fakat kredi karti dogrulamasi isteyebilir).
