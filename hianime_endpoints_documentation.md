# HiAnime + MAL Scraper API Documentation

## 📋 Overview

**API Version:** 2.0.0  
**Base URL:** `https://hianime-api-b6ix.onrender.com`  
**Documentation:** `/docs` (Swagger UI) | `/redoc` (ReDoc)  
**Last Updated:** December 23, 2025  

This API provides REST endpoints for scraping anime data from HiAnime.to and integrates with MyAnimeList's official API.

---

## 🚀 Quick Start

```bash
# Health Check
curl https://hianime-api-b6ix.onrender.com/

# Search for anime
curl "https://hianime-api-b6ix.onrender.com/api/search?keyword=naruto"

# Get anime details
curl "https://hianime-api-b6ix.onrender.com/api/anime/naruto-677"
```

---

## 📊 Response Format

All endpoints return JSON with a consistent structure:

### Success Response
```json
{
  "success": true,
  "count": 10,
  "page": 1,
  "data": [...]
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message description"
}
```

---

## 🔍 API Endpoints

### Root / Health Check

#### `GET /`
API health check and endpoint listing.

**Response:**
```json
{
  "status": "online",
  "api": "HiAnime + MAL Scraper API",
  "version": "2.0.0",
  "mal_enabled": true,
  "total_endpoints": 24,
  "endpoints": {...}
}
```

---

## 🔎 Search Endpoints

### Search Anime

#### `GET /api/search`
Search for anime by keyword.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `keyword` | string | ✅ Yes | - | Search term (min 1 character) |
| `page` | integer | No | 1 | Page number (≥1) |

**Example:**
```bash
GET /api/search?keyword=naruto&page=1
```

**Response:**
```json
{
  "success": true,
  "count": 20,
  "page": 1,
  "data": [
    {
      "title": "Naruto",
      "slug": "naruto-677",
      "url": "https://hianime.to/naruto-677",
      "poster": "https://cdn.noitatnemucod.net/...",
      "type": "TV",
      "episodes": {"sub": 220, "dub": 220},
      "duration": "23m"
    }
  ]
}
```

---

## 📂 Browse Endpoints

### Get Popular Anime

#### `GET /api/popular`
Get most popular anime.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number |

**Example:**
```bash
GET /api/popular?page=1
```

---

### Get Top Airing

#### `GET /api/top-airing`
Get currently airing popular anime.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number |

**Example:**
```bash
GET /api/top-airing?page=1
```

---

### Get Recently Updated

#### `GET /api/recently-updated`
Get recently updated anime with new episodes.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number |

**Example:**
```bash
GET /api/recently-updated?page=1
```

---

### Get Completed Anime

#### `GET /api/completed`
Get completed anime series.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number |

**Example:**
```bash
GET /api/completed?page=1
```

---

### Get Subbed Anime

#### `GET /api/subbed`
Get anime with subtitles.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number |

**Example:**
```bash
GET /api/subbed?page=1
```

---

### Get Dubbed Anime

#### `GET /api/dubbed`
Get dubbed anime.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number |

**Example:**
```bash
GET /api/dubbed?page=1
```

---

## 🏷️ Genre & Type Endpoints

### Get Anime by Genre

#### `GET /api/genre/{genre}`
Get anime filtered by genre.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `genre` | string | ✅ Yes | Genre slug (path parameter) |
| `page` | integer | No | Page number |

**Available Genres:**
```
action, adventure, cars, comedy, dementia, demons, drama, ecchi, fantasy, 
game, harem, historical, horror, isekai, josei, kids, magic, martial-arts, 
mecha, military, music, mystery, parody, police, psychological, romance, 
samurai, school, sci-fi, seinen, shoujo, shoujo-ai, shounen, shounen-ai, 
slice-of-life, space, sports, super-power, supernatural, thriller, vampire
```

**Example:**
```bash
GET /api/genre/action?page=1
```

---

### Get Anime by Type

