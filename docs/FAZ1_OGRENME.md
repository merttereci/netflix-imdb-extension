# Faz 1: Temel Altyapi - Detayli Ogrenme Dokumani

> Bu dokuman Python bilmeyen biri icin Faz 1'de yapilanlari aciklar.

---

## Icindekiler

1. [Ne Yaptik?](#ne-yaptik)
2. [Kullanilan Teknolojiler](#kullanilan-teknolojiler)
3. [Proje Yapisi](#proje-yapisi)
4. [Dosya Dosya Aciklama](#dosya-dosya-aciklama)
5. [Onemli Terimler Sozlugu](#onemli-terimler-sozlugu)
6. [Kod Ornekleri ve Aciklamalari](#kod-ornekleri-ve-aciklamalari)

---

## Ne Yaptik?

Faz 1'de **backend API'nin iskeletini** olusturduk. Henuz calismiyor cunku:
- Veritabani baglantisi yok (Faz 2'de yapilacak)
- Veritabaninda veri yok (Faz 2'de IMDB verileri yuklenecek)

Ama tum yapi hazir:
- API istekleri alabilecek endpoint'ler
- Veritabani modeli (tablo yapisi)
- Konfigürasyon sistemi

---

## Kullanilan Teknolojiler

### 1. Python
**Nedir?** Programlama dili. Okunmasi kolay, web gelistirmede cok yaygin.

**Neden secildi?** 
- Ogrenilmesi kolay
- Data science ve web'de cok kullaniliyor
- FastAPI gibi modern framework'ler var

### 2. FastAPI
**Nedir?** Python icin web framework (uygulamanin iskeleti).

**Ne yapar?**
- HTTP isteklerini dinler (GET, POST, vs.)
- URL'lere gore fonksiyonlari calistirir
- JSON formatinda cevap dondurur

**Alternatifler:** Flask, Django (daha eski), Express.js (Node.js icin)

**Neden secildi?**
- Cok hizli (async destegi)
- Otomatik dokumantasyon (/docs sayfasi)
- Type checking (hatalari erkenden yakalar)

### 3. SQLAlchemy
**Nedir?** ORM (Object-Relational Mapping) kutuphanesi.

**Ne yapar?**
```
SQL yazmak yerine:
SELECT * FROM movies WHERE title = 'Inception'

Python yazarsin:
Movie.query.filter(Movie.title == 'Inception').first()
```

**Neden kullanilir?**
- SQL bilmeden veritabani islemleri
- Veritabani degisse (MySQL -> PostgreSQL) kod degismez
- Python objeleri ile calisirsin, tablolarla degil

### 4. Pydantic
**Nedir?** Veri dogrulama (validation) kutuphanesi.

**Ne yapar?**
```python
# Kullanici yanlis veri gonderirse hata verir
class MovieRating:
    title: str      # Text olmali
    rating: float   # 0-10 arasi olmali
    year: int       # Sayi olmali
```

**Neden kullanilir?**
- API'ye gelen verileri kontrol eder
- Yanlis formattaki verileri reddeder
- Otomatik hata mesajlari uretir

### 5. PostgreSQL
**Nedir?** Iliskisel veritabani (SQL veritabani).

**Neden secildi?**
- Acik kaynak, ucretsiz
- Buyuk veriler icin uygun (10M+ satir)
- Full-text search destegi (metin arama)
- Industri standardi

---

## Proje Yapisi

```
backend/
│
├── app/                    # Ana uygulama klasoru
│   ├── __init__.py        # Python'a "bu bir paket" der
│   ├── main.py            # Uygulama baslangic noktasi
│   ├── config.py          # Ayarlar (veritabani URL'i vs.)
│   ├── database.py        # Veritabani baglantisi
│   ├── schemas.py         # API icin veri modelleri
│   │
│   ├── models/            # Veritabani tablolari
│   │   ├── __init__.py
│   │   └── movie.py       # Film tablosu
│   │
│   └── routes/            # API endpoint'leri
│       ├── __init__.py
│       └── movies.py      # Film API'leri
│
├── requirements.txt       # Gerekli kutuphaneler
├── .env.example          # Ornek ayar dosyasi
└── README.md             # Proje aciklamasi
```

### Neden Bu Yapi?

| Klasor/Dosya | Amac |
|--------------|------|
| `app/` | Tum uygulama kodu tek yerde |
| `models/` | Veritabani tablolari ayri |
| `routes/` | API endpoint'leri ayri |
| `schemas.py` | API veri modelleri ayri |

Bu ayirima **Separation of Concerns** (Endişelerin Ayrımı) denir.
Her sey kendi yerinde, kod karisik degil.

---

## Dosya Dosya Aciklama

### 1. requirements.txt - Bagimliliklar

```
fastapi==0.109.0          # Web framework
uvicorn[standard]==0.27.0 # Web sunucusu (FastAPI'yi calistirir)
sqlalchemy==2.0.25        # ORM (veritabani)
psycopg2-binary==2.9.9    # PostgreSQL driver
python-dotenv==1.0.0      # .env dosyalarini okur
pydantic==2.5.3           # Veri dogrulama
pydantic-settings==2.1.0  # Ayar yonetimi
```

**Nasilkullanilir?**
```bash
pip install -r requirements.txt
```

---

### 2. main.py - Ana Uygulama

```python
from fastapi import FastAPI

app = FastAPI(title="Netflix IMDB Rating API")

@app.get("/")
def root():
    return {"message": "Merhaba Dunya"}
```

**Satir satir aciklama:**

| Satir | Anlami |
|-------|--------|
| `from fastapi import FastAPI` | FastAPI kutuphanesini ice aktar |
| `app = FastAPI(...)` | Yeni bir FastAPI uygulamasi olustur |
| `@app.get("/")` | "/" adresine GET istegi gelince... |
| `def root():` | ...bu fonksiyonu calistir |
| `return {...}` | JSON olarak bu veriyi dondur |

**CORS Nedir?**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Herkes erisebilir
)
```

Tarayicilar guvenlik icin farkli sitelerden gelen istekleri engeller.
Netflix.com'dan bizim API'mize istek gelmesi icin CORS gerekli.

---

### 3. config.py - Ayarlar

```python
class Settings(BaseSettings):
    database_url: str = "postgresql://localhost:5432/netflix_imdb"
    
    class Config:
        env_file = ".env"
```

**Ne yapar?**
- `.env` dosyasindan ayarlari okur
- Sifreleri kodda yazmak yerine dosyada tutariz
- `.env` dosyasi GitHub'a YUKLENMEZ (guvenlik)

**Ornek .env dosyasi:**
```
DATABASE_URL=postgresql://user:password@supabase.co:5432/db
```

---

### 4. database.py - Veritabani Baglantisi

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Onemli Kavramlar:**

| Terim | Anlami |
|-------|--------|
| Engine | Veritabanina baglantiyi yoneten obje |
| Session | Bir "konusma" - islemler bittikten sonra kapanir |
| yield | Fonksiyon ortasinda degeri don, sonra devam et |

**Neden `yield` kullaniyoruz?**
```
1. Veritabani baglantisi ac
2. Islemi yap
3. Baglanti kapat (hata olsa bile)
```
Bu pattern "context manager" veya "try-finally" olarak bilinir.

---

### 5. models/movie.py - Veritabani Tablosu

```python
from sqlalchemy import Column, String, Integer, Float

class Movie(Base):
    __tablename__ = "movies"
    
    id = Column(Integer, primary_key=True)
    imdb_id = Column(String(20), unique=True)
    title = Column(String(500))
    year = Column(Integer)
    rating = Column(Float)
    votes = Column(Integer)
```

**Bu kod ne yapar?**

Veritabaninda su tabloyu tanimlar:

| Sutun | Tip | Aciklama |
|-------|-----|----------|
| id | Sayi | Benzersiz ID (otomatik artar) |
| imdb_id | Metin | "tt1234567" formatinda |
| title | Metin | Film adi |
| year | Sayi | Yapim yili |
| rating | Ondalik | IMDB puani (8.5 gibi) |
| votes | Sayi | Kac kisi oylamis |

**Index nedir?**
```python
Index('ix_movies_title_year', 'title', 'year')
```

Kitaptaki indeks gibi. "Inception 2010" aramak icin tum tabloyu taramak yerine direkt o sayfaya git.

**Performans farkla:**
- Index olmadan: 10M satirda 5 saniye
- Index ile: 10M satirda 10ms

---

### 6. schemas.py - API Veri Modelleri

```python
from pydantic import BaseModel, Field

class MovieRating(BaseModel):
    imdb_id: str
    title: str
    year: int = None
    rating: float = Field(ge=0, le=10)  # 0-10 arasi
    votes: int
```

**SQLAlchemy Model vs Pydantic Schema:**

| | SQLAlchemy Model | Pydantic Schema |
|-|------------------|-----------------|
| Amac | Veritabani tablosu | API response |
| Nerede | Veritabanina yazilir | Kullaniciya gonderilir |
| Ornek | `Movie` class | `MovieRating` class |

**Neden ikisi de var?**
- Veritabaninda `created_at`, `updated_at` gibi ekstra alanlar var
- API'de bunlari gostermek istemeyiz
- Schema, "neyi gosterecegimizi" belirler

---

### 7. routes/movies.py - API Endpoint'leri

```python
from fastapi import APIRouter, Query

router = APIRouter()

@router.get("/rating")
def get_movie_rating(
    title: str = Query(..., min_length=1),
    year: int = Query(None)
):
    # Veritabanindan film bul
    movie = db.query(Movie).filter(Movie.title == title).first()
    return movie
```

**Endpoint'ler:**

| URL | Metod | Ne Yapar |
|-----|-------|----------|
| `/api/rating?title=Inception&year=2010` | GET | Tek film rating'i |
| `/api/search?q=dark` | GET | Film ara |
| `/api/movie/tt1234567` | GET | IMDB ID ile bul |
| `/api/health` | GET | API calisiyor mu? |

**Query vs Path Parameter:**

```
Query Parameter:  /api/rating?title=Inception&year=2010
                             ↑ ? isareti, anahtar=deger seklinde

Path Parameter:   /api/movie/tt1234567
                            ↑ URL'in parcasi
```

---

## Onemli Terimler Sozlugu

| Terim | Turkce | Aciklama |
|-------|--------|----------|
| API | Uygulama Programlama Arayuzu | Uygulamalar arasi iletisim |
| REST | - | API tasarim standardi |
| Endpoint | Uc nokta | API'nin bir URL'i |
| Framework | Cerceve | Hazir kod altyapisi |
| ORM | Nesne-Iliski Haritalama | SQL yerine Python yazma |
| Schema | Sema | Veri yapisi tanimi |
| Middleware | Ara katman | Istek/cevap arasinda calisan kod |
| CORS | - | Farkli siteler arasi erisim izni |
| Dependency Injection | Bagimlili Enjeksiyonu | Bagimli degisnkleri disaridan verme |
| Session | Oturum | Veritabani ile gecici baglanti |
| Index | Indeks | Veritabaninda hizli arama icin yapi |
| Validation | Dogrulama | Verinin dogru formatta kontrolu |

---

## Kod Ornekleri ve Aciklamalari

### Ornek 1: Basit Endpoint

```python
@app.get("/merhaba")
def merhaba():
    return {"mesaj": "Merhaba Dunya"}
```

**Test:**
```
Tarayicida ac: http://localhost:8000/merhaba
Sonuc: {"mesaj": "Merhaba Dunya"}
```

### Ornek 2: Parametre Alan Endpoint

```python
@app.get("/selam/{isim}")
def selam(isim: str):
    return {"mesaj": f"Selam {isim}!"}
```

**Test:**
```
URL: http://localhost:8000/selam/Mert
Sonuc: {"mesaj": "Selam Mert!"}
```

### Ornek 3: Query Parameter

```python
@app.get("/toplam")
def toplam(a: int, b: int = 0):
    return {"sonuc": a + b}
```

**Test:**
```
URL: http://localhost:8000/toplam?a=5&b=3
Sonuc: {"sonuc": 8}
```

### Ornek 4: Veritabani Sorgusu

```python
def film_bul(title: str):
    # SQL: SELECT * FROM movies WHERE title = 'Inception'
    return db.query(Movie).filter(Movie.title == title).first()
```

---

## Siradaki Adim: Faz 2

Faz 2'de:
1. Gercek veritabani olusturulacak (Supabase)
2. IMDB dataset indirilecek
3. 10M+ film verisi veritabanina yuklenecek
4. API gercekten calisir hale gelecek

---

## Kaynaklar

- FastAPI Dokumantasyonu: https://fastapi.tiangolo.com/
- SQLAlchemy Dokumantasyonu: https://docs.sqlalchemy.org/
- Pydantic Dokumantasyonu: https://docs.pydantic.dev/
- PostgreSQL Dokumantasyonu: https://www.postgresql.org/docs/

---

---

## 7. Derinlemesine Mimari Analiz (Advanced)

### Neden 'Repository Pattern' Kullanmadik?

Buyuk projelerde genellikle `Controller -> Service -> Repository -> Database` katmanlari kullanilir. Biz ise direkt `Route -> Database` yapiyoruz (Active Record benzeri).

**Karar:** Bu proje bir "Extension API" oldugu icin is mantigi (Business Logic) cok az. Sadece veri okuyup donuyoruz. Ekstra katmanlar (Service/Repository) karmasiklik yaratacakti. Eger ileride "Kullanici Yorumlari", "Favori Listeleri" gibi karmasik ozellikler eklersek, Service katmani eklemeliyiz.

### Veritabani Baglanti Havuzu (Connection Pooling)

`database.py` dosyasinda `create_engine` fonksiyonu arkada bir **Connection Pool** yonetir.

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=5,        # Ayni anda 5 acik baglanti
    max_overflow=10     # Yogunlukta ekstra 10 baglantiya izin ver
)
```

**Neden Onemli?**
Her API isteginde veritabanina yeni bir "TCP Handshake" ve "Authentication" yapmak cok pahalidir (50-100ms). Connection pool, acik baglantilari hazir tutar ve gelen istege kiralar. Islem bitince baglanti kapanmaz, havuza doner. Bu sayede DB erisimi <1ms olur.

### Environment Degiskenleri ve Guvenlik

`.env` dosyasi ile calismanin kritik kurallari vardir:

1.  **Git'e Yukleme:** `.gitignore` dosyasinda mutlaka `.env` olmali.
2.  **Type Casting:** `os.getenv` hep string doner. Port numaralari icin `int()` cevrimi yapilmali yoksa uygulama coker.
3.  **Validation:** `pydantic-settings` kutuphanesini bu yuzden kullaniyoruz. Eger `DATABASE_URL` eksikse uygulama hic baslamaz (Fail Fast).

```python
# kotu yaklasim
db_url = os.getenv("DB_URL") # Eger yoksa None doner, hata sonra cikar

# iyi yaklasim (Bizim kullandigimiz)
class Settings(BaseSettings):
    database_url: str # Eksikse Pydantic baslangicta hata firlatir
```

---

## 8. SQLAlchemy: Lazy vs Eager Loading

Faz 1'de basit sorgular attik ama Faz 5'te (Cache) ve ileride karsimiza cikacak bir kavram: **N+1 Sorgu Sorunu**.

Su anki kodumuzda:
```python
movie = db.query(Movie).first()
```
Bu sadece film verisini ceker. Eger film'in turlerini (Genre) baska tabloda tutsaydik (One-to-Many), erismeye calistigimizda SQLAlchemy gidip TEKRAR sorgu atacakti (Lazy Loading).

100 film listelerken her biri icin genre sorgusu atilirsa: 1 (Film listesi) + 100 (Genreler) = 101 sorgu. Veritabani olur.

**Cozum (Eager Loading):**
```python
# joinedload ile tek sorguda hepsini cek
movies = db.query(Movie).options(joinedload(Movie.genres)).all()
```
Bu projede `genres` kolonunu string olarak (`Action, Drama`) tuttugumuz icin bu sorundan bilerek kacindik (Denormalizasyon).

---

## 9. FastAPI vs Digerleri: 2026 Perspektifi

Neden Django veya Flask degil?

| Ozellik | Django | Flask | FastAPI |
|---------|--------|-------|---------|
| Hız | Yavaş | Orta | **Çok Hızlı** (Starlette, Pydantic) |
| Async | Sonradan eklendi | Desteklemez (genelde) | **Native Async** |
| Type Hint | Opsiyonel | Opsiyonel | **Zorunlu** (Python 3.12+) |
| Validation | Form tabanli | Eklenti ile | **Otomatik** (Pydantic) |

**Karar:** 2026 yilinda yeni bir mikroservis veya API yaziyorsaniz, **FastAPI** endustri standardidir. Django sadece cok karmasik admin paneli gerektiren CMS projelerinde tercih edilir.

---

## 10. Kod Okuma Rehberi

Projeyi anlamaya calisiyorsan okuma siran soyle olmali:

1.  `models/` (Veri yapisi) -> Veritabaninda ne var?
2.  `schemas.py` (API kontrati) -> Disariya ne veriyoruz?
3.  `routes/` (Logic) -> Veriyi nasil isliyoruz?
4.  `main.py` (Giris) -> Nasil birlestiriyoruz?

---

*Bu dokuman ogrenme amaclidir.*
