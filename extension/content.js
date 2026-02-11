/**
 * Netflix IMDB Extension - Content Script
 * 
 * OGRENME NOTU - Content Script:
 * - Netflix sayfasina enjekte olur
 * - Document'in DOM'una erisebilir
 * - Ama Netflix'in JavaScript scope'una erismez (izole)
 * 
 * GOREV:
 * 1. Netflix detay modal'ini izle (MutationObserver)
 * 2. Modal acilinca baslik ve yili oku
 * 3. Background script'e mesaj gonder
 * 4. Gelen rating'i DOM'a ekle
 */

console.log('[Content] Netflix IMDB Extension yuklendi');

// Rating badge zaten eklenmis mi kontrol
const BADGE_CLASS = 'imdb-rating-badge';

/**
 * OGRENME NOTU - Debounce Mekanizmasi:
 * Netflix'te modal acildiginda DOM milisaniyeler icinde 10-20 kere degisir.
 * MutationObserver her degisikligi yakalar ve handleModalOpen cagrilir.
 * Debounce: Arka arkaya gelen cagirilarin sadece SONUNCUSUNU isler.
 * 
 * Nasil calisir:
 * 1. Olay tetiklendi -> Timer baslat (300ms)
 * 2. 50ms sonra yeni olay geldi -> Eski timer'i iptal et, yeni timer baslat
 * 3. 300ms baska olay gelmezse -> Fonksiyonu calistir
 */
let modalDebounceTimer = null;
let isProcessing = false;  // Ayni anda birden fazla istek onleme

/**
 * Netflix DOM'undan baslik bilgisini cikarir
 * Netflix surekli class isimlerini degistirdigi icin birden fazla selector deniyoruz
 */
function extractTitleFromModal() {
    // Detay modal selector'lari (Netflix bunlari degistirebilir)
    const selectors = [
        // Modal baslik alani
        '.previewModal--player-titleTreatment-logo',
        '.previewModal--player-titleTreatmentWrapper img',
        // Fallback: Modal icerisindeki herhangi bir baslik
        '[data-uia="preview-modal-title"]',
        '.previewModal--info h1',
        '.previewModal--info strong',
        // Mini modal
        '.Mini--title',
        // Watch page
        '.title-title',
    ];
    
    for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element) {
            // img ise alt text, degilse text content
            const title = element.alt || element.getAttribute('aria-label') || element.textContent;
            if (title && title.trim()) {
                console.log('[Content] Baslik bulundu:', title, '(selector:', selector, ')');
                return title.trim();
            }
        }
    }
    
    console.log('[Content] Baslik bulunamadi, denenen selectorlar:', selectors);
    return null;
}

/**
 * Netflix DOM'undan yil bilgisini cikarir
 */
function extractYearFromModal() {
    const selectors = [
        '[data-uia="preview-modal-year"]',
        '.year',
        '.previewModal--info .year',
    ];
    
    for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element) {
            const yearText = element.textContent.trim();
            const year = parseInt(yearText);
            if (!isNaN(year) && year > 1900 && year < 2100) {
                console.log('[Content] Yil bulundu:', year);
                return year;
            }
        }
    }
    
    // Yil bulunamazsa null don (API yilsiz da arama yapabilir)
    return null;
}

/**
 * Rating badge'ini modal'a ekler
 */
function addRatingBadge(rating, title) {
    // Onceki badge varsa kaldir
    const existingBadge = document.querySelector(`.${BADGE_CLASS}`);
    if (existingBadge) {
        existingBadge.remove();
    }
    
    // Metadata alanini bul (tur, sure vb. yanina ekleyecegiz)
    const metadataSelectors = [
        '.previewModal--info',
        '.preview-modal-container',
        '.about-wrapper',
        '.titleCard--metadataWrapper',
    ];
    
    let metadataContainer = null;
    for (const selector of metadataSelectors) {
        metadataContainer = document.querySelector(selector);
        if (metadataContainer) break;
    }
    
    if (!metadataContainer) {
        console.log('[Content] Metadata container bulunamadi, badge eklenemedi');
        return;
    }
    
    // Badge olustur
    const badge = document.createElement('div');
    badge.className = BADGE_CLASS;
    badge.innerHTML = `
        <span class="imdb-logo">IMDb</span>
        <span class="imdb-score">${rating}</span>
    `;
    
    // Konumu ayarla (metadataContainer'a gore)

    
    metadataContainer.insertBefore(badge, metadataContainer.firstChild);
    console.log('[Content] Rating badge eklendi:', rating);
}

/**
 * Modal acildiginda cagrilir
 */
