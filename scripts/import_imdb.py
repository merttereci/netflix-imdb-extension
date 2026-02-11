"""
IMDB Data Pipeline - Veri Isleme ve Yukleme Script'i

OGRENME NOTU:
Bu script IMDB dataset'lerini okur, isler ve Supabase'e yukler.

ETL (Extract, Transform, Load) pattern'i:
- Extract: TSV dosyalarini oku
- Transform: Filtrele, birlestir, temizle
- Load: Veritabanina yukle

KULLANIM:
    python scripts/import_imdb.py

GEREKSINIMLER:
    pip install pandas sqlalchemy psycopg2-binary python-dotenv tqdm
"""

import os
import sys
from pathlib import Path

# Proje root'unu path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from tqdm import tqdm

# .env dosyasini yukle
load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

# Konfigurasyon
IMDB_DATA_PATH = Path("C:/Users/Mert/Downloads/imdb")  # Forward slash kullan
DATABASE_URL = os.getenv("DATABASE_URL")

# Filtre ayarlari
MIN_VOTES = 1000  # Minimum oy sayisi
TITLE_TYPES = ['movie', 'tvSeries', 'tvMiniSeries']  # Dahil edilecek tipler


def create_tables(engine):
    """
    Veritabani tablolarini olustur
    
    OGRENME NOTU:
    SQLAlchemy ile raw SQL calistirabilirsin.
    text() fonksiyonu SQL injection'a karsi koruma saglar.
    """
    print("[INFO] Tablolar olusturuluyor...")
    
    with engine.connect() as conn:
        # movies tablosu
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS movies (
                id SERIAL PRIMARY KEY,
                imdb_id VARCHAR(20) UNIQUE NOT NULL,
                title VARCHAR(500) NOT NULL,
                original_title VARCHAR(500),
                year INTEGER,
                rating FLOAT,
                votes INTEGER,
                runtime_minutes INTEGER,
                genres VARCHAR(200),
                title_type VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS ix_movies_imdb_id ON movies(imdb_id);
            CREATE INDEX IF NOT EXISTS ix_movies_title ON movies(title);
            CREATE INDEX IF NOT EXISTS ix_movies_year ON movies(year);
        """))
        
        # movie_titles tablosu (lokalize basliklar)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS movie_titles (
                id SERIAL PRIMARY KEY,
                imdb_id VARCHAR(20) NOT NULL,
                title VARCHAR(500) NOT NULL,
                region VARCHAR(10),
                language VARCHAR(10),
                is_original BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (imdb_id) REFERENCES movies(imdb_id) ON DELETE CASCADE
            );
            
            CREATE INDEX IF NOT EXISTS ix_movie_titles_imdb_id ON movie_titles(imdb_id);
            CREATE INDEX IF NOT EXISTS ix_movie_titles_title ON movie_titles(title);
            CREATE INDEX IF NOT EXISTS ix_movie_titles_region ON movie_titles(region);
        """))
        
        conn.commit()
    
    print("[OK] Tablolar olusturuldu!")


def load_and_filter_basics(path: Path) -> pd.DataFrame:
    """
    title.basics.tsv.gz dosyasini oku ve filtrele
    
    OGRENME NOTU - Pandas Chunk Reading:
    Buyuk dosyalari parcalar halinde okumak memory tasarrufu saglar.
    chunksize parametresi her seferinde kac satir okunacagini belirler.
    """
    print("[INFO] title.basics.tsv.gz okunuyor...")
    
    # Sadece gerekli sutunlari oku (memory tasarrufu)
    usecols = ['tconst', 'titleType', 'primaryTitle', 'originalTitle', 
               'startYear', 'runtimeMinutes', 'genres', 'isAdult']
    
    chunks = []
    total_rows = 0
    filtered_rows = 0
    
    # Chunk chunk oku
    for chunk in tqdm(pd.read_csv(
        path / 'title.basics.tsv.gz',
        sep='\t',
        compression='gzip',
        usecols=usecols,
        dtype={'startYear': str, 'runtimeMinutes': str},  # \N degerler icin string
        chunksize=100000,
        na_values='\\N'
    ), desc="Basics"):
        total_rows += len(chunk)
        
        # Filtrele
        filtered = chunk[
            (chunk['titleType'].isin(TITLE_TYPES)) &
            (chunk['isAdult'] == 0)
        ]
        
        filtered_rows += len(filtered)
        chunks.append(filtered)
    
    df = pd.concat(chunks, ignore_index=True)
    print(f"[OK] Basics: {total_rows:,} satirdan {filtered_rows:,} kayit alindi")
    
    return df


