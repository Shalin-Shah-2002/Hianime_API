# Flutter Integration Guide for HiAnime API

Complete guide for integrating video streaming in Flutter apps with the HiAnime API.

## 🚀 Base URL

```
https://hianime-api-b6ix.onrender.com
```

---

## 📺 Video Streaming Endpoints

### Understanding the Flow

```
1. Search/Browse → Get anime slug
2. Get Episodes → Get episode_id  
3. Get Stream → Get video URL + proxy_url
4. Play Video → Use proxy_url for mobile!
```

---

## 🔗 All Video Streaming Endpoints

### 1. Get Episode List
```
GET /api/episodes/{anime_slug}
```

**Example:** `/api/episodes/one-piece-100`

**Response:**
```json
{
  "success": true,
  "count": 1122,
  "data": [
    {
      "number": 1,
      "title": "I'm Luffy! The Man Who's Gonna Be King of the Pirates!",
      "episode_id": "2141",
      "url": "/watch/one-piece-100?ep=2141",
      "is_filler": false
    }
  ]
}
```

---

### 2. Get Video Servers
```
GET /api/servers/{episode_id}
```

**Example:** `/api/servers/2143`

**Response:**
```json
{
  "success": true,
  "episode_id": "2143",
  "data": [
    {"server_id": "1", "server_name": "HD-1", "server_type": "sub"},
    {"server_id": "2", "server_name": "HD-2", "server_type": "sub"},
    {"server_id": "3", "server_name": "HD-1", "server_type": "dub"}
  ]
}
```

---

### 3. Get Video Sources (Embed URLs)
```
GET /api/sources/{episode_id}?server_type=sub
```

**Example:** `/api/sources/2143?server_type=sub`

Returns embed URLs (iframe URLs) - not directly playable.

---

### 4. ⭐ Get Streaming Links (MAIN ENDPOINT)
```
GET /api/stream/{episode_id}?server_type=sub&include_proxy_url=true
```

**Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `episode_id` | string | required | Episode ID (e.g., "2143") |
| `server_type` | string | "sub" | "sub", "dub", or "all" |
| `include_proxy_url` | bool | false | **SET TO `true` FOR MOBILE!** |

**Example:** `/api/stream/2143?server_type=sub&include_proxy_url=true`

**Response:**
```json
{
  "success": true,
  "episode_id": "2143",
  "server_type": "sub",
  "total_streams": 3,
  "streams": [
    {
      "name": "HD-1 (SUB)",
      "server_name": "HD-1",
      "server_type": "sub",
      "sources": [
        {
          "file": "https://sunburst93.live/_v7/.../master.m3u8",
          "proxy_url": "/api/proxy/m3u8?url=aHR0cHM6...&ref=aHR0cHM6...",
          "type": "hls",
          "quality": "auto",
          "isM3U8": true,
          "host": "sunburst93.live"
        }
      ],
      "subtitles": [
        {"file": "https://cc.megacloud.tv/.../eng.vtt", "label": "English", "kind": "captions"}
      ],
      "skips": {
        "intro": {"start": 0, "end": 85},
        "outro": {"start": 1300, "end": 1420}
      },
      "headers": {
        "Referer": "https://megacloud.blog/",
        "User-Agent": "Mozilla/5.0..."
      }
    }
  ]
}
```

---

### 5. 🆕 M3U8 Proxy (For Mobile Apps)
```
GET /api/proxy/m3u8?url={base64_url}&ref={base64_referer}
```

**What it does:**
- Fetches m3u8 playlist with correct headers
- Rewrites ALL internal URLs to go through proxy
- Enables seamless playback on iOS/Android

**Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `url` | string | Base64 encoded m3u8 URL |
| `ref` | string | Base64 encoded referer (from stream headers) |

---

### 6. 🆕 Segment Proxy
```
GET /api/proxy/segment?url={base64_url}&ref={base64_referer}
```

Proxies video segments (.ts, .aac, encryption keys). Used internally by m3u8 proxy.

---

### 7. Extract Stream from Embed
```
GET /api/extract-stream?url={embed_url}
```

Extracts playable m3u8 from embed URLs directly.

---

