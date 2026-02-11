"""
Film Baslik Modeli (Lokalize Isimler)

OGRENME NOTU:
- Netflix Turkiye'de filmler Turkce isimlerle gosteriliyor
- IMDB title.akas dataset'i lokalize isimleri icerir
- Bu tablo Turkce isim -> IMDB ID eslestirmesi saglar

TURKCE KARAKTER NOTU:
- PostgreSQL UTF-8 encoding kullanir
- Turkce karakterler: İ, ı, Ğ, ğ, Ş, ş, Ü, ü, Ö, ö, Ç, ç
- Case-insensitive arama icin lower() + collation kullan
"""

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models.movie import Base


class MovieTitle(Base):
    """
    Film Lokalize Baslik Modeli
    
    Bir filmin birden fazla basligi olabilir:
    - Turkce: "Başlangıç"
    - Ingilizce: "Inception"
    - Japonca: "インセプション"
    
    IMDB title.akas.tsv.gz dosyasindan gelir.
    """
    
    __tablename__ = "movie_titles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # IMDB ID - movies tablosuna referans
    imdb_id = Column(String(20), ForeignKey("movies.imdb_id"), nullable=False, index=True)
    
    # Lokalize baslik
    title = Column(String(500), nullable=False)
    search_title = Column(String(500), index=True)  # Hizli arama icin
    
    # Bolge ve dil
    region = Column(String(10))  # TR, US, DE, JP, etc.
    language = Column(String(10))  # tr, en, de, ja, etc.
    
    # Orijinal baslik mi?
    is_original = Column(Boolean, default=False)
    
    # Indexler
    __table_args__ = (
        # Title uzerinde arama icin
        Index('ix_movie_titles_title_lower', 'title'),
        # Region filtresi icin
        Index('ix_movie_titles_region', 'region'),
        # Composite: imdb_id + region
        Index('ix_movie_titles_imdb_region', 'imdb_id', 'region'),
    )
    
    def __repr__(self):
        return f"<MovieTitle {self.imdb_id}: {self.title} ({self.region})>"
