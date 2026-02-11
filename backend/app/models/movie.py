"""
Veritabani Modelleri

OGRENME NOTU:
- SQLAlchemy bir ORM (Object-Relational Mapping) kutuphanesidir
- Python class'lari ile veritabani tablolarini tanimlariz
- SQL yazmadan veritabani islemleri yapabiliriz

MULAKATTA SORULUR:
- "ORM nedir?" -> Veritabani tablolarini Python objeleri olarak temsil etme
- "N+1 problemi nedir?" -> Her kayit icin ayri sorgu atma hatasi
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# Base class - tum modeller bundan turetilir
Base = declarative_base()


class Movie(Base):
    """
    Film/Dizi modeli
    
    IMDB dataset'inden gelen verileri tutar.
    
    OGRENME NOTU - Indexler:
    Index, veritabaninda arama hizlandirmak icin kullanilir.
    Kitaptaki "indeks" gibi dusun - tum sayfalar yerine direkt konuya git.
    
    PERFORMANS:
    - Index OLMADAN: Full table scan (yavas)
    - Index ILE: B-tree lookup (hizli)
    """
    
    __tablename__ = "movies"
    
    # Primary key - benzersiz tanimlayici
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # IMDB ID (tt1234567 formatinda)
    imdb_id = Column(String(20), unique=True, nullable=False, index=True)
    
    # Film bilgileri
    title = Column(String(500), nullable=False)
    original_title = Column(String(500))
    year = Column(Integer, index=True)  # Index: yila gore arama hizli olsun
    
    # Rating bilgileri
    rating = Column(Float)  # IMDB puani (0-10)
    votes = Column(Integer)  # Oy sayisi
    
    # Ek bilgiler
    runtime_minutes = Column(Integer)
    genres = Column(String(200))  # Virgul ile ayrilmis: "Action,Drama"
    title_type = Column(String(50))  # movie, tvSeries, tvEpisode, etc.
    
    # Composite index - title + year ile arama cok hizli olacak
    # OGRENME NOTU: Netflix'ten gelen veri "Inception 2010" seklinde
    # Bu index tam olarak bu arama icin optimize edilmis
    __table_args__ = (
        Index('ix_movies_title_year', 'title', 'year'),
    )
    
    def __repr__(self):
        return f"<Movie {self.imdb_id}: {self.title} ({self.year}) - {self.rating}>"
    
    def to_dict(self):
        """Model'i dictionary'e cevir - API response icin"""
        return {
            "imdb_id": self.imdb_id,
            "title": self.title,
            "year": self.year,
            "rating": self.rating,
            "votes": self.votes,
            "genres": self.genres,
            "runtime_minutes": self.runtime_minutes
        }
