# ADR-011: Deployment Platformunun Railway'den Vercel'e Tasinmasi

## Tarih
17 Mart 2026

## Durum
Kabul Edildi

## Baglam
Projenin Faz 6 asamasinda backend API (FastAPI) Railway platformu uzerinde barindirilmaya baslanmisti. Ancak Railway'in ucretsiz deneme suresi bittigi icin API servis disi kalmistir.  
Ilk etapta Render dusunulmus olmakla birlikte, kullanicinin (Mert) Render'in bazi senaryolarda ucret/kredi karti gerektirebilecegini sezinlemesi/deneyimlemesi uzerine, tamamen ucretsiz (Hobby tier isminde kart gerektirmeyen bir plana sahip) ve daha hizli bir alternatif olan **Vercel** platformuna gecilmesine karar verilmistir.

## Karar
Backend API'nin barindirma platformu Vercel'e (vercel.com) tasinacaktir. Vercel uzerinde Python (FastAPI) projeleri "Serverless Functions" mantigiyla calistirilmaktadir.

## Sonuclar

### Olumlu:
1. **100% Ucretsiz:** Vercel Hobby plan kredi karti gerektirmez.
2. **Cold Start Avantaji:** Vercel'in Serverless Edge agi sayesinde, uygulamanin Render gibi 15 dk inaktivitede tamamen uyuyup ilk acilista 1 dakika beklemesi gibi bir sorunu daha az/hizli olacaktir.
3. **Kolay Entegrasyon:** Proje ana dizinindeki `vercel.json` dosyasi kullanilarak API aninda canliya cikarilacaktir.

### Olumsuz:
1. **Serverless Kisitlamalari:** Geleneksel sunucular gibi surekli ayakta duran (long-running) bir arka plan islemi yapilamaz. Her API istegi 10 saniye icinde cevap vermelidir (Aksi takdirde Vercel Timeout atar). Projemizin (Supabase+Redis) ortalama yanit suresi <200ms oldugu icin bu bir sorun teskil etmemektedir.

### Implementasyon Detaylari:
- **Yapilandirma:** Ana dizinde `vercel.json` olusturulmus ve `@vercel/python` builder'i kullanilarak `/api/index.py` tanimlanmistir.
- **Entrypoint:** `/api/index.py` dosyasi eklenmis, bu dosya `backend` dizinini Python path'ine dahil ederek FastAPI objesini (app) serverless ortama uyumlu hale getirmistir.
- **Bagimliliklar:** Vercel root dizinden requirements bekledigi icin `backend/requirements.txt` dosyasi root dizine de kopyalanmistir.
- **Cevre Degiskenleri:** Vercel projesi (Project Settings -> Environment Variables) kismindan `DATABASE_URL` ve `REDIS_URL` atanacaktir.

## Alternatifler
Eger Serverless mantigi ile (ornek: in-memory cache calismamasi) ileride sorun yasanirsa, yari-kalici sunucu isteyen **Koyeb** veya **Hugging Face Spaces** denenecektir.
