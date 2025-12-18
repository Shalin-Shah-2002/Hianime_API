"""
HiAnime.to Scraper API
======================
FastAPI REST API for accessing HiAnime scraper functionality

Run with: uvicorn api:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
from pydantic import BaseModel
from dataclasses import asdict

from hianime_scraper import HiAnimeScraper, SearchResult, AnimeInfo, Episode

# Import MAL clients
try:
    from mal_api import MALApiClient, MALUserClient
    mal_client = MALApiClient()
    MAL_ENABLED = True
except (ImportError, ValueError) as e:
    print(f"MAL API not available: {e}")
    mal_client = None
    MAL_ENABLED = False

# Initialize FastAPI app
app = FastAPI(
    title="HiAnime Scraper API",
    description="REST API for scraping anime data from HiAnime.to",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize scraper (singleton)
scraper = HiAnimeScraper(rate_limit=True)


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class AnimeSearchResponse(BaseModel):
    success: bool
    count: int
    page: int
    data: List[dict]


class EpisodeListResponse(BaseModel):
    success: bool
    count: int
    data: List[dict]


class AnimeDetailResponse(BaseModel):
    success: bool
    data: Optional[dict]


class ErrorResponse(BaseModel):
    success: bool = False
    error: str


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def serialize_results(results: List[SearchResult]) -> List[dict]:
    """Convert SearchResult objects to dictionaries"""
    return [asdict(r) for r in results]


def serialize_details(details: AnimeInfo) -> dict:
    """Convert AnimeInfo object to dictionary"""
    return asdict(details) if details else None


# =============================================================================
# API ROUTES
# =============================================================================

@app.get("/", tags=["Root"])
async def root():
    """API Health Check"""
    return {
        "status": "online",
        "api": "HiAnime + MAL Scraper API",
        "version": "2.0.0",
        "mal_enabled": MAL_ENABLED,
        "total_endpoints": 24 if MAL_ENABLED else 16,
        "endpoints": {
            "search": "/api/search?keyword=naruto",
            "filter": "/api/filter?type=tv&status=airing",
            "popular": "/api/popular",
            "top_airing": "/api/top-airing",
            "recently_updated": "/api/recently-updated",
            "completed": "/api/completed",
            "subbed": "/api/subbed",
            "dubbed": "/api/dubbed",
            "genre": "/api/genre/{genre}",
            "type": "/api/type/{type}",
            "az_list": "/api/az/{letter}",
            "producer": "/api/producer/{producer_slug}",
            "anime_details": "/api/anime/{slug}",
            "episodes": "/api/episodes/{slug}",
            "mal_search": "/api/mal/search?query=naruto",
            "mal_details": "/api/mal/anime/{mal_id}",
            "mal_ranking": "/api/mal/ranking?type=all",
            "mal_seasonal": "/api/mal/seasonal?year=2024&season=winter",
            "mal_user_auth": "/api/mal/user/auth (POST)",
            "combined_search": "/api/combined/search?query=naruto",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


# -----------------------------------------------------------------------------
# SEARCH
# -----------------------------------------------------------------------------

@app.get("/api/search", response_model=AnimeSearchResponse, tags=["Search"])
async def search_anime(
    keyword: str = Query(..., description="Search keyword", min_length=1),
    page: int = Query(1, ge=1, description="Page number")
):
    """
    Search for anime by keyword
    
    - **keyword**: Search term (required)
    - **page**: Page number (default: 1)
    """
    try:
        results = scraper.search(keyword, page=page)
        return {
            "success": True,
            "count": len(results),
            "page": page,
            "data": serialize_results(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# BROWSE ENDPOINTS
# -----------------------------------------------------------------------------

@app.get("/api/popular", response_model=AnimeSearchResponse, tags=["Browse"])
async def get_popular(
    page: int = Query(1, ge=1, description="Page number")
):
    """Get most popular anime"""
    try:
        results = scraper.get_most_popular(page=page)
        return {
            "success": True,
            "count": len(results),
            "page": page,
            "data": serialize_results(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/top-airing", response_model=AnimeSearchResponse, tags=["Browse"])
async def get_top_airing(
    page: int = Query(1, ge=1, description="Page number")
):
    """Get currently airing anime"""
    try:
        results = scraper.get_top_airing(page=page)
        return {
            "success": True,
            "count": len(results),
            "page": page,
            "data": serialize_results(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recently-updated", response_model=AnimeSearchResponse, tags=["Browse"])
async def get_recently_updated(
    page: int = Query(1, ge=1, description="Page number")
):
    """Get recently updated anime"""
    try:
        results = scraper.get_recently_updated(page=page)
        return {
            "success": True,
            "count": len(results),
            "page": page,
            "data": serialize_results(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/completed", response_model=AnimeSearchResponse, tags=["Browse"])
async def get_completed(
    page: int = Query(1, ge=1, description="Page number")
):
    """Get completed anime"""
    try:
        results = scraper.get_completed(page=page)
        return {
            "success": True,
            "count": len(results),
            "page": page,
            "data": serialize_results(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# GENRE & TYPE
# -----------------------------------------------------------------------------

@app.get("/api/genre/{genre}", response_model=AnimeSearchResponse, tags=["Genre & Type"])
async def get_by_genre(
    genre: str,
    page: int = Query(1, ge=1, description="Page number")
):
    """
    Get anime by genre
    
    Available genres: action, adventure, cars, comedy, dementia, demons, drama,
    ecchi, fantasy, game, harem, historical, horror, isekai, josei, kids, magic,
    martial-arts, mecha, military, music, mystery, parody, police, psychological,
    romance, samurai, school, sci-fi, seinen, shoujo, shoujo-ai, shounen,
    shounen-ai, slice-of-life, space, sports, super-power, supernatural,
    thriller, vampire
    """
    try:
        results = scraper.get_by_genre(genre, page=page)
        return {
            "success": True,
            "count": len(results),
            "page": page,
            "data": serialize_results(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/type/{type_name}", response_model=AnimeSearchResponse, tags=["Genre & Type"])
async def get_by_type(
    type_name: str,
    page: int = Query(1, ge=1, description="Page number")
):
    """
    Get anime by type
    
    Available types: movie, tv, ova, ona, special, music
    """
    try:
        results = scraper.get_by_type(type_name, page=page)
        return {
            "success": True,
            "count": len(results),
            "page": page,
            "data": serialize_results(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# ADVANCED FILTER
# -----------------------------------------------------------------------------

@app.get("/api/filter", response_model=AnimeSearchResponse, tags=["Filter"])
async def advanced_filter(
    type: Optional[str] = Query(None, description="Type: movie, tv, ova, ona, special, music"),
    status: Optional[str] = Query(None, description="Status: finished, airing, upcoming"),
    rated: Optional[str] = Query(None, description="Rating: g, pg, pg-13, r, r+, rx"),
    score: Optional[int] = Query(None, ge=1, le=10, description="Minimum score (1-10)"),
    season: Optional[str] = Query(None, description="Season: spring, summer, fall, winter"),
    language: Optional[str] = Query(None, description="Language: sub, dub"),
    genres: Optional[str] = Query(None, description="Comma-separated genres"),
    sort: Optional[str] = Query("default", description="Sort: default, recently_added, recently_updated, score, name_az, released_date, most_watched"),
    page: int = Query(1, ge=1, description="Page number")
):
    """
    Advanced filter for anime
    
    Filter by multiple criteria simultaneously
    """
    try:
        genre_list = genres.split(",") if genres else None
        
        results = scraper.advanced_filter(
            type=type,
            status=status,
            rated=rated,
            score=score,
            season=season,
            language=language,
            genres=genre_list,
            sort=sort,
            page=page
        )
        return {
            "success": True,
            "count": len(results),
            "page": page,
            "data": serialize_results(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# ANIME DETAILS
# -----------------------------------------------------------------------------

@app.get("/api/anime/{slug}", response_model=AnimeDetailResponse, tags=["Details"])
async def get_anime_details(slug: str):
    """
    Get detailed information about an anime
    
    - **slug**: Anime slug (e.g., "naruto-677", "one-piece-100")
    """
    try:
        details = scraper.get_anime_details(slug)
        if not details:
            raise HTTPException(status_code=404, detail="Anime not found")
        
        return {
            "success": True,
            "data": serialize_details(details)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# A-Z LIST
# -----------------------------------------------------------------------------

@app.get("/api/az/{letter}", response_model=AnimeSearchResponse, tags=["A-Z List"])
async def get_az_list(
    letter: str,
    page: int = Query(1, ge=1, description="Page number")
):
    """
    Get anime alphabetically by first letter
    
    - **letter**: Single letter A-Z or "other" for non-alphabetic
    """
    try:
        results = scraper.get_az_list(letter.upper(), page=page)
        return {
            "success": True,
            "count": len(results),
            "page": page,
            "data": serialize_results(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# SUBBED / DUBBED
# -----------------------------------------------------------------------------

@app.get("/api/subbed", response_model=AnimeSearchResponse, tags=["Browse"])
async def get_subbed_anime(
    page: int = Query(1, ge=1, description="Page number")
):
    """Get anime with subtitles"""
    try:
        results = scraper.get_subbed_anime(page=page)
        return {
            "success": True,
            "count": len(results),
            "page": page,
            "data": serialize_results(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dubbed", response_model=AnimeSearchResponse, tags=["Browse"])
async def get_dubbed_anime(
    page: int = Query(1, ge=1, description="Page number")
):
    """Get dubbed anime"""
    try:
        results = scraper.get_dubbed_anime(page=page)
        return {
            "success": True,
            "count": len(results),
            "page": page,
            "data": serialize_results(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# PRODUCER / STUDIO
# -----------------------------------------------------------------------------

@app.get("/api/producer/{producer_slug}", response_model=AnimeSearchResponse, tags=["Producer"])
async def get_by_producer(
    producer_slug: str,
    page: int = Query(1, ge=1, description="Page number")
):
    """
    Get anime by producer/studio
    
    - **producer_slug**: Producer slug (e.g., "studio-pierrot", "mappa", "toei-animation")
    """
    try:
        results = scraper.get_by_producer(producer_slug, page=page)
        return {
            "success": True,
            "count": len(results),
            "page": page,
            "data": serialize_results(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# EPISODE LIST
# -----------------------------------------------------------------------------

@app.get("/api/episodes/{slug}", response_model=EpisodeListResponse, tags=["Episodes"])
async def get_episodes(slug: str):
    """
    Get full episode list for an anime (via AJAX API)
    
    - **slug**: Anime slug with ID (e.g., "naruto-677", "one-piece-100")
    
    Returns all episodes with:
    - Episode number, title (English & Japanese)
    - Direct episode URL with episode ID
    - Filler status (when available)
    """
    try:
        episodes = scraper.get_episodes(slug)
        return {
            "success": True,
            "count": len(episodes),
            "data": [asdict(ep) for ep in episodes]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# MYANIMELIST ENDPOINTS (Public - No Auth Required)
# =============================================================================

@app.get("/api/mal/search", tags=["MyAnimeList"])
async def mal_search(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Results limit")
):
    """
    Search anime on MyAnimeList (official API)
    
    - Uses official MAL API
    - Returns detailed anime information including scores, rankings
    """
    if not MAL_ENABLED:
        raise HTTPException(status_code=503, detail="MAL API not configured")
    
    try:
        results = mal_client.search(query, limit=limit)
        return {
            "success": True,
            "source": "myanimelist",
            "count": len(results),
            "data": [asdict(r) for r in results]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/mal/anime/{mal_id}", tags=["MyAnimeList"])
async def mal_anime_details(mal_id: int):
    """
    Get anime details from MyAnimeList by MAL ID
    
    - **mal_id**: MyAnimeList anime ID
    """
    if not MAL_ENABLED:
        raise HTTPException(status_code=503, detail="MAL API not configured")
    
    try:
        anime = mal_client.get_anime_details(mal_id)
        if not anime:
            raise HTTPException(status_code=404, detail="Anime not found on MAL")
        
        return {
            "success": True,
            "source": "myanimelist",
            "data": asdict(anime)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/mal/ranking", tags=["MyAnimeList"])
async def mal_ranking(
    type: str = Query("all", description="Ranking type: all, airing, upcoming, tv, movie, bypopularity, favorite"),
    limit: int = Query(10, ge=1, le=100, description="Results limit")
):
    """
    Get anime rankings from MyAnimeList
    
    Ranking types:
    - **all**: Top Anime Series
    - **airing**: Top Airing Anime
    - **upcoming**: Top Upcoming Anime
    - **tv**: Top Anime TV Series
    - **movie**: Top Anime Movies
    - **bypopularity**: Most Popular Anime
    - **favorite**: Most Favorited Anime
    """
    if not MAL_ENABLED:
        raise HTTPException(status_code=503, detail="MAL API not configured")
    
    try:
        results = mal_client.get_ranking(type, limit=limit)
        return {
            "success": True,
            "source": "myanimelist",
            "ranking_type": type,
            "count": len(results),
            "data": [asdict(r) for r in results]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/mal/seasonal", tags=["MyAnimeList"])
async def mal_seasonal(
    year: int = Query(..., description="Year (e.g., 2024)"),
    season: str = Query(..., description="Season: winter, spring, summer, fall"),
    limit: int = Query(10, ge=1, le=100, description="Results limit")
):
    """
    Get seasonal anime from MyAnimeList
    
    - **year**: Year (e.g., 2024, 2025)
    - **season**: winter (Jan-Mar), spring (Apr-Jun), summer (Jul-Sep), fall (Oct-Dec)
    """
    if not MAL_ENABLED:
        raise HTTPException(status_code=503, detail="MAL API not configured")
    
    if season not in ["winter", "spring", "summer", "fall"]:
        raise HTTPException(status_code=400, detail="Invalid season. Use: winter, spring, summer, fall")
    
    try:
        results = mal_client.get_seasonal(year, season, limit=limit)
        return {
            "success": True,
            "source": "myanimelist",
            "year": year,
            "season": season,
            "count": len(results),
            "data": [asdict(r) for r in results]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# MYANIMELIST USER AUTHENTICATION (User's Own Credentials)
# =============================================================================

class UserAuthRequest(BaseModel):
    """Request model for user authentication"""
    client_id: str
    client_secret: Optional[str] = None
    redirect_uri: str


class TokenExchangeRequest(BaseModel):
    """Request model for token exchange"""
    client_id: str
    client_secret: Optional[str] = None
    code: str
    code_verifier: str
    redirect_uri: str


class UserListRequest(BaseModel):
    """Request model for accessing user's anime list"""
    client_id: str
    access_token: str
    status: Optional[str] = None
    limit: int = 100