def load_ratings(path: Path) -> pd.DataFrame:
    """title.ratings.tsv.gz dosyasini oku"""
    print("[INFO] title.ratings.tsv.gz okunuyor...")
    
    df = pd.read_csv(
        path / 'title.ratings.tsv.gz',
        sep='\t',
        compression='gzip'
    )
    
    # Minimum oy filtresi
    df = df[df['numVotes'] >= MIN_VOTES]
    
    print(f"[OK] Ratings: {len(df):,} kayit (votes >= {MIN_VOTES})")
    return df


def load_turkish_titles(path: Path, valid_ids: set) -> pd.DataFrame:
    """
    title.akas.tsv.gz dosyasindan Turkce basliklari al
    
    OGRENME NOTU:
    valid_ids parametresi ile sadece bizim veritabanimizda olan
    filmlerin lokalize basliklarini aliyoruz. Bu memory ve storage tasarrufu saglar.
    """
    print("[INFO] title.akas.tsv.gz okunuyor (sadece TR)...")
    
    usecols = ['titleId', 'title', 'region', 'language', 'isOriginalTitle']
    
    chunks = []
    
    for chunk in tqdm(pd.read_csv(
        path / 'title.akas.tsv.gz',
        sep='\t',
        compression='gzip',
        usecols=usecols,
        dtype={'isOriginalTitle': str},
        chunksize=100000,
        na_values='\\N'
    ), desc="Akas"):
        # Sadece TR bolgesi VE bizim filmlerimiz
        filtered = chunk[
            (chunk['region'] == 'TR') &
            (chunk['titleId'].isin(valid_ids))
        ]
        
        if len(filtered) > 0:
            chunks.append(filtered)
    
    if chunks:
        df = pd.concat(chunks, ignore_index=True)
        print(f"[OK] Turkish titles: {len(df):,} kayit")
        return df
    else:
        print("[WARN] Turkce baslik bulunamadi!")
        return pd.DataFrame()


def merge_data(basics: pd.DataFrame, ratings: pd.DataFrame) -> pd.DataFrame:
    """
    basics ve ratings tablolarini birlestir
    
    OGRENME NOTU - Pandas Merge:
    SQL'deki JOIN islemine denk gelir.
    inner join: Sadece her iki tabloda olan kayitlar
    """
    print("[INFO] Veriler birlestiriliyor...")
    
    merged = basics.merge(ratings, left_on='tconst', right_on='tconst', how='inner')
    
    print(f"[OK] Birlestirildi: {len(merged):,} kayit")
    return merged


def prepare_movies_df(df: pd.DataFrame) -> pd.DataFrame:
    """Veritabanina yuklemek icin DataFrame'i hazirla"""
    
    # Sutun isimlerini degistir
    result = pd.DataFrame({
        'imdb_id': df['tconst'],
        'title': df['primaryTitle'],
        'original_title': df['originalTitle'],
        'year': pd.to_numeric(df['startYear'], errors='coerce').astype('Int64'),
        'rating': df['averageRating'],
        'votes': df['numVotes'],
        'runtime_minutes': pd.to_numeric(df['runtimeMinutes'], errors='coerce').astype('Int64'),
        'genres': df['genres'],
        'title_type': df['titleType']
    })
    
    # NaN degerleri temizle
    result = result.dropna(subset=['imdb_id', 'title'])
    
    return result


