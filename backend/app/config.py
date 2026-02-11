"""
Uygulama Konfigurasyonu

OGRENME NOTU:
- Environment variable'lar hassas bilgileri (sifre, API key) koddan ayirmak icindir
- pydantic-settings ile type-safe config yapilabilir
- .env dosyasi git'e EKLENMEMELI (.gitignore'a ekle)
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Uygulama ayarlari
    
    OGRENME NOTU:
    BaseSettings sinifi environment variable'lari otomatik okur.
    Ornegin DATABASE_URL env var'i settings.database_url olarak erisilebilir.
    """
    
    # Veritabani
    database_url: str = "postgresql://localhost:5432/netflix_imdb"
    
    # Redis Cache ayarlari
    # OGRENME NOTU:
    # Upstash Redis URL'i rediss:// (SSL) ile baslar, lokal Redis redis:// ile baslar
    redis_url: str = "redis://localhost:6379"
    cache_ttl: int = 3600  # Cache suresi (saniye) - 1 saat
    cache_enabled: bool = True  # Cache acik/kapali
    
    # API ayarlari
    api_title: str = "Netflix IMDB Rating API"
    debug: bool = False  # Production'da False, lokalde .env'de DEBUG=true yap
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """
    Settings singleton pattern
    
    OGRENME NOTU:
    @lru_cache() decorator'u fonksiyonun sonucunu cache'ler.
    Her cagirisinda yeni Settings olusturmak yerine ayni instance'i dondurur.
    Bu bir "singleton pattern" ornegi - mulakatta sorulabilir!
    """
    return Settings()


# Global settings instance
settings = Settings()