## ⚠️ CRITICAL: Understanding `file` vs `proxy_url`

| Field | Use Case | Headers Needed? |
|-------|----------|-----------------|
| `file` | Web browsers, players that support headers | ✅ Yes |
| `proxy_url` | **Mobile apps (Flutter, iOS, Android)** | ❌ No |

### Why Mobile Apps MUST Use `proxy_url`

```
❌ WRONG: Using `file` URL directly
   → iOS AVPlayer can't send custom headers
   → Error: OSStatus -12660 (Permission denied)

✅ CORRECT: Using `proxy_url`  
   → Server adds headers automatically
   → Works on all platforms!
```

---

## 🔧 Flutter Implementation

### Dependencies (pubspec.yaml)

```yaml
dependencies:
  http: ^1.1.0
  video_player: ^2.8.1
  # OR for more features:
  better_player: ^0.0.84
```

### API Service Class

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class HiAnimeApi {
  static const String baseUrl = 'https://hianime-api-b6ix.onrender.com';

  // ============================================
  // EPISODE ENDPOINTS
  // ============================================

  /// Get all episodes for an anime
  static Future<List<Episode>> getEpisodes(String animeSlug) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/episodes/$animeSlug'),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return (data['data'] as List)
          .map((e) => Episode.fromJson(e))
          .toList();
    }
    throw Exception('Failed to get episodes');
  }

  // ============================================
  // VIDEO SERVER ENDPOINTS
  // ============================================

  /// Get available servers for an episode
  static Future<List<VideoServer>> getServers(String episodeId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/servers/$episodeId'),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return (data['data'] as List)
          .map((s) => VideoServer.fromJson(s))
          .toList();
    }
    throw Exception('Failed to get servers');
  }

  // ============================================
  // ⭐ STREAMING ENDPOINTS (MAIN)
  // ============================================

  /// Get streaming links with proxy URLs for mobile
  /// 
  /// ALWAYS set includeProxy=true for mobile apps!
  static Future<StreamResponse> getStreamingLinks({
    required String episodeId,
    String serverType = 'sub',
    bool includeProxy = true,  // ALWAYS true for mobile!
  }) async {
    final response = await http.get(
      Uri.parse(
        '$baseUrl/api/stream/$episodeId?server_type=$serverType&include_proxy_url=$includeProxy'
      ),
    );

    if (response.statusCode == 200) {
      return StreamResponse.fromJson(jsonDecode(response.body));
    }
    throw Exception('Failed to get streams');
  }

  /// Build the full proxy URL for video playback
  /// 
  /// Use this URL directly in video_player - NO headers needed!
  static String buildProxyUrl(String proxyPath) {
    return '$baseUrl$proxyPath';
  }

  // ============================================
  // SEARCH & BROWSE ENDPOINTS
  // ============================================

  static Future<List<SearchResult>> search(String query, {int page = 1}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/search?keyword=${Uri.encodeComponent(query)}&page=$page'),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return (data['data'] as List)
          .map((item) => SearchResult.fromJson(item))
          .toList();
    }
    throw Exception('Search failed');
  }

  static Future<AnimeDetails> getAnimeDetails(String slug) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/anime/$slug'),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return AnimeDetails.fromJson(data['data']);
    }
    throw Exception('Failed to get anime details');
  }
}
```

### Data Models

```dart
// ============================================
// STREAMING MODELS
// ============================================

class StreamResponse {
  final bool success;
  final String episodeId;
  final int totalStreams;
  final List<StreamData> streams;

  StreamResponse({
    required this.success,
    required this.episodeId,
    required this.totalStreams,
    required this.streams,
  });

  factory StreamResponse.fromJson(Map<String, dynamic> json) {
    return StreamResponse(
      success: json['success'] ?? false,
      episodeId: json['episode_id'] ?? '',
      totalStreams: json['total_streams'] ?? 0,
      streams: (json['streams'] as List?)
          ?.map((s) => StreamData.fromJson(s))
          .toList() ?? [],
    );
  }
  
  /// Get the best stream (first available)
  StreamData? get bestStream => streams.isNotEmpty ? streams.first : null;
}

