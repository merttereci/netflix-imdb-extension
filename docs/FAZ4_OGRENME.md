# Faz 4: Chrome Extension - Ogrenme Notlari

## Ozet
Netflix IMDB Rating Extension basariyla gelistirildi ve calisiyor.

---

## Yapilan Isler

### 1. Extension Altyapisi
- Manifest V3 formati kullanildi
- Service Worker (background.js) ile API iletisimi
- Content Script (content.js) ile Netflix DOM manipulasyonu
- MutationObserver ile dinamik modal izleme

### 2. API Entegrasyonu
- Background script CSP engellerini asiyor
- chrome.runtime.sendMessage ile mesajlasma
- /rating endpoint'ine istek atiliyor

### 3. DOM Manipulasyonu
- `.previewModal--info strong` selector'u calisiyor
- Rating badge modal'a enjekte ediliyor
- IMDB sarisi tema kullanildi

---

## Karsilasilan Sorunlar ve Cozumler

| Sorun | Cozum |
|-------|-------|
| Ikon eksik hatasi | Manifest'ten ikon referanslari kaldirildi |
| Extension context invalidated | Netflix sayfasi hard refresh (`Ctrl+Shift+R`). Gelecekte auto-reconnect eklenecek. |
| Yil uyusmazligi (Stranger Things 2016 vs 2025) | Yil filtresini kaldirdik |
| Curly quote (') vs normal apostrof (') | [COZULDU] API `normalize_turkish` fonksiyonunda curly quote -> straight quote donusumu eklendi. |
| Antoloji Dizileri (Monster: The Ed Gein Story) | Veritabaninda sadece ana dizi adi ("Monster") var. Alt baslikli sezonlar bulunamiyor (Edge Case). |
| TV Series bulunamadi (Solar Opposites) | Veritabaninda olmayan icerikler |

---

## Teknik Ogrenimler

### Chrome Extension Mimarisi
- **Manifest V3:** Service Worker kullanimi (background page yerine)
- **Content Script:** Izole calisir, Netflix JS'ine erismez
- **Mesajlasma:** chrome.runtime.sendMessage async calisir, return true gerekli
- **Context Invalidation:** Extension guncellendiginde content script yetim kalir, sayfa yenilenmeli.

### Karakter Kodlama (Encoding)
- Netflix bazi basliklarda curly quote (`%E2%80%99`) kullaniyor.
- Veritabaninda straight quote (`'`) var.
- API katmaninda normalizasyon yaparak bu sorun cozuldu.

---

---

## 4. Teknik Derinlemesine Bakis (Deep Dive)

### Chrome Extension Mimarisi (Manifest V3)

Google, 2023'te Manifest V2'yi kaldirdi ve V3'e gecti. En buyuk fark **Service Worker** yapisidir.

**Eski (V2):** Background Page. Web sayfasi gibi surekli acik dururdu. Hafiza yerdi.
**Yeni (V3):** Service Worker. Event-driven calisir.
- Mesaj gelince uyanir.
- Isini yapar.
- 30 saniye bos kalinca **UYUR (Terminate)**.

**Karsilastigimiz Sorun (Context Invalidated):**
Extension guncellendiginde veya Service Worker yeniden baslatildiginda, eski Content Script (sayfada gomulu olan) ile baglanti kopuyor.
- **Hata:** `Extension context invalidated`
- **Sebep:** Content Script "yetim" kaliyor.
- **Cozum:** Sayfayi yenilemek (`Ctrl+Shift+R`). Gelecek versiyonda `chrome.runtime.id` kontrolu ile otomatik reconnect yapilabilir.

### Post-Mortem: "Ghost Badge" Bug (Orphan Element)

**Senaryo:**
Kullanici bir filme tiklayip hemen kapatiyor. Radyo butonuna basip ana sayfaya donuyor.
**Hata:** Ekranin sag tarafinda (alakasiz bir yerde) havada asili kalan bir IMDB puani ("7.0") goruluyor.
**Yan Etki:** Sonraki hicbir filmde puan cikmiyor.

