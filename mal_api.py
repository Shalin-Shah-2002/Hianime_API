"""
MyAnimeList Official API Client
===============================
Supports both server-side (public data) and user authentication

Features:
- Search anime
- Get anime details
- Rankings & seasonal anime
- User authentication (OAuth2 with PKCE)
- User anime list access

Privacy Note: User credentials are never stored on our servers.
"""

import os
import httpx
import secrets
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class MALAnime:
    """MyAnimeList Anime Data Model"""
    mal_id: int
    title: str
    main_picture: Optional[Dict[str, str]] = None
    alternative_titles: Optional[Dict] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    synopsis: Optional[str] = None
    mean_score: Optional[float] = None
    rank: Optional[int] = None
    popularity: Optional[int] = None
    num_episodes: Optional[int] = None
    status: Optional[str] = None
    genres: Optional[List[Dict]] = None
    studios: Optional[List[Dict]] = None
    source: Optional[str] = None
    rating: Optional[str] = None
    media_type: Optional[str] = None


@dataclass
class MALUserAnimeEntry:
    """User's anime list entry"""
    anime: MALAnime
    status: str  # watching, completed, on_hold, dropped, plan_to_watch
    score: int
    num_episodes_watched: int
    updated_at: str


# =============================================================================
# SERVER-SIDE CLIENT (Public Data - Uses Server Credentials)
# =============================================================================

