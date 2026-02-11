/**
 * Netflix IMDB Extension - Background Script (Service Worker)
 * 
 * OGRENME NOTU - Manifest V3'te Service Worker:
 * - Manifest V2'de "background page" vardi (surekli acik)
 * - Manifest V3'te "service worker" var (event-driven, gerektiginde uyanir)
 * - Bu sayede bellek kullanimi duser
 * 
 * FAZ 5 EKLEME - In-Memory Cache:
 * Service Worker icinde bir Map objesi ile son istenen rating'leri tutuyoruz.
 * Ayni film icin 5 dakika icinde tekrar API'ye sormadan cache'ten donuyoruz.
 * Bu, Redis cache'in USTUNE ek bir katman - "multi-level cache" ornegi.
 * 
 * OGRENME NOTU - Multi-Level Cache:
 * Seviye 1: Service Worker in-memory (Map) -> ~0ms, en hizli
 * Seviye 2: Redis (Upstash) -> ~3ms
 * Seviye 3: PostgreSQL (Supabase) -> ~50-200ms
 * 
 * GOREV:
 * Content script'ten gelen mesajlari dinle, API'ye istek at, sonucu don.
 * CSP (Content Security Policy) engellerini bu sekilde asiyoruz.
 */

// API Base URL - Test icin localhost, production'da degisecek
const API_BASE_URL = 'https://api-production-d6dc.up.railway.app';

/**
 * In-Memory Rating Cache
 * 
 * OGRENME NOTU - Map vs Object:
 * Map kullanmamizin sebebi: key siralama garantisi, size ozelligi,
 * ve has/delete gibi metotlarin temiz API'si.
 * 
 * Her entry: { data: {...}, timestamp: Date.now() }
 */
const ratingCache = new Map();
const CACHE_DURATION = 5 * 60 * 1000; // 5 dakika (milisaniye)

/**
 * Cache'ten oku (varsa ve suresi dolmadiysa)
 */
function getCachedRating(title) {
    const key = title.toLowerCase();
    const entry = ratingCache.get(key);
    
    if (!entry) return null;
    
    // Sure kontrolu
    if (Date.now() - entry.timestamp > CACHE_DURATION) {
        ratingCache.delete(key);  // Suresi dolmus, sil
        return null;
    }
    
    return entry.data;
}

/**
 * Cache'e yaz
 */
function setCachedRating(title, data) {
    const key = title.toLowerCase();
    ratingCache.set(key, {
        data: data,
        timestamp: Date.now()
    });
    
    // Cache'in cok buyumesini onle (max 200 entry)
    if (ratingCache.size > 200) {
        // En eski entry'yi sil (Map ilk eklenen sirada tutar)
        const firstKey = ratingCache.keys().next().value;
        ratingCache.delete(firstKey);
    }
}

/**
 * Mesaj Dinleyici
 * Content script'ten gelen istekleri isler
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'GET_RATING') {
        // Oncelikle in-memory cache'e bak
        const cached = getCachedRating(request.title);
        if (cached) {
            console.log('[Background] In-Memory Cache HIT:', request.title);
            sendResponse({ success: true, data: cached });
            return true;
        }
        
        console.log('[Background] In-Memory Cache MISS, API\'ye soruyorum:', request.title);
        fetchRating(request.title, request.year)
            .then(data => {
                // Basarili sonucu cache'e yaz
                setCachedRating(request.title, data);
                sendResponse({ success: true, data });
            })
            .catch(error => sendResponse({ success: false, error: error.message }));
        
        // async cevap donecegimiz icin true donuyoruz
        return true;
    }
    
    /**
     * OGRENME NOTU - Batch Mesaj Tipi:
     * Content script gorunen kartlarin basliklarini toplu gonderir.
     * Once in-memory cache'e bakariz, olmayanlar icin batch API'ye sorariz.
     * Sonuclari hem cache'e hem content script'e doneriz.
     */
    if (request.type === 'GET_BATCH_RATING') {
        const titles = request.titles || [];
        console.log('[Background] Batch istek:', titles.length, 'baslik');
        
        // Once cache'ten bul, olmayanlar icin API'ye sor
        const results = {};
        const uncachedTitles = [];
        
        for (const title of titles) {
            const cached = getCachedRating(title);
            if (cached) {
                results[title.toLowerCase()] = cached;
            } else {
                uncachedTitles.push(title);
            }
        }
        
        if (uncachedTitles.length === 0) {
            console.log('[Background] Batch: Tumu cache\'ten geldi');
            sendResponse({ success: true, data: results });
            return true;
        }
        
        // Cache'te olmayanlar icin batch API'ye sor
        fetchBatchRatings(uncachedTitles)
            .then(apiResults => {
                // API sonuclarini cache'e yaz ve birlestir
                for (const [title, rating] of Object.entries(apiResults)) {
                    if (rating) {
                        setCachedRating(title, rating);
                    }
                    results[title] = rating;
                }
                sendResponse({ success: true, data: results });
            })
            .catch(error => {
                console.error('[Background] Batch API hatasi:', error);
                // Cache'ten bulunanlari yine de don
                sendResponse({ success: true, data: results });
            });
        
        return true;
    }
});

/**
 * API'den rating bilgisini ceker
 * @param {string} title - Film/dizi basligi
 * @param {number|null} year - Yapim yili (opsiyonel)
 */
async function fetchRating(title, year = null) {
    let url = `${API_BASE_URL}/api/rating?title=${encodeURIComponent(title)}`;
    
    if (year) {
        url += `&year=${year}`;
    }
    
    console.log('[Background] API istegi:', url);
    
    const response = await fetch(url);
    
    if (!response.ok) {
        throw new Error(`Film bulunamadi: ${title}`);
    }
    
    const data = await response.json();
    
    // X-Cache header'ini logla (Redis cache durumu)
    const cacheStatus = response.headers.get('X-Cache');
    if (cacheStatus) {
        console.log(`[Background] Redis Cache: ${cacheStatus}`);
    }
    
    console.log('[Background] API cevabi:', data);
    
    return data;
}

/**
 * Batch API'den birden fazla filmin rating'ini ceker
 * 
 * OGRENME NOTU - POST vs GET:
 * Birden fazla baslik gondermek icin POST body kullaniyoruz.
 * GET query string'de 20 baslik gondermeye calismak URL'i cok uzatir.
 * 
 * @param {string[]} titles - Film/dizi basliklari
 * @returns {Object} { "title": {rating data}, ... }
 */
async function fetchBatchRatings(titles) {
    const url = `${API_BASE_URL}/api/ratings/batch`;
    
    console.log('[Background] Batch API istegi:', titles.length, 'baslik');
    
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ titles: titles })
    });
    
    if (!response.ok) {
        throw new Error(`Batch API hatasi: ${response.status}`);
    }
    
    const data = await response.json();
    console.log(`[Background] Batch API cevabi: ${data.found} bulundu, ${data.not_found} bulunamadi`);
    
    return data.results;
}

// Service worker basladiginda log
console.log('[Background] Netflix IMDB Extension service worker yuklendi (cache + batch aktif)');
