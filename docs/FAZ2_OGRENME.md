# Faz 2: Data Pipeline - Ogrenme Dokumani

> Bu dokuman Faz 2'deki kavramlari, kodlari ve ogrenilenleri aciklar.
> Durum: TAMAMLANDI

## Sonuclar

| Metrik | Deger |
|--------|-------|
| Toplam film | 59,980 |
| Turkce baslik | 23,976 |
| Tahmini boyut | 25.1 MB |
| Yukleme suresi | ~15 dakika |

---

## Icindekiler

1. [Bu Fazda Ne Yapiyoruz?](#bu-fazda-ne-yapiyoruz)
2. [ETL Pattern](#etl-pattern)
3. [Pandas Kutuphanesi](#pandas-kutuphanesi)
4. [Script Aciklamasi](#script-aciklamasi)
5. [Terimler Sozlugu](#terimler-sozlugu)
6. [Karsilasilan Sorunlar](#karsilasilan-sorunlar)

---

## Bu Fazda Ne Yapiyoruz?

IMDB'nin resmi dataset'lerini indirip, isleyip, veritabanina yukluyoruz.

```
IMDB Dataset (TSV dosyalari)
    |
    v
Python Script (Pandas ile isle)
    |
    v
Supabase (PostgreSQL veritabani)
```

**Dosyalar:**
- title.basics.tsv.gz (207 MB) - Film bilgileri
- title.ratings.tsv.gz (7.9 MB) - Puanlar
- title.akas.tsv.gz (455 MB) - Lokalize basliklar

---

## ETL Pattern

ETL = Extract, Transform, Load

| Adim | Anlami | Bu Projede |
|------|--------|------------|
| Extract | Veri cikar | TSV dosyalarini oku |
| Transform | Donustur | Filtrele, birlestir, temizle |
| Load | Yukle | Veritabanina yaz |

Bu pattern veri muhendisliginde (Data Engineering) cok yaygin.

**Mulakatta sorarlar:** "ETL nedir? Ornek verir misin?"

---

## Pandas Kutuphanesi

### Pandas Nedir?

Python'un veri analizi kutuphanesi. Excel tablolari gibi verilerle calismayi saglar.

### Neden Pandas?

| Alternatif | Neden Secilmedi |
|------------|-----------------|
| Pure Python (list, dict) | Yavas, karmasik kod |
| NumPy | Sayisal veriler icin, tablo yapisi yok |
| PySpark | Bu veri boyutu icin gereksiz karmasiklik |
| SQL direkt | Python'da islem esnekligi yok |

### Temel Kavramlar

**DataFrame:** 2 boyutlu tablo (Excel gibi)
```python
import pandas as pd

# DataFrame olustur
df = pd.DataFrame({
    'film': ['Inception', 'Matrix', 'Interstellar'],
    'yil': [2010, 1999, 2014],
    'puan': [8.8, 8.7, 8.6]
})

# Sonuc:
#          film   yil  puan
# 0    Inception  2010   8.8
# 1       Matrix  1999   8.7
# 2  Interstellar 2014   8.6
```

**Series:** Tek sutun
```python
puanlar = df['puan']  # [8.8, 8.7, 8.6]
```

### Dosya Okuma

```python
# CSV oku
df = pd.read_csv('dosya.csv')

# TSV oku (tab ile ayrilmis)
df = pd.read_csv('dosya.tsv', sep='\t')

# Gzip sikistirilmis dosya oku
df = pd.read_csv('dosya.tsv.gz', compression='gzip')
```

### Filtreleme

```python
# Tek kosul
action = df[df['genre'] == 'Action']

# Birden fazla kosul (& = AND, | = OR)
filtered = df[(df['year'] >= 2000) & (df['rating'] > 8.0)]

# isin - birden fazla degerden biri
movies = df[df['type'].isin(['movie', 'tvSeries'])]
```

### Birlestirme (Merge)

```python
# SQL JOIN gibi
# basics + ratings birlestir
merged = basics.merge(
    ratings,
    on='tconst',      # Ortak sutun
    how='inner'       # Sadece her ikisinde olan
)
```

| how | SQL Karsiligi | Anlami |
|-----|---------------|--------|
| inner | INNER JOIN | Sadece eslesenler |
| left | LEFT JOIN | Sol tablonun tamami |
| right | RIGHT JOIN | Sag tablonun tamami |
| outer | FULL OUTER JOIN | Her iki tablonun tamami |

### Chunk Reading (Buyuk Dosyalar)

Dosya cok buyukse, tamamini RAM'e sigmaz. Parcalar halinde oku:

```python
# 100000 satir olarak oku
for chunk in pd.read_csv('buyuk_dosya.csv', chunksize=100000):
    # Her chunk bir DataFrame
    filtered = chunk[chunk['votes'] > 1000]
    process(filtered)
```

**Neden onemli?**
- title.basics: ~10M satir, ~2GB
- RAM'e sigmaz veya sistemi yavaslatir
- Chunk ile parcalar halinde isle

---

## Script Aciklamasi

`scripts/import_imdb.py` dosyasinin adim adim aciklamasi:

### 1. Konfigurasyon

```python
IMDB_DATA_PATH = Path("C:/Users/Mert/Downloads/imdb")
DATABASE_URL = os.getenv("DATABASE_URL")  # .env'den oku
MIN_VOTES = 1000  # Minimum oy filtresi
```

### 2. Tablo Olusturma

```python
def create_tables(engine):
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS movies (...)
    """))
```

**Neden raw SQL?**
- Tablolar henuz yok
- SQLAlchemy modelleri tablolari otomatik olusturmaz (migration lazim)
- Basit projeler icin raw SQL yeterli

### 3. Veri Okuma ve Filtreleme

```python
def load_and_filter_basics(path):
    for chunk in pd.read_csv(..., chunksize=100000):
        # Sadece filmler ve diziler (short, episode degil)
        filtered = chunk[chunk['titleType'].isin(['movie', 'tvSeries'])]
        # Adult icerik disla
        filtered = filtered[filtered['isAdult'] == 0]
```

### 4. Birlestirme

```python
def merge_data(basics, ratings):
    # basics + ratings = tek tablo
    return basics.merge(ratings, on='tconst', how='inner')
```

### 5. Veritabanina Yukleme

```python
def upload_to_database(engine, movies_df):
    movies_df.to_sql('movies', engine, if_exists='append')
```

**to_sql parametreleri:**
- `if_exists='append'` - Mevcut tabloya ekle
- `if_exists='replace'` - Tabloyu sil, yeniden olustur
- `index=False` - DataFrame index'ini sutun olarak ekleme
- `chunksize=1000` - 1000'er satir olarak yukle

---

## Terimler Sozlugu

| Terim | Turkce | Aciklama |
|-------|--------|----------|
| ETL | Cikar, Donustur, Yukle | Veri pipeline pattern'i |
| DataFrame | Veri cercevesi | 2D tablo yapisi |
| Chunk | Parca | Buyuk dosyayi parcalar halinde okuma |
| TSV | Tab-Separated Values | Tab ile ayrilmis degerler |
| CSV | Comma-Separated Values | Virgul ile ayrilmis degerler |
| gzip | - | Sikistirma formati |
| Merge | Birlestirme | Iki tabloyu birlestirme |
| Filter | Filtreleme | Kosullara gore satir secme |
| Index | Indeks | Satir numarasi |

---

## Karsilasilan Sorunlar

### Sorun 1: Supabase DNS Sorunu

**Hata:** `could not translate host name to address`

**Sebep:** Supabase altyapi sorunu - yeni projeler icin DNS kayitlari olusmuyor

**Cozum:** Bekle veya alternatif veritabani kullan

**Ogrenilen:** Cloud servisleri her zaman calismayabilir. Alternatif plan onemli.

### Sorun 2: Path Formati (Windows)

**Hata:** IDE'de renk bozuk gorunumu

**Sebep:** Windows path'leri backslash (`\`) kullaniyor

**Cozum:** Forward slash (`/`) veya raw string (`r"..."`) kullan

```python
# Yanlis (Windows'da sorun cikarabilir)
path = "C:\Users\Mert\Downloads"

# Dogru - raw string
path = r"C:\Users\Mert\Downloads"

# Dogru - forward slash (heryerde calisir)
path = "C:/Users/Mert/Downloads"

# En iyi - pathlib
from pathlib import Path
path = Path("C:/Users/Mert/Downloads")
```

---

## Yararli Kaynaklar

- Pandas Dokumantasyonu: https://pandas.pydata.org/docs/
- Pandas Cheat Sheet: https://pandas.pydata.org/Pandas_Cheat_Sheet.pdf
- SQLAlchemy + Pandas: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html

---

## Siradaki Adimlar

1. Supabase DNS sorunu cozulunce script'i calistir
2. Veriyi yukle
3. Faz 3'e gec (Backend API)

---

---

## 7. Derinlemesine Data Engineering Analizi

### Performans ve Bellek Yonetimi (Chunking)

Neden `chunksize=100000` kullandik?

`title.basics.tsv.gz` dosyasi acildiginda RAM'de 2-3 GB yer kaplar. Python'un Garbage Collector'i ve Pandas'in overhead'i ile bu 8-10 GB'a cikabilir. Eger 8GB RAM'i olan bir bilgisayarda calistirirsaniz bilgisayar kilitlenir (Swap alanina duser).

**Chunking ile:**
1. 100.000 satir oku (~50MB RAM)
2. Islem yap (Filtrele)
3. 2.000 satir kalsin
4. Hafizayi temizle
5. Devam et

Bu yontemle 100GB'lik dosyayi bile 4GB RAM ile isleyebilirsiniz. Buna **Streaming Processing** denir.

### Veritabani Indeksleme Stratejisi (B-Tree)

Script icinde indexes olusturduk:
```sql
CREATE INDEX IF NOT EXISTS ix_movies_title ON movies(title);
CREATE INDEX IF NOT EXISTS ix_movies_imdb_id ON movies(imdb_id);
```

**Neden?**
Veritabani varsayilan olarak "Heap" yapisinda tutulur (sirasiz). Bir film ararken 1. satirdan baslayip 60.000. satira kadar tek tek bakar (Full Table Scan).

Index, tablonun yaninda kucuk bir "B-Tree" (Balanced Tree) olusturur. Bu sayede arama suresi `O(N)` yerine `O(log N)` olur.
- Indexsiz: 60.000 islem
- Indexli: ~16 islem (`2^16 = 65536`)

**Dezavantaji:** Yazma islemi yavaslar (Cunku hem tabloya hem indexe yazilir). Bu yuzden sadece arama yapilan kolonlara index ekledik.

### Snapshot vs Live Data (Veri Tutarliligi)

Kullanici sorusu: *"Film oylari artinca DB guncelleniyor mu?"*

**Cevap:** Hayir. Bizim mimarimiz **Snapshot (Anlik Goruntu)** mimarisidir.
- **Avantaj:** API cok hizli (Disaridan veri cekmiyor). Offline calisabilir.
- **Dezavantaj:** Veri eskimeye mahkumdur.

**Cozum:** Data Pipeline otomasyonu (Airflow veya Cron Job). Her hafta script tekrar calisip veriyi guncellemeli (Upsert mantigi).

---

## 8. Alternatif Teknolojiler: Pandas vs Polars

2026 yilinda Python veri dunyasinda **Polars** firtinasi esiyor. Biz neden Pandas kullandik?

| Ozellik | Pandas | Polars |
|---------|--------|--------|
| Dil | C/Cython | Rust |
| Hız | Orta | Cok Yuksek |
| Bellek | Yuksek | Dusuk |
| Yayginlik | Cok Yaygin | Yukseliyor |

**Neden Pandas Sectik?**
1. Postgres (`psycopg2`) ile uyumu cok daha olgun.
2. Ogrenme notlarinda temel standardi anlatmak istedik.
3. 60K satir icin hiz farki milisaniyeler mertebesinde.

Eger veri 10 Milyon satir olsaydi, kesinlikle Polars secerdik.

---

## 9. Gelecek Olceklenebilirlik (Future Scaling)

Eger veritabanina tum IMDB verisini (10+ Milyon satir) koysaydik ne olurdu?

1.  **Postgres Yetersiz Kalabilirdi:** `LIKE %...%` sorgulari yavaslardi.
2.  **Cozum:** **Elasticsearch** veya **Postgres Full Text Search (tsvector)** kullanilmaliydi.
3.  **Partitioning:** Tabloyu yillara gore bolmek (`movies_2020`, `movies_2021`...) gerekebilirdi.

Bizim projemiz "MVP" (Minimum Viable Product) oldugu icin `votes > 1000` filtresi ile veri setini "Smart optimize" ettik.

---

*Bu dokuman ogrenme amaclidir.*
