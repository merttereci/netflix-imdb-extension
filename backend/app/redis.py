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
import time
from app.config import settings

logger = logging.getLogger(__name__)


# Global Redis client - None ise cache devre disi
_redis_client = None

# Son baglanti denemesinin zamani - basarisiz denemeden sonra her istekte
# 5 sn timeout beklememek icin en fazla RETRY_INTERVAL'da bir tekrar deniyoruz
_last_attempt = None  # None: hic denenmedi
RETRY_INTERVAL = 60  # saniye


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
    global _redis_client, _last_attempt
    _last_attempt = time.monotonic()

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

    OGRENME NOTU - Lazy Init (Serverless):
    Vercel gibi serverless ortamlarda startup event'i guvenilir sekilde
    calismayabilir ya da o anki tek bir baglanti hatasi instance omru boyunca
    cache'i kapali birakir. Bu yuzden client yoksa ilk istekte baglanmayi deniyoruz.
    """
    if _redis_client is None and settings.cache_enabled and (
            _last_attempt is None or time.monotonic() - _last_attempt > RETRY_INTERVAL):
        init_redis()
    return _redis_client
