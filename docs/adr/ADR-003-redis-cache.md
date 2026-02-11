# ADR-003: Redis Cache Kullanimi

## Durum
Kabul Edildi (Opsiyonel)


## Baglam

API response surelerini iyilestirmek ve veritabani yukunu azaltmak icin cache mekanizmasi dusunuluyor.

**Sorular:**
- Cache gerekli mi?
- Hangi cache teknolojisi?
- Ne zaman implement edilmeli?

## Karar

**Redis** kullanilacak, ancak **opsiyonel** ve **sonradan eklenecek**.

Baslangicta cache olmadan calisacak, gerekirse eklenecek.

## Alternatifler

### Cache Kullanmama
| Ozellik | Deger |
|---------|-------|
| Avantaj | Basitlik, az karmasiklik |
| Dezavantaj | Her istek veritabanina gider |
| Karar | Baslangic icin yeterli |

### In-Memory Cache (Python lru_cache)
| Ozellik | Deger |
|---------|-------|
| Avantaj | Ekstra servis yok, basit |
| Dezavantaj | Server restart'ta kaybolur, multi-instance'da paylasilmaz |
| Karar | Kucuk projeler icin uygun |

### Memcached
| Ozellik | Deger |
|---------|-------|
| Avantaj | Basit, hizli |
| Dezavantaj | Redis kadar ozellik zengini degil |
| Karar | Redis daha genis kullanim alani |

### Redis
| Ozellik | Deger |
|---------|-------|
| Avantaj | TTL, veri yapilari, pub/sub, persistence |
| Dezavantaj | Ekstra servis yonetimi |
| Karar | SECILDI |

## Sonuclar

### Olumlu
- **Performans:** Ayni sorgu <1ms (DB: 10-50ms)
- **DB yuku:** Tekrar eden sorgular DB'ye gitmez
- **TTL:** Otomatik cache temizligi
- **CV Degeri:** Cache pattern bilgisi degerli

### Olumsuz
- **Karmasiklik:** Ekstra servis yonetimi
- **Cache Invalidation:** "Veri degisti, cache'i temizle" problemi
- **Maliyet:** Upstash free tier limiti (10K/gun)

### Notlar
- **Implementasyon zamani:** Faz 3 sonrasi (API calistiktan sonra)
- **Hosting:** Upstash (serverless Redis, 10K istek/gun free)
- **Pattern:** Cache-aside (lazim olunca cache'e yaz)
- **TTL:** 24 saat (IMDB verileri nadiren degisir)

## Cache Pattern

```
Istek geldi -> Cache'de var mi?
                |
        Evet   |   Hayir
        |           |
   Cache'den don   DB'den cek
                    |
                Cache'e yaz
                    |
                  Dondur
```

## Referanslar
- Redis Docs: https://redis.io/docs/
- Upstash: https://upstash.com/
- Cache Patterns: https://docs.aws.amazon.com/whitepapers/latest/database-caching-strategies-using-redis/caching-patterns.html