async function handleModalOpen() {
    // Zaten bir istek devam ediyorsa atla
    if (isProcessing) {
        console.log('[Content] Istek devam ediyor, atlaniyor');
        return;
    }
    
    // Badge zaten var mi?
    if (document.querySelector(`.${BADGE_CLASS}`)) {
        console.log('[Content] Badge zaten var, atlaniyor');
        return;
    }
    
    const title = extractTitleFromModal();
    if (!title) {
        console.log('[Content] Baslik alinamadi, rating aranmiyor');
        return;
    }
    
    // NOT: Yil gondermiyoruz cunku Netflix dizilerde yanlis yil gosteriyor
    
    console.log('[Content] Rating isteniyor:', { title });
    console.time('RatingFetchDuration');
    
    isProcessing = true;
    
    // Background script'e mesaj gonder
    try {
        const response = await chrome.runtime.sendMessage({
            type: 'GET_RATING',
            title: title,
            year: null
        });
        
        console.timeEnd('RatingFetchDuration');

        if (response.success) {
            addRatingBadge(response.data.rating, response.data.title);
        } else {
            console.log('[Content] Rating bulunamadi:', response.error);
        }
    } catch (error) {
        console.error('[Content] Hata:', error);
    } finally {
        isProcessing = false;
    }
}

/**
 * MutationObserver ile DOM degisikliklerini izle
 * Modal acildiginda tetiklenir
 */
function setupObserver() {
    const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            if (mutation.addedNodes.length > 0) {
                // Modal acildi mi kontrol et
                const modal = document.querySelector('.previewModal--container, .detail-modal');
                if (modal) {
                    // DEBOUNCE: Timer varsa iptal et, yenisini kur
                    if (modalDebounceTimer) clearTimeout(modalDebounceTimer);
                    modalDebounceTimer = setTimeout(handleModalOpen, 300);
                    break;
                }
            }
        }
    });
    
    // Body'yi izle
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    console.log('[Content] MutationObserver aktif (debounce: 300ms)');
}

// Sayfa yuklendikten sonra observer'i baslat
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setupObserver();
        setupCardObserver();
    });
} else {
    setupObserver();
    setupCardObserver();
}

// DEBUG: Netflix'in guncel DOM yapisini logla
console.log('[Content] DEBUG - Sayfa URL:', window.location.href);

// ============================================
// ANASAYFA KART RATING SISTEMI
//
// OGRENME NOTU - IntersectionObserver:
// Scroll event dinlemek yerine IntersectionObserver kullaniyoruz.
// Farklar:
// - scroll event: Her piksel kaydirildiginda tetiklenir (performans sorunu)
// - IntersectionObserver: Sadece eleman gorunur/gorunmez oldugunda tetiklenir
// Browser'in kendi optimizasyonunu kullanir, main thread'i bloklamaz.
//
// MULAKATTA SORULUR:
// - "IntersectionObserver ne ise yarar?" -> Lazy loading, infinite scroll, analytics
// - "Scroll event'ten farki?" -> Performans: observer async, scroll sync
// ============================================

const CARD_BADGE_CLASS = 'imdb-card-badge';
const processedCards = new Set();  // Zaten islenmis kartlari takip et
let batchTimer = null;  // Batch debounce timer
let pendingTitles = new Map();  // Baslik -> kart element eslemesi

/**
 * Kart'tan baslik cikarir
 * Netflix kartlarinda baslik: a[aria-label] veya p.fallback-text
 * 
 * @param {Element} cardElement - .slider-item elementi
 * @returns {string|null} Film/dizi basligi
 */
function extractTitleFromCard(cardElement) {
    // 1. aria-label (en guvenilir - erisilebilirlik standardi)
    const link = cardElement.querySelector('a[aria-label]');
    if (link) {
        const label = link.getAttribute('aria-label');
        if (label && label.trim()) return label.trim();
    }
    
    // 2. Fallback text
    const fallback = cardElement.querySelector('p.fallback-text');
    if (fallback && fallback.textContent.trim()) {
        return fallback.textContent.trim();
    }
    
    return null;
}

/**
 * Tek bir karta IMDB badge ekler
 * 
 * @param {Element} cardElement - .slider-item elementi
 * @param {number|null} rating - IMDB puani
 */
function addCardBadge(cardElement, rating) {
    if (!rating) return;
    
    // Badge zaten var mi?
    if (cardElement.querySelector(`.${CARD_BADGE_CLASS}`)) return;
    
    // Poster container'i bul
    const boxart = cardElement.querySelector('.boxart-container');
    if (!boxart) return;
    
    // Badge olustur
    const badge = document.createElement('div');
    badge.className = CARD_BADGE_CLASS;
    badge.innerHTML = `
        <span class="imdb-card-logo">IMDb</span>
        <span class="imdb-card-score">${rating.toFixed(1)}</span>
    `;
    
    boxart.appendChild(badge);
}