@app.post("/api/mal/user/auth", tags=["MyAnimeList User Auth"])
async def mal_user_get_auth_url(request: UserAuthRequest):
    """
    Get OAuth2 authorization URL for MAL user login
    
    ⚠️ **PRIVACY NOTICE**:
    - We DO NOT store your client_id or client_secret
    - Your credentials are used only for this request
    - Authentication happens directly with MyAnimeList
    
    **How to get your credentials:**
    1. Go to https://myanimelist.net/apiconfig
    2. Create a new API application
    3. Copy your Client ID and Client Secret
    
    **Returns:**
    - auth_url: Open this URL to login to MAL
    - code_verifier: Save this! You'll need it for token exchange
    - state: Security parameter
    """
    try:
        user_client = MALUserClient(
            client_id=request.client_id,
            client_secret=request.client_secret
        )
        
        auth_data = user_client.get_authorization_url(redirect_uri=request.redirect_uri)
        
        return {
            "success": True,
            "message": "Open auth_url in browser to login. Save code_verifier for token exchange.",
            "privacy_notice": "We DO NOT store your credentials. This request is stateless.",
            "data": auth_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/mal/user/token", tags=["MyAnimeList User Auth"])
async def mal_user_exchange_token(request: TokenExchangeRequest):
    """
    Exchange authorization code for access token
    
    ⚠️ **PRIVACY NOTICE**:
    - We DO NOT store your tokens
    - Save your tokens securely on your end
    - Tokens are returned to you, not stored on our servers
    
    **After getting auth code from callback:**
    1. Extract 'code' from callback URL
    2. Use the code_verifier from previous step
    3. Call this endpoint to get access_token
    """
    try:
        user_client = MALUserClient(
            client_id=request.client_id,
            client_secret=request.client_secret
        )
        
        tokens = user_client.exchange_code_for_token(
            code=request.code,
            code_verifier=request.code_verifier,
            redirect_uri=request.redirect_uri
        )
        
        return {
            "success": True,
            "message": "Save these tokens securely. We DO NOT store them.",
            "privacy_notice": "Tokens are returned to you only. Store them securely on your end.",
            "data": tokens
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/mal/user/animelist", tags=["MyAnimeList User Auth"])
async def mal_user_get_animelist(request: UserListRequest):
    """
    Get user's anime list
    
    ⚠️ **PRIVACY NOTICE**:
    - We DO NOT store your access token
    - Your list data is returned to you only
    
    **Status options:**
    - watching
    - completed
    - on_hold
    - dropped
    - plan_to_watch
    - (leave empty for all)
    """
    try:
        user_client = MALUserClient(client_id=request.client_id)
        user_client.set_access_token(request.access_token)
        
        anime_list = user_client.get_user_anime_list(
            status=request.status,
            limit=request.limit
        )
        
        return {
            "success": True,
            "privacy_notice": "We DO NOT store your data. This response is not logged.",
            "count": len(anime_list),
            "data": anime_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/mal/user/profile", tags=["MyAnimeList User Auth"])
async def mal_user_get_profile(
    client_id: str = Body(...),
    access_token: str = Body(...)
):
    """
    Get authenticated user's MAL profile
    
    ⚠️ **PRIVACY NOTICE**:
    - We DO NOT store your access token or profile data
    """
    try:
        user_client = MALUserClient(client_id=client_id)
        user_client.set_access_token(access_token)
        
        profile = user_client.get_user_info()
        
        return {
            "success": True,
            "privacy_notice": "We DO NOT store your profile data.",
            "data": profile
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# COMBINED ENDPOINTS (HiAnime + MAL)
# =============================================================================

@app.get("/api/combined/search", tags=["Combined"])
async def combined_search(
    query: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=20, description="Results per source")
):
    """
    Search both HiAnime and MyAnimeList simultaneously
    
    Returns results from both sources for comparison:
    - HiAnime: Streaming info, episodes
    - MAL: Scores, rankings, detailed info
    """
    results = {
        "success": True,
        "query": query,
        "sources": {
            "hianime": {"enabled": True, "results": [], "error": None},
            "myanimelist": {"enabled": MAL_ENABLED, "results": [], "error": None}
        }
    }
    
    # HiAnime results
    try:
        hianime_results = scraper.search(query, page=1)[:limit]
        results["sources"]["hianime"]["results"] = serialize_results(hianime_results)
        results["sources"]["hianime"]["count"] = len(hianime_results)
    except Exception as e:
        results["sources"]["hianime"]["error"] = str(e)
    
    # MAL results
    if MAL_ENABLED:
        try:
            mal_results = mal_client.search(query, limit=limit)
            results["sources"]["myanimelist"]["results"] = [asdict(r) for r in mal_results]
            results["sources"]["myanimelist"]["count"] = len(mal_results)
        except Exception as e:
            results["sources"]["myanimelist"]["error"] = str(e)
    else:
        results["sources"]["myanimelist"]["error"] = "MAL API not configured"
    
    return results


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": str(exc)}
    )


# =============================================================================
# RUN SERVER
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
