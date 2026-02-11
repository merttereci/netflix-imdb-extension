# ADR-001: Veritabani Olarak PostgreSQL Secimi

## Durum
Kabul Edildi


## Baglam

Netflix IMDB Rating Extension projesi icin bir veritabani secmemiz gerekiyor.

**Gereksinimler:**
- 10 milyon+ film/dizi kaydi depolama
- Hizli metin arama (film adi ile)
- TSV (Tab-Separated Values) formatinda veri import etme
- Ucretsiz veya dusuk maliyetli hosting

## Karar

**PostgreSQL** kullanacagiz.

## Alternatifler

### MongoDB
| Ozellik | Deger |
|---------|-------|
| Tip | NoSQL (Document) |
| Avantaj | Flexible schema, JSON native |
| Dezavantaj | Bu proje icin gereksiz karmasiklik |
| Neden Secilmedi | Verimiz zaten yapisal (flat), NoSQL gereksiz |

### MySQL
| Ozellik | Deger |
|---------|-------|
| Tip | Relational (SQL) |
| Avantaj | Cok yaygin, stabil |
| Dezavantaj | Full-text search PostgreSQL kadar guclu degil |
| Neden Secilmedi | PostgreSQL daha modern ve ozellik zengini |

### SQLite
| Ozellik | Deger |
|---------|-------|
| Tip | Embedded SQL |
| Avantaj | Kurulum gerektirmez, dosya bazli |
| Dezavantaj | 10M+ satir icin yavas, concurrent erisim zayif |
| Neden Secilmedi | Production icin uygun degil |

## Sonuclar

### Olumlu
- **Full-text search:** Native destek, pg_trgm ile fuzzy matching
- **TSV import:** COPY komutu ile hizli bulk import
- **Performans:** B-tree ve GIN index'ler ile hizli sorgular
- **Hosting:** Supabase ile 500MB ucretsiz
- **CV Degeri:** Industri standardi, mulakatlarda sorulan

### Olumsuz
- **Hosting gerekli:** SQLite gibi embedded degil
- **Setup:** MongoDB'den biraz daha karmasik schema

### Notlar
- Supabase uzerinde host edilecek (Free tier: 500MB)
- index title + year composite index ile arama optimize edildi
- Connection pooling gerekirse PgBouncer eklenebilir

## Referanslar
- PostgreSQL Docs: https://www.postgresql.org/docs/
- Supabase: https://supabase.com/
- pg_trgm extension: https://www.postgresql.org/docs/current/pgtrgm.html
