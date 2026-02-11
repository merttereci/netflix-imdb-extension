# ADR 007: Arama Performansi ve Turkce Karakter Optimizasyonu

**Durum:** Kabul Edildi

## Bagiamsal

Projemizdeki film arama ozelligi (`/api/search`) Turkce karakterlere duyarli olmali. Ornegin kullanici "Baslangic" yazdiginda "Başlangıç" filmini bulmali.

PostgreSQL `ILIKE` operatoru ASCII duyarsizdir (case-insensitive) ama Turkce karakterleri (ş->s, ı->i) eslestirmez.

Ilk cozum olarak tum veriyi RAM'e cekip Python icinde `normalize_turkish` fonksiyonu ile karsilastirdik. Ancak:
1. Veri seti buyudukce RAM kullanimi artacak.
2. Her arama icin 60K+ kayit donguye sokuluyor (CPU intensive).
3. Veritabani indexleri kullanilamiyor.

## Karar

Veritabanina normalize edilmis bir arama sutunu (`search_title`) eklemeye karar verdik.

1. Sadece `movie_titles` tablosuna `search_title` sutunu eklenecek.
2. Bu sutun, basligin Turkce karakterlerden arindirilmis ve kucuk harfe cevrilmis halini tutacak.
   - Ornek Title: "Başlangıç"
   - Search Title: "baslangic"
3. Bu sutun uzerine veritabani index'i (`INDEX`) eklenecek.
4. API sorgulari bu sutun uzerinden EXACT MATCH (tam eslesme) ile yapilacak: 
   `WHERE search_title = 'baslangic'`

## Sonuclar

### Olumlu
- **Performans:** Index kullanildigi icin arama milisaniyeler surer.
- **Olceklenebilirlik:** Milyonlarca kayit olsa bile RAM tuketimi artmaz.
- **CPU:** Normalizasyon sadece sorgu parametresi icin 1 kere yapilir.

### Olumsuz
- **Depolama:** Veritabaninda ekstra sutun oldugu icin disk alani artar (onemsiz miktarda).
- **Bakim:** Veri eklerken/guncellerken `search_title` alaninin da guncellenmesi gerekir.

## Uygulama Plani

1. Migration scripti (`add_search_titles.py`) ile mevcut veriler guncellenecek.
2. API kodu (`movies.py`) SQL tabanli aramaya gore guncellenecek.
