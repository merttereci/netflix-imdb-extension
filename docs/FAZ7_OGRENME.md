# Faz 7 Ogrenme Dokumani: Anasayfa Kart Rating'leri

## Bu Fazda Ogrenilen Kavramlar

### 1. Batch API Pattern (N+1 Problem Cozumu)

**Problem:** 100 kart = 100 ayri HTTP istegi. Her biri TCP handshake, DNS lookup,
TLS negotiation iceriyor. Bu cok yavas ve kaynak israfci.

**Cozum:** Batch endpoint ile 100 kart = 5 istek (20'serli gruplar).

```
Oncesi: GET /api/rating?title=X  (x100 kez)
Sonrasi: POST /api/ratings/batch  body: {titles: [...20 tane]} (x5 kez)
```

**MULAKATTA SORULUR:**
- "N+1 problemi nedir?" -> Her satir icin ayri sorgu. ORM'lerde cok yaygin.
- "Nasil cozersin?" -> Batch/bulk islemler, JOIN, eager loading
- "Batch size nasil belirlenir?" -> Cok kucuk: yeterli optimizasyon yok.
  Cok buyuk: tek istek cok uzun surer. 10-50 arasi genelde ideal.

### 2. IntersectionObserver API

**Ne:** Bir DOM elemaninin viewport'ta (ekranda) gorunup gorunmedigini izler.

**Neden scroll event degil?**

| Ozellik | scroll event | IntersectionObserver |
|---------|-------------|---------------------|
| Tetiklenme | Her piksel kaydirildiginda | Sadece gorunurluk degisince |
| Thread | Main thread (bloklayci) | Asenkron (browser optimize eder) |
| Performans | Kotuye gider (throttle/debounce gerekir) | Dogal olarak iyi |
| Kullanim | Eski yontem | Modern standart |

**Temel Kullanim:**
```javascript
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            // Element ekranda gorunuyor!
            console.log('Gorundu:', entry.target);
            observer.unobserve(entry.target); // Artik izleme
        }
    });
}, {
    threshold: 0.1,    // %10 gorunurse tetikle
    rootMargin: '50px' // 50px onceden tetikle
});

// Izlemeye al
document.querySelectorAll('.kart').forEach(el => observer.observe(el));
```

**Gercek Dunya Kullanim Alanlari:**
- Lazy loading (resimlerin gecikmeli yuklenmesi)
- Infinite scroll (sayfa sonu tespit)
- Analytics (gorunum sayaci)
- Animasyon tetikleme

**MULAKATTA SORULUR:**
- "Lazy loading nasil yapilir?" -> IntersectionObserver ile
- "Performans optimizasyonu?" -> Scroll yerine observer, debounce

### 3. POST vs GET - Ne Zaman Hangisi?

**Temel Kural:** GET = okuma, POST = yazma. Ama her zaman gecerli degil.

**POST Kullanmanin Meşru Sebepleri (okuma isleminde bile):**
1. URL uzunluk siniri (2000-8000 karakter)
2. Karmasik sorgu parametreleri (nested JSON)
3. Hassas veri (arama terimleri URL'de gorunmesin)

**Gercek Ornekler:**
- GraphQL: Tum sorgular POST (karmasik query body)
- ElasticSearch: POST /_search (karmasik arama filtreleri)
- Google Translate: POST (buyuk metin bloklari)

### 4. CSS Position: Absolute / Relative

**Badge overlay icin kullandigimiz teknik:**

```css
.parent {
    position: relative;  /* Referans noktasi */
}

.badge {
    position: absolute;  /* Parent'a gore konumlanir */
    top: 4px;
    right: 4px;
}
```

**Kurallar:**
- `absolute` eleman en yakin `relative` parent'a gore konumlanir
- Parent'ta `relative` yoksa `body`'ye gore konumlanir
- `pointer-events: none` ile alttaki elemanlarin tiklanabilirligini koruruz

### 5. Debounced Batch Pattern

**Kombine teknik:** Debounce + Batch birlikte kullanildi.

```
Kart 1 gorundu (0ms)   -> pendingTitles'a ekle, timer baslat (300ms)
Kart 2 gorundu (50ms)  -> pendingTitles'a ekle, timer sifirla (300ms)
Kart 3 gorundu (100ms) -> pendingTitles'a ekle, timer sifirla (300ms)
...300ms sessizlik...
Timer doldu -> 3 basligi tek batch olarak gonder
```

Eger 20 kart birikirse timer beklemeden hemen gonderilir (max batch size).

### 6. Multi-Level Cache Kaniti (Gercek Veri)

Test sirasinda kanitlanan cache katmanlari:

```
Better Call Saul:
  1. Anasayfa karti -> Batch API -> DB'den geldi (~100ms)
  2. background.js Map'e yazildi
  3. Modal acildi -> Map'ten geldi (1.35ms!)
  4. API'ye HIC SORULMADI
```

Bu 3 katmanli cache (Map -> Redis -> PostgreSQL) mimarisinin
gercek dunyada calistiginin kaniti.

## Kullanilan Teknolojiler

| Teknoloji | Kullanim Yeri |
|-----------|--------------|
| IntersectionObserver | Kart gorunurluk tespiti |
| MutationObserver | Yeni eklenen kartlari tespit |
| Map (JavaScript) | In-memory cache (background.js) |
| Set (JavaScript) | Islenmis kart takibi |
| CSS position: absolute | Badge overlay |
| POST /api/ratings/batch | Toplu rating sorgulama |
| Debounce + Batch | Verimli istek yonetimi |

## Test Sonuclari

- 50 kart islendi, 8 batch istegi ile
- ~%98 basari orani
- In-memory cache: 1.35ms (API'ye gitmeden)
- Badge'ler kartlarin sag ust kosesinde gorunuyor
- Hover'da badge gizleniyor (Netflix CSS'i ile dogal uyum)