class StreamData {
  final String name;
  final String serverName;
  final String serverType;
  final List<StreamSource> sources;
  final List<Subtitle> subtitles;
  final SkipTimes? skips;
  final Map<String, String> headers;

  StreamData({
    required this.name,
    required this.serverName,
    required this.serverType,
    required this.sources,
    required this.subtitles,
    this.skips,
    required this.headers,
  });

  factory StreamData.fromJson(Map<String, dynamic> json) {
    return StreamData(
      name: json['name'] ?? '',
      serverName: json['server_name'] ?? '',
      serverType: json['server_type'] ?? '',
      sources: (json['sources'] as List?)
          ?.map((s) => StreamSource.fromJson(s))
          .toList() ?? [],
      subtitles: (json['subtitles'] as List?)
          ?.map((s) => Subtitle.fromJson(s))
          .toList() ?? [],
      skips: json['skips'] != null ? SkipTimes.fromJson(json['skips']) : null,
      headers: Map<String, String>.from(json['headers'] ?? {}),
    );
  }
  
  /// Get the best source (first available)
  StreamSource? get bestSource => sources.isNotEmpty ? sources.first : null;
}

class StreamSource {
  final String file;         // Original URL (needs headers)
  final String? proxyUrl;    // ⭐ USE THIS FOR MOBILE!
  final String type;
  final String quality;
  final bool isM3U8;
  final String host;

  StreamSource({
    required this.file,
    this.proxyUrl,
    required this.type,
    required this.quality,
    required this.isM3U8,
    required this.host,
  });

  factory StreamSource.fromJson(Map<String, dynamic> json) {
    return StreamSource(
      file: json['file'] ?? '',
      proxyUrl: json['proxy_url'],
      type: json['type'] ?? 'hls',
      quality: json['quality'] ?? 'auto',
      isM3U8: json['isM3U8'] ?? true,
      host: json['host'] ?? '',
    );
  }
  
  /// Check if proxy URL is available
  bool get hasProxy => proxyUrl != null && proxyUrl!.isNotEmpty;
}

class Subtitle {
  final String file;
  final String label;
  final String kind;

  Subtitle({required this.file, required this.label, required this.kind});

  factory Subtitle.fromJson(Map<String, dynamic> json) {
    return Subtitle(
      file: json['file'] ?? '',
      label: json['label'] ?? 'Unknown',
      kind: json['kind'] ?? 'captions',
    );
  }
}

class SkipTimes {
  final TimeRange? intro;
  final TimeRange? outro;

  SkipTimes({this.intro, this.outro});

  factory SkipTimes.fromJson(Map<String, dynamic> json) {
    return SkipTimes(
      intro: json['intro'] != null ? TimeRange.fromJson(json['intro']) : null,
      outro: json['outro'] != null ? TimeRange.fromJson(json['outro']) : null,
    );
  }
}

class TimeRange {
  final int start;
  final int end;

  TimeRange({required this.start, required this.end});

  factory TimeRange.fromJson(Map<String, dynamic> json) {
    return TimeRange(
      start: json['start'] ?? 0,
      end: json['end'] ?? 0,
    );
  }
  
  Duration get startDuration => Duration(seconds: start);
  Duration get endDuration => Duration(seconds: end);
}

// ============================================
// OTHER MODELS
// ============================================

class Episode {
  final int number;
  final String? title;
  final String episodeId;
  final bool isFiller;

  Episode({
    required this.number,
    this.title,
    required this.episodeId,
    this.isFiller = false,
  });

  factory Episode.fromJson(Map<String, dynamic> json) {
    return Episode(
      number: json['number'] ?? 0,
      title: json['title'],
      episodeId: json['episode_id']?.toString() ?? '',
      isFiller: json['is_filler'] ?? false,
    );
  }
}

class VideoServer {
  final String serverId;
  final String serverName;
  final String serverType;

  VideoServer({
    required this.serverId,
    required this.serverName,
    required this.serverType,
  });

  factory VideoServer.fromJson(Map<String, dynamic> json) {
    return VideoServer(
      serverId: json['server_id']?.toString() ?? '',
      serverName: json['server_name'] ?? '',
      serverType: json['server_type'] ?? 'sub',
    );
  }
}

