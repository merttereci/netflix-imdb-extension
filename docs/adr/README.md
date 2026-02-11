# Architecture Decision Records (ADR)

Bu klasor projedeki mimari kararlarin kayitlarini icerir.

## ADR Nedir?

ADR'lar, yazilim projelerinde alinan onemli kararlarin **neden** alindini dokumante eder.

## Format

Her ADR su bolumlerden olusur:
- **Durum**: Kabul edildi / Reddedildi / Oneri
- **Baglam**: Problemi tanimlar
- **Karar**: Ne yaptik?
- **Alternatifler**: Diger secenekler
- **Sonuclar**: Olumlu/olumsuz etkiler

## ADR Listesi

| ADR | Baslik | Durum |
|-----|--------|-------|
| [ADR-001](ADR-001-postgresql-secimi.md) | PostgreSQL Secimi | Kabul Edildi |
| [ADR-002](ADR-002-fastapi-secimi.md) | FastAPI Secimi | Kabul Edildi |
| [ADR-003](ADR-003-redis-cache.md) | Redis Cache | Kabul Edildi (Opsiyonel) |
| [ADR-004](ADR-004-imdb-dataset.md) | IMDB Dataset Kullanimi | Kabul Edildi |
| [ADR-005](ADR-005-monorepo-yaklasimi.md) | Monorepo Yaklasimi | Kabul Edildi |
| [ADR-006](ADR-006-lokalize-baslik-destegi.md) | Lokalize Baslik Destegi | Kabul Edildi |

## Yeni ADR Ekleme

1. `ADR-XXX-konu-adi.md` formatinda dosya olustur
2. Template'i kopyala ve doldur
3. Bu README'deki listeye ekle

## Template

```markdown
# ADR-XXX: [Baslik]

## Durum
[Kabul Edildi / Reddedildi / Oneri / Kismen Kabul]

## Tarih
[Tarih]

## Baglam
[Problemin aciklamasi]

## Karar
[Ne yapildi/yapilacak]

## Alternatifler
[Diger secenekler ve neden secilmedigi]

## Sonuclar
### Olumlu
- ...

### Olumsuz
- ...

### Notlar
- ...
```
