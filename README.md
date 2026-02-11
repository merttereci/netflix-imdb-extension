# Netflix IMDB Rating Extension

Netflix'te film ve dizi kartlarinin uzerinde IMDB puanlarini otomatik olarak gosteren bir Chrome Extension. Kendi backend API'si, veritabani ve cache sistemi ile tam bir full-stack projedir.

## Nasil Calisiyor?

```
Netflix Sayfasi          Chrome Extension            Backend API
┌──────────────┐      ┌──────────────────┐      ┌──────────────────┐
│              │      │                  │      │                  │
│  Film Karti  │─────>│  content.js      │─────>│  FastAPI         │
│  (DOM)       │      │  Baslik cikar    │      │  /api/rating     │
│              │      │                  │      │  /api/ratings/    │
│  ┌────────┐  │      │  background.js   │<─────│   batch          │
│  │IMDb 8.7│  │<─────│  Rating al       │      │                  │
│  └────────┘  │      │  Badge ekle      │      │  PostgreSQL      │
│              │      │                  │      │  Redis Cache     │
└──────────────┘      └──────────────────┘      └──────────────────┘
```

**Anasayfa kartlari:** IntersectionObserver ile gorunen kartlari tespit eder, basliklarini toplar, Batch API ile toplu sorgular ve her kartın sag ust kosesine kucuk IMDB badge koyar.

**Detay modali:** Film/dizi detayina tiklandiginda modal icerisinde buyuk IMDB badge gosterir.

## Proje Durumu

| Faz | Icerik | Durum |
|-----|--------|-------|
| Faz 1: Temel Altyapi | Proje yapisi, Git, dizin organizasyonu | Tamamlandi |
| Faz 2: Data Pipeline | IMDB dataset indirme, Pandas ile isleme, PostgreSQL'e aktarma | Tamamlandi |
| Faz 3: Backend API | FastAPI, SQLAlchemy, Turkce baslik destegi, arama | Tamamlandi |
| Faz 4: Chrome Extension | Content script, MutationObserver, modal rating badge | Tamamlandi |
| Faz 5: Cache & Performans | Redis (Upstash), Cache-Aside pattern, debounce, multi-level cache | Tamamlandi |
| Faz 6: Deployment | CI/CD, production deploy | Tamamlandi |
| Faz 7: Anasayfa Kartlari | Batch API, IntersectionObserver, kart badge overlay | Tamamlandi |

## Teknoloji Stack

| Kategori | Teknoloji | Neden |
|----------|-----------|-------|
| Backend Framework | Python + FastAPI | Async destegi, otomatik OpenAPI dokumantasyonu |
| Database | PostgreSQL (Supabase) | Full-text search, 60K kayit, free tier |
| Cache | Redis (Upstash) | Serverless Redis, Cache-Aside pattern |
| Extension | Chrome Manifest V3 | Modern extension standardi, service worker |
| Frontend | Vanilla JavaScript | Basit, framework gerektirmiyor |
| Data Processing | Pandas | 10M+ satir IMDB verisi isleme |
| ORM | SQLAlchemy | Python ekosisteminin standart ORM'i |

## Mimari

### Multi-Level Cache

Proje 3 katmanli bir cache mimarisi kullaniyor:

```
Istek geldi
    │
    v
┌─────────────────────────────┐
│ Seviye 1: In-Memory (Map)   │  ~0-1ms
│ background.js icerisinde    │  5 dk TTL, max 200 entry
│ En hizli, en kisa omurlu    │
└──────────┬──────────────────┘
           │ MISS
           v
┌─────────────────────────────┐
│ Seviye 2: Redis (Upstash)   │  ~3ms
│ Sunucu tarafinda            │  1 saat TTL
│ Orta hiz, orta omur         │
└──────────┬──────────────────┘
           │ MISS
           v
┌─────────────────────────────┐
│ Seviye 3: PostgreSQL        │  ~50-200ms
│ Kalici depolama             │  60K film/dizi
│ En yavas, kalici            │
└─────────────────────────────┘
```

**Gercek test sonucu:** Ayni film once anasayfa kartinda batch ile soruldu (PostgreSQL, ~100ms). Sonra modal acildiginda in-memory cache'ten geldi (**1.35ms**).

### Batch API (N+1 Problem Cozumu)

Anasayfa'da 50-100 kart gorunur. Her biri icin ayri API istegi atmak yerine:

```
Oncesi:  GET /api/rating?title=X   x100 istek = 100 HTTP baglantisi
Sonrasi: POST /api/ratings/batch   x5 istek   = 5 HTTP baglantisi (20'serli)
```

### Netflix DOM Entegrasyonu

| Bilgi | Selector | Aciklama |
|-------|----------|----------|
| Film adi (kart) | `a[aria-label]` | Accessibility standardi, en guvenilir |
| Film adi (yedek) | `p.fallback-text` | Poster yuklenemezse gorunen metin |
| Kart container | `[data-uia="title-card-container"]` | Netflix'in test attribute'u |
| Poster alani | `.boxart-container` | Badge'in yerlestirilecegi alan |
| Modal baslik | `.previewModal--info strong` | Modal icindeki baslik |