class SearchResult {
  final String id;
  final String title;
  final String? thumbnail;
  final String? type;
  final int? episodesSub;
  final int? episodesDub;

  SearchResult({
    required this.id,
    required this.title,
    this.thumbnail,
    this.type,
    this.episodesSub,
    this.episodesDub,
  });

  factory SearchResult.fromJson(Map<String, dynamic> json) {
    return SearchResult(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      thumbnail: json['thumbnail'],
      type: json['type'],
      episodesSub: json['episodes_sub'],
      episodesDub: json['episodes_dub'],
    );
  }
}

class AnimeDetails {
  final String id;
  final String title;
  final String? synopsis;
  final String? thumbnail;
  final List<String> genres;
  final double? malScore;

  AnimeDetails({
    required this.id,
    required this.title,
    this.synopsis,
    this.thumbnail,
    this.genres = const [],
    this.malScore,
  });

  factory AnimeDetails.fromJson(Map<String, dynamic> json) {
    return AnimeDetails(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      synopsis: json['synopsis'],
      thumbnail: json['thumbnail'],
      genres: List<String>.from(json['genres'] ?? []),
      malScore: json['mal_score']?.toDouble(),
    );
  }
}
```

---

## 🎥 Video Player Implementation

### Simple Video Player (video_player package)

```dart
import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';

class AnimeVideoPlayer extends StatefulWidget {
  final String episodeId;
  final String serverType;

  const AnimeVideoPlayer({
    required this.episodeId,
    this.serverType = 'sub',
    Key? key,
  }) : super(key: key);

  @override
  State<AnimeVideoPlayer> createState() => _AnimeVideoPlayerState();
}

class _AnimeVideoPlayerState extends State<AnimeVideoPlayer> {
  VideoPlayerController? _controller;
  StreamResponse? _streamData;
  bool _isLoading = true;
  String? _error;
  int _currentServerIndex = 0;

  @override
  void initState() {
    super.initState();
    _loadStream();
  }

  Future<void> _loadStream() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      // ⭐ IMPORTANT: Always include proxy URL for mobile!
      final response = await HiAnimeApi.getStreamingLinks(
        episodeId: widget.episodeId,
        serverType: widget.serverType,
        includeProxy: true,  // MUST be true!
      );

      if (response.streams.isEmpty) {
        throw Exception('No streams available');
      }

      _streamData = response;
      await _initializePlayer(_currentServerIndex);
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _initializePlayer(int serverIndex) async {
    // Dispose old controller
    await _controller?.dispose();

    final stream = _streamData!.streams[serverIndex];
    final source = stream.sources.first;

    // ⭐ USE PROXY URL - NO HEADERS NEEDED!
    final videoUrl = source.proxyUrl != null
        ? HiAnimeApi.buildProxyUrl(source.proxyUrl!)
        : source.file;

    print('Playing URL: $videoUrl');

    _controller = VideoPlayerController.networkUrl(
      Uri.parse(videoUrl),
      // Only add headers if NOT using proxy
      httpHeaders: source.proxyUrl == null ? stream.headers : {},
    );

    try {
      await _controller!.initialize();
      await _controller!.play();
      setState(() => _isLoading = false);
    } catch (e) {
      setState(() {
        _error = 'Failed to play video: $e';
        _isLoading = false;
      });
    }
  }

  void _switchServer(int index) {
    if (index != _currentServerIndex) {
      _currentServerIndex = index;
      _initializePlayer(index);
    }
  }

  void _skipIntro() {
    final intro = _streamData?.streams[_currentServerIndex].skips?.intro;
    if (intro != null) {
      _controller?.seekTo(intro.endDuration);
    }
  }

