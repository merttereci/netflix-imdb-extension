"""
Cache Routes - Cache Yonetim Endpoint'leri

OGRENME NOTU:
Bu endpoint'ler gelistirme ve debug icin kullanilir.
Production'da /cache/flush gibi tehlikeli endpoint'ler
authentication ile korunmali veya kapatilmali.
"""

from fastapi import APIRouter
from app.utils.cache import get_cache_stats
from app.redis import get_redis_client

router = APIRouter()


@router.get(
    "/cache/stats",
    summary="Cache istatistikleri",
    description="Redis cache hit/miss sayilari ve baglanti durumu"
)
def cache_stats():
    """
    Cache istatistiklerini dondur.
    
    OGRENME NOTU:
    Bu tarz monitoring endpoint'leri production'da onemlidir.
    Cache hit ratio dusukse, TTL veya key stratejisi gozden gecirilmeli.
    
    Ideal hit ratio: %80+ (cok sorgu cache'ten donmeli)
    """
    stats = get_cache_stats()
    
    total = stats["hits"] + stats["misses"]
    if total > 0:
        stats["hit_ratio"] = round(stats["hits"] / total * 100, 1)
    else:
        stats["hit_ratio"] = 0.0
    
    return stats


@router.delete(
    "/cache/flush",
    summary="Cache temizle (Gelistirme icin)",
    description="Tum cache'i temizler. DIKKAT: Production'da kullanma!"
)
def cache_flush():
    """
    Tum cache'i temizle.
    
    OGRENME NOTU:
    flushdb() Redis'teki tum key'leri siler.
    Bu islem geri alinamaz!
    Production'da bu endpoint authentication ile korunmali.
    """
    client = get_redis_client()
    if not client:
        return {"message": "Redis bagli degil", "flushed": False}
    
    try:
        client.flushdb()
        return {"message": "Cache temizlendi", "flushed": True}
    except Exception as e:
        return {"message": f"Hata: {e}", "flushed": False}
