"""
Movies API Routes

OGRENME NOTU:
- APIRouter ile route'lari gruplandiririz
- Dependency injection ile veritabani session'i aliriz
- Her endpoint bir HTTP metodu (GET, POST, etc.)
- Faz 5: Cache-Aside pattern eklendi (Redis)

MULAKATTA SORULUR:
- "REST API nedir?" -> HTTP metodlari ile kaynak yonetimi
- "GET vs POST farki?" -> GET okuma, POST olusturma
- "Cache-Aside pattern nasil calisir?" -> Once cache'e bak, yoksa DB'den al, cache'e yaz
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional

from app.database import get_db
from app.models.movie import Movie
from app.models.movie_title import MovieTitle
from app.schemas import MovieRating, MovieSearch, ErrorResponse, BatchRatingRequest, BatchRatingResponse
from app.utils.turkish import normalize_turkish, turkish_contains
from app.utils.cache import (
    cache_get, cache_set,
    make_rating_key, make_movie_key, make_search_key
)

# Router olustur
router = APIRouter()


@router.get(
    "/rating",
    response_model=MovieRating,
    responses={404: {"model": ErrorResponse}},
    summary="Film rating getir",
    description="Film adi (Turkce veya Ingilizce) ve yila gore IMDB rating'i dondurur"
)
def get_movie_rating(
    title: str = Query(..., description="Film adi (Turkce veya Ingilizce)", min_length=1),
    year: Optional[int] = Query(None, description="Yapim yili", ge=1900, le=2030),
    db: Session = Depends(get_db)
):
    """
    Film rating'i getir - Turkce ve Ingilizce baslik destekli
    
    OGRENME NOTU - Cache-Aside Pattern Burada Uygulanir:
    1. Cache key olustur (normalize edilmis baslik)
    2. Cache'e bak -> varsa direkt don (HIT)
    3. Yoksa DB'den cek -> cache'e yaz -> don (MISS)
    
    Response header'inda X-Cache: HIT veya MISS bilgisi eklenir.
    Bu sayede cache'in calisip calismadigini gorebilirsin.
    """
    
    normalized_title = normalize_turkish(title)
    
    # --- CACHE-ASIDE: Oncelikle cache'e bak ---
    cache_key = make_rating_key(title)
    cached = cache_get(cache_key)
    if cached:
        print(f"[Cache] HIT: {cache_key}")
        response = JSONResponse(content=cached)
        response.headers["X-Cache"] = "HIT"
        return response
    
    # --- CACHE MISS: DB'den cek ---
    print(f"[Cache] MISS: {cache_key}")
    
    # 1. Movies tablosu (Ingilizce/Orijinal) - Tam Eslesme
    query = db.query(Movie).filter(func.lower(Movie.title) == normalized_title)
    
    if year:
        query = query.filter(Movie.year == year)
        
    movie = query.order_by(Movie.votes.desc()).first()
    
    # 2. MovieTitles tablosu (Turkce/Yerel) - Tam Eslesme
    if not movie:
        tr_query = db.query(MovieTitle).filter(MovieTitle.search_title == normalized_title)
        tr_titles = tr_query.all()
        
        candidates = []
        for tr in tr_titles:
            m = db.query(Movie).filter(Movie.imdb_id == tr.imdb_id).first()
            if m:
                if year and m.year != year:
                    continue
                candidates.append(m)
        
        if candidates:
            candidates.sort(key=lambda x: x.votes or 0, reverse=True)
            movie = candidates[0]
    
    if not movie:
        raise HTTPException(
            status_code=404,
            detail=f"Film bulunamadi: {title}" + (f" ({year})" if year else "")
        )
    
    # --- CACHE'E YAZ: Sonraki isteklerde hizli donsun ---
    movie_data = MovieRating.model_validate(movie).model_dump()
    cache_set(cache_key, movie_data)
    
    response = JSONResponse(content=movie_data)
    response.headers["X-Cache"] = "MISS"
    return response


@router.get(
    "/search",
    response_model=MovieSearch,
    summary="Film ara",
    description="Film adina gore arama yapar (Turkce ve Ingilizce), birden fazla sonuc donebilir"
)
def search_movies(
    q: str = Query(..., description="Arama sorgusu (Turkce veya Ingilizce)", min_length=2),
    limit: int = Query(50, description="Maksimum sonuc sayisi", ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Film ara - Turkce ve Ingilizce baslik destekli
    
    OGRENME NOTU - Arama Stratejisi:
    1. Tum filmleri cek
    2. Python'da normalize ederek karsilastir
    3. Turkce basliklarda da ara
    
    PERFORMANS NOTU:
    Bu yaklasim kucuk veritabanlari icin uygun (~60K kayit).
    Buyuk veritabanlarinda PostgreSQL full-text search kullanilmali.
    """
    
    normalized_q = normalize_turkish(q)
    results = []
    found_ids = set()
    
    # DB Limit stratejisi: 
    # Populariteye gore siralama olmadigi icin genis bir havuz cekmeliyiz.
    # Kullanici 10 istese de biz 100 cekip, rating'e gore siralayip en iyi 10'u donelim.
    db_limit = min(limit * 10, 500)
    
    # 1. Ingilizce basliklarda ara
    movies = db.query(Movie).filter(
        func.lower(Movie.title).contains(func.lower(q))
    ).limit(db_limit).all()
    
    for m in movies:
        results.append(m)
        found_ids.add(m.imdb_id)
    
    # 2. Turkce basliklarda ara (search_title)
    tr_titles = db.query(MovieTitle).filter(
        MovieTitle.search_title.contains(normalized_q)
    ).limit(db_limit).all()
    
    for tr in tr_titles:
        if tr.imdb_id not in found_ids:
            movie = db.query(Movie).filter(Movie.imdb_id == tr.imdb_id).first()
            if movie:
                results.append(movie)
                found_ids.add(tr.imdb_id)

    # Sonuclari rating'e gore sirala
    results.sort(key=lambda m: m.rating or 0, reverse=True)
    
    # Limit uygula (En son)
    results = results[:limit]
    
    return MovieSearch(
        results=[MovieRating.model_validate(m) for m in results],
        total=len(results),
        query=q
    )


