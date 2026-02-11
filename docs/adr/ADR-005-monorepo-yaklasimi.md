# ADR-005: Monorepo Yaklasimi

## Durum
Kabul Edildi


## Baglam

Proje iki ana bilesenden olusuyor:
1. Backend API (Python/FastAPI)
2. Chrome Extension (JavaScript)

Bu bilesenleri nasil organize edecegiz?

## Karar

**Monorepo** yaklasimi kullanacagiz - tek repository'de tum kod.

```
extension/
├── backend/          # Python API
├── extension/        # Chrome Extension
├── docs/            # Dokumantasyon
└── scripts/         # Yardimci scriptler
```

## Alternatifler

### Ayri Repository'ler
| Ozellik | Deger |
|---------|-------|
| Yapi | netflix-imdb-api + netflix-imdb-extension |
| Avantaj | Bagimsiz deploy, bagimsiz versioning |
| Dezavantaj | Koordinasyon zor, iki repo yonetimi |
| Neden Secilmedi | Kucuk proje icin gereksiz karmasiklik |

### Monorepo
| Ozellik | Deger |
|---------|-------|
| Yapi | Tek repo, alt klasorler |
| Avantaj | Kolay yonetim, atomic commits |
| Dezavantaj | Buyuk takimlar icin merge conflict |
| Karar | SECILDI |

## Sonuclar

### Olumlu
- **Basitlik:** Tek repo, tek README, tek LICENSE
- **Atomic commits:** Backend + Extension degisikligi tek commit
- **Kolay navigation:** Her sey bir yerde
- **CV/Portfolio:** Tek link paylasimi kolay

### Olumsuz
- **Buyume:** Buyuk takim olunca zorlanabilir (bu proje icin gecerli degil)
- **Deploy:** Farkli deploy pipeline'lari gerekebilir

### Notlar

**Klasor Yapisi:**
```
extension/
├── backend/
│   ├── app/
│   └── requirements.txt
├── extension/        (Faz 4'te olusturulacak)
│   ├── manifest.json
│   └── src/
├── docs/
│   ├── adr/
│   └── FAZ1_OGRENME.md
├── scripts/          (Faz 2'de olusturulacak)
│   └── import_imdb.py
├── AI_TALIMAT.md
├── OGRENME_NOTLARI.md
└── READMEPROTOTIP.md
```

**Deploy Stratejisi:**
- Backend: Render/Railway (backend/ klasoru)
- Extension: Chrome Web Store (extension/ klasoru)
- Her biri ayri deploy edilir ama kod tek yerde

## Referanslar
- Monorepo vs Multi-repo: https://blog.nrwl.io/misconceptions-about-monorepos-monorepo-monolith-df1250d4b03c
