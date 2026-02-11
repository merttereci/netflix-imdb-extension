"""
Veritabani Baglantisi

OGRENME NOTU:
- SQLAlchemy iki mod destekler: Core ve ORM
- Biz ORM kullaniyoruz (daha Pythonic)
- Engine: Veritabani baglantisini yoneten obje
- Session: Her istek icin ayri bir "konusma" - transaction yonetimi

MULAKATTA SORULUR:
- "Connection pooling nedir?" -> Baglantilari yeniden kullanma
- "Transaction nedir?" -> Atomik islem grubu (ya hepsi ya hicbiri)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Engine olustur
# OGRENME NOTU: pool_pre_ping=True baglantinin hala gecerli oldugunu kontrol eder
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Baglanti kontrolu
    echo=settings.debug  # Debug modda SQL sorgularini goster
)

# Session factory
# OGRENME NOTU: autocommit=False -> Her degisiklik icin manuel commit gerekli
# Bu, hatalarda rollback yapabilmemizi saglar
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency injection icin veritabani session'i
    
    OGRENME NOTU - Dependency Injection:
    FastAPI'de dependency injection cok onemli bir pattern.
    Bu fonksiyon her request icin yeni bir session olusturur
    ve request bitince session'i kapatir.
    
    yield kullanimi:
    - yield oncesi: Setup (session olustur)
    - yield: Session'i route'a ver
    - yield sonrasi: Cleanup (session kapat)
    
    Bu pattern "context manager" benzeri calisir.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
