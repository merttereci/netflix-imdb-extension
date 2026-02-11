# Faz 5 Ogrenme Dokumani - Cache & Performans (Redis)

**Konu:** Backend Redis cache entegrasyonu ve Extension performans optimizasyonu

---

## 1. Redis Nedir?

Redis (Remote Dictionary Server), RAM'de calisan bir key-value store.
Veritabani DEGIL, gecici hafiza katmani (cache layer).

**Veritabani vs Redis:**

| Ozellik | PostgreSQL | Redis |
|---------|-----------|-------|
| Veri nerede | Disk (kalici) | RAM (gecici) |
| Hiz | ~50-200ms | ~1-5ms |
| Sorgu | SQL, JOIN, filtre | Sadece key ile get/set |
| Veri kaliciligi | Sonsuza kadar | TTL suresi kadar |
| Kapanirsa | Veri korunur | Veri kaybolur |

---

## 2. Cache-Aside Pattern

Bu projede kullandigimiz pattern. "Lazy Loading" olarak da bilinir.

**Akis:**
```
1. Istek gelir (ornegin "Inception" rating'i)
2. Redis'e bak -> Varsa (HIT) -> Direkt don (3ms)
3. Redis'te yoksa (MISS) -> Supabase'den cek (150ms) -> Redis'e yaz -> Don
4. TTL dolunca Redis otomatik siler -> Sonraki istek tekrar DB'ye gider
```

**Neden bu pattern?**
- Okuma agirlikli isler icin ideal (bizim senaryomuz)
- Cache bos baslar, talep geldikce dolar ("warm-up")
- DB ve cache senkronizasyonu basit

**Alternatif pattern'ler (bilgi icin):**
- **Write-Through:** Her DB yaziminda cache'i de guncelle. Daha tutarli ama yazma yavasi.
- **Write-Behind:** Cache'e yaz, arka planda DB'ye yaz. Hizli ama veri kaybi riski var.

---

## 3. TTL (Time To Live)

Cache'teki verinin ne kadar sure kalacagi.

**Bizim projede:** 3600 saniye (1 saat)

**Neden 1 saat?**
- IMDB rating'leri sik degismiyor (gunluk bile olmaz)
- 1 saat, gereksiz DB sorgularini %99 azaltir
- Cok uzun TTL (ornegin 24 saat) ise eski veri riski tasir

**TTL Stratejileri:**
| Senaryo | Onerilen TTL |
|---------|-------------|
| Neredeyse hic degismeyen veri (IMDB rating) | 1-24 saat |
| Sik degisen veri (hava durumu) | 5-15 dakika |
| Kullanici oturumu (session) | 30 dakika |
| Arama sonuclari | 10 dakika |

---

## 4. Upstash Redis

Serverless Redis hizmeti. Sunucu yonetimi gerektirmez.

**Ozellikler:**
- Free tier: Gunluk 10.000 komut
- SSL/TLS ile guvenli baglanti (`rediss://`)
- REST API de sunuyor (biz klasik Redis protokolu kullaniyoruz)

**Baglanti:**
```python
# Upstash URL formati
# rediss:// = SSL ile baglanti (cift 's')
# redis://  = SSL olmadan (lokal icin)
client = redis.from_url(
    "rediss://default:SIFRE@ENDPOINT.upstash.io:6379",
    ssl_cert_reqs="none"  # Upstash icin gerekli
)
```

**Karsilasilan sorun:** Python redis kutuphanesi varsayilan olarak SSL sertifika dogrulamasi yapar. Upstash kendi sertifikasini yonetir, bu yuzden `ssl_cert_reqs="none"` eklenmeli.

---

## 5. Multi-Level Cache

Projede 3 katmanli cache yapisi kuruldu:

```
Seviye 1: Service Worker In-Memory (Map)  -> ~0ms
Seviye 2: Redis (Upstash)                 -> ~3ms
Seviye 3: PostgreSQL (Supabase)           -> ~50-200ms
```

**Istek akisi:**
1. Extension'da kullanici Inception'a tiklar
2. Background.js in-memory cache'e bakar -> MISS
3. API'ye istek atar
4. API Redis'e bakar -> MISS
5. API Supabase'den ceker -> 150ms
6. API sonucu Redis'e yazar (TTL: 1 saat)
7. Background.js sonucu Map'e yazar (TTL: 5 dakika)
8. Tekrar tiklanirsa: Background.js Map'ten doner -> ~0ms

---

## 6. Debounce Mekanizmasi

**Sorun:** Netflix DOM'u modal acildiginda 10-20 kere degisir. MutationObserver her degisikligi yakalar.

**Cozum:** Sadece son degisikligi isler.

```javascript
let timer = null;
// Her DOM degisikliginde:
if (timer) clearTimeout(timer);  // Onceki timer'i iptal et
timer = setTimeout(handleModalOpen, 300);  // 300ms sonra calistir
```

**Mantik:** 300ms icinde yeni olay gelmezse isler. Gelirse timer sifirlanir.

---

## 7. X-Cache Header

API response'larina eklenen ozel header. Cache durumunu gosterir.

```
X-Cache: MISS  -> Supabase'den geldi (ilk istek)
X-Cache: HIT   -> Redis'ten geldi (cache'ten)
```

Bu header debugging ve monitoring icin cok kullanisli. Production'da cache hit ratio'yu olcmek icin kullanilir.

---

## 8. Olusturulan Dosyalar

| Dosya | Amac |
|-------|------|
| `backend/app/redis.py` | Redis baglanti yonetimi |
| `backend/app/utils/cache.py` | Cache-Aside helper fonksiyonlari |
| `backend/app/routes/cache_routes.py` | /cache/stats ve /cache/flush endpoint'leri |

## 9. Degistirilen Dosyalar

| Dosya | Degisiklik |
|-------|-----------|
| `backend/app/routes/movies.py` | 3 endpoint'e cache-aside pattern eklendi |
| `backend/app/main.py` | Redis startup event ve cache routes eklendi |
| `backend/app/config.py` | cache_ttl, cache_enabled ayarlari |
| `backend/requirements.txt` | redis paketi eklendi |
| `backend/.env` | REDIS_URL, CACHE_TTL, CACHE_ENABLED |
| `extension/content.js` | Debounce mekanizmasi (300ms) |
| `extension/background.js` | In-memory Map cache (5dk TTL) |

---

## 10. Mulakat Baglantilari

**Soru:** "Cache neden gerekli?"
**Cevap:** Ayni veri icin tekrar tekrar DB'ye gitmemek, yanit suresini dusurmek, DB uzerindeki yuku azaltmak.

**Soru:** "Cache-Aside pattern nedir?"
**Cevap:** Once cache'e bak, yoksa DB'den al ve cache'e yaz. Okuma agirlikli isler icin ideal.

**Soru:** "Cache invalidation nasil yapilir?"
**Cevap:** TTL ile otomatik silme (bizim yontem), veya veri degistiginde manuel silme.

**Soru:** "Cache servisi duserse ne olur?"
**Cevap:** Fail-open stratejisi: Cache yoksa DB'den devam eder, kullanici fark etmez.

**Soru:** "Multi-level cache nedir?"
**Cevap:** Birden fazla cache katmani: L1 (in-memory), L2 (Redis), L3 (DB). Her seviye gittikce yavaslar ama daha kalicidir.

---

**Arastirilacak:**
- [ ] Cache stampede (thundering herd) problemi
- [ ] Redis Pub/Sub ile cache invalidation
- [ ] Redis data structures (Hash, Set, Sorted Set)
- [ ] Redis Cluster vs Sentinel
- [ ] Rate limiting Redis ile nasil yapilir
