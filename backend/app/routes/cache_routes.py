"""
Cache Routes - Cache Yonetim Endpoint'leri

OGRENME NOTU:
Bu endpoint'ler gelistirme ve debug icin kullanilir ve sadece okuma yapar.
Cache'i silen endpoint'ler production'da kimlik dogrulamasiz acik birakilmamali.
"""

from fastapi import APIRouter
from app.utils.cache import get_cache_stats

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
