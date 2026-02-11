"""
Netflix IMDB Rating API - FastAPI Backend

Bu dosya FastAPI uygulamasinin ana giris noktasidir.

OGRENME NOTU:
- FastAPI, modern Python web framework'udur
- Async/await destekler (yuksek performans)
- Otomatik OpenAPI dokumantasyonu uretir (/docs)
- Pydantic ile type validation yapar
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import movies
from app.routes import cache_routes
from app.config import settings
from app.redis import init_redis

# FastAPI uygulamasi olustur
app = FastAPI(
    title="Netflix IMDB Rating API",
    description="Netflix'te gosterilen filmler icin IMDB rating'lerini donduren API",
    version="1.0.0"
)

# CORS ayarlari - Chrome Extension'dan istek alabilmek icin gerekli
# OGRENME NOTU: CORS (Cross-Origin Resource Sharing)
# Tarayici guvenlik politikasi, farkli domain'lerden gelen istekleri engeller
# Extension'imiz netflix.com'dan bizim API'mize istek atacagi icin CORS gerekli
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da kisitlanmali
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route'lari ekle
app.include_router(movies.router, prefix="/api", tags=["Movies"])
app.include_router(cache_routes.router, prefix="/api", tags=["Cache"])


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


@app.get("/")
def root():
    """API ana sayfa - basit bir hosgeldin mesaji"""
    return {
        "message": "Netflix IMDB Rating API",
        "docs": "/docs",
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
