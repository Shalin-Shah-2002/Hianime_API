# HiAnime + MAL Scraper API

A powerful REST API for accessing anime data from HiAnime.to and MyAnimeList, with built-in **stream proxying for mobile apps** (Flutter, iOS, Android).

## 🚀 Live API

**Base URL:** `https://hianime-api-b6ix.onrender.com`

**Interactive Docs:** [https://hianime-api-b6ix.onrender.com/docs](https://hianime-api-b6ix.onrender.com/docs)

## ⭐ Features

- **Search & Browse**: Search anime, filter by genre, type, status
- **Episode Data**: Get full episode lists with streaming links
- **Video Streaming**: Extract playable .m3u8 URLs for video players
- **🆕 Stream Proxy**: Built-in proxy to bypass CDN restrictions for mobile apps
- **MAL Integration**: Search, rankings, seasonal anime from MyAnimeList
- **User Authentication**: OAuth2 flow for MAL user data (privacy-focused)

---

## ⚠️ Important: DNS Configuration (Recommended)

Some ISPs (e.g., Airtel, Jio, etc.) **block anime streaming sites at the DNS level**, which causes stream extraction to fail with "File not found" or connection errors. To avoid this, **use Cloudflare DNS (`1.1.1.1`)** on both your server and client devices.

### macOS

1. Open **System Settings** → **Network**
2. Select your active connection (Wi-Fi or Ethernet) → click **Details…**
3. Go to the **DNS** tab
4. Click **+** and add:
   ```
   1.1.1.1
   1.0.0.1
   ```
5. Click **OK** → **Apply**

**Or via Terminal:**
```bash
networksetup -setdnsservers Wi-Fi 1.1.1.1 1.0.0.1
```

### Windows

1. Open **Control Panel** → **Network and Internet** → **Network and Sharing Center**
2. Click your active connection → **Properties**
3. Select **Internet Protocol Version 4 (TCP/IPv4)** → **Properties**
4. Choose **Use the following DNS server addresses**:
   - Preferred DNS: `1.1.1.1`
   - Alternate DNS: `1.0.0.1`
5. Click **OK** → **Close**

**Or via Command Prompt (Admin):**
```cmd
netsh interface ip set dns "Wi-Fi" static 1.1.1.1
netsh interface ip add dns "Wi-Fi" 1.0.0.1 index=2
```

### iPhone / iPad (iOS)

1. Open **Settings** → **Wi-Fi**
2. Tap the **(i)** icon next to your connected network
3. Scroll down and tap **Configure DNS** → select **Manual**
4. Remove existing entries, then tap **Add Server** and add:
   ```
   1.1.1.1
   1.0.0.1
   ```
5. Tap **Save**

**Or install the [1.1.1.1 app](https://apps.apple.com/app/1-1-1-1-faster-internet/id1423538627) for one-tap setup.**

### Android

**Android 9+ (Private DNS — works on all networks including mobile data):**

1. Open **Settings** → **Network & Internet** → **Private DNS**
2. Select **Private DNS provider hostname**
3. Enter:
   ```
   one.one.one.one
   ```
4. Tap **Save**

**Or install the [1.1.1.1 app](https://play.google.com/store/apps/details?id=com.cloudflare.onedotonedotonedotone) for one-tap setup.**

> **Why Cloudflare DNS?** It's fast (lowest latency globally), privacy-focused (no logging), and doesn't block anime/streaming domains unlike many ISP DNS servers.

---

## 📱 For Flutter/Mobile Developers

**The stream proxy is specifically designed for mobile apps!**

iOS/Android video players can't send custom headers with HLS streams, which causes playback failures (`OSStatus error -12660`). Our proxy handles this automatically.

### Quick Start for Flutter

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:video_player/video_player.dart';

class AnimePlayer {
  static const String apiBase = 'https://hianime-api-b6ix.onrender.com';
  
  Future<String> getProxyStreamUrl(String episodeId) async {
    // 1. Get streaming links with proxy URLs
    final response = await http.get(Uri.parse(
      '$apiBase/api/stream/$episodeId?server_type=sub&include_proxy_url=true'
    ));
    
    final data = jsonDecode(response.body);
    
    if (data['success'] && data['streams'].isNotEmpty) {
      // 2. Use the proxy_url (NOT the original file URL)
      final proxyPath = data['streams'][0]['sources'][0]['proxy_url'];
      return '$apiBase$proxyPath';  // Full proxy URL
    }
    
    throw Exception('No streams available');
  }
  
  Future<VideoPlayerController> initializePlayer(String episodeId) async {
    final streamUrl = await getProxyStreamUrl(episodeId);
    
    // 3. Play directly - no headers needed!
    final controller = VideoPlayerController.networkUrl(Uri.parse(streamUrl));
    await controller.initialize();
    
    return controller;
  }
}
```

### Why Use `proxy_url`?

| URL Type | Works on Mobile? | Reason |
|----------|------------------|--------|
| `file` (original) | ❌ No | Requires headers that iOS/Android can't send |
| `proxy_url` | ✅ Yes | Server adds headers automatically |

---

## 🔗 API Endpoints

### Health Check
```
GET /
```

---

## 📺 Streaming Endpoints

### Get Streaming Links ⭐ MAIN ENDPOINT
```
GET /api/stream/{episode_id}?server_type=sub&include_proxy_url=true
```

**Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `episode_id` | string | required | Episode ID (e.g., "2143") |
| `server_type` | string | "sub" | "sub", "dub", or "all" |
| `include_proxy_url` | bool | false | **Set to `true` for mobile apps!** |

**Response:**
```json
{
  "success": true,
  "episode_id": "2143",
  "streams": [
    {
      "name": "HD-1 (SUB)",
      "sources": [
        {
          "file": "https://cdn.example.com/master.m3u8",
          "proxy_url": "/api/proxy/m3u8?url=...&ref=...",
          "quality": "auto",
          "type": "hls"
        }
      ],
      "subtitles": [
        {"file": "https://cc.example.com/sub.vtt", "label": "English"}
      ],
      "headers": {
        "Referer": "https://megacloud.blog/",
        "User-Agent": "..."
      },
      "skips": {
        "intro": {"start": 0, "end": 85},
        "outro": {"start": 1300, "end": 1420}
      }
    }
  ]
}
```

**Usage:**
- **Web browsers**: Use `file` URL with `headers`
- **Mobile apps**: Use `proxy_url` (prepend base URL)

---

### M3U8 Proxy 🆕
```
GET /api/proxy/m3u8?url={base64_url}&ref={base64_referer}
```

Proxies m3u8 playlists and **automatically rewrites all segment URLs** to go through the proxy. This enables seamless HLS playback on iOS/Android.

**Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `url` | string | Base64 encoded m3u8 URL |
| `ref` | string | Base64 encoded referer URL (from stream headers) |

**What it does:**
1. Fetches the m3u8 playlist server-side with proper headers
2. Rewrites all `.m3u8` sub-playlist URLs → `/api/proxy/m3u8?url=...&ref=...`
3. Rewrites all `.ts` segment URLs → `/api/proxy/segment?url=...&ref=...`
4. Rewrites encryption key URIs → `/api/proxy/segment?url=...&ref=...`
5. Returns the modified playlist that plays seamlessly

---

### Segment Proxy 🆕
```
GET /api/proxy/segment?url={base64_url}&ref={base64_referer}
```

Proxies HLS segments (`.ts`, `.aac`, encryption keys). Used internally by the m3u8 proxy.

---

## 🔍 Search & Browse

### Search Anime
```
GET /api/search?keyword={query}&page=1
```

### Browse Categories
```
GET /api/popular?page=1
GET /api/top-airing?page=1
GET /api/recently-updated?page=1
GET /api/completed?page=1
GET /api/subbed?page=1
GET /api/dubbed?page=1
```

### Filter by Genre/Type
```
GET /api/genre/{genre}?page=1
GET /api/type/{type}?page=1
```

**Genres:** action, adventure, comedy, drama, fantasy, horror, isekai, romance, sci-fi, slice-of-life, sports, supernatural, thriller, etc.

**Types:** movie, tv, ova, ona, special, music

### Advanced Filter
```
GET /api/filter?type=tv&status=airing&season=winter&language=sub&genres=action,fantasy&sort=score&page=1
```

### A-Z List
```
GET /api/az/{letter}?page=1
```

### By Producer/Studio
```
GET /api/producer/{producer_slug}?page=1
```

---

## 📋 Anime Details & Episodes

### Get Anime Details
```
GET /api/anime/{slug}
```

### Get Episode List
```
GET /api/episodes/{slug}
```

### Get Video Servers
```
GET /api/servers/{episode_id}
```

### Get Video Sources (Embed URLs)
```
GET /api/sources/{episode_id}?server_type=sub
```

### Extract Stream from Embed
```
GET /api/extract-stream?url={embed_url}
```

---

## 🎌 MyAnimeList Integration

### Search MAL
```
GET /api/mal/search?query={query}&limit=10
```

### Get MAL Anime Details
```
GET /api/mal/anime/{mal_id}
```

### Rankings
```
GET /api/mal/ranking?type=all&limit=10
```
**Types:** all, airing, upcoming, tv, movie, bypopularity, favorite

### Seasonal Anime
```
GET /api/mal/seasonal?year=2024&season=winter&limit=10
```

### Combined Search (HiAnime + MAL)
```
GET /api/combined/search?query={query}&limit=5
```

---

## 🔐 MAL User Authentication

Privacy-focused OAuth2 flow. Your credentials are **NEVER stored** on our servers.

### Step 1: Get Auth URL
```
POST /api/mal/user/auth
Content-Type: application/json

{
  "client_id": "your_mal_client_id",
  "client_secret": "your_mal_client_secret",
  "redirect_uri": "https://your-app.com/callback"
}
```

### Step 2: Exchange Token
```
POST /api/mal/user/token
```

### Step 3: Get User Data
```
POST /api/mal/user/animelist
POST /api/mal/user/profile
```

---

## 🧪 Testing with Postman

### Import Collection

```json
{
  "info": {"name": "HiAnime API", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"},
  "variable": [{"key": "base_url", "value": "https://hianime-api-b6ix.onrender.com"}],
  "item": [
    {"name": "Health Check", "request": {"method": "GET", "url": "{{base_url}}/"}},
    {"name": "Search Anime", "request": {"method": "GET", "url": "{{base_url}}/api/search?keyword=naruto&page=1"}},
    {"name": "Get Episodes", "request": {"method": "GET", "url": "{{base_url}}/api/episodes/one-piece-100"}},
    {"name": "Get Streaming Links", "request": {"method": "GET", "url": "{{base_url}}/api/stream/2143?server_type=sub&include_proxy_url=true"}}
  ]
}
```

### Quick Test URLs

| Test | URL |
|------|-----|
| Health | `https://hianime-api-b6ix.onrender.com/` |
| Search | `https://hianime-api-b6ix.onrender.com/api/search?keyword=naruto` |
| Stream | `https://hianime-api-b6ix.onrender.com/api/stream/2143?server_type=sub&include_proxy_url=true` |

---

## 📱 Mobile Integration Examples

### Android (Kotlin + ExoPlayer)

```kotlin
val apiBase = "https://hianime-api-b6ix.onrender.com"

// Get proxy URL from API response
val proxyUrl = "$apiBase${jsonResponse.streams[0].sources[0].proxyUrl}"

// Play directly with ExoPlayer - no headers needed!
val mediaItem = MediaItem.fromUri(proxyUrl)
exoPlayer.setMediaItem(mediaItem)
exoPlayer.prepare()
exoPlayer.play()
```

### iOS (Swift + AVPlayer)

```swift
let apiBase = "https://hianime-api-b6ix.onrender.com"

// Get proxy URL from API response
let proxyUrl = URL(string: "\(apiBase)\(stream.sources[0].proxyUrl)")!

// Play directly with AVPlayer - no headers needed!
let player = AVPlayer(url: proxyUrl)
player.play()
```

---

## 🔧 Local Development

### Run Locally

```bash
# Clone repository
git clone https://github.com/Shalin-Shah-2002/Hianime_API.git
cd Hianime_API

# Install dependencies
pip install -r requirements.txt

# Set environment variables (optional, for MAL)
export MAL_CLIENT_ID=your_client_id

# Run server
uvicorn api:app --reload --port 8000

# Open docs
open http://localhost:8000/docs
```

### Deploy to Render

1. Fork this repository
2. Create new Web Service on Render
3. Connect your repo
4. Configure the service:

   **Build Command:**
   ```bash
   pip install -r requirements.txt
   ```

   **Start Command:**
   ```bash
   uvicorn api:app --host 0.0.0.0 --port $PORT
   ```

5. Add these environment variables in Render dashboard:

| Variable | Required | Description |
|----------|----------|-------------|
| `BASE_URL` | ✅ Yes | `https://hianimez.is` |
| `MAL_CLIENT_ID` | ❌ Optional | Your MAL API client ID (for MAL features) |
| `MAL_CLIENT_SECRET` | ❌ Optional | Your MAL API client secret |
| `MAL_REDIRECT_URI` | ❌ Optional | Your OAuth redirect URI |

**Environment Variables Example:**
```env
BASE_URL=https://hianimez.is
MAL_CLIENT_ID=your_client_id_here
MAL_CLIENT_SECRET=your_client_secret_here
MAL_REDIRECT_URI=https://your-app.com/callback
```

> **Note:** `BASE_URL` is required for the scraper to work. MAL variables are only needed if you want to use MyAnimeList integration features.

---

## ❓ Troubleshooting

### Video not playing on iOS/Android?

**Error:** `OSStatus error -12660` or `Permission denied`

**Solution:** 
1. Use `include_proxy_url=true` in your API call
2. Use the `proxy_url` field, NOT the `file` field
3. Prepend your API base URL to the proxy path

### Proxy returning 403?

**Cause:** Using old/expired stream URLs

**Solution:** Always get **fresh** URLs from `/api/stream/{id}`. Stream URLs expire quickly (minutes to hours).

### M3U8 loads but segments fail?

**Cause:** Old API version without referer passthrough

**Solution:** Make sure you're using the latest API. The proxy now includes `&ref=` parameter for proper referer headers.

---

## 📄 License

MIT License - Use freely for personal and commercial projects.

## ⚠️ Disclaimer

This API is for **educational purposes only**. Please:
- Respect website Terms of Service
- Implement appropriate rate limiting
- Do not overload servers
- Be aware of legal implications in your jurisdiction

---

## 🤝 Contributing

Pull requests welcome! Please open an issue first to discuss changes.
