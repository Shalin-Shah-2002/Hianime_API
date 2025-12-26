"""
HiAnime.to Scraper API
======================
FastAPI REST API for accessing HiAnime scraper functionality

Run with: uvicorn api:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, Query, Body, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, Response, HTMLResponse, FileResponse
from typing import Optional, List
from pydantic import BaseModel
from dataclasses import asdict
import httpx
import base64
import re
import asyncio
import tempfile
import os
import subprocess
import shutil
import time
from urllib.parse import urljoin

from hianime_scraper import HiAnimeScraper, SearchResult, AnimeInfo, Episode, VideoServer, VideoSource

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
        "version": "2.3.1",
        "mal_enabled": MAL_ENABLED,
        "total_endpoints": 30 if MAL_ENABLED else 22,
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
            "video_servers": "/api/servers/{episode_id}",
            "video_sources": "/api/sources/{episode_id}?server_type=sub",
            "watch_sources": "/api/watch/{anime_slug}?ep={episode_id}&server_type=sub",
            "streaming_links": "/api/stream/{episode_id}?server_type=sub  ⭐ USE THIS FOR FLUTTER!",
            "download_links": "/api/download/{episode_id}?server_type=sub  📥 GET DOWNLOAD URLS",
            "download_mp4": "/api/download/mp4/{episode_id}  🎬 DOWNLOAD AS MP4 FILE!",
            "download_check": "/api/download/mp4/check  ✅ CHECK FFMPEG STATUS",
            "extract_stream": "/api/extract-stream?url={embed_url}",
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


# -----------------------------------------------------------------------------
# VIDEO SOURCES
# -----------------------------------------------------------------------------

@app.get("/api/servers/{episode_id}", tags=["Video Sources"])
async def get_video_servers(episode_id: str):
    """
    Get available video servers for an episode
    
    - **episode_id**: Episode ID from the URL (e.g., "2142" from ?ep=2142)
    
    Returns list of available servers with their type (sub/dub/raw)
    """
    try:
        servers = scraper.get_video_servers(episode_id)
        return {
            "success": True,
            "episode_id": episode_id,
            "count": len(servers),
            "data": [asdict(s) for s in servers]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sources/{episode_id}", tags=["Video Sources"])
async def get_episode_sources(
    episode_id: str,
    server_type: str = Query("sub", description="Server type: sub, dub, or all")
):
    """
    Get video sources/streaming links for an episode
    
    - **episode_id**: Episode ID from the URL (e.g., "2142" from ?ep=2142)
    - **server_type**: Filter by type - "sub" (default), "dub", or "all"
    
    Returns embed URLs for each available server.
    """
    try:
        result = scraper.get_episode_sources(episode_id, server_type)
        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/watch/{anime_slug}", tags=["Video Sources"])
async def get_watch_sources(
    anime_slug: str,
    ep: str = Query(..., description="Episode ID parameter (e.g., 2142)"),
    server_type: str = Query("sub", description="Server type: sub, dub, or all")
):
    """
    Get video sources from a watch URL format
    
    Example: /api/watch/one-piece-100?ep=2142
    
    - **anime_slug**: Anime slug (e.g., "one-piece-100")
    - **ep**: Episode ID parameter from the original URL
    - **server_type**: Filter by type - "sub" (default), "dub", or "all"
    
    This endpoint mimics the HiAnime watch URL structure:
    https://hianime.to/watch/one-piece-100?ep=2142
    """
    try:
        result = scraper.get_watch_sources(anime_slug, ep, server_type)
        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# STREAMING LINKS (Actual playable URLs for Flutter/Mobile Apps)
# -----------------------------------------------------------------------------

@app.get("/api/stream/{episode_id}", tags=["Video Sources"])
async def get_streaming_links(
    episode_id: str,
    server_type: str = Query("sub", description="Server type: sub, dub, or all"),
    include_proxy_url: bool = Query(False, description="Include proxied URLs that bypass Cloudflare")
):
    """
    🎬 Get actual streaming links (.m3u8) for video players
    
    **USE THIS FOR FLUTTER/MOBILE APPS!**
    
    This endpoint returns actual playable video URLs that work directly
    in video players like:
    - Flutter: video_player, chewie, better_player
    - Android: ExoPlayer
    - iOS: AVPlayer
    - Desktop: VLC
    
    - **episode_id**: Episode ID from the URL (e.g., "2142" from ?ep=2142)
    - **server_type**: Filter by type - "sub" (default), "dub", or "all"
    - **include_proxy_url**: If true, adds `proxy_url` field that bypasses Cloudflare
    
    **Response includes:**
    - `streams`: Array with name, sources (each with file, headers), subtitles
    - `sources[].file`: The m3u8 URL
    - `sources[].headers`: **Per-source headers** - USE THESE for each URL!
    - `skips`: intro/outro skip timestamps
    - `proxy_url`: (optional) URL through our proxy that bypasses Cloudflare
    
    **⚠️ IMPORTANT: Each source has its own headers!**
    When playing a video, use the `headers` from that specific source object,
    not the stream-level headers. This ensures ALL streaming URLs work!
    
    **If streams don't work directly**, use `include_proxy_url=true` and use the
    `proxy_url` field instead - this routes through our server to bypass blocks.
    """
    try:
        result = scraper.get_streaming_links(episode_id, server_type)
        
        # Add proxy URLs if requested
        if include_proxy_url and result.get('streams'):
            for stream in result['streams']:
                for source in stream.get('sources', []):
                    original_url = source.get('file', '')
                    if original_url:
                        encoded = base64.b64encode(original_url.encode()).decode()
                        # Get the referer from THIS source's headers (per-source headers!)
                        source_headers = source.get('headers', {})
                        stream_headers = stream.get('headers', {})
                        # Prefer source-specific referer, fall back to stream headers
                        source_referer = source_headers.get('Referer', stream_headers.get('Referer', 'https://megacloud.blog/'))
                        encoded_referer = base64.b64encode(source_referer.encode()).decode()
                        source['proxy_url'] = f"/api/proxy/m3u8?url={encoded}&ref={encoded_referer}"
        
        return result  # Already includes success field
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/extract-stream", tags=["Video Sources"])
async def extract_stream(
    url: str = Query(..., description="Embed URL to extract stream from")
):
    """
    Extract streaming URL from any supported embed URL
    
    Directly extracts playable .m3u8 URL from embed URLs like:
    - megacloud.blog/embed-2/...
    - rapid-cloud.co/embed-6/...
    
    - **url**: The embed URL to extract from
    
    Returns the actual streaming URL that can be played in video players.
    """
    try:
        result = scraper.extract_stream_url(url)
        if not result:
            raise HTTPException(status_code=404, detail="Could not extract stream from URL")
        return {
            "success": True,
            **result
        }
    except HTTPException:
        raise
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
# STREAM PROXY ENDPOINT (Bypass Cloudflare)
# =============================================================================

@app.get("/api/proxy/m3u8", tags=["Streaming"])
async def proxy_m3u8(
    request: Request,
    url: str = Query(..., description="Base64 encoded m3u8 URL"),
    ref: str = Query(None, description="Base64 encoded referer URL"),
    referer: str = Query("https://megacloud.blog/", description="Referer header (deprecated, use ref)")
):
    """
    Proxy endpoint to fetch m3u8 streams through the server.
    This bypasses Cloudflare protection by making the request server-side.
    All segment URLs are rewritten to go through the proxy for seamless playback.
    
    Usage:
    1. Base64 encode your m3u8 URL
    2. Call: /api/proxy/m3u8?url={base64_encoded_url}&ref={base64_encoded_referer}
    
    Example:
    - Original URL: https://example.com/master.m3u8
    - Encoded: aHR0cHM6Ly9leGFtcGxlLmNvbS9tYXN0ZXIubTN1OA==
    - Call: /api/proxy/m3u8?url=aHR0cHM6Ly9leGFtcGxlLmNvbS9tYXN0ZXIubTN1OA==
    """
    try:
        # Decode URL
        try:
            decoded_url = base64.b64decode(url).decode('utf-8')
        except:
            # If not base64, try using directly
            decoded_url = url
        
        # Decode referer from base64 if provided
        actual_referer = referer  # Use old param as fallback
        if ref:
            try:
                actual_referer = base64.b64decode(ref).decode('utf-8')
            except:
                pass
        
        # Try to determine the correct referer based on the CDN domain
        if not ref:
            url_lower = decoded_url.lower()
            # Map CDN domains to their required referers
            if 'megacloud' in url_lower or 'rapid-cloud' in url_lower:
                actual_referer = "https://megacloud.blog/"
            elif 'vidplay' in url_lower or 'vidstream' in url_lower:
                actual_referer = "https://vidplay.site/"
            elif 'filemoon' in url_lower:
                actual_referer = "https://filemoon.sx/"
            elif 'rabbitstream' in url_lower:
                actual_referer = "https://rabbitstream.net/"
            # New CDN patterns (sunburst, rainveil, brstorm, etc.)
            elif any(cdn in url_lower for cdn in ['sunburst', 'rainveil', 'brstorm', 'binanime', 'cdn.', 'cache', 'hls']):
                actual_referer = "https://megacloud.blog/"
            # For other unknown CDNs, use megacloud as default (most common)
            else:
                actual_referer = "https://megacloud.blog/"
        
        headers = {
            "Referer": actual_referer,
            "Origin": actual_referer.rstrip('/').rsplit('/', 1)[0] if '/' in actual_referer else actual_referer,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
        }
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(decoded_url, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Upstream returned {response.status_code}"
                )
            
            content = response.content
            content_type = response.headers.get('content-type', 'application/vnd.apple.mpegurl')
            
            # Get base URL for the API proxy
            # Use X-Forwarded headers if behind reverse proxy, otherwise use request base
            forwarded_proto = request.headers.get('x-forwarded-proto', request.url.scheme)
            forwarded_host = request.headers.get('x-forwarded-host', request.url.netloc)
            api_base_url = f"{forwarded_proto}://{forwarded_host}"
            
            # If it's an m3u8 playlist, rewrite ALL URLs to go through our proxy
            if b'#EXTM3U' in content or '.m3u8' in decoded_url:
                base_url = '/'.join(decoded_url.split('/')[:-1])
                lines = content.decode('utf-8').split('\n')
                new_lines = []
                
                # Encode the referer to pass along to sub-requests
                encoded_referer = base64.b64encode(actual_referer.encode()).decode()
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        new_lines.append(line)
                        continue
                    
                    if line.startswith('#'):
                        # Handle URI in tags like #EXT-X-KEY:URI="..."
                        if 'URI="' in line:
                            def replace_uri(match):
                                uri = match.group(1)
                                if not uri.startswith('http'):
                                    uri = f"{base_url}/{uri}"
                                encoded = base64.b64encode(uri.encode()).decode()
                                return f'URI="{api_base_url}/api/proxy/segment?url={encoded}&ref={encoded_referer}"'
                            line = re.sub(r'URI="([^"]+)"', replace_uri, line)
                        new_lines.append(line)
                    else:
                        # This is a URL line (segment or sub-playlist)
                        segment_url = line
                        if not segment_url.startswith('http'):
                            segment_url = f"{base_url}/{segment_url}"
                        
                        # Encode and proxy through appropriate endpoint
                        encoded = base64.b64encode(segment_url.encode()).decode()
                        if segment_url.endswith('.m3u8'):
                            # Sub-playlist - proxy through m3u8 endpoint with referer
                            proxied_url = f"{api_base_url}/api/proxy/m3u8?url={encoded}&ref={encoded_referer}"
                        else:
                            # Segment (.ts, .aac, etc.) - proxy through segment endpoint with referer
                            proxied_url = f"{api_base_url}/api/proxy/segment?url={encoded}&ref={encoded_referer}"
                        new_lines.append(proxied_url)
                
                content = '\n'.join(new_lines).encode('utf-8')
            
            return Response(
                content=content,
                media_type=content_type,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                    "Cache-Control": "no-cache"
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/proxy/segment", tags=["Streaming"])
async def proxy_segment(
    url: str = Query(..., description="Base64 encoded segment URL"),
    ref: str = Query(None, description="Base64 encoded referer URL"),
    referer: str = Query("https://megacloud.blog/", description="Referer header (deprecated, use ref)")
):
    """
    Proxy endpoint for HLS segments (.ts, .aac, encryption keys, etc.).
    This is the main segment proxy used by the m3u8 rewriter.
    Automatically detects content type from the response.
    """
    try:
        try:
            decoded_url = base64.b64decode(url).decode('utf-8')
        except:
            decoded_url = url
        
        # Decode referer from base64 if provided
        actual_referer = referer
        if ref:
            try:
                actual_referer = base64.b64decode(ref).decode('utf-8')
            except:
                pass
        
        headers = {
            "Referer": actual_referer,
            "Origin": actual_referer.rstrip('/').rsplit('/', 1)[0] if '/' in actual_referer else actual_referer,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
        }
        
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(decoded_url, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Segment fetch failed")
            
            # Determine content type from response or URL
            content_type = response.headers.get('content-type', 'application/octet-stream')
            if decoded_url.endswith('.ts'):
                content_type = "video/mp2t"
            elif decoded_url.endswith('.aac') or decoded_url.endswith('.m4a'):
                content_type = "audio/aac"
            elif decoded_url.endswith('.key') or 'key' in decoded_url:
                content_type = "application/octet-stream"
            
            return Response(
                content=response.content,
                media_type=content_type,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                    "Cache-Control": "max-age=3600"
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/proxy/ts", tags=["Streaming"])
async def proxy_ts_segment(
    url: str = Query(..., description="Base64 encoded .ts segment URL"),
    referer: str = Query("https://megacloud.blog/", description="Referer header")
):
    """
    Proxy endpoint for .ts video segments (legacy - use /api/proxy/segment instead).
    Use this when playing HLS streams that require header authentication.
    """
    try:
        try:
            decoded_url = base64.b64decode(url).decode('utf-8')
        except:
            decoded_url = url
        
        headers = {
            "Referer": referer,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(decoded_url, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Segment fetch failed")
            
            return Response(
                content=response.content,
                media_type="video/mp2t",
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "*"
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# COMBINED ENDPOINTS (HiAnime + MAL)
# =============================================================================

@app.get("/api/player", tags=["Streaming"], response_class=HTMLResponse)
async def video_player(
    request: Request,
    url: str = Query(..., description="Base64 encoded m3u8 URL"),
    ref: str = Query(None, description="Base64 encoded referer URL")
):
    """
    HTML video player page that plays m3u8 streams using HLS.js.
    
    Usage:
    1. Base64 encode your m3u8 URL
    2. Open: /api/player?url={base64_encoded_url}&ref={base64_encoded_referer}
    
    This provides a web-based video player instead of downloading the m3u8 file.
    """
    # Build the proxy URL
    forwarded_proto = request.headers.get('x-forwarded-proto', request.url.scheme)
    forwarded_host = request.headers.get('x-forwarded-host', request.url.netloc)
    api_base_url = f"{forwarded_proto}://{forwarded_host}"
    
    proxy_url = f"{api_base_url}/api/proxy/m3u8?url={url}"
    if ref:
        proxy_url += f"&ref={ref}"
    
    # Decode URL for display
    try:
        decoded_url = base64.b64decode(url).decode('utf-8')
    except:
        decoded_url = url
    
    html_content = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HiAnime Stream Player</title>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            background: #0f0f0f;
            color: #fff;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }}
        h1 {{
            margin-bottom: 20px;
            color: #ff6b9d;
        }}
        .player-container {{
            width: 100%;
            max-width: 1200px;
            background: #1a1a1a;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        }}
        video {{
            width: 100%;
            max-height: 80vh;
            background: #000;
        }}
        .controls {{
            padding: 15px 20px;
            background: #1a1a1a;
            border-top: 1px solid #333;
        }}
        .info {{
            margin-top: 20px;
            padding: 15px 20px;
            background: #1a1a1a;
            border-radius: 8px;
            width: 100%;
            max-width: 1200px;
        }}
        .info p {{
            color: #888;
            font-size: 12px;
            word-break: break-all;
        }}
        .status {{
            padding: 10px;
            text-align: center;
            color: #888;
        }}
        .error {{
            color: #ff4444;
            padding: 20px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <h1>🎬 HiAnime Stream Player</h1>
    
    <div class="player-container">
        <video id="video" controls autoplay></video>
        <div id="status" class="status">Loading stream...</div>
    </div>
    
    <div class="info">
        <p><strong>Stream URL:</strong> {decoded_url[:100]}...</p>
    </div>

    <script>
        const video = document.getElementById('video');
        const status = document.getElementById('status');
        const streamUrl = "{proxy_url}";
        
        if (Hls.isSupported()) {{
            const hls = new Hls({{
                debug: false,
                enableWorker: true,
                lowLatencyMode: true,
                backBufferLength: 90
            }});
            
            hls.loadSource(streamUrl);
            hls.attachMedia(video);
            
            hls.on(Hls.Events.MANIFEST_PARSED, function(event, data) {{
                status.textContent = 'Stream ready - ' + data.levels.length + ' quality levels available';
                video.play().catch(e => {{
                    status.textContent = 'Click to play';
                }});
            }});
            
            hls.on(Hls.Events.ERROR, function(event, data) {{
                if (data.fatal) {{
                    status.innerHTML = '<span class="error">Error: ' + data.type + ' - ' + data.details + '</span>';
                    switch(data.type) {{
                        case Hls.ErrorTypes.NETWORK_ERROR:
                            console.log('Network error, trying to recover...');
                            hls.startLoad();
                            break;
                        case Hls.ErrorTypes.MEDIA_ERROR:
                            console.log('Media error, trying to recover...');
                            hls.recoverMediaError();
                            break;
                        default:
                            hls.destroy();
                            break;
                    }}
                }}
            }});
            
            hls.on(Hls.Events.LEVEL_SWITCHED, function(event, data) {{
                const level = hls.levels[data.level];
                if (level) {{
                    status.textContent = 'Playing: ' + level.width + 'x' + level.height + ' @ ' + Math.round(level.bitrate/1000) + 'kbps';
                }}
            }});
        }} else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
            // Safari native HLS support
            video.src = streamUrl;
            video.addEventListener('loadedmetadata', function() {{
                status.textContent = 'Stream ready (native HLS)';
                video.play();
            }});
        }} else {{
            status.innerHTML = '<span class="error">Your browser does not support HLS playback</span>';
        }}
    </script>
</body>
</html>
'''
    return HTMLResponse(content=html_content)


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
# DOWNLOAD ENDPOINT (Get downloadable video links)
# =============================================================================

@app.get("/api/download/{episode_id}", tags=["Download"])
async def get_download_links(
    request: Request,
    episode_id: str,
    server_type: str = Query("sub", description="Server type: sub, dub, or all"),
    quality: str = Query("auto", description="Preferred quality: auto, 1080p, 720p, 480p, 360p")
):
    """
    📥 Get downloadable video links for an episode
    
    Returns video URLs optimized for downloading. Includes:
    - Direct stream URLs with required headers
    - Proxy URLs that work without headers (for simpler downloaders)
    - Download commands for ffmpeg/yt-dlp
    
    **Parameters:**
    - **episode_id**: Episode ID from the URL (e.g., "2142" from ?ep=2142)
    - **server_type**: "sub" (default), "dub", or "all"
    - **quality**: Preferred quality (auto selects best available)
    
    **Response includes:**
    - `download_options`: List of downloadable streams
    - Each option has `direct_url`, `proxy_url`, and `download_commands`
    
    **Usage:**
    1. Use `proxy_url` for simple HTTP downloads (no headers needed)
    2. Use `direct_url` with provided `headers` for advanced tools
    3. Use `download_commands.ffmpeg` to download with ffmpeg
    4. Use `download_commands.yt_dlp` to download with yt-dlp
    """
    try:
        # Get streaming links first
        result = scraper.get_streaming_links(episode_id, server_type)
        
        if not result.get('streams'):
            return {
                "success": False,
                "error": "No streams found for this episode",
                "episode_id": episode_id
            }
        
        # Get base URL for proxy
        forwarded_proto = request.headers.get('x-forwarded-proto', request.url.scheme)
        forwarded_host = request.headers.get('x-forwarded-host', request.url.netloc)
        api_base_url = f"{forwarded_proto}://{forwarded_host}"
        
        download_options = []
        
        for stream in result['streams']:
            server_name = stream.get('server_name', 'Unknown')
            server_type_str = stream.get('server_type', 'sub')
            
            for source in stream.get('sources', []):
                direct_url = source.get('file', '')
                if not direct_url:
                    continue
                
                source_headers = source.get('headers', stream.get('headers', {}))
                referer = source_headers.get('Referer', 'https://megacloud.blog/')
                user_agent = source_headers.get('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                
                # Create proxy URL (no headers needed for this)
                encoded_url = base64.b64encode(direct_url.encode()).decode()
                encoded_referer = base64.b64encode(referer.encode()).decode()
                proxy_url = f"{api_base_url}/api/proxy/m3u8?url={encoded_url}&ref={encoded_referer}"
                
                # Generate download commands
                # FFmpeg command for HLS streams
                ffmpeg_cmd = f'ffmpeg -headers "Referer: {referer}\\r\\nUser-Agent: {user_agent}\\r\\n" -i "{direct_url}" -c copy -bsf:a aac_adtstoasc "output.mp4"'
                
                # yt-dlp command (works with most streams)
                ytdlp_cmd = f'yt-dlp --referer "{referer}" --user-agent "{user_agent}" -o "%(title)s.%(ext)s" "{direct_url}"'
                
                # aria2c for direct downloads (if MP4)
                aria2_cmd = f'aria2c --referer="{referer}" --user-agent="{user_agent}" -o "output.mp4" "{direct_url}"'
                
                download_option = {
                    "server": f"{server_name} ({server_type_str.upper()})",
                    "quality": source.get('quality', 'auto'),
                    "type": source.get('type', 'hls'),
                    "is_m3u8": source.get('isM3U8', True),
                    "direct_url": direct_url,
                    "proxy_url": proxy_url,
                    "headers": source_headers,
                    "download_commands": {
                        "ffmpeg": ffmpeg_cmd,
                        "yt_dlp": ytdlp_cmd,
                        "aria2c": aria2_cmd if not source.get('isM3U8', True) else None
                    },
                    "notes": {
                        "proxy_url": "Use this URL directly - no headers needed, works in browsers and simple downloaders",
                        "direct_url": "Requires headers to be sent with the request",
                        "ffmpeg": "Best for HLS (.m3u8) streams - converts to MP4",
                        "yt_dlp": "Universal downloader - handles most video formats automatically"
                    }
                }
                
                # Add subtitles info if available
                if stream.get('subtitles'):
                    download_option['subtitles'] = stream['subtitles']
                
                download_options.append(download_option)
        
        # Filter by quality if specified
        if quality != "auto":
            filtered = [opt for opt in download_options if quality in opt.get('quality', '').lower()]
            if filtered:
                download_options = filtered
        
        return {
            "success": True,
            "episode_id": episode_id,
            "server_type": server_type,
            "total_options": len(download_options),
            "download_options": download_options,
            "instructions": {
                "browser": "Copy the proxy_url and paste in browser to download",
                "mobile_app": "Use proxy_url with any HTTP download library",
                "desktop": "Use ffmpeg or yt-dlp commands for best results",
                "flutter": "Use dio or http package with proxy_url (no headers needed)"
            },
            "recommended": {
                "method": "proxy_url",
                "reason": "Works without additional configuration - headers are handled server-side"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# MP4 VIDEO DOWNLOAD (Downloads all segments and converts to MP4)
# =============================================================================

# Store for tracking download progress
download_progress = {}


@app.get("/api/download/mp4/check", tags=["Download"])
async def check_ffmpeg():
    """
    Check if FFmpeg is available for MP4 conversion
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            return {
                "success": True,
                "ffmpeg_available": True,
                "version": version_line,
                "message": "FFmpeg is available. MP4 downloads will work!"
            }
    except:
        pass
    
    return {
        "success": True,
        "ffmpeg_available": False,
        "message": "FFmpeg not found."
    }