#### `GET /api/type/{type_name}`
Get anime filtered by type.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type_name` | string | ✅ Yes | Anime type (path parameter) |
| `page` | integer | No | Page number |

**Available Types:**
- `movie` - Anime movies
- `tv` - TV series
- `ova` - Original Video Animation
- `ona` - Original Net Animation
- `special` - Special episodes
- `music` - Music videos

**Example:**
```bash
GET /api/type/movie?page=1
```

---

## 🔧 Advanced Filter

#### `GET /api/filter`
Advanced search with multiple filters.

| Parameter | Type | Required | Values | Description |
|-----------|------|----------|--------|-------------|
| `type` | string | No | `movie`, `tv`, `ova`, `ona`, `special`, `music` | Anime type |
| `status` | string | No | `finished`, `airing`, `upcoming` | Airing status |
| `rated` | string | No | `g`, `pg`, `pg-13`, `r`, `r+`, `rx` | Age rating |
| `score` | integer | No | 1-10 | Minimum score |
| `season` | string | No | `spring`, `summer`, `fall`, `winter` | Season |
| `language` | string | No | `sub`, `dub` | Audio language |
| `genres` | string | No | Comma-separated | Genre filters |
| `sort` | string | No | See below | Sort order |
| `page` | integer | No | ≥1 | Page number |

**Sort Options:**
- `default` - Default sorting
- `recently_added` - Newest first
- `recently_updated` - Recently updated
- `score` - Highest score first
- `name_az` - Alphabetical A-Z
- `released_date` - By release date
- `most_watched` - Most popular

**Example:**
```bash
GET /api/filter?type=tv&status=airing&genres=action,fantasy&sort=score&page=1
```

---

## 📝 Anime Details

### Get Anime Information

#### `GET /api/anime/{slug}`
Get detailed information about a specific anime.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `slug` | string | ✅ Yes | Anime slug with ID (e.g., `naruto-677`) |

**Example:**
```bash
GET /api/anime/naruto-677
```

**Response:**
```json
{
  "success": true,
  "data": {
    "title": "Naruto",
    "japanese_title": "ナルト",
    "slug": "naruto-677",
    "poster": "https://cdn.noitatnemucod.net/...",
    "description": "...",
    "type": "TV",
    "status": "Finished Airing",
    "aired": "Oct 3, 2002 to Feb 8, 2007",
    "premiered": "Fall 2002",
    "duration": "23m",
    "episodes": {"sub": 220, "dub": 220},
    "studios": ["Studio Pierrot"],
    "producers": ["TV Tokyo", "Aniplex"],
    "genres": ["Action", "Adventure", "Fantasy"],
    "score": "8.0"
  }
}
```

---

## 📺 Episodes

### Get Episode List

#### `GET /api/episodes/{slug}`
Get full episode list for an anime.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `slug` | string | ✅ Yes | Anime slug with ID |

**Example:**
```bash
GET /api/episodes/naruto-677
```

**Response:**
```json
{
  "success": true,
  "count": 220,
  "data": [
    {
      "number": 1,
      "title": "Enter: Naruto Uzumaki!",
      "japanese_title": "参上！うずまきナルト",
      "url": "https://hianime.to/watch/naruto-677?ep=12345",
      "episode_id": "12345",
      "filler": false
    }
  ]
}
```

---

## 🔤 A-Z List

#### `GET /api/az/{letter}`
Get anime alphabetically by first letter.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `letter` | string | ✅ Yes | Single letter A-Z or `other` |
| `page` | integer | No | Page number |

**Example:**
```bash
GET /api/az/N?page=1
GET /api/az/other?page=1
```

---

## 🏭 Producer / Studio

#### `GET /api/producer/{producer_slug}`
Get anime by producer or studio.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `producer_slug` | string | ✅ Yes | Producer/studio slug |
| `page` | integer | No | Page number |

**Example Slugs:**
- `studio-pierrot`
- `mappa`
- `toei-animation`
- `ufotable`
- `wit-studio`
- `bones`

**Example:**
```bash
GET /api/producer/mappa?page=1
```

---

## 🔵 MyAnimeList Endpoints

> **Note:** MAL endpoints require the MAL API to be configured on the server.

### MAL Search

#### `GET /api/mal/search`
Search anime on MyAnimeList.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✅ Yes | - | Search query |
| `limit` | integer | No | 10 | Results limit (1-100) |

**Example:**
```bash
GET /api/mal/search?query=naruto&limit=10
```

---

### MAL Anime Details

#### `GET /api/mal/anime/{mal_id}`
Get anime details from MyAnimeList by ID.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `mal_id` | integer | ✅ Yes | MyAnimeList anime ID |

**Example:**
```bash
GET /api/mal/anime/20
```

---

### MAL Ranking

#### `GET /api/mal/ranking`
Get anime rankings from MyAnimeList.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `type` | string | No | `all` | Ranking type |
| `limit` | integer | No | 10 | Results limit (1-100) |

**Ranking Types:**
- `all` - Top Anime Series
- `airing` - Top Airing Anime
- `upcoming` - Top Upcoming Anime
- `tv` - Top TV Series
- `movie` - Top Movies
- `bypopularity` - Most Popular
- `favorite` - Most Favorited

**Example:**
```bash
GET /api/mal/ranking?type=airing&limit=20
```

---

### MAL Seasonal Anime

#### `GET /api/mal/seasonal`
Get seasonal anime from MyAnimeList.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `year` | integer | ✅ Yes | Year (e.g., 2024) |
| `season` | string | ✅ Yes | `winter`, `spring`, `summer`, `fall` |
| `limit` | integer | No | Results limit (1-100) |

**Seasons:**
- `winter` - January to March
- `spring` - April to June
- `summer` - July to September
- `fall` - October to December

**Example:**
```bash
GET /api/mal/seasonal?year=2024&season=fall&limit=20
```

---

## 🔐 MAL User Authentication

These endpoints allow users to authenticate with their own MAL credentials.

### Get Auth URL

#### `POST /api/mal/user/auth`
Get OAuth2 authorization URL for MAL user login.

**Request Body:**
```json
{
  "client_id": "your_mal_client_id",
  "client_secret": "your_mal_client_secret",
  "redirect_uri": "https://your-app.com/callback"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Open auth_url in browser to login. Save code_verifier for token exchange.",
  "privacy_notice": "We DO NOT store your credentials. This request is stateless.",
  "data": {
    "auth_url": "https://myanimelist.net/v1/oauth2/authorize?...",
    "code_verifier": "abc123...",
    "state": "xyz789..."
  }
}
```

---

### Exchange Token

#### `POST /api/mal/user/token`
Exchange authorization code for access token.

**Request Body:**
```json
{
  "client_id": "your_mal_client_id",
  "client_secret": "your_mal_client_secret",
  "code": "authorization_code_from_callback",
  "code_verifier": "code_verifier_from_previous_step",
  "redirect_uri": "https://your-app.com/callback"
}
```

---

### Get User Anime List

#### `POST /api/mal/user/animelist`
Get authenticated user's anime list.

**Request Body:**
```json
{
  "client_id": "your_mal_client_id",
  "access_token": "user_access_token",
  "status": "watching",
  "limit": 100
}
```

**Status Options:**
- `watching`
- `completed`
- `on_hold`
- `dropped`
- `plan_to_watch`
- *(empty for all)*

---

### Get User Profile

#### `POST /api/mal/user/profile`
Get authenticated user's MAL profile.

**Request Body:**
```json
{
  "client_id": "your_mal_client_id",
  "access_token": "user_access_token"
}
```

---

## 🔗 Combined Endpoints

### Combined Search

#### `GET /api/combined/search`
Search both HiAnime and MyAnimeList simultaneously.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✅ Yes | - | Search query |
| `limit` | integer | No | 5 | Results per source (1-20) |

**Example:**
```bash
GET /api/combined/search?query=demon%20slayer&limit=5
```

**Response:**
```json
{
  "success": true,
  "query": "demon slayer",
  "sources": {
    "hianime": {
      "enabled": true,
      "count": 5,
      "results": [...],
      "error": null
    },
    "myanimelist": {
      "enabled": true,
      "count": 5,
      "results": [...],
      "error": null
    }
  }
}
```

---

## 📖 Interactive Documentation

Access interactive API documentation:

- **Swagger UI:** `https://hianime-api-b6ix.onrender.com/docs`
- **ReDoc:** `https://hianime-api-b6ix.onrender.com/redoc`

