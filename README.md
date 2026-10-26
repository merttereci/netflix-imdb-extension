**English** | [Türkçe](README.tr.md)

# Netflix IMDb Rating Extension

<!--
![Demo](docs/images/demo.gif)

![Screenshot](docs/images/screenshot.png)
-->

A Chrome extension that adds IMDb ratings to movie and TV show cards on Netflix. Ratings come from a PostgreSQL database built from IMDb's official datasets, served by a FastAPI service with a Redis cache in front of it.

## Installation

1. Download the latest zip from the [Releases](https://github.com/merttereci/netflix-imdb-extension/releases) page and extract it.
2. Open `chrome://extensions` in Chrome and turn on **Developer mode** (top right).
3. Click **Load unpacked** and select the folder that contains `manifest.json`.
4. Open Netflix. Ratings appear on homepage cards and in the detail modal.

The extension talks to the live API, so nothing else needs to be installed.

## How It Works

```
Netflix Page             Chrome Extension            Backend API
┌──────────────┐      ┌──────────────────┐      ┌──────────────────┐
│              │      │                  │      │                  │
│  Title Card  │─────>│  content.js      │─────>│  FastAPI         │
│  (DOM)       │      │  Reads title     │      │  /api/rating     │
│              │      │                  │      │  /api/ratings/   │
│  ┌────────┐  │      │  background.js   │<─────│   batch          │
│  │IMDb 8.7│  │<─────│  Fetches rating  │      │                  │
│  └────────┘  │      │  Adds badge      │      │  PostgreSQL      │
│              │      │                  │      │  Redis           │
└──────────────┘      └──────────────────┘      └──────────────────┘
```

**Homepage cards:** An IntersectionObserver picks up cards as they scroll into view. Their titles are collected and sent to the Batch API in groups of up to 20. The rating is shown as a small badge in the top-right corner of the poster.

**Detail modal:** When a title's detail modal opens (detected with a MutationObserver, 300 ms debounce), a larger IMDb badge is added inside it.

## Tech Stack

| Category | Technology | Why |
|----------|------------|-----|
| Backend | Python + FastAPI | Automatic OpenAPI docs, Pydantic validation |
| Database | PostgreSQL (Supabase) | Relational data, free tier |
| Cache | Redis (Upstash) | Serverless Redis, Cache-Aside |
| Hosting | Vercel (Python serverless function) | Automatic deploys through Git integration |
| Extension | Chrome Manifest V3 | Current, service-worker-based standard |
| Frontend | Vanilla JavaScript | No framework needed |
| Data processing | Pandas | Reads the large IMDb TSV files in 100k-row chunks |
| ORM | SQLAlchemy | The standard Python ORM |

## Architecture

### Multi-Level Cache

```
Request
    │
    v
┌─────────────────────────────┐
│ Level 1: In-memory (Map)    │  5 min TTL, max 200 entries
│ inside background.js        │
└──────────┬──────────────────┘
           │ MISS
           v
┌─────────────────────────────┐
│ Level 2: Redis (Upstash)    │  1 hour TTL
│ server side                 │  single MGET per batch
└──────────┬──────────────────┘
           │ MISS
           v
┌─────────────────────────────┐
│ Level 3: PostgreSQL         │  Persistent storage
│ (Supabase)                  │
└─────────────────────────────┘
```

- Cards and the detail modal share the same in-memory cache. If a card's title is opened in the modal within 5 minutes, no API request is made.
- Under Manifest V3, Chrome shuts down an idle service worker. When that happens the in-memory cache is lost and requests fall through to Redis.
- The hit/miss counters in `/api/cache/stats` live in each serverless instance's own memory. Vercel can run several instances and restart them, so these numbers are not global. `total_keys` is read directly from Redis.

### Measurements

**In the browser:** A title was first fetched through the batch request on a homepage card (PostgreSQL, ~100 ms). When its detail modal was opened, the rating came from the in-memory cache in **1.35 ms**.

**Live API** (October 2026, end to end from the client, keep-alive connection):

| Request | Median | Samples |
|---------|--------|---------|
| `/api/rating`, Redis MISS (PostgreSQL) | 152 ms | 12 |
| `/api/rating`, Redis HIT | 93 ms | 22 |
| `/api/health` (baseline) | 95 ms | 11 |

These times include network latency. A Redis HIT is about as fast as `/api/health`, which means the Redis read itself is negligible next to the network round trip.

### Batch API

```
Before:  GET  /api/rating?title=X   100 cards = 100 requests
After:   POST /api/ratings/batch    100 cards = 5 requests (20 per batch)
```

- `content.js` queues visible cards and sends them when no new card arrives for 300 ms or when 20 titles have piled up.
- `background.js` checks the in-memory cache first and only asks the API for the missing titles.
- The backend accepts up to 20 titles per request (21 returns 422). It looks up all titles in Redis with a single `MGET`. Titles not found in Redis are queried in the database one by one and written to the cache.

### How Search Works

There is no full-text search. Titles are normalized before comparison: lowercased, with Turkish characters mapped to ASCII (`Başlangıç` → `baslangic`).

- **`/api/rating` and batch:** First an exact match on `LOWER(title) = ?` in the `movies` table, picking the one with the most votes if there are several. If nothing matches, an exact match on the `search_title` column of `movie_titles`, which holds Turkish titles.
- **`/api/search`:** A partial match with `LIKE '%query%'` on the same two tables, with results sorted by rating in the application.
- **`search_title`:** The normalized form of each Turkish title. `scripts/add_search_titles.py` fills it with a chain of SQL `REPLACE` calls and adds an index on it.

### Netflix DOM Integration

Netflix now uses hashed CSS class names on its cards, so the extension relies on the stable `data-uia` and `aria-label` attributes instead.

| What | Selector | Notes |
|------|----------|-------|
| Card | `[data-uia="standard-card"]`, `[data-uia="ranked-card"]` | Regular and Top 10 cards. `.slider-item` kept as a fallback for the old layout. |
| Card title | The card's own `aria-label`, or `a[aria-label]` | Fallback: `p.fallback-text` |
| Card badge host | `.boxart-container` | Otherwise the parent of the card's `img` |
| Detail modal | `.previewModal--container`, `.detail-modal` | Detected with a MutationObserver |
| Modal title | `.previewModal--player-titleTreatment-logo` | Uses the logo's `alt` text. Fallbacks tried in order include `[data-uia="preview-modal-title"]` and `.previewModal--info strong`. |
| Modal badge host | `.previewModal--info` | |

**Card detection:** IntersectionObserver (`threshold: 0.1`, `rootMargin: 50px`). Cards added later are picked up by a MutationObserver and observed too.

## Database

| Table | Rows | Description |
|-------|------|-------------|
| movies | 59,980 | IMDb movies and TV shows (rating, votes, genres) |
| movie_titles | 23,976 | Turkish titles (IMDb akas, `region = TR`) |

**Source:** IMDb official datasets (title.basics, title.ratings, title.akas)
**Filter:** At least 1,000 votes, only `movie`, `tvSeries` and `tvMiniSeries`, adult titles excluded

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/rating?title=X` | Single title. Optional `year` parameter, returns an `X-Cache: HIT/MISS` header. |
| POST | `/api/ratings/batch` | Batch lookup (up to 20 titles) |
| GET | `/api/search?q=X` | Partial-match search |
| GET | `/api/movie/{imdb_id}` | Lookup by IMDb ID |
| GET | `/api/cache/stats` | Cache statistics (hit/miss per instance) |
| GET | `/api/health` | Health check |

Interactive API docs: `/docs`

## Deployment

The API runs on Vercel as a Python serverless function in the `lhr1` (London) region. Vercel's Git integration deploys automatically on every push to `main`. `vercel.json` routes all requests to `api/index.py`, which exposes the FastAPI app from `backend/`. Dependencies are installed from the root `requirements.txt`.

## Project Structure

```
netflix-imdb-extension/
├── api/
│   └── index.py                # Vercel entry point
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   ├── movie.py        # Movie model (SQLAlchemy)
│   │   │   └── movie_title.py  # Turkish title model
│   │   ├── routes/
│   │   │   ├── movies.py       # Rating, batch and search endpoints
│   │   │   └── cache_routes.py # Cache statistics
│   │   ├── utils/
│   │   │   ├── turkish.py      # Turkish character normalization
│   │   │   └── cache.py        # Redis cache helpers
│   │   ├── main.py             # FastAPI app, CORS
│   │   ├── config.py           # Environment variables
│   │   ├── database.py         # SQLAlchemy connection
│   │   ├── redis.py            # Redis connection
│   │   └── schemas.py          # Pydantic schemas
│   ├── requirements.txt
│   └── .env.example
├── extension/                  # Chrome extension (Manifest V3)
│   ├── manifest.json
│   ├── content.js              # Reads the Netflix DOM, adds badges
│   ├── background.js           # API requests and in-memory cache
│   ├── styles.css
│   ├── popup.html
│   └── popup.js                # API connection status
├── scripts/
│   ├── import_imdb.py          # IMDb datasets -> PostgreSQL
│   ├── add_search_titles.py    # Fills the search_title column
│   ├── test_db.py              # Test script that queries the database
│   └── requirements.txt
├── docs/
│   └── adr/                    # Architecture Decision Records (11)
├── requirements.txt            # Dependencies installed by Vercel
├── vercel.json
├── README.md
└── README.tr.md
```

## Architecture Decisions (ADR)

The ADRs are written in Turkish.

| ADR | Decision |
|-----|----------|
| [ADR-001](docs/adr/ADR-001-postgresql-secimi.md) | PostgreSQL as the database |
| [ADR-002](docs/adr/ADR-002-fastapi-secimi.md) | FastAPI as the backend framework |
| [ADR-003](docs/adr/ADR-003-redis-cache.md) | Redis cache (Upstash, Cache-Aside) |
| [ADR-004](docs/adr/ADR-004-imdb-dataset.md) | IMDb official datasets |
| [ADR-005](docs/adr/ADR-005-monorepo-yaklasimi.md) | Monorepo (backend and extension in one repo) |
| [ADR-006](docs/adr/ADR-006-lokalize-baslik-destegi.md) | Turkish title support (IMDb akas) |
| [ADR-007](docs/adr/ADR-007-arama-optimizasyonu.md) | Search: normalization and exact-match priority |
| [ADR-008](docs/adr/ADR-008-netflix-kart-ve-cache-stratejisi.md) | Netflix cards and cache strategy |
| [ADR-009](docs/adr/ADR-009-batch-api-kart-stratejisi.md) | Batch API and IntersectionObserver |
| [ADR-010](docs/adr/ADR-010-railway-deployment.md) | Deployment on Railway (superseded by ADR-011) |
| [ADR-011](docs/adr/ADR-011-vercel-deployment.md) | Move from Railway to Vercel |

## What I Learned

- **Backend:** REST API design, FastAPI, SQLAlchemy, Pydantic
- **Database:** PostgreSQL, Supabase, normalization
- **Caching:** Redis, Cache-Aside, TTL, multi-level caching, MGET
- **Deployment:** Vercel serverless, environment variables
- **Chrome extensions:** Manifest V3, content and background scripts, messaging API
- **Web APIs:** IntersectionObserver, MutationObserver, DOM manipulation
- **Performance:** Debouncing, batching, solving the N+1 problem
- **Architecture:** Writing ADRs, YAGNI

## License

This is a personal and educational project. IMDb data comes from IMDb's official datasets.