@app.get("/api/download/mp4/{episode_id}", tags=["Download"])
async def download_video_mp4(
    request: Request,
    background_tasks: BackgroundTasks,
    episode_id: str,
    server_type: str = Query("sub", description="Server type: sub or dub"),
    server_index: int = Query(0, description="Server index (0 = first/best)"),
    filename: Optional[str] = Query(None, description="Custom filename (without extension)"),
    quality: str = Query("best", description="Quality: best, 1080, 720, 480, 360")
):
    """
    📥 Download video as MP4 - FAST PARALLEL SEGMENT DOWNLOAD!
    
    Downloads segments in parallel (100 concurrent) and merges them into MP4.
    Handles encrypted/protected HLS streams with .jpg segments.
    """
    temp_dir = None
    try:
        # Get streaming links
        result = scraper.get_streaming_links(episode_id, server_type)
        
        if not result.get('streams'):
            raise HTTPException(status_code=404, detail="No streams found")
        
        streams = result['streams']
        if server_index >= len(streams):
            server_index = 0
        
        stream = streams[server_index]
        sources = stream.get('sources', [])
        
        if not sources:
            raise HTTPException(status_code=404, detail="No sources found")
        
        source = sources[0]
        m3u8_url = source.get('file', '')
        
        if not m3u8_url:
            raise HTTPException(status_code=404, detail="No M3U8 URL")
        
        source_headers = source.get('headers', stream.get('headers', {}))
        referer = source_headers.get('Referer', 'https://megacloud.blog/')
        
        if filename:
            output_filename = f"{filename}.mp4"
        else:
            output_filename = f"episode_{episode_id}_{server_type}.mp4"
        
        temp_dir = tempfile.mkdtemp(prefix=f"dl_{episode_id}_")
        output_file = os.path.join(temp_dir, "output.mp4")
        
        # ============================================
        # STEP 1: Download all segments in parallel
        # ============================================
        start_time = time.time()
        print(f"\n{'='*60}")
        print(f"🎬 FAST DOWNLOAD: Episode {episode_id}")
        print(f"{'='*60}")
        
        headers = {
            "Referer": referer,
            "Origin": referer.rstrip('/'),
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        
        connector = httpx.Limits(max_keepalive_connections=100, max_connections=100)
        
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
            follow_redirects=True,
            limits=connector
        ) as client:
            
            # Get M3U8 playlist
            print("📋 Fetching playlist...")
            resp = await client.get(m3u8_url, headers=headers)
            m3u8_content = resp.text
            
            base_url = m3u8_url.rsplit('/', 1)[0] + '/'
            
            # Check if master playlist - need to get variant playlist
            actual_m3u8_url = m3u8_url
            if '#EXT-X-STREAM-INF' in m3u8_content:
                print("📋 Found master playlist, selecting quality...")
                lines = m3u8_content.strip().split('\n')
                variants = []
                
                for i, line in enumerate(lines):
                    if line.startswith('#EXT-X-STREAM-INF'):
                        resolution = None
                        bandwidth = 0
                        if 'RESOLUTION=' in line:
                            res_match = line.split('RESOLUTION=')[1].split(',')[0].split('x')
                            if len(res_match) >= 2:
                                resolution = int(res_match[1])
                        if 'BANDWIDTH=' in line:
                            bw_str = line.split('BANDWIDTH=')[1].split(',')[0]
                            bandwidth = int(bw_str)
                        
                        if i + 1 < len(lines):
                            url = lines[i + 1].strip()
                            if not url.startswith('http'):
                                url = urljoin(base_url, url)
                            variants.append({
                                'url': url,
                                'resolution': resolution,
                                'bandwidth': bandwidth
                            })
                
                if variants:
                    variants.sort(key=lambda x: (x['resolution'] or 0, x['bandwidth']), reverse=True)
                    selected = variants[0]
                    if quality != "best":
                        target = int(quality)
                        for v in variants:
                            if v['resolution'] and v['resolution'] <= target:
                                selected = v
                                break
                    
                    actual_m3u8_url = selected['url']
                    print(f"✅ Selected: {selected['resolution']}p (bandwidth: {selected['bandwidth']})")
                    
                    # Fetch the variant playlist
                    resp = await client.get(actual_m3u8_url, headers=headers)
                    m3u8_content = resp.text
                    base_url = actual_m3u8_url.rsplit('/', 1)[0] + '/'
            
            # Parse segments from playlist
            segments = []
            for line in m3u8_content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    if line.startswith('http'):
                        segments.append(line)
                    else:
                        segments.append(urljoin(base_url, line))
            
            total = len(segments)
            print(f"📦 Found {total} segments")
            
            if not segments:
                raise HTTPException(status_code=500, detail="No segments found in playlist")
            
            # PARALLEL DOWNLOAD - 100 at a time!
            downloaded = [0]
            failed = [0]
            semaphore = asyncio.Semaphore(100)
            
            async def download_one(idx, url):
                async with semaphore:
                    path = os.path.join(temp_dir, f"seg_{idx:05d}.ts")
                    for attempt in range(3):  # Retry up to 3 times
                        try:
                            r = await client.get(url, headers=headers)
                            r.raise_for_status()
                            content = r.content
                            if len(content) > 0:
                                with open(path, 'wb') as f:
                                    f.write(content)
                                downloaded[0] += 1
                                if downloaded[0] % 10 == 0 or downloaded[0] == total:
                                    pct = int(downloaded[0] * 100 / total)
                                    print(f"\r⬇️  Downloading: {downloaded[0]}/{total} ({pct}%)", end="", flush=True)
                                return path
                        except Exception as e:
                            if attempt == 2:
                                failed[0] += 1
                                return None
                            await asyncio.sleep(0.5)
                    return None
            
            print(f"⚡ Downloading {total} segments (100 parallel)...")
            
            tasks = [download_one(i, url) for i, url in enumerate(segments)]
            results = await asyncio.gather(*tasks)
            
            seg_files = [r for r in results if r]
            print(f"\n✅ Downloaded: {len(seg_files)}/{total} segments")
            
            if len(seg_files) < total * 0.9:
                raise HTTPException(status_code=500, detail=f"Too many failures: {failed[0]}/{total}")
        
        # ============================================
        # STEP 2: Convert to MP4 with FFmpeg
        # ============================================
        print("🔄 Converting to MP4...", flush=True)
        
        concat_file = os.path.join(temp_dir, "list.txt")
        with open(concat_file, 'w') as f:
            for sf in sorted(seg_files):
                f.write(f"file '{sf}'\n")
        
        print(f"📝 Created concat list: {concat_file}", flush=True)
        
        # Try FFmpeg concat first - use subprocess.run for simplicity (sync is ok here)
        import subprocess
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
            "-f", "concat", "-safe", "0", "-i", concat_file,
            "-c", "copy", "-bsf:a", "aac_adtstoasc",
            "-movflags", "+faststart", output_file
        ]
        
        print(f"🚀 Running FFmpeg...", flush=True)
        proc_result = subprocess.run(ffmpeg_cmd, capture_output=True, timeout=300)
        stdout = proc_result.stdout
        stderr = proc_result.stderr
        print(f"📍 FFmpeg finished with code: {proc_result.returncode}", flush=True)
        
        if proc_result.returncode != 0 or not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
            print(f"⚠️ FFmpeg concat failed (rc={proc_result.returncode}), trying direct merge...", flush=True)
            if stderr:
                print(f"FFmpeg stderr: {stderr.decode()[:500]}", flush=True)
            
            # Fallback: direct binary concat then remux
            ts_file = os.path.join(temp_dir, "combined.ts")
            with open(ts_file, 'wb') as out:
                for sf in sorted(seg_files):
                    with open(sf, 'rb') as inp:
                        out.write(inp.read())
            
            print(f"📦 Combined TS size: {os.path.getsize(ts_file)/1024/1024:.1f}MB", flush=True)
            
            # Now remux to MP4
            ffmpeg_cmd2 = [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
                "-i", ts_file,
                "-c", "copy", "-bsf:a", "aac_adtstoasc",
                "-movflags", "+faststart", output_file
            ]
            
            print(f"🚀 Running FFmpeg remux...", flush=True)
            proc_result2 = subprocess.run(ffmpeg_cmd2, capture_output=True, timeout=300)
            stdout2 = proc_result2.stdout
            stderr2 = proc_result2.stderr
            print(f"📍 FFmpeg remux finished with code: {proc_result2.returncode}", flush=True)
            
            if proc_result2.returncode != 0 or not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
                print(f"⚠️ FFmpeg remux failed (rc={proc_result2.returncode})", flush=True)
                if stderr2:
                    print(f"FFmpeg stderr: {stderr2.decode()[:500]}")
                # Last resort: use TS file directly
                print("⚠️ Using raw TS file...")
                output_file = ts_file
                output_filename = output_filename.replace('.mp4', '.ts')
        
        if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
            raise HTTPException(status_code=500, detail="Failed to create output file")
        
        file_size = os.path.getsize(output_file)
        elapsed = time.time() - start_time
        
        print(f"✅ Ready! Size: {file_size/1024/1024:.1f}MB, Time: {elapsed:.1f}s")
        print(f"📤 Streaming to client...")
        
        # ============================================
        # STEP 3: Stream file to client
        # ============================================
        final_output_file = output_file  # Capture for closure
        final_temp_dir = temp_dir  # Capture for cleanup
        
        def file_iterator():
            """Generator to stream file in chunks"""
            try:
                with open(final_output_file, 'rb') as f:
                    while chunk := f.read(1048576):  # 1MB chunks
                        yield chunk
                print(f"🎉 Download complete! Total time: {time.time() - start_time:.1f}s")
            except Exception as e:
                print(f"❌ Error streaming: {e}")
        
        # Schedule cleanup after response
        def cleanup():
            try:
                shutil.rmtree(final_temp_dir, ignore_errors=True)
                print(f"🧹 Cleaned up: {final_temp_dir}")
            except Exception as e:
                print(f"⚠️ Cleanup error: {e}")
        
        background_tasks.add_task(cleanup)
        
        return StreamingResponse(
            file_iterator(),
            media_type="video/mp4" if output_file.endswith('.mp4') else "video/mp2t",
            headers={
                "Content-Disposition": f'attachment; filename="{output_filename}"',
                "Content-Length": str(file_size),
                "Access-Control-Allow-Origin": "*",
            }
        )
        
    except HTTPException:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as e:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/mp4/status/{episode_id}", tags=["Download"])
async def get_download_status(episode_id: str):
    """
    Check download progress for an episode
    
    Returns the current download status and progress percentage.
    """
    if episode_id in download_progress:
        return download_progress[episode_id]
    return {
        "status": "not_started",
        "progress": 0,
        "message": "Download not started or already completed"
    }


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
