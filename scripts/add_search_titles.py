import sys
from pathlib import Path
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import time

# Backend klasorunu path'e ekle
sys.path.append(str(Path(__file__).parent.parent / 'backend'))

def migrate():
    load_dotenv(Path('backend/.env'))
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("HATA: DATABASE_URL bulunamadi!")
        return

    engine = create_engine(database_url)
    
    def get_normalize_sql(column_name):
        """
        SQL REPLACE fonksiyonlari zinciri olusturur.
        NOT: PostgreSQL'de tek tirnak icin '' (cift) kullanilir.
        """
        sql = column_name
        
        # Ozel karakterler (curly quotes, dashes)
        # Key: Unicode karakter, Value: ASCII karsilik
        special_chars = [
            ('\u2019', "''"),  # Right Single Quotation Mark -> '
            ('\u2018', "''"),  # Left Single Quotation Mark -> '
            ('\u201C', '"'),   # Left Double Quotation Mark -> "
            ('\u201D', '"'),   # Right Double Quotation Mark -> "
            ('\u2013', '-'),   # En Dash -> -
            ('\u2014', '-'),   # Em Dash -> -
        ]
        for special, normal in special_chars:
            # SQL icinde tek tirnak escape: ' -> ''
            sql = f"REPLACE({sql}, '{special}', '{normal}')"
        
        # Turkce karakterler
        turkish_chars = [
            ('Ş', 's'), ('ş', 's'),
            ('İ', 'i'), ('ı', 'i'),
            ('Ç', 'c'), ('ç', 'c'),
            ('Ğ', 'g'), ('ğ', 'g'),
            ('Ü', 'u'), ('ü', 'u'),
            ('Ö', 'o'), ('ö', 'o'),
        ]
        for tr, eng in turkish_chars:
            sql = f"REPLACE({sql}, '{tr}', '{eng}')"
        
        return f"LOWER({sql})"

    print("Veritabani baglantisi kuruldu...")
    
    with engine.connect() as conn:
        conn.execute(text("COMMIT"))
        
        # 1. Movies tablosunu TEMIZLE (Gereksiz kolon siliniyor)
        print("1. Movies tablosundan search_title siliniyor (Clean up)...")
        try:
            conn.execute(text("ALTER TABLE movies DROP COLUMN IF EXISTS search_title"))
            print("   Silindi.")
        except Exception as e:
            print(f"   Hata (onemsiz): {e}")

        # 2. Movie Titles tablosuna kolon ekle ve doldur
        print("2. Movie Titles tablosu hazirlaniyor...")
        conn.execute(text("ALTER TABLE movie_titles ADD COLUMN IF NOT EXISTS search_title VARCHAR(500)"))
        
        print("3. Movie Titles verileri guncelleniyor (Bulk SQL)...")
        start = time.time()
        
        update_titles_sql = f"""
            UPDATE movie_titles 
            SET search_title = {get_normalize_sql('title')}
        """
        print("   SQL:", update_titles_sql[:200], "...")
        conn.execute(text(update_titles_sql))
        conn.commit()
        print(f"   Tamamlandi! Sure: {time.time() - start:.2f} saniye")
        
        # 4. Index Olustur
        print("4. Index olusturuluyor...")
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_movie_titles_search_title ON movie_titles(search_title)"))
        
    print("\nMigration BASARIYLA TAMAMLANDI!")

if __name__ == "__main__":
    migrate()
