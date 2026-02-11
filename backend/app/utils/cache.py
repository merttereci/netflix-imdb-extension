"""
Cache Utility - Redis Cache Helper Fonksiyonlari

OGRENME NOTU - Cache-Aside Pattern:
Bu dosya Cache-Aside (Lazy Loading) pattern'ini uygular:
1. Istek gelir -> cache'e bak
2. Varsa (HIT) -> direkt don
3. Yoksa (MISS) -> DB'den cek -> cache'e yaz -> don

MULAKATTA SORULUR:
- "Cache-Aside ne zaman kullanilir?" -> Okuma agirlikli isler (bizim senaryomuz)
- "Write-Through ne zaman kullanilir?" -> Yazma sonrasi cache guncellemek gerektiginde
- "Cache key nasil tasarlanir?" -> Tutarli, normalize, collision'siz

ONEMLI KAVRAM - Cache Key Tasarimi:
Key ornekleri:
  "rating:inception" -> Inception filminin rating sonucu
  "movie:tt1375666" -> IMDB ID ile film bilgisi
  "search:dark" -> "dark" arama sonuclari

Key'lerin tutarli olmasi icin title normalize edilir (lowercase, ASCII).
"""

import json
from typing import Optional, Any
from app.redis import get_redis_client
from app.config import settings


# Cache istatistikleri (uygulama hafizasinda tutuluyor)
_cache_stats = {
    "hits": 0,
    "misses": 0,
}


def get_cache_stats() -> dict:
    """Cache istatistiklerini dondur"""
    client = get_redis_client()
    stats = dict(_cache_stats)
    stats["enabled"] = settings.cache_enabled
    stats["connected"] = client is not None
    
    if client:
        try:
            stats["total_keys"] = client.dbsize()
        except Exception:
            stats["total_keys"] = -1
    else:
        stats["total_keys"] = 0
    
    return stats


def cache_get(key: str) -> Optional[Any]:
    """
    Cache'ten veri oku.
    
    OGRENME NOTU:
    - Redis'te her sey string olarak saklanir
    - JSON.loads ile tekrar Python dict'e donusturuyoruz
    - Key yoksa veya Redis baglantisi yoksa None dondurur
    
    Returns:
        Veri varsa dict, yoksa None
    """
    client = get_redis_client()
    if not client:
        return None
    
    try:
        data = client.get(key)
        if data:
            _cache_stats["hits"] += 1
            return json.loads(data)
        else:
            _cache_stats["misses"] += 1
            return None
    except Exception as e:
        print(f"[Cache] Okuma hatasi (key={key}): {e}")
        _cache_stats["misses"] += 1
        return None


def cache_get_multi(keys: list[str]) -> dict[str, Any]:
    """
    Birden fazla key icin cache'ten veri oku (MGET).
    
    OGRENME NOTU - Batch Optimization:
    - 20 tane GET istegi atmak yerine 1 tane MGET atariz.
    - Network round-trip suresini 20 kat iyilestirir (teorik olarak).
    - Redis single-threaded oldugu icin, cok sayida kucuk komut gondermek yerine
      tek buyuk komut gondermek throughput'u (islem kapasitesi) arttirir.
    
    Returns:
        Bulunan kayitlarin dict hali: {key: value}
    """
    client = get_redis_client()
    if not client or not keys:
        return {}
    
    try:
        # Redis MGET: Tek seferde n tane key sor
        values = client.mget(keys)
        
        results = {}
        hits = 0
        misses = 0
        
        for key, value in zip(keys, values):
            if value:
                results[key] = json.loads(value)
                hits += 1
            else:
                misses += 1
        
        _cache_stats["hits"] += hits
        _cache_stats["misses"] += misses
        
        return results
        
    except Exception as e:
        print(f"[Cache] MGET hatasi: {e}")
        return {}


def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """
    Cache'e veri yaz.
    
    OGRENME NOTU - TTL (Time To Live):
    - Verinin cache'te ne kadar sure kalacagini belirler
    - TTL dolunca Redis otomatik siler
    - Bu sayede eski veri birikmez
    - Bizim projede 3600 saniye (1 saat) kullaniyoruz
    - Neden 1 saat? IMDB rating'leri sik degismiyor
    
    Args:
        key: Cache anahtari (ornegin "rating:inception")
        value: Saklanacak veri (dict)
        ttl: Sure (saniye), None ise config'teki default kullanilir
    
    Returns:
        Basarili ise True
    """
    client = get_redis_client()
    if not client:
        return False
    
    try:
        ttl = ttl or settings.cache_ttl
        serialized = json.dumps(value)
        client.setex(key, ttl, serialized)
        return True
    except Exception as e:
        print(f"[Cache] Yazma hatasi (key={key}): {e}")
        return False


def cache_delete(key: str) -> bool:
    """Cache'ten veri sil"""
    client = get_redis_client()
    if not client:
        return False
    
    try:
        client.delete(key)
        return True
    except Exception as e:
        print(f"[Cache] Silme hatasi (key={key}): {e}")
        return False


def make_rating_key(title: str) -> str:
    """
    Rating sorgusu icin cache key olustur.
    
    OGRENME NOTU - Key Normalize:
    Ayni film farkli sekillerde yazilabilir:
    - "Inception", "INCEPTION", "inception" -> hepsi ayni key olmali
    - normalize_turkish zaten bunu yapiyor, biz de ayni fonksiyonu kullaniyoruz
    """
    from app.utils.turkish import normalize_turkish
    normalized = normalize_turkish(title)
    return f"rating:{normalized}"


def make_movie_key(imdb_id: str) -> str:
    """IMDB ID ile film icin cache key"""
    return f"movie:{imdb_id}"


def make_search_key(query: str) -> str:
    """Arama sorgusu icin cache key"""
    from app.utils.turkish import normalize_turkish
    normalized = normalize_turkish(query)
    return f"search:{normalized}"