/**
 * Biriken basliklari toplu olarak background'a gonderir
 * 
 * OGRENME NOTU - Debounced Batch:
 * Scroll sirasinda kartlar tek tek gorunur hale gelir.
 * Her kart icin ayri istek atmak yerine 300ms bekleyip
 * gorunen tum kartlari tek batch'te gondeririz.
 */
function flushPendingBatch() {
    if (pendingTitles.size === 0) return;
    
    // Pending'leri kopyala ve temizle
    const currentBatch = new Map(pendingTitles);
    pendingTitles.clear();
    
    const titles = Array.from(currentBatch.keys());
    console.log(`[Content] Batch gonderiliyor: ${titles.length} baslik`);
    
    // Background'a batch mesaji gonder
    chrome.runtime.sendMessage(
        { type: 'GET_BATCH_RATING', titles: titles },
        (response) => {
            if (chrome.runtime.lastError) {
                console.error('[Content] Batch hatasi:', chrome.runtime.lastError);
                return;
            }
            
            if (response && response.success && response.data) {
                // Her karta badge ekle
                for (const [title, cardElement] of currentBatch.entries()) {
                    const ratingData = response.data[title.toLowerCase()];
                    if (ratingData && ratingData.rating) {
                        addCardBadge(cardElement, ratingData.rating);
                    }
                }
                
                const foundCount = Object.values(response.data).filter(v => v && v.rating).length;
                console.log(`[Content] Batch sonucu: ${foundCount}/${titles.length} karta badge eklendi`);
            }
        }
    );
}

/**
 * Bir karti isleme kuyruklarina ekler
 * 
 * @param {Element} cardElement - Gorunen kart elementi
 */
function queueCard(cardElement) {
    const title = extractTitleFromCard(cardElement);
    if (!title) return;
    
    // Zaten islenmis mi?
    const cardId = cardElement.querySelector('.title-card')?.id || title;
    if (processedCards.has(cardId)) return;
    processedCards.add(cardId);
    
    // Batch kuyruklarina ekle
    pendingTitles.set(title, cardElement);
    
    // Debounce: 300ms icinde baska kart gelmezse batch gonder
    if (batchTimer) clearTimeout(batchTimer);
    batchTimer = setTimeout(flushPendingBatch, 300);
    
    // Max 20 birikince de gonder (debounce beklemeden)
    if (pendingTitles.size >= 20) {
        clearTimeout(batchTimer);
        flushPendingBatch();
    }
}

/**
 * IntersectionObserver ile gorunen kartlari tespit eder
 * 
 * OGRENME NOTU - IntersectionObserver Kullanimi:
 * 1. Observer olustur (callback + options)
 * 2. Izlemek istedigin elementleri observe() ile ekle
 * 3. Element gorunur oldugunda callback cagrilir
 * 4. isIntersecting: true ise element viewport'ta gorunuyor
 * 
 * threshold: 0.1 = Elementin %10'u gorundugunde tetikle
 */
function setupCardObserver() {
    // IntersectionObserver: Kart gorunur oldugunda tetiklenir
    const observer = new IntersectionObserver((entries) => {
        for (const entry of entries) {
            if (entry.isIntersecting) {
                queueCard(entry.target);
                // Islendikten sonra izlemeyi birak (performans)
                observer.unobserve(entry.target);
            }
        }
    }, {
        threshold: 0.1,  // %10 gorunurse tetikle
        rootMargin: '50px'  // 50px onceden tetikle (preload)
    });
    
    // Mevcut kartlari izlemeye al
    function observeExistingCards() {
        const cards = document.querySelectorAll('.slider-item');
        cards.forEach(card => {
            // Zaten islenmis mi kontrol et
            const cardId = card.querySelector('.title-card')?.id;
            if (cardId && processedCards.has(cardId)) return;
            
            observer.observe(card);
        });
    }
    
    // Ilk tarama
    observeExistingCards();
    
    // Netflix dinamik olarak yeni satirlar ekler (scroll ile)
    // MutationObserver ile yeni eklenen kartlari da izle
    const domObserver = new MutationObserver((mutations) => {
        let hasNewCards = false;
        for (const mutation of mutations) {
            if (mutation.addedNodes.length > 0) {
                for (const node of mutation.addedNodes) {
                    if (node.nodeType === 1 && (
                        node.classList?.contains('slider-item') ||
                        node.querySelector?.('.slider-item')
                    )) {
                        hasNewCards = true;
                        break;
                    }
                }
            }
            if (hasNewCards) break;
        }
        
        if (hasNewCards) {
            // Kisa gecikme ile yeni kartlari tara
            setTimeout(observeExistingCards, 200);
        }
    });
    
    domObserver.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    console.log('[Content] Kart IntersectionObserver aktif');
}
