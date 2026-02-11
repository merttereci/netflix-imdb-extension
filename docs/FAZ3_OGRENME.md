# Faz 3: Backend API - Ogrenme Dokumani

> Bu dokuman Faz 3'teki kavramlari, kodlari ve ogrenilenleri aciklar.
> Durum: TAMAMLANDI

## Sonuclar

| Endpoint | Durum | Ornek |
|----------|-------|-------|
| GET /api/health | Calisiyor | {status: "healthy"} |
| GET /api/rating | Calisiyor | ?title=Inception -> rating: 8.8 |
| GET /api/search | Calisiyor | ?q=dark+knight -> 3 sonuc |
| GET /api/movie/{id} | Calisiyor | /tt1375666 -> Inception |

---

## 1. FastAPI Nedir?

FastAPI, modern Python web framework'u. Flask'a benzer ama daha hizli.

**Ozellikleri:**
- Async/await destegi (yuksek performans)
- Otomatik dokumantasyon (/docs sayfasi)
- Type validation (Pydantic ile)
- Dependency injection

**Ornek:**
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/hello")
def hello():
    return {"message": "Merhaba"}
```

---

## 2. Endpoint Nedir?

API'nin erisim noktasi. Her endpoint bir URL + HTTP metodu.

| HTTP Metodu | Anlam | Ornek |
|-------------|-------|-------|
| GET | Veri oku | /api/movie/tt123 |
| POST | Veri olustur | /api/movie (body ile) |
| PUT | Veri guncelle | /api/movie/tt123 |
| DELETE | Veri sil | /api/movie/tt123 |

Biz sadece GET kullaniyoruz (okuma API'si).

---

## 3. Pydantic Schema Nedir?

Request/Response formatini tanimlar. Validation yapar.

```python
from pydantic import BaseModel

class MovieRating(BaseModel):
    imdb_id: str
    title: str
    rating: float
    
    class Config:
        from_attributes = True  # ORM model'den olusturulabilir
```

**Fark:**
- SQLAlchemy Model -> Veritabani tablosu
- Pydantic Schema -> API formati

---

## 4. Dependency Injection Nedir?

Bir fonksiyonun ihtiyaci olan seyleri disaridan almasi.

```python
def get_rating(db: Session = Depends(get_db)):
    # db otomatik enjekte edilir
    return db.query(Movie).first()
```

**Neden onemli:**
- Test edilebilirlik (mock db verebilirsin)
- Kod tekrari onlenir
- Session yonetimi otomatik

---

## 5. CORS Nedir?

Cross-Origin Resource Sharing. Tarayici guvenlik politikasi.

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tum domain'ler
    allow_methods=["*"],  # Tum metodlar
)
```

**Neden gerekli:**
- Extension netflix.com'dan bizim API'mize istek atacak
- Farkli domain = farkli origin
- CORS olmadan tarayici engeller

---

## Turkce Karakter ve Arama Optimizasyonu (ADR-007)

Netflix entegrasyonu icin "Baslangic" -> "Inception" eslesmesi kritikti. Iki farkli yontem denedik:

### Yontem 1: RAM Tabanli Arama (Python Loop) - [BASARISIZ]
Tum filmleri (`db.query(Movie).all()`) cekip, Python icinde loop ile `normalize_turkish` fonksiyonundan gecirdik.
- **Sorun:** 60.000 kayit icin bile yavas. 100 kullanici ayni anda girse sunucu kilitlenir (RAM ve CPU darboğazi).
- **Ders:** Veritabani islemlerini ASLA Python tarafina tasima (N+1 veya Full Table Scan in Memory hatasi).

### Yontem 2: Veritabani Tabanli Arama (Optimized) - [BASARILI]
Veritabanina `search_title` adinda, verinin "temizlenmis" (ASCII, lowercase) halini tutan bir kolon ekledik.

1. **Migration:** `add_search_titles.py` ile veritabanindaki "Başlangıç" verisini "baslangic" olarak bu kolona yazdik.
2. **Sorgu:**
   ```python
   # Exact Match (Tam Eslesme)
   db.query(MovieTitle).filter(MovieTitle.search_title == 'baslangic')
   ```
   
**Neden Exact Match?**
Netflix bize filmin TAM adini veriyor ("Inception" veya "Başlangıç"). Kullanici aramasi yapmiyoruz ("Incep..." gibi). Bu yuzden `ILIKE` veya `CONTAINS` yerine ESITTIR (`==`) kullandik. Bu sayede "The Beginning" gibi alakasiz filmler gelmiyor, sadece aradigimiz film (Inception) geliyor.

**Sonuc:**
- 0.01 saniye sorgu suresi (Index sayesinde)
- Dusuk RAM kullanimi
- Dogru sonuc (Exact match)

---

## 6. Karsilasilan Sorunlar ve Cozumleri
 
