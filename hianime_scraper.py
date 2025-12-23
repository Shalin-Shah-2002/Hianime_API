"""
HiAnime.to Web Scraper - Production-Ready Implementation
========================================================
A comprehensive scraper for extracting anime data from HiAnime.to

Author: Senior Web Scraping Engineer
Version: 1.0.0
Date: December 2024

Features:
- Search functionality with advanced filters
- Browse by category, genre, type
- Anime detail extraction
- Episode list retrieval
- Rate limiting and retry logic
- Proxy rotation support
- Session management
"""

import os
import re
import json
import time
import random
import logging
from typing import Optional, List, Dict, Any, Generator
from dataclasses import dataclass, asdict, field
from urllib.parse import urljoin, urlencode, quote
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class AnimeInfo:
    """Data model for anime information"""
    id: str
    slug: str
    title: str
    url: str
    thumbnail: Optional[str] = None
    type: Optional[str] = None  # TV, Movie, OVA, ONA, Special
    duration: Optional[str] = None
    rating: Optional[str] = None  # PG-13, 18+, etc.
    status: Optional[str] = None  # Airing, Finished
    episodes_sub: Optional[int] = None
    episodes_dub: Optional[int] = None
    mal_score: Optional[float] = None
    synopsis: Optional[str] = None
    japanese_title: Optional[str] = None
    synonyms: Optional[str] = None
    aired: Optional[str] = None
    premiered: Optional[str] = None
    genres: List[str] = field(default_factory=list)
    studios: List[str] = field(default_factory=list)
    producers: List[str] = field(default_factory=list)


@dataclass
class SearchResult:
    """Data model for search results"""
    title: str
    url: str
    id: str
    slug: str  # e.g., "naruto-677" - use this for get_episodes/get_details
    thumbnail: Optional[str] = None
    type: Optional[str] = None
    duration: Optional[str] = None
    episodes_sub: Optional[int] = None
    episodes_dub: Optional[int] = None


@dataclass
class Episode:
    """Data model for episode information"""
    number: int
    title: Optional[str] = None
    url: Optional[str] = None
    id: Optional[str] = None
    japanese_title: Optional[str] = None
    is_filler: bool = False


@dataclass
class VideoServer:
    """Data model for video server information"""
    server_id: str
    server_name: str
    server_type: str  # "sub", "dub", or "raw"


@dataclass
class VideoSource:
    """Data model for video source information"""
    episode_id: str
    server_id: str
    server_name: str
    server_type: str  # "sub", "dub", or "raw"
    sources: List[Dict[str, Any]] = field(default_factory=list)  # Contains url, quality, type
    tracks: List[Dict[str, Any]] = field(default_factory=list)  # Subtitles/captions
    intro: Optional[Dict[str, int]] = None  # Intro skip times
    outro: Optional[Dict[str, int]] = None  # Outro skip times


# =============================================================================
# CONFIGURATION
# =============================================================================

class ScraperConfig:
    """Configuration settings for the scraper"""
    
    BASE_URL = os.getenv("BASE_URL", "https://hianime.to")
    CDN_URL = "https://cdn.noitatnemucod.net"
    
    # Rate limiting
    MIN_DELAY = 1.0  # Minimum seconds between requests
    MAX_DELAY = 3.0  # Maximum seconds between requests
    
    # Retry settings
    MAX_RETRIES = 3
    RETRY_BACKOFF = 0.5
    
    # Timeout settings
    REQUEST_TIMEOUT = 30
    
    # User agents for rotation
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    # Available genres
    GENRES = [
        "action", "adventure", "cars", "comedy", "dementia", "demons", 
        "drama", "ecchi", "fantasy", "game", "harem", "historical", 
        "horror", "isekai", "josei", "kids", "magic", "marial-arts", 
        "mecha", "military", "music", "mystery", "parody", "police", 
        "psychological", "romance", "samurai", "school", "sci-fi", 
        "seinen", "shoujo", "shoujo-ai", "shounen", "shounen-ai", 
        "slice-of-life", "space", "sports", "super-power", "supernatural", 
        "thriller", "vampire"
    ]
    
    # Available types
    TYPES = ["movie", "tv", "ova", "ona", "special", "music"]
    
    # Status options
    STATUSES = ["finished", "airing", "upcoming"]
    
    # Sort options
    SORT_OPTIONS = [
        "default", "recently_added", "recently_updated", 
        "score", "name_az", "released_date", "most_watched"
    ]


# =============================================================================
# HTTP CLIENT
# =============================================================================

