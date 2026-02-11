/**
 * Netflix IMDB Extension - Popup Script
 * 
 * Extension toolbar ikonuna tiklandiginda acilan popup'in logici.
 * API baglantisini kontrol eder ve durumu gosterir.
 */

const API_BASE_URL = 'https://api-production-d6dc.up.railway.app';

document.addEventListener('DOMContentLoaded', async () => {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    const apiUrl = document.getElementById('apiUrl');
    
    apiUrl.textContent = `API: ${API_BASE_URL}`;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/health`);
        
        if (response.ok) {
            const data = await response.json();
            statusDot.classList.remove('offline');
            statusText.textContent = `Bagli (v${data.version})`;
        } else {
            throw new Error('API cevap vermiyor');
        }
    } catch (error) {
        statusDot.classList.add('offline');
        statusText.textContent = 'API baglantisi yok';
        console.error('API kontrolu basarisiz:', error);
    }
});
