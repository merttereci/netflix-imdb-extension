"""
Redis Baglanti Modulu

OGRENME NOTU - Redis Baglanti Yonetimi:
- Redis baglantisi uygulama basladiginda kurulur
- Baglanti hatalarinda API calismaya devam eder (graceful fallback)
- Bu "fail-open" stratejisi: cache yoksa DB'den devam et

MULAKATTA SORULUR:
- "Cache servisi duserse ne olur?" -> Fail-open: DB'den devam eder, kullanici fark etmez
- "Singleton pattern nedir?" -> get_redis_client her zaman ayni instance'i doner
"""

import redis
import logging
from app.config import settings

logger = logging.getLogger(__name__)


# Global Redis client - None ise cache devre disi
_redis_client = None


def init_redis():
    """
    Redis baglantisini baslat.
    
    OGRENME NOTU:
    - redis.from_url() URL'deki bilgilerle baglanti kurar
    - decode_responses=True: Redis byte doner, biz string istiyoruz
    - ping() ile baglanti test edilir
    - Hata olursa None doner -> cache devre disi, API calismaya devam eder
    
    OGRENME NOTU - SSL ve Upstash:
    Upstash Redis URL'i rediss:// ile baslar (SSL/TLS baglanti).
    Python redis kutuphanesi varsayilan olarak SSL sertifika dogrulamasi yapar.
    Upstash kendi sertifikasini yonetir, bu yuzden ssl_cert_reqs="none" 
    ayarini eklememiz gerekiyor. Aksi halde baglanti basarisiz olur.
    """
    global _redis_client
    
    if not settings.cache_enabled:
        logger.info("Cache devre disi (CACHE_ENABLED=false)")
        return None
    
    try:
        # Upstash icin SSL ayarlari
        # rediss:// URL'lerinde ssl=True otomatik aktif olur
        # ssl_cert_reqs="none" -> sertifika dogrulamasi yapma (Upstash icin gerekli)
        client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=3,
            ssl_cert_reqs="none",  # Upstash sertifika dogrulamasi gerektirmez
        )
        client.ping()
        _redis_client = client
        logger.info(f"Redis baglanti basarili: {settings.redis_url[:40]}...")
        return client
    except Exception as e:
        logger.warning(f"Redis baglanti BASARISIZ (API cache'siz devam edecek): {e}")
        _redis_client = None
        return None


def get_redis_client():
    """
    Redis client singleton dondur.
    None donerse cache kullanilmayacak.
    """
    return _redis_client