---

## ⚠️ Error Codes

| Status Code | Description |
|-------------|-------------|
| `200` | Success |
| `400` | Bad Request - Invalid parameters |
| `404` | Not Found - Anime/resource not found |
| `500` | Internal Server Error |
| `503` | Service Unavailable - MAL API not configured |

---

## 📝 Rate Limiting

The API implements rate limiting to prevent abuse. Please be respectful of the service.

---

## 🛠️ Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn api:app --reload --port 8000

# Access locally
http://localhost:8000
http://localhost:8000/docs
```

---

## 📜 Legal Notice

- This API scrapes data from HiAnime.to for educational purposes
- HiAnime does not store files on their servers
- MyAnimeList data is accessed via official MAL API
- Use responsibly and respect terms of service
| `/subbed-anime` | Anime with subtitles | `?page=1` |
| `/dubbed-anime` | Dubbed anime | `?page=1` |

#### By Type
| Endpoint | Description |
|----------|-------------|
| `/movie` | Movies only |
| `/tv` | TV series |
| `/ova` | Original Video Animation |
| `/ona` | Original Net Animation |
| `/special` | Special episodes |

#### By Genre
```
GET /genre/{genre-slug}
```

**Format:** `/genre/{genre}?page={page}`

**Examples:**
```
https://hianime.to/genre/action
https://hianime.to/genre/action?page=2
https://hianime.to/genre/adventure
https://hianime.to/genre/romance
```

**Total Genre Pages Example:** Action has ~98 pages

#### A-Z List (Alphabetical Browse)
```
GET /az-list
GET /az-list/{letter}
GET /az-list/other  (# symbols)
GET /az-list/0-9
GET /az-list/A through Z
```

---

### 4. Anime Detail Pages

#### Anime Info Page
```
GET /{anime-slug}-{anime-id}
```

**URL Pattern:** `/{title-slug}-{numeric-id}`

**Examples:**
```
https://hianime.to/naruto-677
https://hianime.to/one-piece-100
https://hianime.to/demon-slayer-kimetsu-no-yaiba-47
https://hianime.to/solo-leveling-season-2-arise-from-the-shadow-19413
```

**Response Data Points:**
- Title (English/Japanese/Synonyms)
- Synopsis/Description
- Episode count (sub/dub)
- Type (TV/Movie/OVA/etc.)
- Duration
- Status
- Aired dates
- Premiered season
- MAL Score
- Genres (linked)
- Studios
- Producers
- Characters & Voice Actors
- Related Anime
- Recommendations
- Promotional Videos

---

### 5. Watch/Streaming Endpoints

#### Watch Page
```
GET /watch/{anime-slug}-{anime-id}
```

**Example:**
```
https://hianime.to/watch/naruto-677
```

**Features Available:**
- Episode list (Sub/Dub counts shown)
- Server selection
- Auto-play toggle
- Auto-next toggle
- Auto-skip intro toggle
- Light on/off mode
- Watch2gether integration

#### Episode-Specific (Inferred Pattern)
```
GET /watch/{anime-slug}-{anime-id}?ep={episode-number}
```

---

### 6. Community Endpoints

```
GET /community/board           - Community main board
GET /community/post/{slug}-{id} - Individual posts
GET /community/user/{user-id}   - User profiles
```

**Example:**
```
https://hianime.to/community/post/searching-for-my-friends-302069
https://hianime.to/community/user/10234613
```

---

### 7. Producer/Studio Pages

```
GET /producer/{producer-slug}
```

**Example:**
```
https://hianime.to/producer/studio-pierrot
https://hianime.to/producer/tv-tokyo
https://hianime.to/producer/aniplex
```

---

### 8. Character & People Pages

```
GET /character/{character-slug}-{id}
GET /people/{person-slug}-{id}
```

**Examples:**
```
https://hianime.to/character/naruto-uzumaki-9
https://hianime.to/character/sakura-haruno-291
https://hianime.to/people/junko-takeuchi-103
```

---

### 9. Special Features

```
GET /watch2gether                    - Watch together feature
GET /watch2gether/create/{anime-id}  - Create watch party
GET /random                          - Random anime redirect
GET /events                          - Events page
GET /news                            - News articles
GET /app-download                    - Mobile app download
```

---

### 10. Static/Info Pages

```
GET /terms     - Terms of Service
GET /dmca      - DMCA policy
GET /contact   - Contact page
```

---

## 📦 Sitemap Structure

**Main Sitemap Index:** `https://hianime.to/sitemap.xml`

| Sitemap File | Content |
|--------------|---------|
| `/sitemap-page.xml` | Static pages |
| `/sitemap-genre.xml` | Genre pages |
| `/sitemap-type.xml` | Type pages (movie, tv, ova, ona, special) |
| `/sitemap-movie-1.xml` through `/sitemap-movie-5.xml` | Movie listings |

---

## 🖼️ CDN/Asset URLs

### Image Patterns

**Thumbnails:**
```
https://cdn.noitatnemucod.net/thumbnail/300x400/100/{image-hash}.jpg
```

**Avatars:**
```
https://cdn.noitatnemucod.net/avatar/100x100/{series}/{filename}
```

**Examples:**
```
https://cdn.noitatnemucod.net/thumbnail/300x400/100/bcd84731a3eda4f4a306250769675065.jpg
https://cdn.noitatnemucod.net/avatar/100x100/attack_on_titan/aot_10.png
```

---

## 📊 Pagination Patterns

All list endpoints support pagination via query parameter:

```
?page={number}
```

**Observed Limits:**
| Endpoint | Max Pages |
|----------|-----------|
| `/most-popular` | ~50 |
| `/top-airing` | ~11 |
| `/recently-updated` | ~213 |
| `/completed` | ~208 |
| `/genre/action` | ~98 |
| `/filter` | ~236 |

---

## 🔄 Identified AJAX/API Patterns

Based on analysis, the site likely uses internal AJAX endpoints for:

1. **Episode List Loading** - Dynamic episode lists
2. **Server Selection** - Video source switching  
3. **Search Autocomplete** - Live search suggestions
4. **Top 10 Tabs** - Today/Week/Month switching
5. **Comments Loading** - Lazy-loaded comments

**Likely AJAX Endpoint Patterns (to be verified via network analysis):**
```
/ajax/episode/list?id={anime-id}
/ajax/episode/servers?episodeId={ep-id}
/ajax/search/suggest?keyword={query}
/ajax/home/widget/top10?type={day|week|month}
```

---

## 📝 Data Schema Examples

### Anime Card Data Structure
```json
{
  "id": "19932",
  "slug": "one-punch-man-season-3",
  "title": "One-Punch Man Season 3",
  "url": "/one-punch-man-season-3-19932",
  "thumbnail": "https://cdn.noitatnemucod.net/thumbnail/300x400/100/269a2fc7ec4b9c0592493ef192ad2a9d.jpg",
  "type": "TV",
  "duration": "24m",
  "rating": "18+",
  "episodes": {
    "sub": 10,
    "dub": 3
  }
}
```

### Search Result Pattern
```json
{
  "title": "Naruto",
  "url": "/naruto-677?ref=search",
  "type": "TV",
  "duration": "23m",
  "episodes": {
    "sub": 220,
    "dub": 220
  }
}
```

---

## ⚠️ Anti-Scraping Considerations

### Observed Protections:
1. **Cloudflare Protection** - Standard Cloudflare CDN
2. **JavaScript Rendering** - Some content requires JS execution
3. **Dynamic Content Loading** - AJAX-based episode/server data

### Recommended Bypass Strategies:
1. Use headless browser (Playwright/Puppeteer) for JS-rendered content
2. Implement request delays (2-5 seconds between requests)
3. Rotate User-Agents
4. Use residential proxies for high-volume scraping
5. Respect rate limits to avoid IP bans

---

## 🛠️ Implementation Notes

### Rate Limiting Recommendations:
- **Conservative:** 1 request per 3 seconds
- **Moderate:** 1 request per 1.5 seconds  
- **Aggressive:** 1 request per 0.5 seconds (risk of blocking)

### Required Headers:
```
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
```

### Session Handling:
- Cookies may be required for authenticated features
- Some features require JavaScript execution
- Video streams are hosted on 3rd party servers

---

## 📁 Output Format Recommendations

For scraping results, recommend storing in:

1. **JSON** - For API responses and structured data
2. **CSV** - For anime lists and search results
3. **SQLite/PostgreSQL** - For persistent storage with relationships

---

## 🔗 External Integrations

The site integrates with:
- **MyAnimeList (MAL)** - Score data
- **YouTube** - Promotional videos
- **Discord** - Community server
- **Twitter** - Social sharing
- **Reddit** - Community subreddit (/r/HiAnimeZone)

---

*Documentation compiled through systematic endpoint discovery and web page analysis.*
