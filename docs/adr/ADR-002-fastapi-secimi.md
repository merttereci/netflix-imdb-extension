# ADR-002: Backend Framework Olarak FastAPI Secimi

## Durum
Kabul Edildi


## Baglam

Chrome extension'dan HTTP istekleri alacak bir backend API gerekiyor.

**Gereksinimler:**
- REST API endpoint'leri
- JSON response
- Hizli response time (<100ms)
- Kolay ogrenme egrisi
- Iyi dokumantasyon

## Karar

**Python + FastAPI** kullanacagiz.

## Alternatifler

### Flask (Python)
| Ozellik | Deger |
|---------|-------|
| Tip | Micro framework |
| Avantaj | Basit, minimal, eski ve stabil |
| Dezavantaj | Async native desteklemiyor, dokumantasyon manuel |
| Neden Secilmedi | FastAPI daha modern ve ozellik zengini |

### Django (Python)
| Ozellik | Deger |
|---------|-------|
| Tip | Full-stack framework |
| Avantaj | Batteries-included, admin panel |
| Dezavantaj | Bu proje icin cok agir, overkill |
| Neden Secilmedi | Sadece API lazim, Django gereksiz buyuk |

### Express.js (Node.js)
| Ozellik | Deger |
|---------|-------|
| Tip | Minimal Node.js framework |
| Avantaj | JavaScript ecosystem, non-blocking I/O |
| Dezavantaj | Type safety zayif (TypeScript gerekir) |
| Neden Secilmedi | Python tercih edildi (data science baglantisi) |

### Go (Gin/Echo)
| Ozellik | Deger |
|---------|-------|
| Tip | Compiled language |
| Avantaj | Cok hizli, static typing |
| Dezavantaj | Ogrenme egrisi dik, ecosystem kucuk |
| Neden Secilmedi | Bu proje icin gereksiz karmasiklik |

## Sonuclar

### Olumlu
- **Async destegi:** Native async/await ile yuksek concurrency
- **Otomatik dokumantasyon:** /docs endpoint'i ile Swagger UI
- **Type hints:** Pydantic ile runtime validation
- **Performans:** Flask'tan 3-5x hizli
- **Kolay ogrenme:** Decorator-based routing
- **CV Degeri:** Modern, trend, cok aranan

### Olumsuz
- **Nispeten yeni:** Flask kadar olgun degil (2018'den beri)
- **Ecosystem:** Django/Flask kadar genis degil

### Notlar
- uvicorn ASGI server ile calistirilacak
- Pydantic v2 ile entegre (veri validation)
- OpenAPI/Swagger otomatik uretiliyor

## Referanslar
- FastAPI Docs: https://fastapi.tiangolo.com/
- Uvicorn: https://www.uvicorn.org/
- Pydantic: https://docs.pydantic.dev/