| Sorun | Sebebi | Cozum |
|-------|--------|-------|
| `ModuleNotFoundError` | venv aktif degildi | `pip install -r requirements.txt` |
| Turkce arama bos donuyor (`q=Başlangıç`) | DB'de 'Başlangıç' var, sorguda 'Baslangic' gidiyor (Encoding) | `search_title` kolonu eklenip normalize edildi |
| "Beginning" arayinca Inception cikmiyor | "Beginning" iceren cok fazla film var, limit doluyor | `Exact Match` yapilarak sadece tam eslesen film getirildi |
| `pydantic.ValidationError` | DB'den gelen obje Pydantic semasina uymuyor | ORM objeleri icin `from_attributes = True` eklendi |

---

## 7. Ogrenilen Kavramlar

**Mulakat sorulari:**
- "REST API nedir?" -> HTTP metodlari ile kaynak yonetimi
- "GET vs POST farki?" -> GET okuma, POST olusturma
- "Dependency Injection nedir?" -> Bagimliliklarin disaridan enjekte edilmesi
- "CORS nedir?" -> Cross-origin istek izin yonetimi

**Arastirilacak:**
- [ ] FastAPI middleware sistemi
- [ ] Rate limiting nasil eklenir
- [ ] API versiyonlama stratejileri

---

## 8. Detayli Arama Mantigi (Search Logic)

Backend'in en karmasik kismi burasi. Iki farkli ihtiyacimiz var:

### Senaryo A: Rating Bulma (`/api/rating`)
- **Amac:** Netflix'teki "Inception" filminin puanini bulmak.
- **Yontem:** **Exact Match (Tam Eslesme)**
- **Neden?** Eger "Partial Match" (Icinde gecen) yaparsak, "Inception" aradigimizda "Inception: The Beginning" gibi yan sanayi filmler gelebilir. Biz %100 dogru filmi istiyoruz.
- **Kod:** `filter(Movie.title == title)` (Esittir cift esittir ile)

### Senaryo B: Arama Kutusu (`/api/search`)
- **Amac:** Kullanici "dark" yazinca icinde dark gecenleri bulmak.
- **Yontem:** **Partial Match (Esnek Eslesme)**
- **Kod:** `filter(Movie.title.contains(q))` veya `ilike` (Case insensitive like)

---

## 9. Turkce Karakter ve Normalizasyon (Derin Bakis)

`utils/turkish.py` dosyasindaki `normalize_turkish` fonksiyonu projenin gizli kahramani.

**Sorun:**
1. Veritabaninda: `Başlangıç`
2. Netflix URL/API: `Baslangic` veya `BASLANGIC`
3. Netflix UI (Curly Quote): `Guillermo del Toro’s` (Egik kesme)
4. Veritabani (Straight Quote): `Guillermo del Toro's` (Duz kesme)

**Cozum Algoritmasi:**
1.  Metni al.
2.  **Curly Quote Fix:** `’` gordugun yere `'` koy. (Gecmis hatalardan ogrendik!)
3.  **Turkce Map:** `ş->s`, `ı->i`, `ğ->g` donusumu yap.
4.  **Lowercase:** Hepsini kucult.
5.  Sonuc: `guillermo del toro's` == `guillermo del toro's`.

Bu sayede:
- `İSTANBUL` -> `istanbul`
- `IŞIK` -> `isik`
- `Pinocchio’s` -> `pinocchio's`

Hepsi tek bir standarta (ASCII Lowercase) indirgenir ve oyle karsilastirilir.

---

## 10. FastAPI Dependency Injection (Bagimlilik Enjeksiyonu)

`Depends(get_db)` sihri nedir?

```python
def get_movie(db: Session = Depends(get_db)):
    pass
```

FastAPI burada **"Context Manager"** yonetir:
1.  Istek geldigi an `get_db()` calisir -> Baglanti acilir.
2.  Fonksiyon calisir, veri cekilir.
3.  Fonksiyon bitince (return edince) -> `finally: db.close()` calisir.

Eger bunu elle yapmaya calissaydik (`db = SessionLocal()`) ama kapatmayi unutsaydik, 10-15 istek sonra veritabani "Too many connections" hatasi verip kilitlenirdi. `Depends` bunu garanti altina alir.

---

## 11. Pydantic ve Veri Guvenligi

API'ye gelen veriler `schemas.py` icindeki siniflar tarafindan denetlenir.

**Ornek Saldiri:**
Kullanici `limit` parametresine `-100` veya `1000000` gonderirse ne olur?

Kodumuzda:
```python
limit: int = Query(50, ge=1, le=100)
```
- `ge=1`: Greater or Equal 1 (En az 1)
- `le=100`: Less or Equal 100 (En cok 100)

FastAPI bunu otomatik kontrol eder. Eger kullanici `limit=10000` gonderirse kodumuz hic calismaz, FastAPI direkt `422 Unprocessable Entity` hatasi doner. Bu da sunucumuzu **ReDoS (Regex DoS)** ve **Memory Exhaustion** saldirilarindan korur.

---

*Bu dokuman ogrenme amaclidir.*