**Kart tespiti:** `IntersectionObserver` ile gorunen kartlar tespit edilir. Scroll event'e gore cok daha performansli (async, main thread bloklamaz).

## Veritabani

| Tablo | Kayit Sayisi | Aciklama |
|-------|-------------|----------|
| movies | 59,980 | IMDB filmleri (rating, votes, genres) |
| movie_titles | 23,976 | Turkce basliklar (IMDB akas dataset) |

**Veri Kaynagi:** IMDB Official Datasets (title.basics, title.ratings, title.akas)
**Filtre:** numVotes >= 1000 (dusuk oylu icerikler haric)

## API Endpoints

| Method | Endpoint | Aciklama |
|--------|----------|----------|
| GET | `/api/rating?title=X` | Tek film rating sorgula |
| POST | `/api/ratings/batch` | Toplu rating sorgula (max 20) |
| GET | `/api/search?q=X` | Film/dizi ara |
| GET | `/api/movie/{imdb_id}` | IMDB ID ile sorgula |
| GET | `/api/cache/stats` | Cache istatistikleri |
| GET | `/api/health` | Saglik kontrolu |

## Proje Yapisi

```
extension/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── models/
│   │   │   ├── movie.py        # Film modeli (SQLAlchemy)
│   │   │   └── movie_title.py  # Turkce baslik modeli
│   │   ├── routes/
│   │   │   ├── movies.py       # Film API endpoint'leri
│   │   │   └── cache_routes.py # Cache yonetim endpoint'leri
│   │   ├── utils/
│   │   │   ├── turkish.py      # Turkce karakter normalizasyonu
│   │   │   └── cache.py        # Redis cache helper'lari
│   │   ├── main.py             # FastAPI uygulama giris noktasi
│   │   ├── config.py           # Pydantic ayarlar (env)
│   │   ├── database.py         # SQLAlchemy baglanti yonetimi
│   │   └── redis.py            # Redis baglanti yonetimi
│   ├── requirements.txt
│   └── .env.example
├── extension/                  # Chrome Extension (Manifest V3)
│   ├── manifest.json           # Extension konfigurasyonu
│   ├── content.js              # Netflix DOM okuma + badge ekleme
│   ├── background.js           # API iletisimi + in-memory cache
│   ├── styles.css              # Modal ve kart badge stilleri
│   ├── popup.html              # Extension popup
│   └── popup.js
├── scripts/
│   ├── import_imdb.py          # IMDB dataset -> PostgreSQL pipeline
│   └── test_db.py              # Veritabani test scripti
├── docs/
│   ├── adr/                    # Architecture Decision Records (9 adet)
│   ├── FAZ1_OGRENME.md         # Faz ogrenme dokumanlari
│   ├── FAZ2_OGRENME.md
│   ├── FAZ3_OGRENME.md
│   ├── FAZ4_OGRENME.md
│   ├── FAZ5_OGRENME.md
│   └── FAZ7_OGRENME.md
└── README.MD                   # Proje dokumantasyonu
```

## Kurulum

### Backend

```bash
cd backend
pip install -r requirements.txt

# .env dosyasi olustur
cp .env.example .env
# DATABASE_URL ve REDIS_URL'i guncelle

# Sunucuyu baslat
python -m uvicorn app.main:app --host 127.0.0.1 --port 8006 --reload
```

### Chrome Extension

1. Chrome'da `chrome://extensions` adresine git
2. "Gelistirici modu" nu ac (sag ust kose)
3. "Paketlenmemis oge yukle" tikla
4. `extension/extension/` klasorunu sec
5. Netflix'e git, filmlerin uzerinde IMDB badge'lerini gor

## Mimari Kararlar (ADR)

| ADR | Karar |
|-----|-------|
| ADR-001 | PostgreSQL secimi (full-text search, genis ekosistem) |
| ADR-002 | FastAPI secimi (async, otomatik docs, Pydantic) |
| ADR-003 | Redis cache (Upstash serverless, Cache-Aside pattern) |
| ADR-004 | IMDB official dataset (legal, kapsamli, TSV format) |
| ADR-005 | Monorepo yaklasimi (backend + extension ayni repo) |
| ADR-006 | Lokalize baslik destegi (Turkce IMDB akas) |
| ADR-007 | Arama optimizasyonu (normalize + exact match oncelikli) |
| ADR-008 | Netflix kart ve cache stratejisi |
| ADR-009 | Batch API ve IntersectionObserver stratejisi |

## Ogrenme Konulari

Bu proje kapsaminda ogrenilenler:

- **Backend:** REST API tasarimi, FastAPI, SQLAlchemy ORM, Pydantic validation
- **Database:** PostgreSQL, Supabase, migration, normalizasyon
- **Cache:** Redis, Cache-Aside pattern, TTL, multi-level cache
- **Chrome Extension:** Manifest V3, content/background script, messaging API
- **Web API'ler:** IntersectionObserver, MutationObserver, DOM manipulation
- **Performans:** Debounce, batch processing, N+1 problem cozumu
- **Mimari:** ADR yazma, faz bazli gelistirme, YAGNI prensibi

## Lisans

Bu proje kisisel/egitim amaclidir. IMDB verileri resmi dataset'lerden alinmistir.