class MALApiClient:
    """
    MyAnimeList API Client for public data
    
    Uses server-side Client ID for public endpoints.
    No user authentication required.
    """
    
    BASE_URL = "https://api.myanimelist.net/v2"
    
    def __init__(self):
        self.client_id = os.getenv("MAL_CLIENT_ID")
        
        if not self.client_id:
            raise ValueError("MAL_CLIENT_ID not found in environment variables")
        
        self.client = httpx.Client(
            headers={"X-MAL-CLIENT-ID": self.client_id},
            timeout=30.0
        )
    
    def search(self, query: str, limit: int = 10, offset: int = 0) -> List[MALAnime]:
        """Search anime by title"""
        params = {
            "q": query,
            "limit": min(limit, 100),
            "offset": offset,
            "fields": "id,title,main_picture,alternative_titles,start_date,end_date,synopsis,mean,rank,popularity,num_episodes,status,genres,studios,source,rating,media_type"
        }
        
        response = self.client.get(f"{self.BASE_URL}/anime", params=params)
        response.raise_for_status()
        
        data = response.json()
        return [self._parse_anime(item["node"]) for item in data.get("data", [])]
    
    def get_anime_details(self, anime_id: int) -> Optional[MALAnime]:
        """Get detailed anime information by MAL ID"""
        fields = "id,title,main_picture,alternative_titles,start_date,end_date,synopsis,mean,rank,popularity,num_episodes,status,genres,studios,source,rating,media_type,background,related_anime,recommendations"
        
        response = self.client.get(
            f"{self.BASE_URL}/anime/{anime_id}",
            params={"fields": fields}
        )
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        return self._parse_anime(response.json())
    
    def get_ranking(
        self, 
        ranking_type: str = "all",
        limit: int = 10,
        offset: int = 0
    ) -> List[MALAnime]:
        """
        Get anime rankings
        
        ranking_type options:
        - all: Top Anime Series
        - airing: Top Airing Anime
        - upcoming: Top Upcoming Anime
        - tv: Top Anime TV Series
        - movie: Top Anime Movies
        - bypopularity: Most Popular Anime
        - favorite: Most Favorited Anime
        """
        params = {
            "ranking_type": ranking_type,
            "limit": min(limit, 100),
            "offset": offset,
            "fields": "id,title,main_picture,mean,rank,popularity,num_episodes,status,genres,media_type"
        }
        
        response = self.client.get(f"{self.BASE_URL}/anime/ranking", params=params)
        response.raise_for_status()
        
        data = response.json()
        results = []
        for item in data.get("data", []):
            anime = self._parse_anime(item["node"])
            anime.rank = item.get("ranking", {}).get("rank")
            results.append(anime)
        
        return results
    
    def get_seasonal(
        self,
        year: int,
        season: str,
        sort: str = "anime_score",
        limit: int = 10,
        offset: int = 0
    ) -> List[MALAnime]:
        """
        Get seasonal anime
        
        season options: winter, spring, summer, fall
        sort options: anime_score, anime_num_list_users
        """
        params = {
            "sort": sort,
            "limit": min(limit, 100),
            "offset": offset,
            "fields": "id,title,main_picture,mean,rank,popularity,num_episodes,status,genres,start_date,media_type"
        }
        
        response = self.client.get(
            f"{self.BASE_URL}/anime/season/{year}/{season}",
            params=params
        )
        response.raise_for_status()
        
        data = response.json()
        return [self._parse_anime(item["node"]) for item in data.get("data", [])]
    
    def _parse_anime(self, data: Dict) -> MALAnime:
        """Parse API response to MALAnime dataclass"""
        return MALAnime(
            mal_id=data.get("id"),
            title=data.get("title"),
            main_picture=data.get("main_picture"),
            alternative_titles=data.get("alternative_titles"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            synopsis=data.get("synopsis"),
            mean_score=data.get("mean"),
            rank=data.get("rank"),
            popularity=data.get("popularity"),
            num_episodes=data.get("num_episodes"),
            status=data.get("status"),
            genres=data.get("genres"),
            studios=data.get("studios"),
            source=data.get("source"),
            rating=data.get("rating"),
            media_type=data.get("media_type")
        )


# =============================================================================
# USER AUTHENTICATION CLIENT (Uses User's Own Credentials)
# =============================================================================

class MALUserClient:
    """
    MyAnimeList User Authentication Client
    
    ⚠️ PRIVACY NOTICE:
    - User credentials (client_id, client_secret) are provided by the user
    - We DO NOT store any credentials on our servers
    - All authentication happens client-side
    - Tokens are returned to the user, not stored
    
    This allows users to:
    - Access their anime list
    - Update their watch status
    - Get personalized recommendations
    """
    
    BASE_URL = "https://api.myanimelist.net/v2"
    AUTH_URL = "https://myanimelist.net/v1/oauth2"
    
    def __init__(self, client_id: str, client_secret: str = None):
        """
        Initialize with user's own MAL API credentials
        
        Args:
            client_id: User's MAL API Client ID
            client_secret: User's MAL API Client Secret (optional for some flows)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        
        self.client = httpx.Client(timeout=30.0)
    
    # =========================================================================
    # OAUTH2 AUTHENTICATION (PKCE Flow)
    # =========================================================================
    
    def generate_pkce_pair(self) -> Dict[str, str]:
        """
        Generate PKCE code verifier and challenge
        
        Returns dict with:
        - code_verifier: Store this securely, needed for token exchange
        - code_challenge: Used in authorization URL
        """
        code_verifier = secrets.token_urlsafe(100)[:128]
        # MAL uses 'plain' method
        code_challenge = code_verifier
        
        return {
            "code_verifier": code_verifier,
            "code_challenge": code_challenge
        }
    
    def get_authorization_url(self, redirect_uri: str, state: str = None) -> Dict[str, str]:
        """
        Get OAuth2 authorization URL for user login
        
        Args:
            redirect_uri: Where MAL will redirect after auth (must match your app settings)
            state: Optional state parameter for security
        
        Returns:
            {
                "auth_url": "https://myanimelist.net/v1/oauth2/authorize?...",
                "code_verifier": "store_this_securely",
                "state": "random_state"
            }
        """
        pkce = self.generate_pkce_pair()
        state = state or secrets.token_urlsafe(16)
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "code_challenge": pkce["code_challenge"],
            "code_challenge_method": "plain",
            "state": state,
            "redirect_uri": redirect_uri
        }
        
        auth_url = f"{self.AUTH_URL}/authorize?" + "&".join(f"{k}={v}" for k, v in params.items())
        
        return {
            "auth_url": auth_url,
            "code_verifier": pkce["code_verifier"],
            "state": state
        }
    
    def exchange_code_for_token(
        self, 
        code: str, 
        code_verifier: str, 
        redirect_uri: str
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from callback
            code_verifier: The code_verifier from get_authorization_url
            redirect_uri: Same redirect_uri used in authorization
        
        Returns:
            {
                "access_token": "...",
                "refresh_token": "...",
                "expires_in": 2678400,
                "token_type": "Bearer"
            }
        """
        data = {
            "client_id": self.client_id,
            "grant_type": "authorization_code",
            "code": code,
            "code_verifier": code_verifier,
            "redirect_uri": redirect_uri
        }
        
        if self.client_secret:
            data["client_secret"] = self.client_secret
        
        response = self.client.post(f"{self.AUTH_URL}/token", data=data)
        response.raise_for_status()
        
        tokens = response.json()
        self.access_token = tokens.get("access_token")
        self.refresh_token = tokens.get("refresh_token")
        
        return tokens
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh an expired access token"""
        data = {
            "client_id": self.client_id,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        if self.client_secret:
            data["client_secret"] = self.client_secret
        
        response = self.client.post(f"{self.AUTH_URL}/token", data=data)
        response.raise_for_status()
        
        tokens = response.json()
        self.access_token = tokens.get("access_token")
        self.refresh_token = tokens.get("refresh_token")
        
        return tokens
    
    def set_access_token(self, access_token: str):
        """Set access token for authenticated requests"""
        self.access_token = access_token
    
    # =========================================================================
    # USER DATA ENDPOINTS (Requires Authentication)
    # =========================================================================
    
    def _auth_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        if not self.access_token:
            raise ValueError("Access token required. Call exchange_code_for_token first.")
        return {"Authorization": f"Bearer {self.access_token}"}
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get authenticated user's profile info"""
        response = self.client.get(
            f"{self.BASE_URL}/users/@me",
            headers=self._auth_headers(),
            params={"fields": "id,name,picture,gender,birthday,location,joined_at,anime_statistics"}
        )
        response.raise_for_status()
        return response.json()
    
    def get_user_anime_list(
        self,
        status: str = None,
        sort: str = "list_updated_at",
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get user's anime list
        
        status options: watching, completed, on_hold, dropped, plan_to_watch
        sort options: list_score, list_updated_at, anime_title, anime_start_date
        """
        params = {
            "sort": sort,
            "limit": min(limit, 1000),
            "offset": offset,
            "fields": "list_status,num_episodes,synopsis,mean,rank,popularity,genres,media_type"
        }
        
        if status:
            params["status"] = status
        
        response = self.client.get(
            f"{self.BASE_URL}/users/@me/animelist",
            headers=self._auth_headers(),
            params=params
        )
        response.raise_for_status()
        
        return response.json().get("data", [])
    
    def update_anime_status(
        self,
        anime_id: int,
        status: str = None,
        score: int = None,
        num_watched_episodes: int = None
    ) -> Dict[str, Any]:
        """
        Update anime in user's list
        
        status options: watching, completed, on_hold, dropped, plan_to_watch
        score: 0-10
        """
        data = {}
        if status:
            data["status"] = status
        if score is not None:
            data["score"] = score
        if num_watched_episodes is not None:
            data["num_watched_episodes"] = num_watched_episodes
        
        response = self.client.patch(
            f"{self.BASE_URL}/anime/{anime_id}/my_list_status",
            headers=self._auth_headers(),
            data=data
        )
        response.raise_for_status()
        return response.json()
    
    def delete_anime_from_list(self, anime_id: int) -> bool:
        """Remove anime from user's list"""
        response = self.client.delete(
            f"{self.BASE_URL}/anime/{anime_id}/my_list_status",
            headers=self._auth_headers()
        )
        return response.status_code == 200
    
    def get_suggestions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get personalized anime suggestions"""
        response = self.client.get(
            f"{self.BASE_URL}/anime/suggestions",
            headers=self._auth_headers(),
            params={
                "limit": min(limit, 100),
                "fields": "id,title,main_picture,mean,rank,num_episodes,status,genres,synopsis"
            }
        )
        response.raise_for_status()
        return response.json().get("data", [])


# =============================================================================
# QUICK TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("MyAnimeList API Client Test")
    print("=" * 60)
    
    try:
        # Test server-side client
        client = MALApiClient()
        
        print("\n📍 Search Test: 'Naruto'")
        results = client.search("Naruto", limit=3)
        for anime in results:
            print(f"  • {anime.title} - Score: {anime.mean_score}")
        
        print("\n📍 Top Anime Rankings")
        top = client.get_ranking("all", limit=5)
        for anime in top:
            print(f"  #{anime.rank} {anime.title} - Score: {anime.mean_score}")
        
        print("\n📍 Winter 2024 Anime")
        seasonal = client.get_seasonal(2024, "winter", limit=5)
        for anime in seasonal:
            print(f"  • {anime.title} - Score: {anime.mean_score}")
        
        print("\n✅ All tests passed!")
        
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("Please set MAL_CLIENT_ID in your .env file")
    except Exception as e:
        print(f"\n❌ Error: {e}")
