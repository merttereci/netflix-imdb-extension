# ADR-009: Batch API ve Anasayfa Kart Stratejisi

## Durum
Kabul edildi

## Baglam
Netflix anasayfasinda 50-100 film/dizi karti gorunuyor. Her karta IMDB rating
badge eklemek icin verimli bir yontem gerekiyor. Tek tek API istegi atmak
N+1 problemi olusturur.

## Karar

### 1. Batch API Endpoint (POST /api/ratings/batch)
- Tek istekte max 20 baslik sorgulanabilir
- POST kullanildi (GET query string siniri nedeniyle)
- Her baslik icin cache-aside pattern uygulanir
- Cache'te olanlar DB'ye gitmez

### 2. IntersectionObserver ile Kart Tespiti
- Scroll event yerine IntersectionObserver kullanildi
- Performans avantaji: async, main thread bloklamaz
- threshold: 0.1 (%10 gorunurse tetikle)
- rootMargin: 50px (onceden tetikle)

### 3. Debounced Batch Gonderim
- Kartlar tek tek gorunur olur, 300ms debounce ile biriktirilir
- 20 kart birikince debounce beklemeden gonderilir
- processedCards Set ile ayni kart tekrar islenmez

### 4. Badge Overlay (position: absolute)
- .boxart-container'a position:relative eklendi
- Badge sag ust koseye yerlestirildi
- pointer-events: none ile kart etkilesimi korundu

## Alternatifler
- **Tek tek GET istekleri:** N+1 problemi, 100 kart = 100 istek
- **WebSocket:** Over-engineering, polling gereksiz
- **Scroll event:** Performans sorunu, her piksel tetikler

## Sonuc
- 50 kart, 8 batch istegi ile islendi
- ~%98 basari orani
- In-memory cache sayesinde modal acilisinda 1.35ms response suresi
