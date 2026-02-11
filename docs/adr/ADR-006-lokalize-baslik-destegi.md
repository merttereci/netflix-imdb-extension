# ADR-006: Lokalize Baslik Destegi (title.akas)

## Durum
Kabul Edildi


## Baglam

Netflix Turkiye'de film/dizi isimleri Turkce gosteriliyor:
- Netflix: "Başlangıç" -> IMDB: "Inception"
- Netflix: "Esaretin Bedeli" -> IMDB: "The Shawshank Redemption"

Sadece `primaryTitle` ile arama yaparsak esleme basarisiz olur.

## Karar

**title.akas.tsv.gz** dataset'ini kullanarak lokalize baslik tablosu ekleyecegiz.

## Teknik Detaylar

### Yeni Tablo: movie_titles

```sql
CREATE TABLE movie_titles (
    id SERIAL PRIMARY KEY,
    imdb_id VARCHAR(20) REFERENCES movies(imdb_id),
    title VARCHAR(500) NOT NULL,
    region VARCHAR(10),      -- TR, US, DE, etc.
    language VARCHAR(10),    -- tr, en, de, etc.
    is_original BOOLEAN DEFAULT FALSE
);

CREATE INDEX ix_movie_titles_title ON movie_titles(title);
CREATE INDEX ix_movie_titles_region ON movie_titles(region);
```

### Arama Stratejisi

```
1. Turkce baslik ile ara (region=TR)
2. Bulunamazsa orijinal baslik ile ara
3. Bulunamazsa fuzzy match dene
```

## Turkce Karakter Sorunlari

| Karakter | Sorun | Cozum |
|----------|-------|-------|
| İ, ı | Buyuk/kucuk i farki | Unicode normalization |
| Ğ, ğ | Ozel karakter | UTF-8 encoding |
| Ş, ş | Ozel karakter | UTF-8 + collation |
| Ü, ü, Ö, ö | Diaeresis | UTF-8 |

### PostgreSQL Cozumu

```sql
-- Turkce collation
CREATE COLLATION turkish (
    provider = icu,
    locale = 'tr-TR'
);

-- Veya case-insensitive arama
CREATE EXTENSION unaccent;
SELECT * FROM movie_titles 
WHERE unaccent(lower(title)) = unaccent(lower('Başlangıç'));
```

## Alternatifler

### Sadece primaryTitle Kullanma
- Dezavantaj: Turkce isimler bulunmaz
- Karar: REDDEDILDI

### Tum Diller Dahil
- Dezavantaj: 1.5GB veri, cok buyuk
- Karar: REDDEDILDI

### Sadece TR + Orijinal
- Avantaj: Kucuk veri seti, ilgili diller
- Karar: SECILDI

## Sonuclar

### Olumlu
- Netflix TR isimleri bulunur
- Turkce karakter destegi
- Daha iyi kullanici deneyimi

### Olumsuz
- Ekstra tablo, ekstra storage
- Import suresi artar
- Karmasiklik artar

### Notlar
- Sadece region=TR ve is_original=1 kayitlari import edilecek
- UTF-8 encoding zorunlu
- PostgreSQL Turkish collation kullanilacak

## Referanslar
- IMDB Datasets: https://developer.imdb.com/non-commercial-datasets/
- PostgreSQL Collation: https://www.postgresql.org/docs/current/collation.html
- Unicode Normalization: https://unicode.org/reports/tr15/
