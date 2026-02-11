# ADR-008: Netflix Kart Gorunumu ve Cache Stratejisi

**Durum:** Oneri
Kabul Edildi

## Baglam
Projenin nihai amaci, sadece film detayinda degil, Netflix anasayfasindaki tum film kartlarinda (thumbnails) IMDB puanini gostermektir. 
Ancak bu durum ciddi performans ve DOM manipulasyon zorluklari dogurur.

### Zorluklar
1.  **Yuksek Istek Sayisi:** Anasayfada yuzlerce kart ve infinite scroll var. Her kart icin API istegi atilirsa veritabani coker.
2.  **Dinamik DOM:** Netflix kartlari hover oldugunda buyur (`transform: scale`). Yanlis konumlandirma, puanin kaybolmasina veya kaymasina neden olur.
3.  **Film Adi Bulma:** Kartlarda genelde metin olarak film adi yazmaz, sadece resim vardir.

## Karar

### 1. Performans: Redis Cache ve IntersectionObserver
- **Redis Cache:** Populer Netflix icerikleri (yaklasik 500-1000 film) %99 oranda aynidir. Bu veriler Redis'te tutulacak. API yaniti ~10ms'ye indirilecek.
- **IntersectionObserver:** Sadece ekranda gorunur olan (viewport icine giren) kartlar icin API istegi atilacak. Sayfanin altindaki gorunmeyen yukler icin istek atilmayacak.

### 2. Veri Okuma: Aria-Label
- Kartlarin uzerindeki film adi gorsel olsa da, erisilebilirlik (a11y) icin `aria-label` attribute'u bulunur.
- Örn: `<a aria-label="Stranger Things">` veya resim üzerindeki `alt` etiketi.
- Content script bu veriyi okuyarak API'ye soracak.

### 3. DOM Manipulasyonu: Absolute Positioning
- Rating badge'i kartin icindeki ana resim konteynerine (boxart) gore konumlandirilacak.
- CSS: `position: absolute; top: 5px; right: 5px; z-index: 100;`
- Bu sayede kart hover ile buyuse bile (`scale`), badge resimle birlikte orantili olarak hareket edecek.

## Teknik Uygulama Plani (Faz 6)

1.  **Backend:** Redis entegrasyonu ve Cache Middleware yazilmasi.
2.  **Frontend:** `IntersectionObserver` ile kart izleme mekanizmasi.
3.  **Deploy:** Production ortaminda Redis (Upstash) kurulumu.

## Sonuclar
- **Olumlu:** Kullanici deneyimi maksimize edilir (her yerde puan). Performans sorunu Redis ile cozulur.
- **Olumsuz:** Gelistirme eforu yuksektir. DOM degisikliklerine karsi daha kirilgan bir yapi (Netflix HTML yapisini degistirirse bozulabilir).
