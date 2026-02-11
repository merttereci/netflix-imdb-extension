"""
Turkce Karakter Normalizasyonu

OGRENME NOTU:
Turkce karakterler (ş, ı, ç, ğ, ü, ö) ile ASCII karsiliklari (s, i, c, g, u, o)
arasinda eslestirme yapmamiz gerekiyor. Cunku:
- Netflix "Başlangıç" gonderebilir
- Kullanici "Baslangic" yazabilir
- Veritabaninda "Başlangıç" var

Bu modul her iki taraftaki metni normalize ederek eslestirme sagliyor.
"""

# Turkce -> ASCII karakter eslestirmesi
TURKISH_CHAR_MAP = {
    'ş': 's', 'Ş': 'S',
    'ı': 'i', 'İ': 'I',
    'ç': 'c', 'Ç': 'C',
    'ğ': 'g', 'Ğ': 'G',
    'ü': 'u', 'Ü': 'U',
    'ö': 'o', 'Ö': 'O',
}


def normalize_turkish(text: str) -> str:
    """
    Turkce karakterleri ASCII karsiliklarina donusturur.
    
    Ornek:
        "Başlangıç" -> "baslangic"
    """
    if not text:
        return text
    
    # Smart quotes -> Straight quotes
    result = text.replace('\u2019', "'").replace('\u2018', "'")

    for tr_char, ascii_char in TURKISH_CHAR_MAP.items():
        result = result.replace(tr_char, ascii_char)
    
    return result.lower()


def turkish_match(text1: str, text2: str) -> bool:
    """
    Iki metni Turkce karakter farki olmadan karsilastirir.
    
    Ornek:
        turkish_match("Başlangıç", "Baslangic") -> True
        turkish_match("Yıldızlararası", "yildizlararasi") -> True
    """
    return normalize_turkish(text1) == normalize_turkish(text2)


def turkish_contains(haystack: str, needle: str) -> bool:
    """
    needle, haystack icinde var mi kontrol eder (Turkce karakter farki olmadan).
    
    Ornek:
        turkish_contains("Başlangıç", "baslang") -> True
    """
    return normalize_turkish(needle) in normalize_turkish(haystack)
