# Faz 6: Deployment ve CI/CD - Ogrenme Dokumani

> Bu dokuman Faz 6'daki kavramlari, kodlari ve ogrenilenleri aciklar.
> Durum: TAMAMLANDI

## Ozet

FastAPI backend uygulamamizi Railway platformuna deploy ettik. GitHub ile entegre ederek, her push isleminde otomatik deploy (CI/CD) sagladik.

---

## 1. Neden Railway?

Render, Fly.io, Vercel ve Heroku gibi alternatifler arasindan **Railway** sectik.

| Ozellik | Railway | Render | Heroku |
|---------|---------|--------|--------|
| Kurulum | Cok Basit | Basit | Orta |
| Free Tier | $5 kredi/ay | 1 Ay & Uyku Modu | Kaldirildi |
| CI/CD | Otomatik | Otomatik | Otomatik |
| Config | UI veya TOML | UI veya YAML | CLI/Procfile |

**Karar:** Railway, hem setup kolayligi hem de deneme kredisinin esnekligi nedeniyle secildi. Ayrica Upstash (Redis) ve Supabase (Postgres) disaridan baglandigi icin sadece compute gucu kullaniyoruz.

---

## 2. Procfile Nedir?

Railway, Heroku ve diger PAAS (Platform as a Service) saglayicilari uygulamanin nasil calisacagini bilmek ister. `Procfile` bunu tanimlar.

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- **web:** Bu bir web sunucusu (background worker degil).
- **uvicorn:** FastAPI'yi calistiran ASGI sunucusu.
- **host 0.0.0.0:** Dis dunyadan gelen isteklere acik ol (localhost degil).
- **$PORT:** Railway'in atadigi portu dinamik olarak kullan.

---

## 3. Environment Variables (Sirlar)

Lokalde `.env` dosyasinda tuttugumuz sifreleri (DB URL, Redis URL) GitHub'a atmadik (`.gitignore` sayesinde).

Railway uzerinde bu degiskenleri **"Variables"** sekmesinden elle ekledik:
- `DATABASE_URL`
- `REDIS_URL`
- `CACHE_TTL`
- `CACHE_ENABLED`

Bu sayede kodumuz "Stateless" kaldi ve guvenlik acigi olusmadi. Bu **12-Factor App** prensiplerinden biridir.

---

## 4. CI/CD (Surekli Entegrasyon/Dagitim)

GitHub'a kodumuzu push ettigimizde su akis gerceklesti:

1.  **Push:** `git push origin main`
2.  **Trigger:** Railway repo'daki degisikligi algiladi.
3.  **Build:**
    - Python environment hazirladi.
    - `requirements.txt` okuyup paketleri yukledi.
4.  **Deploy:**
    - `Procfile` komutunu calistirdi.
    - Saglik kontrolu yapti.
    - Eski version'u kapatip yenisine trafik yonlendirdi.

Buna **GitOps** denir. Kod deposu, gercegin tek kaynagi (Single Source of Truth) oldu.

---

## 5. Karsilasilan Sorunlar

| Sorun | Cozum |
|-------|-------|
| `failed to build: pandas` | `pandas` ve `tqdm` sadece veri importu icindi. Runtime'da gereksiz oldugu icin `requirements.txt`'ten cikarildi. |
| `pydantic-core` build hatasi | Python 3.13 henuz bazi paketlerle uyumsuz. `.python-version` dosyasi ile Python 3.12'ye sabitlendi. |
| `FATAL: database does not exist` | Railway'e kopyalanan `DATABASE_URL` sonunda bosluk/enter karakteri kalmis. Temizlendi. |

---

## 6. Mulakat Sorulari

- **Soru:** "Environment variable neden kullanilir?"
- **Cevap:** Kod ile konfigurasyonu ayirmak (Config separation) ve hassas verileri (sifreler) kodun icinde tutmamak icin.

- **Soru:** "CI/CD nedir?"
- **Cevap:** Continuous Integration/Continuous Deployment. Kod degisikliklerinin otomatik olarak test edilip canli ortama alinmasi sureci.

- **Soru:** "Procfile ne ise yarar?"
- **Cevap:** Uygulamanin baslatma komutunu (entry point) platforma bildirir.

---

*Bu dokuman ogrenme amaclidir.*
