"""
Netflix IMDB Rating API - FastAPI Backend

Bu dosya FastAPI uygulamasinin ana giris noktasidir.

OGRENME NOTU:
- FastAPI, modern Python web framework'udur
- Async/await destekler (yuksek performans)
- Otomatik OpenAPI dokumantasyonu uretir (bu projede kapali, API herkese acik degil)
- Pydantic ile type validation yapar
"""

from fastapi import Depends, FastAPI

from app.auth import require_api_key
from app.routes import movies
from app.routes import cache_routes
from app.config import settings
from app.redis import init_redis

# FastAPI uygulamasi olustur
# /docs, /redoc ve /openapi.json kapali: tarayicidan X-API-Key gonderilemedigi icin
# anahtarla korunamiyorlar, acik kalirlarsa API'nin tum yapisini gosterirler.
app = FastAPI(
    title="Netflix IMDB Rating API",
    description="Netflix'te gosterilen filmler icin IMDB rating'lerini donduren API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# CORS middleware yok.
# OGRENME NOTU: CORS (Cross-Origin Resource Sharing)
# Tarayici, bir web sayfasinin baska bir domain'e attigi istegin cevabini
# ancak sunucu CORS header'lari donerse okumasina izin verir.
# Eklentide API'ye istek atan yerler background.js (service worker) ve popup.js;
# ikisi de eklentinin kendi sayfasi. manifest.json'daki host_permissions sayesinde
# bu istekler CORS'a takilmaz. content.js API'ye dogrudan istek atmiyor, background'a mesaj gonderiyor.
# CORS header'i donmemek, web sayfalarindaki JavaScript'in API'yi kullanmasini da engeller.

# Route'lari ekle: /api/health disindaki her endpoint X-API-Key ister
app.include_router(movies.router, prefix="/api", tags=["Movies"], dependencies=[Depends(require_api_key)])
app.include_router(cache_routes.router, prefix="/api", tags=["Cache"], dependencies=[Depends(require_api_key)])


# Uygulama basladiginda Redis'i baslat
@app.on_event("startup")
def startup_event():
    """
    OGRENME NOTU - Startup Event:
    FastAPI uygulamasi basladiginda calisir.
    Redis baglantisini burada kuruyoruz.
    Baglanti basarisiz olursa API yine calisir (cache'siz).
    """
    init_redis()


@app.get("/", dependencies=[Depends(require_api_key)])
def root():
    """API ana sayfa - basit bir hosgeldin mesaji"""
    return {
        "message": "Netflix IMDB Rating API",
        "health": "/api/health"
    }


@app.get("/api/health")
def health_check():
    """
    API saglik kontrolu
    
    OGRENME NOTU:
    Health check endpoint'leri production'da onemlidir.
    Load balancer'lar bu endpoint'i kullanarak sunucunun 
    calisip calismadigini kontrol eder.
    """
    return {"status": "healthy", "version": "1.0.0"}
