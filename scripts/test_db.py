"""Database test script - veritabanini sorgula"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def test_inception():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT imdb_id, title, year, rating, votes 
            FROM movies 
            WHERE title ILIKE '%inception%' 
            LIMIT 10
        """))
        print("Inception arama sonuclari:")
        for row in result:
            print(f"  {row}")

def test_stats():
    with engine.connect() as conn:
        movies = conn.execute(text("SELECT COUNT(*) FROM movies")).scalar()
        titles = conn.execute(text("SELECT COUNT(*) FROM movie_titles")).scalar()
        print(f"\nToplam film: {movies:,}")
        print(f"Toplam Turkce baslik: {titles:,}")

def test_sample():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT imdb_id, title, year, rating, votes 
            FROM movies 
            ORDER BY votes DESC 
            LIMIT 5
        """))
        print("\nEn populer 5 film:")
        for row in result:
            print(f"  {row}")

if __name__ == "__main__":
    test_stats()
    test_inception()
    test_sample()
    
    # Turkce baslik testi
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM movie_titles WHERE imdb_id = 'tt1375666'
        """))
        print("\nInception Turkce baslik:")
        rows = list(result)
        if rows:
            for row in rows:
                print(f"  {row}")
        else:
            print("  Turkce baslik bulunamadi")

