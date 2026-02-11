"""
Pydantic Schemas - API Request/Response modelleri

OGRENME NOTU:
- Pydantic, veri dogrulama (validation) icin kullanilir
- FastAPI ile entegre calisir
- Swagger/OpenAPI dokumantasyonu otomatik uretilir

FARK:
- SQLAlchemy Model -> Veritabani tablosu
- Pydantic Schema -> API request/response formati
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict


class MovieRating(BaseModel):
    """
    Tek bir film rating response'u
    
    OGRENME NOTU:
    Field() ile dokumantasyon ve validation eklenebilir.
    Bu bilgiler /docs sayfasinda gorunur.
    """
    
    imdb_id: str = Field(..., description="IMDB ID (tt1234567 formatinda)")
    title: str = Field(..., description="Film adi")
    year: Optional[int] = Field(None, description="Yapim yili")
    rating: Optional[float] = Field(None, ge=0, le=10, description="IMDB puani (0-10)")
    votes: Optional[int] = Field(None, ge=0, description="Oy sayisi")
    genres: Optional[str] = Field(None, description="Turler (virgul ile ayrilmis)")
    
    class Config:
        # ORM modelden direkt olusturulabilir
        from_attributes = True  # Pydantic v2 icin (eskiden orm_mode=True)


class MovieSearch(BaseModel):
    """Film arama sonucu"""
    
    results: List[MovieRating] = Field(default_factory=list)
    total: int = Field(0, description="Toplam sonuc sayisi")
    query: str = Field(..., description="Arama sorgusu")


class BatchRatingRequest(BaseModel):
    """
    Batch rating istegi - birden fazla filmi tek istekte sorgula
    
    OGRENME NOTU - POST Body vs Query Parameters:
    Birden fazla baslik gondermek icin GET query string yetersiz kalir.
    POST body ile JSON gondermek daha temiz ve URL uzunluk siniri yok.
    
    MULAKATTA SORULUR:
    - "GET vs POST ne zaman kullanilir?" -> GET okuma, POST olusturma/toplu islem
    - "Neden batch?" -> N+1 problem: 100 kart = 100 HTTP istegi yerine 5 istek
    """
    
    titles: List[str] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Sorgulanacak film/dizi basliklari (max 20)"
    )


class BatchRatingResponse(BaseModel):
    """
    Batch rating cevabi
    
    OGRENME NOTU:
    results dict olarak donuyor: { "stranger things": {rating data}, ... }
    Boylece client hangi basligin hangi sonuca denk geldigini bilir.
    """
    
    results: Dict[str, Optional[MovieRating]] = Field(
        default_factory=dict,
        description="Baslik -> rating eslemesi"
    )
    found: int = Field(0, description="Bulunan film sayisi")
    not_found: int = Field(0, description="Bulunamayan film sayisi")


class HealthResponse(BaseModel):
    """API saglik durumu"""
    
    status: str
    version: str
    database: str = "unknown"


class ErrorResponse(BaseModel):
    """
    Hata response'u
    
    OGRENME NOTU:
    Standart hata formati kullanmak API'yi kullanmayi kolaylastirir.
    Client (extension) her zaman ayni formatta hata bekler.
    """
    
    error: str = Field(..., description="Hata mesaji")
    detail: Optional[str] = Field(None, description="Detayli aciklama")
    status_code: int = Field(..., description="HTTP status kodu")
