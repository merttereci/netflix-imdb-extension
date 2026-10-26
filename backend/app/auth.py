"""
API Anahtari Kontrolu

OGRENME NOTU:
Canli API herkese acik degil; IMDb verisi ticari olmayan kullanim kosullariyla geliyor.
/api/health disindaki tum endpoint'ler X-API-Key header'i ister.
Gecerli anahtarlar API_KEYS ortam degiskeninde virgulle ayrilmis liste olarak durur.
Boylece her kisiye ayri anahtar verilir ve gerektiginde tek biri iptal edilebilir.
"""

import secrets
from typing import Optional

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# API_KEYS="anahtar1,anahtar2" -> ["anahtar1", "anahtar2"]
VALID_KEYS = [key.strip() for key in settings.api_keys.split(",") if key.strip()]

if not VALID_KEYS:
    # Bos liste hicbir anahtari kabul etmez; API yanlislikla acik kalmaz
    print("[Auth] API_KEYS tanimli degil, korumali endpoint'lerin hepsi reddedilecek")


def require_api_key(api_key: Optional[str] = Security(api_key_header)) -> None:
    """
    X-API-Key header'ini gecerli anahtarlarla karsilastir, eslesmezse 401 don.

    OGRENME NOTU - Timing Attack:
    Normal == karsilastirmasi ilk farkli karakterde durur; cevap suresinden
    anahtar tahmin edilebilir. secrets.compare_digest her zaman ayni surede calisir.
    Eslesme bulunsa da dongu bitirilir, boylece sure anahtarin sirasina bagli olmaz.
    """
    matched = False
    if api_key:
        provided = api_key.encode()
        for key in VALID_KEYS:
            matched |= secrets.compare_digest(provided, key.encode())

    if not matched:
        raise HTTPException(status_code=401, detail="Gecersiz veya eksik API anahtari")