  void _skipOutro() {
    final outro = _streamData?.streams[_currentServerIndex].skips?.outro;
    if (outro != null) {
      _controller?.seekTo(outro.endDuration);
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        title: Text('Episode ${widget.episodeId}'),
        backgroundColor: Colors.transparent,
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error, color: Colors.red, size: 48),
            SizedBox(height: 16),
            Text(_error!, style: TextStyle(color: Colors.white)),
            SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadStream,
              child: Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (_isLoading) {
      return Center(child: CircularProgressIndicator());
    }

    return Column(
      children: [
        // Video Player
        AspectRatio(
          aspectRatio: _controller!.value.aspectRatio,
          child: VideoPlayer(_controller!),
        ),

        // Controls
        VideoProgressIndicator(_controller!, allowScrubbing: true),
        
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            IconButton(
              icon: Icon(Icons.replay_10, color: Colors.white),
              onPressed: () {
                final pos = _controller!.value.position;
                _controller!.seekTo(pos - Duration(seconds: 10));
              },
            ),
            IconButton(
              icon: Icon(
                _controller!.value.isPlaying ? Icons.pause : Icons.play_arrow,
                color: Colors.white,
                size: 48,
              ),
              onPressed: () {
                setState(() {
                  _controller!.value.isPlaying
                      ? _controller!.pause()
                      : _controller!.play();
                });
              },
            ),
            IconButton(
              icon: Icon(Icons.forward_10, color: Colors.white),
              onPressed: () {
                final pos = _controller!.value.position;
                _controller!.seekTo(pos + Duration(seconds: 10));
              },
            ),
          ],
        ),

        // Skip Buttons
        if (_streamData?.streams[_currentServerIndex].skips != null)
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (_streamData!.streams[_currentServerIndex].skips?.intro != null)
                ElevatedButton(
                  onPressed: _skipIntro,
                  child: Text('Skip Intro'),
                ),
              SizedBox(width: 16),
              if (_streamData!.streams[_currentServerIndex].skips?.outro != null)
                ElevatedButton(
                  onPressed: _skipOutro,
                  child: Text('Skip Outro'),
                ),
            ],
          ),

        // Server Selection
        SizedBox(height: 16),
        Text('Servers', style: TextStyle(color: Colors.white, fontSize: 16)),
        SizedBox(height: 8),
        Wrap(
          spacing: 8,
          children: List.generate(_streamData!.streams.length, (index) {
            final stream = _streamData!.streams[index];
            final isSelected = index == _currentServerIndex;
            return ChoiceChip(
              label: Text(stream.name),
              selected: isSelected,
              onSelected: (_) => _switchServer(index),
            );
          }),
        ),
      ],
    );
  }
}
```

---

## 📋 Complete Endpoint Reference

| Endpoint | Method | Description | For Mobile |
|----------|--------|-------------|------------|
| `/api/search?keyword={q}` | GET | Search anime | ✅ |
| `/api/anime/{slug}` | GET | Anime details | ✅ |
| `/api/episodes/{slug}` | GET | Episode list | ✅ |
| `/api/servers/{episode_id}` | GET | Available servers | ✅ |
| `/api/sources/{episode_id}` | GET | Embed URLs | ⚠️ Not for playback |
| `/api/stream/{episode_id}` | GET | **Streaming URLs** | ⭐ USE THIS |
| `/api/proxy/m3u8?url=...&ref=...` | GET | M3U8 proxy | ⭐ Auto-used |
| `/api/proxy/segment?url=...&ref=...` | GET | Segment proxy | ⭐ Auto-used |
| `/api/extract-stream?url=...` | GET | Extract from embed | ✅ |

---

## 🔑 Key Takeaways

1. **Always use `include_proxy_url=true`** when calling `/api/stream/`
2. **Always use `proxy_url`** field for mobile playback
3. **Never use `file` URL** directly on iOS/Android
4. **Proxy URLs expire** - always fetch fresh URLs before playing
5. **No headers needed** when using proxy URLs

---

## ❓ Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `OSStatus -12660` | Using `file` URL on iOS | Use `proxy_url` instead |
| `403 Forbidden` | Expired URL or wrong headers | Get fresh URL from API |
| `Failed to load` | Network issue | Check internet, retry |
| No streams | Episode not available | Try different server type |

---

## 🚀 Production Checklist

- [ ] Use `proxy_url` for all video playback
- [ ] Handle loading and error states
- [ ] Implement server switching
- [ ] Add skip intro/outro buttons
- [ ] Cache episode lists
- [ ] Handle app lifecycle (pause on background)
