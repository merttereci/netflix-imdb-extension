/**
 * Netflix IMDB Extension - Popup Script
 * 
 * Extension toolbar ikonuna tiklandiginda acilan popup'in logici.
 * config.js'yi, API baglantisini ve API anahtarini kontrol eder, durumu gosterir.
 */

// popup.html config.js'yi bu dosyadan once yukler; dosya yoksa EXTENSION_CONFIG tanimsiz kalir
const CONFIG = self.EXTENSION_CONFIG || {};

document.addEventListener('DOMContentLoaded', async () => {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    const apiUrl = document.getElementById('apiUrl');
    
    const setStatus = (online, text) => {
        statusDot.classList.toggle('offline', !online);
        statusText.textContent = text;
    };
    
    if (!CONFIG.API_BASE_URL || !CONFIG.API_KEY) {
        setStatus(false, 'config.js eksik: API adresi veya anahtar tanimli degil');
        return;
    }
    
    apiUrl.textContent = `API: ${CONFIG.API_BASE_URL}`;
    
    try {
        // 1. API ayakta mi? (/api/health anahtar istemez)
        const health = await fetch(`${CONFIG.API_BASE_URL}/api/health`);
        if (!health.ok) {
            throw new Error(`Health: ${health.status}`);
        }
        const data = await health.json();
        
        // 2. Anahtar gecerli mi? Korumali ve hafif bir endpoint ile dene
        const auth = await fetch(`${CONFIG.API_BASE_URL}/api/cache/stats`, {
            headers: { 'X-API-Key': CONFIG.API_KEY }
        });
        if (auth.status === 401) {
            setStatus(false, 'API anahtari gecersiz');
            return;
        }
        if (!auth.ok) {
            throw new Error(`Cache stats: ${auth.status}`);
        }
        
        setStatus(true, `Bagli (v${data.version})`);
    } catch (error) {
        setStatus(false, 'API baglantisi yok');
        console.error('API kontrolu basarisiz:', error);
    }
});
