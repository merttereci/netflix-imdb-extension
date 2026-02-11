# Netflix IMDB Extension - Backend

FastAPI backend for Netflix IMDB Rating Chrome Extension.

## Setup

```bash
# Virtual environment olustur
python -m venv venv

# Aktif et (Windows)
venv\Scripts\activate

# Paketleri yukle
pip install -r requirements.txt

# Calistir
uvicorn app.main:app --reload
```

## API Endpoints

- `GET /api/rating?title=...&year=...` - Film rating'i getir
- `GET /api/search?q=...` - Film ara
- `GET /api/health` - API durumu

## Environment Variables

`.env` dosyasi olustur:
```
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://... (opsiyonel)
```