class HTTPClient:
    """Handles HTTP requests with retry logic and rate limiting"""
    
    def __init__(
        self,
        proxies: Optional[List[str]] = None,
        rate_limit: bool = True
    ):
        self.session = self._create_session()
        self.proxies = proxies or []
        self.proxy_index = 0
        self.rate_limit = rate_limit
        self.last_request_time = 0
        
    def _create_session(self) -> requests.Session:
        """Create a session with retry strategy"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=ScraperConfig.MAX_RETRIES,
            backoff_factor=ScraperConfig.RETRY_BACKOFF,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with random user agent"""
        return {
            "User-Agent": random.choice(ScraperConfig.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    
    def _get_proxy(self) -> Optional[Dict[str, str]]:
        """Get next proxy from rotation"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.proxy_index]
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        
        return {
            "http": proxy,
            "https": proxy
        }
    
    def _apply_rate_limit(self):
        """Apply rate limiting between requests"""
        if not self.rate_limit:
            return
            
        elapsed = time.time() - self.last_request_time
        delay = random.uniform(ScraperConfig.MIN_DELAY, ScraperConfig.MAX_DELAY)
        
        if elapsed < delay:
            time.sleep(delay - elapsed)
        
        self.last_request_time = time.time()
    
    def get(self, url: str, params: Optional[Dict] = None) -> requests.Response:
        """Make a GET request with all protections"""
        self._apply_rate_limit()
        
        try:
            response = self.session.get(
                url,
                params=params,
                headers=self._get_headers(),
                proxies=self._get_proxy(),
                timeout=ScraperConfig.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response
            
        except requests.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            raise


# =============================================================================
# PARSER UTILITIES
# =============================================================================

class ParserUtils:
    """Utility functions for parsing HTML content"""
    
    @staticmethod
    def extract_anime_id(url: str) -> str:
        """Extract anime ID from URL"""
        match = re.search(r'-(\d+)(?:\?|$)', url)
        return match.group(1) if match else ""
    
    @staticmethod
    def extract_slug(url: str) -> str:
        """Extract full slug from URL (e.g., 'naruto-677' from '/naruto-677?ref=search')"""
        # Get the last path segment and remove query params
        path = url.split('/')[-1].split('?')[0]
        return path if path else ""
    
    @staticmethod
    def parse_episode_count(text: str) -> Optional[int]:
        """Parse episode count from text"""
        if not text:
            return None
        try:
            # Handle formats like "220", "220 220", etc.
            numbers = re.findall(r'\d+', text.strip())
            return int(numbers[0]) if numbers else None
        except (ValueError, IndexError):
            return None
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        return ' '.join(text.split()).strip()


# =============================================================================
# MAIN SCRAPER CLASS
# =============================================================================

class HiAnimeScraper:
    """Main scraper class for HiAnime.to"""
    
    def __init__(
        self,
        proxies: Optional[List[str]] = None,
        rate_limit: bool = True
    ):
        self.client = HTTPClient(proxies=proxies, rate_limit=rate_limit)
        self.base_url = ScraperConfig.BASE_URL
    
    def _get_soup(self, url: str, params: Optional[Dict] = None) -> BeautifulSoup:
        """Get BeautifulSoup object from URL"""
        response = self.client.get(url, params=params)
        return BeautifulSoup(response.text, 'html.parser')
    
    # =========================================================================
    # SEARCH METHODS
    # =========================================================================
    
    def search(
        self,
        keyword: str,
        page: int = 1
    ) -> List[SearchResult]:
        """
        Search for anime by keyword
        
        Args:
            keyword: Search term
            page: Page number (default 1)
            
        Returns:
            List of SearchResult objects
        """
        url = f"{self.base_url}/search"
        params = {"keyword": keyword, "page": page}
        
        logger.info(f"Searching for: {keyword} (page {page})")
        soup = self._get_soup(url, params)
        
        results = []
        anime_items = soup.select('.flw-item')
        
        for item in anime_items:
            try:
                title_elem = item.select_one('.film-name a')
                if not title_elem:
                    continue
                
                title = ParserUtils.clean_text(title_elem.text)
                href = title_elem.get('href', '')
                anime_url = urljoin(self.base_url, href)
                anime_id = ParserUtils.extract_anime_id(href)
                slug = ParserUtils.extract_slug(href)
                
                # Thumbnail
                img_elem = item.select_one('.film-poster img')
                thumbnail = img_elem.get('data-src') or img_elem.get('src') if img_elem else None
                
                # Type and duration
                type_elem = item.select_one('.fdi-item')
                anime_type = ParserUtils.clean_text(type_elem.text) if type_elem else None
                
                duration_elem = item.select_one('.fdi-duration')
                duration = ParserUtils.clean_text(duration_elem.text) if duration_elem else None
                
                # Episode counts
                sub_elem = item.select_one('.tick-sub')
                dub_elem = item.select_one('.tick-dub')
                
                results.append(SearchResult(
                    title=title,
                    url=anime_url,
                    id=anime_id,
                    slug=slug,
                    thumbnail=thumbnail,
                    type=anime_type,
                    duration=duration,
                    episodes_sub=ParserUtils.parse_episode_count(sub_elem.text if sub_elem else ""),
                    episodes_dub=ParserUtils.parse_episode_count(dub_elem.text if dub_elem else "")
                ))
                
            except Exception as e:
                logger.warning(f"Failed to parse search result: {e}")
                continue
        
        logger.info(f"Found {len(results)} results")
        return results
    
    def advanced_filter(
        self,
        type: Optional[str] = None,
        status: Optional[str] = None,
        rated: Optional[str] = None,
        score: Optional[int] = None,
        season: Optional[str] = None,
        language: Optional[str] = None,
        genres: Optional[List[str]] = None,
        sort: Optional[str] = None,
        page: int = 1
    ) -> List[SearchResult]:
        """
        Search with advanced filters
        
        Args:
            type: Anime type (movie, tv, ova, ona, special, music)
            status: Airing status (finished, airing, upcoming)
            rated: Age rating (g, pg, pg-13, r, r+, rx)
            score: Minimum MAL score (1-10)
            season: Season (spring, summer, fall, winter)
            language: Language (sub, dub)
            genres: List of genre slugs
            sort: Sort order
            page: Page number
            
        Returns:
            List of SearchResult objects
        """
        url = f"{self.base_url}/filter"
        params = {"page": page}
        
        if type:
            params["type"] = type
        if status:
            params["status"] = status
        if rated:
            params["rated"] = rated
        if score:
            params["score"] = score
        if season:
            params["season"] = season
        if language:
            params["language"] = language
        if genres:
            params["genres"] = ",".join(genres)
        if sort:
            params["sort"] = sort
        
        logger.info(f"Filtering with params: {params}")
        soup = self._get_soup(url, params)
        
        return self._parse_anime_list(soup)
    
    # =========================================================================
    # BROWSE METHODS
    # =========================================================================
    
    def get_most_popular(self, page: int = 1) -> List[SearchResult]:
        """Get most popular anime"""
        url = f"{self.base_url}/most-popular"
        soup = self._get_soup(url, {"page": page})
        return self._parse_anime_list(soup)
    
    def get_top_airing(self, page: int = 1) -> List[SearchResult]:
        """Get top airing anime"""
        url = f"{self.base_url}/top-airing"
        soup = self._get_soup(url, {"page": page})
        return self._parse_anime_list(soup)
    
    def get_recently_updated(self, page: int = 1) -> List[SearchResult]:
        """Get recently updated anime"""
        url = f"{self.base_url}/recently-updated"
        soup = self._get_soup(url, {"page": page})
        return self._parse_anime_list(soup)
    
    def get_completed(self, page: int = 1) -> List[SearchResult]:
        """Get completed anime"""
        url = f"{self.base_url}/completed"
        soup = self._get_soup(url, {"page": page})
        return self._parse_anime_list(soup)
    
    def get_by_genre(self, genre: str, page: int = 1) -> List[SearchResult]:
        """
        Get anime by genre
        
        Args:
            genre: Genre slug (e.g., "action", "romance")
            page: Page number
        """
        url = f"{self.base_url}/genre/{genre}"
        soup = self._get_soup(url, {"page": page})
        return self._parse_anime_list(soup)
    
    def get_by_type(self, anime_type: str, page: int = 1) -> List[SearchResult]:
        """
        Get anime by type
        
        Args:
            anime_type: Type (movie, tv, ova, ona, special)
            page: Page number
        """
        url = f"{self.base_url}/{anime_type}"
        soup = self._get_soup(url, {"page": page})
        return self._parse_anime_list(soup)
    
    def get_az_list(self, letter: str = "all", page: int = 1) -> List[SearchResult]:
        """
        Get anime by alphabetical listing
        
        Args:
            letter: Letter (A-Z, 0-9, other, or "all")
            page: Page number
        """
        if letter.lower() == "all":
            url = f"{self.base_url}/az-list"
        else:
            url = f"{self.base_url}/az-list/{letter.upper()}"
        
        soup = self._get_soup(url, {"page": page})
        return self._parse_anime_list(soup)
    
    # =========================================================================
    # DETAIL METHODS
    # =========================================================================
    
    def get_anime_details(self, anime_id: str) -> Optional[AnimeInfo]:
        """
        Get detailed information about an anime
        
        Args:
            anime_id: Anime ID or full URL slug
            
        Returns:
            AnimeInfo object with full details
        """
        # Handle both ID and full slug
        if anime_id.startswith("http"):
            url = anime_id
        elif "-" in anime_id:
            url = f"{self.base_url}/{anime_id}"
        else:
            logger.error("Please provide full URL slug (e.g., 'naruto-677')")
            return None
        
        logger.info(f"Fetching details for: {url}")
        soup = self._get_soup(url)
        
        try:
            # Basic info
            title_elem = soup.select_one('.film-name')
            title = ParserUtils.clean_text(title_elem.text) if title_elem else ""
            
            # Synopsis
            synopsis_elem = soup.select_one('.film-description .text')
            synopsis = ParserUtils.clean_text(synopsis_elem.text) if synopsis_elem else ""
            
            # Sidebar info
            info_items = soup.select('.anisc-info .item')
            
            japanese_title = None
            synonyms = None
            aired = None
            premiered = None
            status = None
            mal_score = None
            duration = None
            
            genres = []
            studios = []
            producers = []
            
            for item in info_items:
                label = item.select_one('.item-head')
                value = item.select_one('.name')
                
                if not label:
                    continue
                    
                label_text = ParserUtils.clean_text(label.text).lower()
                
                if "japanese" in label_text:
                    japanese_title = ParserUtils.clean_text(value.text) if value else None
                elif "synonyms" in label_text:
                    synonyms = ParserUtils.clean_text(value.text) if value else None
                elif "aired" in label_text:
                    aired = ParserUtils.clean_text(value.text) if value else None
                elif "premiered" in label_text:
                    premiered = ParserUtils.clean_text(value.text) if value else None
                elif "status" in label_text:
                    status = ParserUtils.clean_text(value.text) if value else None
                elif "mal score" in label_text:
                    score_text = ParserUtils.clean_text(value.text) if value else ""
                    try:
                        mal_score = float(score_text)
                    except ValueError:
                        pass
                elif "duration" in label_text:
                    duration = ParserUtils.clean_text(value.text) if value else None
                elif "genres" in label_text:
                    genre_links = item.select('a')
                    genres = [ParserUtils.clean_text(g.text) for g in genre_links]
                elif "studios" in label_text:
                    studio_links = item.select('a')
                    studios = [ParserUtils.clean_text(s.text) for s in studio_links]
                elif "producers" in label_text:
                    producer_links = item.select('a')
                    producers = [ParserUtils.clean_text(p.text) for p in producer_links]
            
            # Type and rating
            type_elem = soup.select_one('.film-stats .item')
            anime_type = ParserUtils.clean_text(type_elem.text) if type_elem else None
            
            rating_elem = soup.select_one('.tick-pg')
            rating = ParserUtils.clean_text(rating_elem.text) if rating_elem else None
            
            # Episode counts
            sub_elem = soup.select_one('.tick-sub')
            dub_elem = soup.select_one('.tick-dub')
            
            # Thumbnail
            img_elem = soup.select_one('.film-poster img')
            thumbnail = img_elem.get('src') if img_elem else None
            
            # Extract ID and slug from URL
            extracted_id = ParserUtils.extract_anime_id(url)
            slug = ParserUtils.extract_slug(url)
            
            return AnimeInfo(
                id=extracted_id,
                slug=slug,
                title=title,
                url=url,
                thumbnail=thumbnail,
                type=anime_type,
                duration=duration,
                rating=rating,
                status=status,
                episodes_sub=ParserUtils.parse_episode_count(sub_elem.text if sub_elem else ""),
                episodes_dub=ParserUtils.parse_episode_count(dub_elem.text if dub_elem else ""),
                mal_score=mal_score,
                synopsis=synopsis,
                japanese_title=japanese_title,
                synonyms=synonyms,
                aired=aired,
                premiered=premiered,
                genres=genres,
                studios=studios,
                producers=producers
            )
            
        except Exception as e:
            logger.error(f"Failed to parse anime details: {e}")
            return None
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _parse_anime_list(self, soup: BeautifulSoup) -> List[SearchResult]:
        """Parse anime list from page"""
        results = []
        anime_items = soup.select('.flw-item')
        
        for item in anime_items:
            try:
                title_elem = item.select_one('.film-name a')
                if not title_elem:
                    continue
                
                title = ParserUtils.clean_text(title_elem.text)
                href = title_elem.get('href', '')
                anime_url = urljoin(self.base_url, href)
                anime_id = ParserUtils.extract_anime_id(href)
                slug = ParserUtils.extract_slug(href)
                
                # Thumbnail
                img_elem = item.select_one('.film-poster img')
                thumbnail = img_elem.get('data-src') or img_elem.get('src') if img_elem else None
                
                # Type
                type_elem = item.select_one('.fdi-item')
                anime_type = ParserUtils.clean_text(type_elem.text) if type_elem else None
                
                # Duration
                duration_elem = item.select_one('.fdi-duration')
                duration = ParserUtils.clean_text(duration_elem.text) if duration_elem else None
                
                # Episode counts
                sub_elem = item.select_one('.tick-sub')
                dub_elem = item.select_one('.tick-dub')
                
                results.append(SearchResult(
                    title=title,
                    url=anime_url,
                    id=anime_id,
                    slug=slug,
                    thumbnail=thumbnail,
                    type=anime_type,
                    duration=duration,
                    episodes_sub=ParserUtils.parse_episode_count(sub_elem.text if sub_elem else ""),
                    episodes_dub=ParserUtils.parse_episode_count(dub_elem.text if dub_elem else "")
                ))
                
            except Exception as e:
                logger.warning(f"Failed to parse anime item: {e}")
                continue
        
        return results
    
    def get_total_pages(self, soup: BeautifulSoup) -> int:
        """Extract total pages from pagination"""
        last_page = soup.select_one('.pagination .page-item:last-child a')
        if last_page:
            href = last_page.get('href', '')
            match = re.search(r'page=(\d+)', href)
            if match:
                return int(match.group(1))
        return 1
    
    # =========================================================================
    # SUBBED / DUBBED
    # =========================================================================
    
    def get_subbed_anime(self, page: int = 1) -> List[SearchResult]:
        """Get anime with subtitles"""
        url = f"{self.base_url}/subbed-anime"
        soup = self._get_soup(url, {"page": page})
        return self._parse_anime_list(soup)
    
    def get_dubbed_anime(self, page: int = 1) -> List[SearchResult]:
        """Get dubbed anime"""
        url = f"{self.base_url}/dubbed-anime"
        soup = self._get_soup(url, {"page": page})
        return self._parse_anime_list(soup)
    
    # =========================================================================
    # PRODUCER / STUDIO
    # =========================================================================
    
    def get_by_producer(self, producer_slug: str, page: int = 1) -> List[SearchResult]:
        """
        Get anime by producer/studio
        
        Args:
            producer_slug: Producer slug (e.g., "studio-pierrot", "mappa")
            page: Page number
        """
        url = f"{self.base_url}/producer/{producer_slug}"
        soup = self._get_soup(url, {"page": page})
        return self._parse_anime_list(soup)
    
    # =========================================================================
    # EPISODE LIST (AJAX API)
    # =========================================================================
    
    def get_episodes(self, anime_slug: str) -> List[Episode]:
        """
        Get episode list for an anime using AJAX API
        
        Args:
            anime_slug: Anime slug with ID (e.g., "naruto-677")
            
        Returns:
            List of Episode objects
        """
        # Extract anime ID from slug (e.g., "naruto-677" -> "677")
        anime_id = ParserUtils.extract_anime_id(anime_slug)
        if not anime_id:
            logger.error(f"Could not extract anime ID from: {anime_slug}")
            return []
        
        # Use AJAX endpoint
        url = f"{self.base_url}/ajax/v2/episode/list/{anime_id}"
        logger.info(f"Fetching episodes from AJAX: {url}")
        
        try:
            headers = self.client._get_headers()
            headers['Accept'] = 'application/json'
            headers['X-Requested-With'] = 'XMLHttpRequest'
            
            response = self.client.session.get(
                url,
                headers=headers,
                timeout=ScraperConfig.REQUEST_TIMEOUT
            )
            
            data = response.json()
            
            if not data.get('status'):
                logger.warning(f"AJAX request failed: {data.get('msg', 'Unknown error')}")
                return []
            
            html = data.get('html', '')
            soup = BeautifulSoup(html, 'html.parser')
            
            episodes = []
            episode_items = soup.select('a.ssl-item.ep-item, a[data-number]')
            
            for item in episode_items:
                try:
                    ep_num = item.get('data-number')
                    ep_id = item.get('data-id')
                    ep_title = item.get('title', '')
                    ep_href = item.get('href', '')
                    
                    # Get Japanese title if available
                    jp_elem = item.select_one('[data-jname]')
                    jp_title = jp_elem.get('data-jname') if jp_elem else None
                    
                    if ep_num:
                        episodes.append(Episode(
                            number=int(ep_num),
                            title=ParserUtils.clean_text(ep_title) if ep_title else f"Episode {ep_num}",
                            url=urljoin(self.base_url, ep_href) if ep_href else "",
                            id=ep_id,
                            japanese_title=jp_title
                        ))
                    
                except Exception as e:
                    logger.warning(f"Failed to parse episode: {e}")
                    continue
            
            # Sort by episode number
            episodes.sort(key=lambda x: x.number)
            
            logger.info(f"Found {len(episodes)} episodes")
            return episodes
            
        except Exception as e:
            logger.error(f"Failed to fetch episodes: {e}")
            return []

    # =========================================================================
    # VIDEO SOURCE METHODS
    # =========================================================================
    
    def get_video_servers(self, episode_id: str) -> List[VideoServer]:
        """
        Get available video servers for an episode
        
        Args:
            episode_id: Episode ID (e.g., "2142" from ep=2142)
            
        Returns:
            List of VideoServer objects with server info
        """
        url = f"{self.base_url}/ajax/v2/episode/servers?episodeId={episode_id}"
        logger.info(f"Fetching video servers from: {url}")
        
        try:
            headers = self.client._get_headers()
            headers['Accept'] = 'application/json'
            headers['X-Requested-With'] = 'XMLHttpRequest'
            headers['Referer'] = f"{self.base_url}/watch/"
            
            response = self.client.session.get(
                url,
                headers=headers,
                timeout=ScraperConfig.REQUEST_TIMEOUT
            )
            
            data = response.json()
            
            if not data.get('status'):
                logger.warning(f"Server fetch failed: {data.get('msg', 'Unknown error')}")
                return []
            
            html = data.get('html', '')
            soup = BeautifulSoup(html, 'html.parser')
            
            servers = []
            
            # Parse sub servers
            sub_servers = soup.select('.servers-sub .server-item')
            for server in sub_servers:
                server_id = server.get('data-id', '')
                server_name = ParserUtils.clean_text(server.text)
                if server_id:
                    servers.append(VideoServer(
                        server_id=server_id,
                        server_name=server_name,
                        server_type="sub"
                    ))
            
            # Parse dub servers
            dub_servers = soup.select('.servers-dub .server-item')
            for server in dub_servers:
                server_id = server.get('data-id', '')
                server_name = ParserUtils.clean_text(server.text)
                if server_id:
                    servers.append(VideoServer(
                        server_id=server_id,
                        server_name=server_name,
                        server_type="dub"
                    ))
            
            # Parse raw servers (if any)
            raw_servers = soup.select('.servers-raw .server-item')
            for server in raw_servers:
                server_id = server.get('data-id', '')
                server_name = ParserUtils.clean_text(server.text)
                if server_id:
                    servers.append(VideoServer(
                        server_id=server_id,
                        server_name=server_name,
                        server_type="raw"
                    ))
            
            logger.info(f"Found {len(servers)} servers")
            return servers
            
        except Exception as e:
            logger.error(f"Failed to fetch video servers: {e}")
            return []
    
    def get_video_source(self, episode_id: str, server_id: str, server_type: str = "sub") -> Optional[VideoSource]:
        """
        Get video source URL from a specific server
        
        Args:
            episode_id: Episode ID
            server_id: Server ID from get_video_servers()
            server_type: "sub", "dub", or "raw"
            
        Returns:
            VideoSource object with streaming URLs
        """
        url = f"{self.base_url}/ajax/v2/episode/sources?id={server_id}"
        logger.info(f"Fetching video source from: {url}")
        
        try:
            headers = self.client._get_headers()
            headers['Accept'] = 'application/json'
            headers['X-Requested-With'] = 'XMLHttpRequest'
            headers['Referer'] = f"{self.base_url}/watch/"
            
            response = self.client.session.get(
                url,
                headers=headers,
                timeout=ScraperConfig.REQUEST_TIMEOUT
            )
            
            data = response.json()
            
            # The response contains a 'link' to the embed URL
            embed_link = data.get('link', '')
            
            if not embed_link:
                logger.warning("No embed link found in response")
                return None
            
            # Return the embed link information
            return VideoSource(
                episode_id=episode_id,
                server_id=server_id,
                server_name="",  # Will be populated by caller if needed
                server_type=server_type,
                sources=[{
                    "url": embed_link,
                    "type": "iframe",
                    "quality": "auto"
                }],
                tracks=[],
                intro=data.get('intro'),
                outro=data.get('outro')
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch video source: {e}")
            return None
    
    def extract_stream_url(self, embed_url: str) -> Optional[Dict[str, Any]]:
        """
        Extract actual streaming URL (.m3u8) from embed URL
        
        This method extracts the actual playable video stream URL from
        embed URLs (like megacloud.blog). The returned URL can be used
        directly in video players (VLC, Flutter video_player, etc.)
        
        Args:
            embed_url: The embed URL (e.g., "https://megacloud.blog/embed-2/v3/e-1/xxxxx?k=1")
            
        Returns:
            Dictionary containing:
            - sources: List of {url, quality, isM3U8} objects
            - tracks: List of subtitle tracks {url, lang, kind}
            - intro: Intro skip times {start, end}
            - outro: Outro skip times {start, end}
            - headers: Required headers for playback
        """
        logger.info(f"Extracting stream from: {embed_url}")
        
        try:
            # Use external decryption service (similar to consumet.ts)
            # Properly encode the URL
            from urllib.parse import quote as url_quote
            encoded_url = url_quote(embed_url, safe='')
            api_url = f"https://crawlr.cc/9D7F1B3E8?url={encoded_url}"
            
            logger.info(f"Calling extraction API: {api_url[:80]}...")
            
            headers = self.client._get_headers()
            headers['Accept'] = 'application/json'
            
            response = self.client.session.get(
                api_url,
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"Stream extraction failed with status {response.status_code}")
                return None
            
            data = response.json()
            logger.info(f"Extraction API response: sources={bool(data.get('sources'))}, tracks={bool(data.get('tracks'))}")
            
            if not data.get('sources'):
                logger.warning("No sources found in extraction response")
                return None
            
            # Get headers from API response or use defaults
            api_headers = data.get('headers', {})
            
            # Format the response
            result = {
                "sources": [],
                "tracks": [],
                "intro": data.get('intro'),
                "outro": data.get('outro'),
                "headers": {
                    "Referer": api_headers.get('Referer', embed_url),
                    "User-Agent": api_headers.get('User-Agent', headers.get('User-Agent', ''))
                }
            }
            
            # Process sources
            for src in data.get('sources', []):
                source_url = src.get('url', src.get('file', ''))
                if source_url:
                    result["sources"].append({
                        "url": source_url,
                        "quality": src.get('quality', 'auto'),
                        "isM3U8": '.m3u8' in source_url
                    })
            
            # Process subtitle tracks (handle null/None)
            tracks_data = data.get('tracks')
            if tracks_data and isinstance(tracks_data, list):
                for track in tracks_data:
                    if isinstance(track, dict):
                        track_file = track.get('file', track.get('url', ''))
                        if track_file:
                            result["tracks"].append({
                                "url": track_file,
                                "lang": track.get('label', 'Unknown'),
                                "kind": track.get('kind', 'captions')
                            })
            
            logger.info(f"Extracted {len(result['sources'])} sources and {len(result['tracks'])} tracks")
            return result
            
        except Exception as e:
            logger.error(f"Failed to extract stream: {e}", exc_info=True)
            return None
    
    def get_streaming_links(self, episode_id: str, server_type: str = "sub") -> Dict[str, Any]:
        """
        Get actual streaming links (.m3u8) for an episode
        
        This method returns playable video URLs that can be used directly
        in video players like VLC, Flutter video_player, ExoPlayer, etc.
        
        Args:
            episode_id: Episode ID (e.g., "2142")
            server_type: Preferred type - "sub", "dub", or "all"
            
        Returns:
            Dictionary with:
            - episode_id: The episode ID
            - streams: List of stream objects with actual playable URLs
            - headers: Required headers for playback (important for CORS)
        """
        logger.info(f"Getting streaming links for episode {episode_id}")
        
        # First get the embed URLs
        sources_data = self.get_episode_sources(episode_id, server_type)
        
        if not sources_data.get('sources'):
            return {
                "episode_id": episode_id,
                "streams": [],
                "error": "No sources found"
            }
        
        streams = []
        
        for source in sources_data['sources']:
            # Get the embed URL
            embed_sources = source.get('sources', [])
            if not embed_sources:
                continue
            
            embed_url = embed_sources[0].get('url', '')
            if not embed_url or 'iframe' not in embed_sources[0].get('type', ''):
                continue
            
            # Extract actual stream URL
            stream_data = self.extract_stream_url(embed_url)
            
            if stream_data and stream_data.get('sources'):
                server_name = source.get('server_name', 'Unknown')
                
                # Format sources with better naming
                formatted_sources = []
                for src in stream_data['sources']:
                    stream_url = src.get('url', '')
                    # Extract domain for identification
                    domain = ""
                    if stream_url:
                        try:
                            from urllib.parse import urlparse
                            parsed = urlparse(stream_url)
                            domain = parsed.netloc
                        except:
                            domain = "unknown"
                    
                    formatted_sources.append({
                        "file": stream_url,  # Renamed from 'url' to 'file'
                        "type": "hls" if '.m3u8' in stream_url else "mp4",
                        "quality": src.get('quality', 'auto'),
                        "isM3U8": '.m3u8' in stream_url,
                        "host": domain  # Added host/domain for identification
                    })
                
                # Format subtitle tracks
                formatted_tracks = []
                for track in stream_data.get('tracks', []):
                    formatted_tracks.append({
                        "file": track.get('url', ''),
                        "label": track.get('lang', 'Unknown'),
                        "kind": track.get('kind', 'captions')
                    })
                
                streams.append({
                    "name": f"{server_name} ({source.get('server_type', server_type).upper()})",
                    "server_name": server_name,
                    "server_type": source.get('server_type', server_type),
                    "sources": formatted_sources,
                    "subtitles": formatted_tracks,
                    "skips": {
                        "intro": stream_data.get('intro'),
                        "outro": stream_data.get('outro')
                    },
                    "headers": stream_data.get('headers', {})
                })
        
        return {
            "success": True,
            "episode_id": episode_id,
            "server_type": server_type,
            "total_streams": len(streams),
            "streams": streams,
            "usage": {
                "flutter": "Use 'file' as video URL with 'headers' in httpHeaders",
                "note": "Always include headers when fetching stream URLs"
            }
        }
    
    def get_episode_sources(self, episode_id: str, server_type: str = "sub") -> Dict[str, Any]:
        """
        Get all video sources for an episode
        
        Args:
            episode_id: Episode ID (e.g., "2142")
            server_type: Preferred type - "sub", "dub", or "all"
            
        Returns:
            Dictionary with servers and their sources
        """
        servers = self.get_video_servers(episode_id)
        
        if not servers:
            return {
                "episode_id": episode_id,
                "servers": [],
                "sources": []
            }
        
        # Filter by type if specified
        if server_type != "all":
            servers = [s for s in servers if s.server_type == server_type]
        
        sources = []
        for server in servers:
            source = self.get_video_source(episode_id, server.server_id, server.server_type)
            if source:
                source.server_name = server.server_name
                sources.append(source)
        
        return {
            "episode_id": episode_id,
            "servers": [asdict(s) for s in servers],
            "sources": [asdict(s) for s in sources]
        }
    
    def get_watch_sources(self, anime_slug: str, episode_param: str, server_type: str = "sub") -> Dict[str, Any]:
        """
        Get video sources from a watch URL
        
        Args:
            anime_slug: Anime slug (e.g., "one-piece-100")
            episode_param: Episode parameter (e.g., "2142" from ?ep=2142)
            server_type: "sub", "dub", or "all"
            
        Returns:
            Dictionary with episode info and video sources
        """
        logger.info(f"Getting sources for {anime_slug} episode {episode_param}")
        
        # Get episode sources
        result = self.get_episode_sources(episode_param, server_type)
        
        # Add anime and episode info
        result["anime_slug"] = anime_slug
        result["watch_url"] = f"{self.base_url}/watch/{anime_slug}?ep={episode_param}"
        
        return result

    # =========================================================================
    # BULK OPERATIONS
    # =========================================================================
    
    def scrape_all_pages(
        self,
        scrape_func,
        max_pages: Optional[int] = None,
        **kwargs
    ) -> Generator[SearchResult, None, None]:
        """
        Generator that scrapes all pages of a category
        
        Args:
            scrape_func: The scraping function to use
            max_pages: Maximum pages to scrape (None for all)
            **kwargs: Additional arguments for the scrape function
            
        Yields:
            SearchResult objects
        """
        page = 1
        
        while True:
            if max_pages and page > max_pages:
                break
                
            results = scrape_func(page=page, **kwargs)
            
            if not results:
                break
                
            for result in results:
                yield result
            
            page += 1
            logger.info(f"Scraped page {page - 1}")
    
    def export_to_json(self, data: List[Any], filepath: str):
        """Export results to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(
                [asdict(item) for item in data],
                f,
                indent=2,
                ensure_ascii=False
            )
        logger.info(f"Exported {len(data)} items to {filepath}")
    
    def export_to_csv(self, data: List[Any], filepath: str):
        """Export results to CSV file"""
        import csv
        
        if not data:
            return
            
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=asdict(data[0]).keys())
            writer.writeheader()
            for item in data:
                writer.writerow(asdict(item))
        
        logger.info(f"Exported {len(data)} items to {filepath}")


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

def main():
    """Example usage of the scraper"""
    
    # Initialize scraper
    scraper = HiAnimeScraper(rate_limit=True)
    
    # Example 1: Search for anime
    print("\n=== Search Example ===")
    results = scraper.search("naruto", page=1)
    for r in results[:5]:
        print(f"- {r.title} ({r.type}) - {r.episodes_sub} episodes")
    
    # Example 2: Get top airing
    print("\n=== Top Airing ===")
    top_airing = scraper.get_top_airing(page=1)
    for r in top_airing[:5]:
        print(f"- {r.title}")
    
    # Example 3: Filter by genre
    print("\n=== Action Anime ===")
    action = scraper.get_by_genre("action", page=1)
    for r in action[:5]:
        print(f"- {r.title}")
    
    # Example 4: Advanced filter
    print("\n=== Advanced Filter (Completed TV, Score 8+) ===")
    filtered = scraper.advanced_filter(
        type="tv",
        status="finished",
        score=8,
        sort="score",
        page=1
    )
    for r in filtered[:5]:
        print(f"- {r.title}")
    
    # Example 5: Get anime details
    print("\n=== Anime Details ===")
    details = scraper.get_anime_details("naruto-677")
    if details:
        print(f"Title: {details.title}")
        print(f"Japanese: {details.japanese_title}")
        print(f"Episodes: {details.episodes_sub} sub / {details.episodes_dub} dub")
        print(f"Score: {details.mal_score}")
        print(f"Genres: {', '.join(details.genres)}")
        print(f"Synopsis: {details.synopsis[:200]}...")
    
    # Example 6: Export to JSON
    print("\n=== Exporting Data ===")
    scraper.export_to_json(results, "search_results.json")


if __name__ == "__main__":
    main()