def prepare_titles_df(df: pd.DataFrame) -> pd.DataFrame:
    """Lokalize basliklar icin DataFrame'i hazirla"""
    
    result = pd.DataFrame({
        'imdb_id': df['titleId'],
        'title': df['title'],
        'region': df['region'],
        'language': df['language'],
        'is_original': df['isOriginalTitle'].apply(lambda x: x == '1' if pd.notna(x) else False)
    })
    
    return result


def upload_to_database(engine, movies_df: pd.DataFrame, titles_df: pd.DataFrame):
    """
    Verileri veritabanina yukle
    
    OGRENME NOTU - Pandas to_sql:
    DataFrame'i direkt SQL tablosuna yazabilirsin.
    if_exists='append' mevcut tabloya ekler.
    chunksize performans icin onemli.
    """
    print("[INFO] Veriler yukleniyor...")
    
    # Movies tablosu
    print(f"  [UPLOAD] movies: {len(movies_df):,} kayit yukleniyor...")
    movies_df.to_sql(
        'movies',
        engine,
        if_exists='append',
        index=False,
        chunksize=1000,
        method='multi'
    )
    print("  [OK] movies yuklendi!")
    
    # Movie titles tablosu
    if len(titles_df) > 0:
        print(f"  [UPLOAD] movie_titles: {len(titles_df):,} kayit yukleniyor...")
        titles_df.to_sql(
            'movie_titles',
            engine,
            if_exists='append',
            index=False,
            chunksize=1000,
            method='multi'
        )
        print("  [OK] movie_titles yuklendi!")


def main():
    """Ana fonksiyon"""
    print("=" * 60)
    print("IMDB Data Pipeline")
    print("=" * 60)
    
    # Veritabani baglantisi kontrol
    if not DATABASE_URL:
        print("[ERROR] DATABASE_URL bulunamadi!")
        print("   backend/.env dosyasini kontrol et.")
        sys.exit(1)
    
    print(f"[CONFIG] Veri klasoru: {IMDB_DATA_PATH}")
    print(f"[CONFIG] Min votes: {MIN_VOTES}")
    print(f"[CONFIG] Title types: {TITLE_TYPES}")
    print()
    
    # Engine olustur
    engine = create_engine(DATABASE_URL)
    
    # Tablolari olustur
    create_tables(engine)
    print()
    
    # Verileri oku
    basics = load_and_filter_basics(IMDB_DATA_PATH)
    ratings = load_ratings(IMDB_DATA_PATH)
    print()
    
    # Birlestir
    merged = merge_data(basics, ratings)
    print()
    
    # Movies DataFrame hazirla
    movies_df = prepare_movies_df(merged)
    print(f"[INFO] Final movies: {len(movies_df):,} kayit")
    
    # Turkce basliklar
    valid_ids = set(movies_df['imdb_id'].tolist())
    turkish = load_turkish_titles(IMDB_DATA_PATH, valid_ids)
    titles_df = prepare_titles_df(turkish) if len(turkish) > 0 else pd.DataFrame()
    print()
    
    # Boyut tahmini
    movies_size_mb = movies_df.memory_usage(deep=True).sum() / 1024 / 1024
    titles_size_mb = titles_df.memory_usage(deep=True).sum() / 1024 / 1024 if len(titles_df) > 0 else 0
    print(f"[INFO] Tahmini boyut: {movies_size_mb + titles_size_mb:.1f} MB")
    print()
    
    # Kullanici onayi
    response = input("Yuklemeye devam edilsin mi? (e/h): ")
    if response.lower() != 'e':
        print("Iptal edildi.")
        sys.exit(0)
    
    # Yukle
    upload_to_database(engine, movies_df, titles_df)
    
    print()
    print("=" * 60)
    print("[DONE] TAMAMLANDI!")
    print("=" * 60)
    
    # Ozet
    with engine.connect() as conn:
        movies_count = conn.execute(text("SELECT COUNT(*) FROM movies")).scalar()
        titles_count = conn.execute(text("SELECT COUNT(*) FROM movie_titles")).scalar()
    
    print(f"[RESULT] movies: {movies_count:,} kayit")
    print(f"[RESULT] movie_titles: {titles_count:,} kayit")


if __name__ == "__main__":
    main()
