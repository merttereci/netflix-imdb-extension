# ADR 010: Railway Hosting ve Deployment Stratejisi

**Durum:** Kabul Edildi

## Baglam

Projemizin backend API'sini (FastAPI) ve veritabani baglantilarini (Supabase, Upstash) canli bir ortama tasimamiz gerekiyordu. Lokal calisma (`localhost`) sadece gelistirme asamasinda gecerlidir; son kullanicilarin (Extension kullanicilari) erisebilmesi icin public bir URL gereklidir.

## Karar

Hosting platformu olarak **Railway** kullanilmasina karar verildi.

## Neden Railway?

1.  **Kolay Setup:** GitHub reposunu baglayip `Procfile` ile aninda deploy imkani.
2.  **Automatic CI/CD:** Her `git push` isleminde otomatik yeniden build ve deploy.
3.  **Environment Variable Yonetimi:** UI uzerinden guvenli secret yonetimi.
4.  **Loglama:** Canli log takibi (Build ve Deploy loglari).
5.  **Maliyet:** Deneme suresi ve kredileri ogrenme projeleri icin yeterli.

## Alternatifler

### AWS EC2 / DigitalOcean Droplet
- **Avantaj:** Tam kontrol.
- **Dezavantaj:** Sunucu yonetimi (OS update, guvenlik, Nginx config) gerektirir. Bizim projemiz icin fazla is yuku (Overkill).

### Heroku
- **Avantaj:** Klasik, cok dokuman var.
- **Dezavantaj:** Ucretsiz plani kaldirdi (2022).

### Vercel / Netlify
- **Avantaj:** Frontend icin mukemmel.
- **Dezavantaj:** Python/Backend destegi var ama "Serverless Function" mantiginda calisiyor (Time limitler var). Bizim uzun suren islerimiz (Cold start) sorun olabilir.

## Uygulama

1.  Proje kök dizinine `Procfile` eklendi: `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`
2.  AI dosyalari ve `.env` dosyalari `.gitignore` ile repo disinda birakildi.
3.  Python versiyonu `.python-version` ile 3.12'ye sabitlendi (Uyumluluk icin).
4.  `requirements.txt` temizlendi (Development dependencies cikarildi).

## Sonuclar

- API artik `https://api-production-d6dc.up.railway.app` adresinde yayinda.
- Extension, localhost yerine bu adresi kullaniyor.
- Veritabani ve Cache baglantilari production ortaminda basariyla calisiyor.