@router.get(
    "/movie/{imdb_id}",
    response_model=MovieRating,
    responses={404: {"model": ErrorResponse}},
    summary="IMDB ID ile film getir"
)
def get_movie_by_id(
    imdb_id: str,
    db: Session = Depends(get_db)
):
    """
    IMDB ID ile film getir (Cache destekli)
    
    OGRENME NOTU - Path Parameters:
    {imdb_id} URL'in bir parcasi olur: /api/movie/tt1234567
    Query parameter'dan farki: Kaynak tanimlayici olarak kullanilir
    """
    
    # Cache'e bak
    cache_key = make_movie_key(imdb_id)
    cached = cache_get(cache_key)
    if cached:
        response = JSONResponse(content=cached)
        response.headers["X-Cache"] = "HIT"
        return response
    
    movie = db.query(Movie).filter(Movie.imdb_id == imdb_id).first()
    
    if not movie:
        raise HTTPException(
            status_code=404,
            detail=f"Film bulunamadi: {imdb_id}"
        )
    
    # Cache'e yaz
    movie_data = MovieRating.model_validate(movie).model_dump()
    cache_set(cache_key, movie_data)
    
    response = JSONResponse(content=movie_data)
    response.headers["X-Cache"] = "MISS"
    return response


@router.post(
    "/ratings/batch",
    response_model=BatchRatingResponse,
    summary="Toplu rating getir",
    description="Birden fazla film/dizi basligini tek istekte sorgular (max 20)"
)
def get_batch_ratings(
    request: BatchRatingRequest,
    db: Session = Depends(get_db)
):
    """
    Toplu rating sorgulama - Anasayfa kartlari icin
    
    OGRENME NOTU - Batch Pattern:
    N+1 problemini cozer: 20 kart icin 20 ayri HTTP istegi yerine
    tek istek ile tum rating'leri al.
    
    Her baslik icin once cache'e bakar (Cache-Aside).
    Cache'te olmayanlari DB'den toplu ceker.
    
    MULAKATTA SORULUR:
    - "N+1 problemi nedir?" -> Her kayit icin ayri sorgu atmak
    - "Batch processing avantaji?" -> Ag ve DB yuku azalir
    """
    
    results = {}
    found = 0
    not_found = 0
    uncached_titles = []  # Cache'te olmayanlar
    
    # 1. Adim: Her baslik icin once cache'e bak
    for title in request.titles:
        cache_key = make_rating_key(title)
        cached = cache_get(cache_key)
        if cached:
            results[title.lower()] = cached
            found += 1
            # Debug icin detayli log
            print(f"[Batch Cache] HIT: {title}")
        else:
            uncached_titles.append(title)
            print(f"[Batch Cache] MISS: {title}")
    
    # 2. Adim: Cache'te olmayanlari DB'den cek
    for title in uncached_titles:
        normalized_title = normalize_turkish(title)
        movie = None
        
        # Ingilizce baslikta ara
        movie = db.query(Movie).filter(
            func.lower(Movie.title) == normalized_title
        ).order_by(Movie.votes.desc()).first()
        
        # Turkce baslikta ara
        if not movie:
            tr_query = db.query(MovieTitle).filter(
                MovieTitle.search_title == normalized_title
            )
            for tr in tr_query.all():
                m = db.query(Movie).filter(Movie.imdb_id == tr.imdb_id).first()
                if m:
                    movie = m
                    break
        
        if movie:
            movie_data = MovieRating.model_validate(movie).model_dump()
            results[title.lower()] = movie_data
            found += 1
            # Cache'e yaz
            cache_key = make_rating_key(title)
            cache_set(cache_key, movie_data)
        else:
            results[title.lower()] = None
            not_found += 1
    
    print(f"[Batch] {len(request.titles)} baslik soruldu: {found} bulundu, {not_found} bulunamadi")
    
    return BatchRatingResponse(
        results=results,
        found=found,
        not_found=not_found
    )