**Analiz:**
1.  Modal aciliyor, `handleModalOpen` 500ms gecikmeli tetikleniyor.
2.  Bu surede kullanici modali kapatiyor.
3.  `addRatingBadge` calisiyor ama Modal yok edildigi icin `metadataContainer` (`.previewModal--info`) bulunamiyor.
4.  **Hatali Kod:** `if (!metadataContainer) container = document.body` fallback'i vardi.
5.  Badge `document.body`'ye ekleniyor (`position: fixed`).
6.  `document.body` silinmedigi icin badge sonsuza kadar orada kaliyor.
7.  Sonraki filmler acildiginda `if (document.querySelector('.rating-badge'))` kontrolu, bu hayalet badge'i bulup "Zaten var" diyerek cikiyor.

**Cozum:**
Fallback kaldirildi. Eger container yoksa (modal kapandiysa), islem iptal ediliyor.

---

### Post-Mortem: "Guillermo del Toro's Pinocchio" Bug'i

Bu proje sirasinda karsilastigimiz en ilginc bug.

**Senaryo:**
Kullanici Netflix'te "Pinocchio" filmini aciyor. Extension "Film bulunamadi" diyor.
Ama API'ye gidip "Pinocchio" yazinca bulunuyor.

**Analiz Sureci:**
1.  **Loglama:** Background script'e `console.log(url)` ekledik.
2.  **Fark:**
    - Netflix URL: `...title=Guillermo%20del%20Toro%E2%80%99s%20Pinocchio`
    - Bizim Testimiz: `...title=Guillermo%20del%20Toro%27s%20Pinocchio`
3.  **Unicode Farki:**
    - `%E2%80%99` -> **’** (Right Single Quotation Mark - Curly Quote)
    - `%27` -> **'** (Apostrophe - Straight Quote)
4.  **Veritabani:** Veritabaninda straight quote (`'`) kayitli.

**Cozum:**
API'nin `normalize_turkish` fonksiyonuna sadece Turkce karakterleri degil, noktalama isaretlerini de normalize eden bir satir ekledik:
```python
text = text.replace('\u2019', "'").replace('\u2018', "'")
```
Bu sayede Netflix ne gonderirse gondersin, veritabani formatina donusuyor.

### 5. Edge Case: Antoloji Dizileri ("Monster")

Bazı diziler her sezon farklı bir isim alır (Anthology Series).
- **Netflix:** "Monster: The Ed Gein Story" (Sezon 2 adi)
- **IMDB/DB:** "Monster" (Dizi adi)

Bizim algoritmamız "Exact Match" (Tam Eşleşme) yaptığı için:
`"Monster: The Ed Gein Story" == "Monster"` -> **False**

Bu bir "False Negative" durumudur. Cozumu icin "Fuzzy Search" gerekir ama bu da "False Positive" (Yanlis film eslesmesi) riskini artirir.

---

## 5. Gelecek Mimari: Redis ve Kart Gorunumu (ADR-008)

Şu an sadece film detayına girince (Modal) puan gösteriyoruz. Hedefimiz ana sayfadaki tüm kartlarda (Thumbnail) puan göstermek.

**Zorluklar:**
1.  Ana sayfada 100+ film var. 100 API isteği atarsak veritabani çöker.
2.  Netflix "Infinite Scroll" kullanıyor. Aşağı indikçe yeni filmler gelir.
3.  Kartlar hover olunca büyüyor (`transform: scale`). Puan kayabilir.

**Planlanan Mimari (Faz 6):**
1.  **Redis Cache:** API ile DB arasına Redis girecek. Popüler filmler RAM'den 1ms'de gelecek.
2.  **IntersectionObserver:** Sadece ekranda görünen (viewport) kartlar için istek atılacak.
3.  **Position Absolute:** Puan rozeti, kartın içindeki resim kutusuna (Boxart) göre hizalanacak.

Detaylar için: `docs/adr/ADR-008-netflix-kart-ve-cache-stratejisi.md`

---

## 6. Test Sonuclari

Basarili testler:
- Mama (2013) -> 6.2
- Sisu (2022) -> 6.9
- The Watchers (2024) -> 5.7
- Corpse Bride (2005) -> 7.4
- The Revenant (2015) -> 8.0
- Happiness (2021) -> 7.7
- Guillermo del Toro's Pinocchio -> 7.6 (Curly quote fix sonrasi)

Basarisiz (Bilinen Kisitlamalar):
- Monster: The Ed Gein Story (Antoloji isimlendirme farki)
- Solar Opposites (Veritabaninda yok)

---

*Bu dokuman ogrenme amaclidir.*
