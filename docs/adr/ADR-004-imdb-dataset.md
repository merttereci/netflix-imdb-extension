# ADR-004: IMDB Dataset Kullanimi

## Durum
Kabul Edildi


## Baglam

Netflix'teki filmler icin IMDB puanlarini gostermek istiyoruz.
Bu verileri nereden alacagiz?

**Secenekler:**
1. IMDB'nin resmi dataset'leri
2. Ucuncu parti API (OMDb, TMDb)
3. Web scraping

## Karar

**IMDB'nin resmi dataset'lerini** kullanacagiz.

Kaynak: https://datasets.imdbws.com/

## Alternatifler

### OMDb API
| Ozellik | Deger |
|---------|-------|
| Avantaj | Hazir API, kolay entegrasyon |
| Dezavantaj | Gunluk limit (1000 istek), ucuncu parti bagimliligi |
| Neden Secilmedi | Kendi API'mizi yazmak istiyoruz (CV icin) |

### TMDb API
| Ozellik | Deger |
|---------|-------|
| Avantaj | Zengin veri, ucretsiz |
| Dezavantaj | IMDB puani yok, kendi rating sistemi var |
| Neden Secilmedi | IMDB puani istiyoruz |

### Web Scraping
| Ozellik | Deger |
|---------|-------|
| Avantaj | Her veri cekilebilir |
| Dezavantaj | YASADISI, IP ban, TOS ihlali |
| Neden Secilmedi | Legal degil |

### IMDB Official Datasets
| Ozellik | Deger |
|---------|-------|
| Avantaj | Resmi, guncel, legal (kisisel kullanim) |
| Dezavantaj | Ticari kullanim icin lisans gerekli |
| Karar | SECILDI |

## Sonuclar

### Olumlu
- **Legal:** Kisisel/egitim kullanimi serbest
- **Guncel:** Her gun guncelleniyor
- **Kapsamli:** 10M+ film/dizi
- **Ucretsiz:** Indirmek ucretsiz
- **CV Degeri:** "10M satirlik veri seti isladim" denebilir

### Olumsuz
- **Ticari kisitlama:** Urun olarak satilamaz (lisans gerekli)
- **Islem gerekli:** TSV parse etmek, DB'ye yuklemek lazim
- **Boyut:** ~700MB (compressed), islem suresi

### Notlar

**Legal Durum:**
```
Kisisel kullanim: ✅ SERBEST
Egitim amacli: ✅ SERBEST
Ticari kullanim: ❌ LISANS GEREKLI
```

**Dataset Dosyalari:**

| Dosya | Icerik | Boyut |
|-------|--------|-------|
| title.basics.tsv.gz | Film bilgileri | ~700MB |
| title.ratings.tsv.gz | Puanlar | ~25MB |
| name.basics.tsv.gz | Oyuncular | ~700MB |

Bu proje icin sadece `title.basics` ve `title.ratings` kullanilacak.

## Referanslar
- IMDB Datasets: https://developer.imdb.com/non-commercial-datasets/
- Kullanim sartlari: https://help.imdb.com/article/imdb/general-information/can-i-use-imdb-data-in-my-software/G5JTRESSHJBBHTGX
