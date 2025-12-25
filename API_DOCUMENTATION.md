# HiAnime Scraper API Documentation

## Overview

The HiAnime Scraper API provides a comprehensive RESTful interface for accessing anime data from HiAnime.to and MyAnimeList (MAL). It supports searching, browsing, filtering, retrieving details, episodes, video sources, **downloading videos**, and integrating with MAL for both public and user-authenticated endpoints.

- **Base URL:** `/`
- **Version:** 2.3.1
- **Docs:** `/docs` (Swagger UI), `/redoc` (ReDoc)

---

## Table of Contents
1. [Health Check](#health-check)
2. [Search](#search)
3. [Browse](#browse)
4. [Genre & Type](#genre--type)
5. [Advanced Filter](#advanced-filter)
6. [Anime Details](#anime-details)
7. [A-Z List](#a-z-list)
8. [Subbed / Dubbed](#subbed--dubbed)
9. [Producer / Studio](#producer--studio)
10. [Episodes](#episodes)
11. [Video Sources](#video-sources)
12. [Download Endpoints](#download-endpoints-) 📥 **NEW**
13. [MyAnimeList (MAL) Endpoints](#myanimelist-mal-endpoints)
14. [MAL User Authentication](#mal-user-authentication)
15. [Combined Search](#combined-search)

---

## 1. Health Check
- **GET /**
- **Response Example:**
```json
{
  "status": "online",
  "api": "HiAnime + MAL Scraper API",
  "version": "2.0.0",
  "mal_enabled": true,
  "total_endpoints": 24,
  "endpoints": { ... }
}
```

## 2. Search
- **GET /api/search?keyword=naruto&page=1**
- Search for anime by keyword.
- **Parameters:**
  - `keyword` (required): Search term
  - `page` (default: 1)
- **Response Example:**
```json
{
  "success": true,
  "count": 1,
  "page": 1,
  "data": [
    {
      "title": "Naruto",
      "url": "https://hianime.to/anime/naruto-677",
      "id": "naruto-677",
      "slug": "naruto-677",
      "thumbnail": "https://...jpg",
      "type": "TV",
      "duration": "23 min",
      "episodes_sub": 220,
      "episodes_dub": 220
    }
  ]
}
```

## 3. Browse
- **GET /api/popular**: Most popular anime
- **GET /api/top-airing**: Currently airing anime
- **GET /api/recently-updated**: Recently updated anime
- **GET /api/completed**: Completed anime
- **Parameters:**
  - `page` (default: 1)
- **Response Example:** (same as Search)

## 4. Genre & Type
- **GET /api/genre/{genre}**: Anime by genre
- **GET /api/type/{type_name}**: Anime by type (movie, tv, ova, ona, special, music)
- **Parameters:**
  - `genre` or `type_name`
  - `page` (default: 1)
- **Response Example:** (same as Search)

## 5. Advanced Filter
- **GET /api/filter**
- Filter anime by multiple criteria (type, status, rating, score, season, language, genres, sort, page).
- **Parameters:**
  - `type`, `status`, `rated`, `score`, `season`, `language`, `genres`, `sort`, `page`
- **Response Example:** (same as Search)
r
```

## 7. A-Z List
- **GET /api/az/{letter}**
- List anime alphabetically by first letter.
- **Parameters:**
  - `letter`: A-Z or 'other'
  - `page` (default: 1)
- **Response Example:** (same as Search)

## 8. Subbed / Dubbed
- **GET /api/subbed**: Anime with subtitles
- **GET /api/dubbed**: Dubbed anime
- **Parameters:**
  - `page` (default: 1)
- **Response Example:** (same as Search)

## 9. Producer / Studio
- **GET /api/producer/{producer_slug}**
- List anime by producer or studio.
- **Parameters:**
  - `producer_slug`: e.g., studio-pierrot
  - `page` (default: 1)
- **Response Example:** (same as Search)

## 10. Episodes
- **GET /api/episodes/{slug}**
- Retrieve full episode list for an anime.
- **Parameters:**
  - `slug`: Anime slug with ID
- **Response Example:**
```json
{
  "success": true,
  "count": 2,
  "data": [
    {
      "number": 1,
      "title": "Enter: Naruto Uzumaki!",
      "url": "https://hianime.to/episode/naruto-677-ep-1",
      "id": "naruto-677-ep-1",
      "japanese_title": "うずまきナルト登場!",
      "is_filler": false
    },
    {
      "number": 2,
      "title": "My Name is Konohamaru!",
      "url": "https://hianime.to/episode/naruto-677-ep-2",
      "id": "naruto-677-ep-2",
      "japanese_title": "木ノ葉丸登場!",
      "is_filler": false
    }
  ]
}
```

## 11. Video Sources
These endpoints allow you to retrieve video streaming sources for episodes.

### Get Video Servers
- **GET /api/servers/{episode_id}**
- Get available video servers for an episode.
- **Parameters:**
  - `episode_id`: Episode ID from the watch URL (e.g., "2142" from ?ep=2142)
- **Response Example:**
```json
{
  "success": true,
  "episode_id": "2142",
  "count": 4,
  "data": [
    {
      "server_id": "1234",
      "server_name": "HD-1",
      "server_type": "sub"
    },
    {
      "server_id": "1235",
      "server_name": "HD-2",
      "server_type": "sub"
    },
    {
      "server_id": "1236",
      "server_name": "HD-1",
      "server_type": "dub"
    }
  ]
}
```

### Get Episode Sources
- **GET /api/sources/{episode_id}**
- Get video streaming sources/embed URLs for an episode.
- **Parameters:**
  - `episode_id`: Episode ID from the watch URL
  - `server_type` (optional): Filter by type - "sub" (default), "dub", or "all"
- **Response Example:**
```json
{
  "success": true,
  "episode_id": "2142",
  "servers": [
    {
      "server_id": "1234",
      "server_name": "HD-1",
      "server_type": "sub"
    }
  ],
  "sources": [
    {
      "episode_id": "2142",
      "server_id": "1234",
      "server_name": "HD-1",
      "server_type": "sub",
      "sources": [
        {
          "url": "https://embed-url.com/video/...",
          "type": "iframe",
          "quality": "auto"
        }
      ],
      "tracks": [],
      "intro": {"start": 0, "end": 90},
      "outro": {"start": 1340, "end": 1420}
    }
  ]
}
```

### Get Watch Sources (URL Format)
- **GET /api/watch/{anime_slug}?ep={episode_id}**
- Get video sources using the same URL format as HiAnime watch pages.
- **Parameters:**
  - `anime_slug`: Anime slug (e.g., "one-piece-100")
  - `ep`: Episode ID parameter (required)
  - `server_type` (optional): "sub" (default), "dub", or "all"
- **Example:** `/api/watch/one-piece-100?ep=2142&server_type=sub`
- **Response Example:**
```json
{
  "success": true,
  "anime_slug": "one-piece-100",
  "watch_url": "https://hianime.to/watch/one-piece-100?ep=2142",
  "episode_id": "2142",
  "servers": [...],
  "sources": [...]
}
```

## 12. Download Endpoints 📥

These endpoints provide downloadable video links for episodes. Perfect for mobile apps, download managers, or any client that needs to download videos.

### Development Prompt (How This Feature Was Built)
```
Prompt used to create this download feature:

"downloads to the user device .mp4 file give that endpoint proper one"

This prompted the creation of an endpoint that:
1. Fetches the M3U8 playlist from streaming servers
2. Downloads ALL HLS video segments
3. Uses FFmpeg to combine segments into a single MP4 file
4. Streams the final MP4 to the user's device
```

---

### 🎬 Download as MP4 (RECOMMENDED)
- **GET /api/download/mp4/{episode_id}**
- Downloads the actual video as an MP4 file directly to your device.
- **Parameters:**
  - `episode_id` (required): Episode ID from the watch URL (e.g., "147365")
  - `server_type` (optional): "sub" (default) or "dub"
  - `server_index` (optional): Which server to use (0 = first/best)
  - `filename` (optional): Custom filename (without .mp4 extension)
- **Response:** Binary MP4 video file with `Content-Disposition: attachment` header
- **⚠️ Note:** Download may take 1-5 minutes depending on video length!

#### Example Request:
```
GET /api/download/mp4/147365?server_type=sub&filename=NarutoEp1
```

#### How It Works:
1. Fetches M3U8 playlist from streaming server
2. Downloads all HLS video segments (.ts files)
3. Uses FFmpeg to combine into single MP4
4. Streams the MP4 file to your device

---

### ✅ Check FFmpeg Status
- **GET /api/download/mp4/check**
- Verify if FFmpeg is installed and working on the server.
- **Response Example:**
```json
{
  "ffmpeg_available": true,
  "ffmpeg_path": "/opt/homebrew/bin/ffmpeg",
  "message": "FFmpeg is available. MP4 downloads will work!"
}
```

---

### 📥 Get Download Links (Advanced)
- **GET /api/download/{episode_id}**
- Get downloadable video URLs with multiple server options.
- **Parameters:**
  - `episode_id` (required): Episode ID from the watch URL (e.g., "147365")
  - `server_type` (optional): "sub" (default), "dub", or "all"
  - `quality` (optional): "auto" (default), "1080p", "720p", "480p", "360p"
- **Response Example:**
```json
{
  "success": true,
  "episode_id": "147365",
  "server_type": "sub",
  "total_options": 3,
  "download_options": [
    {
      "server": "HD-1 (SUB)",
      "quality": "auto",
      "type": "hls",
      "is_m3u8": true,
      "direct_url": "https://cdn.example.com/.../master.m3u8",
      "proxy_url": "http://your-api.com/api/proxy/m3u8?url=...",
      "headers": {
        "Referer": "https://megacloud.blog/",
        "Origin": "https://megacloud.blog",
        "User-Agent": "Mozilla/5.0..."
      },
      "download_commands": {
        "ffmpeg": "ffmpeg -headers \"Referer: https://megacloud.blog/...\" -i \"https://...\" -c copy \"output.mp4\"",
        "yt_dlp": "yt-dlp --referer \"https://megacloud.blog/\" -o \"%(title)s.%(ext)s\" \"https://...\"",
        "aria2c": null
      },
      "notes": {
        "proxy_url": "Use this URL directly - no headers needed",
        "direct_url": "Requires headers to be sent with the request",
        "ffmpeg": "Best for HLS (.m3u8) streams - converts to MP4",
        "yt_dlp": "Universal downloader - handles most formats"
      },
      "subtitles": [
        {
          "file": "https://mgstatics.xyz/subtitle/.../eng.vtt",
          "label": "English",
          "kind": "captions"
        }
      ]
    }
  ],
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
```

### Usage Examples

#### 🎬 Download MP4 in Browser
```
Just navigate to: http://your-api.com/api/download/mp4/{episode_id}
The MP4 file will download automatically!
```

#### 🎬 Download MP4 with cURL
```bash
curl -L "http://your-api.com/api/download/mp4/147365?server_type=sub" -o episode.mp4
```

#### 🎬 Flutter MP4 Download
```dart
import 'package:dio/dio.dart';

Future<void> downloadEpisodeMp4(String episodeId) async {
  final dio = Dio();
  
  // Direct MP4 download - simple!
  await dio.download(
    'https://your-api.com/api/download/mp4/$episodeId',
    '/path/to/episode.mp4',
    queryParameters: {'server_type': 'sub'},
    onReceiveProgress: (received, total) {
      if (total != -1) {
        print('${(received / total * 100).toStringAsFixed(0)}%');
      }
    },
  );
}
```

---

#### Advanced: Using Download Links with FFmpeg
```bash
# First get the download links
curl "http://your-api.com/api/download/147365?server_type=sub"

# Then use FFmpeg with the direct_url and headers
ffmpeg -headers "Referer: https://megacloud.blog/\r\n" \
  -i "https://cdn.example.com/master.m3u8" \
  -c copy -bsf:a aac_adtstoasc "output.mp4"
```

#### Advanced: Using proxy_url (No Headers Needed)
```bash
curl -L "http://your-api.com/api/proxy/m3u8?url=..." -o video.m3u8
```

#### Advanced: yt-dlp Download
```bash
yt-dlp --referer "https://megacloud.blog/" \
  -o "video.%(ext)s" \
  "https://cdn.example.com/master.m3u8"
```

#### Advanced: Flutter with Download Links
```dart
import 'package:dio/dio.dart';

Future<void> downloadWithProxy(String episodeId) async {
  final dio = Dio();
  
  // 1. Get download links
  final response = await dio.get(
    'https://your-api.com/api/download/$episodeId',
    queryParameters: {'server_type': 'sub'},
  );
  
  // 2. Use proxy_url (no headers needed!)
  final proxyUrl = response.data['download_options'][0]['proxy_url'];
  
  // 3. Download
  await dio.download(proxyUrl, '/path/to/video.mp4',
    onReceiveProgress: (received, total) {
      print('${(received / total * 100).toStringAsFixed(0)}%');
    },
  );
}
```

### Key Points
| Endpoint | Headers Needed? | Best For |
|----------|-----------------|----------|
| `/api/download/mp4/{id}` | ❌ No | **Easiest!** Direct MP4 download to device |
| `proxy_url` | ❌ No | Flutter apps, browsers, simple downloaders |
| `direct_url` | ✅ Yes | Advanced tools like ffmpeg, yt-dlp |

**Recommendation:** Use `/api/download/mp4/{episode_id}` for the easiest integration - just call it and get an MP4 file!

---

## 13. MyAnimeList (MAL) Endpoints
- **GET /api/mal/search?query=naruto&limit=10**: Search anime on MAL
- **GET /api/mal/anime/{mal_id}**: Get anime details from MAL
- **GET /api/mal/ranking?type=all&limit=10**: Get anime rankings from MAL
- **GET /api/mal/seasonal?year=2024&season=winter&limit=10**: Get seasonal anime from MAL
- **Response Example (Search):**
```json
{
  "success": true,
  "source": "myanimelist",
  "count": 1,
  "data": [
    {
      "mal_id": 20,
      "title": "Naruto",
      "main_picture": {"medium": "https://...jpg"},
      "mean_score": 7.9,
      "rank": 100,
      "popularity": 10,
      "num_episodes": 220,
      "status": "finished_airing",
      "genres": [{"id": 1, "name": "Action"}],
      "studios": [{"id": 1, "name": "Studio Pierrot"}],
      "media_type": "tv"
    }
  ]
}
```

## 13. MAL User Authentication
- **POST /api/mal/user/auth**: Get OAuth2 authorization URL
  - **Request Body:**
    ```json
    {
      "client_id": "YOUR_CLIENT_ID",
      "client_secret": "YOUR_CLIENT_SECRET",
      "redirect_uri": "YOUR_REDIRECT_URI"
    }
    ```
  - **Response Example:**
    ```json
    {
      "success": true,
      "message": "Open auth_url in browser to login. Save code_verifier for token exchange.",
      "privacy_notice": "We DO NOT store your credentials. This request is stateless.",
      "data": {
        "auth_url": "https://myanimelist.net/v1/oauth2/authorize?...",
        "code_verifier": "...",
        "state": "..."
      }
    }
    ```
- **POST /api/mal/user/token**: Exchange code for access token
  - **Request Body:**
    ```json
    {
      "client_id": "YOUR_CLIENT_ID",
      "client_secret": "YOUR_CLIENT_SECRET",
      "code": "CODE_FROM_CALLBACK",
      "code_verifier": "CODE_VERIFIER_FROM_AUTH",
      "redirect_uri": "YOUR_REDIRECT_URI"
    }
    ```
  - **Response Example:**
    ```json
    {
      "success": true,
      "message": "Save these tokens securely. We DO NOT store them.",
      "privacy_notice": "Tokens are returned to you only. Store them securely on your end.",
      "data": {
        "access_token": "...",
        "refresh_token": "...",
        "expires_in": 2678400,
        "token_type": "Bearer"
      }
    }
    ```
- **POST /api/mal/user/animelist**: Get user's anime list
  - **Request Body:**
    ```json
    {
      "client_id": "YOUR_CLIENT_ID",
      "access_token": "USER_ACCESS_TOKEN",
      "status": "watching",
      "limit": 100
    }
    ```
  - **Response Example:**
    ```json
    {
      "success": true,
      "privacy_notice": "We DO NOT store your data. This response is not logged.",
      "count": 1,
      "data": [
        {
          "anime": {"mal_id": 20, "title": "Naruto", ...},
          "status": "watching",
          "score": 8,
          "num_episodes_watched": 100,
          "updated_at": "2025-12-22T12:00:00Z"
        }
      ]
    }
    ```
- **POST /api/mal/user/profile**: Get authenticated user's MAL profile
  - **Request Body:**
    ```json
    {
      "client_id": "YOUR_CLIENT_ID",
      "access_token": "USER_ACCESS_TOKEN"
    }
    ```
  - **Response Example:**
    ```json
    {
      "success": true,
      "privacy_notice": "We DO NOT store your profile data.",
      "data": {
        "id": 12345,
        "name": "your_username",
        "picture": "https://...jpg",
        "anime_statistics": { ... }
      }
    }
    ```

**Privacy Notice:** Credentials and tokens are never stored on the server. All authentication is stateless and secure.

## 14. Combined Search
- **GET /api/combined/search?query=naruto&limit=5**
- Search both HiAnime and MAL simultaneously. Returns results from both sources for comparison.
- **Response Example:**
```json
{
  "success": true,
  "query": "naruto",
  "sources": {
    "hianime": {
      "enabled": true,
      "results": [ { ... } ],
      "count": 1,
      "error": null
    },
    "myanimelist": {
      "enabled": true,
      "results": [ { ... } ],
      "count": 1,
      "error": null
    }
  }
}
```

---

## Response Models
- All endpoints return a JSON object with at least `success` and `data` fields. Some include `count`, `page`, or `error`.
- Errors are returned with `success: false` and an `error` message.

---

## Error Handling
- Standardized error responses for all endpoints.
- HTTP status codes and error messages are provided for all failures.

---

## Example Usage

### Search Example
```
GET /api/search?keyword=one%20piece&page=1
```
Response:
```
{
  "success": true,
  "count": 1,
  "page": 1,
  "data": [
    {
      "id": "one-piece-100",
      "title": "One Piece",
      ...
    }
  ]
}
```

---

For more details, see the [OpenAPI docs](/docs) or [ReDoc](/redoc) in your running API instance.
