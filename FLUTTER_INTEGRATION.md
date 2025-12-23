# Flutter Integration Guide for HiAnime API

## Quick Start

### Base URL
```
http://127.0.0.1:8000  (local development)
https://your-domain.com  (production)
```

---

## 🎬 Streaming Endpoints

### 1. Get Playable Stream URLs

**Endpoint:**
```
GET /api/stream/{episode_id}?server_type={sub|dub}&include_proxy_url={true|false}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `episode_id` | string | Yes | Episode ID (e.g., "2142") |
| `server_type` | string | No | `sub` (default), `dub`, or `all` |
| `include_proxy_url` | bool | No | Set `true` if direct URLs are blocked |

**Example Request:**
```
GET http://127.0.0.1:8000/api/stream/2142?server_type=sub&include_proxy_url=true
```

**Response:**
```json
{
  "success": true,
  "episode_id": "2142",
  "server_type": "sub",
  "total_streams": 3,
  "streams": [
    {
      "name": "HD-1 (SUB)",
      "server_name": "HD-1",
      "server_type": "sub",
      "sources": [
        {
          "file": "https://sunshinerays93.live/_v7/.../master.m3u8",
          "type": "hls",
          "quality": "auto",
          "isM3U8": true,
          "host": "sunshinerays93.live",
          "proxy_url": "/api/proxy/m3u8?url=aHR0cHM6Ly9..."
        }
      ],
      "subtitles": [
        {
          "file": "https://mgstatics.xyz/subtitle/.../eng-2.vtt",
          "label": "English",
          "kind": "captions"
        }
      ],
      "skips": {
        "intro": { "start": 31, "end": 111 },
        "outro": { "start": 1376, "end": 1447 }
      },
      "headers": {
        "Referer": "https://hianime.to/",
        "User-Agent": "Mozilla/5.0 ..."
      }
    }
  ]
}
```

---

## 🔧 Flutter Implementation

### Dependencies (pubspec.yaml)

```yaml
dependencies:
  http: ^1.1.0
  better_player: ^0.0.84
  # OR
  video_player: ^2.8.1
  chewie: ^1.7.4
```

### API Service Class

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class HiAnimeApiService {
  static const String baseUrl = 'http://127.0.0.1:8000'; // Change for production
  
  /// Get streaming links for an episode
  /// 
  /// [episodeId] - Episode ID from the URL (e.g., "2142")
  /// [serverType] - "sub", "dub", or "all"
  /// [includeProxy] - Set true if direct URLs don't work
  static Future<StreamResponse> getStreamingLinks({
    required String episodeId,
    String serverType = 'sub',
    bool includeProxy = true,
  }) async {
    final url = Uri.parse(
      '$baseUrl/api/stream/$episodeId?server_type=$serverType&include_proxy_url=$includeProxy'
    );
    
    final response = await http.get(url);
    
    if (response.statusCode == 200) {
      return StreamResponse.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to load streams: ${response.statusCode}');
    }
  }
  
  /// Search for anime
  static Future<List<SearchResult>> searchAnime(String query) async {
    final url = Uri.parse('$baseUrl/api/search?keyword=$query');
    final response = await http.get(url);
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return (data['data'] as List)
          .map((item) => SearchResult.fromJson(item))
          .toList();
    }
    throw Exception('Search failed');
  }
  
  /// Get episodes for an anime
  static Future<List<Episode>> getEpisodes(String animeSlug) async {
    final url = Uri.parse('$baseUrl/api/episodes/$animeSlug');
    final response = await http.get(url);
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return (data['episodes'] as List)
          .map((item) => Episode.fromJson(item))
          .toList();
    }
    throw Exception('Failed to get episodes');
  }
}
```

### Data Models

```dart
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
}

class StreamSource {
  final String file;        // Direct m3u8 URL
  final String? proxyUrl;   // Proxy URL (use if direct fails)
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
}

class SearchResult {
  final String id;
  final String slug;
  final String name;
  final String? poster;
  final String? type;

  SearchResult({
    required this.id,
    required this.slug,
    required this.name,
    this.poster,
    this.type,
  });

  factory SearchResult.fromJson(Map<String, dynamic> json) {
    return SearchResult(
      id: json['id'] ?? '',
      slug: json['slug'] ?? '',
      name: json['name'] ?? '',
      poster: json['poster'],
      type: json['type'],
    );
  }
}

class Episode {
  final String id;
  final int number;
  final String? title;

  Episode({required this.id, required this.number, this.title});

  factory Episode.fromJson(Map<String, dynamic> json) {
    return Episode(
      id: json['id']?.toString() ?? '',
      number: json['number'] ?? 0,
      title: json['title'],
    );
  }
}
```

---

## 🎥 Video Player Implementation

### Option 1: Using BetterPlayer (Recommended)

```dart
import 'package:better_player/better_player.dart';

class VideoPlayerScreen extends StatefulWidget {
  final String episodeId;
  final String serverType;

  const VideoPlayerScreen({
    required this.episodeId,
    this.serverType = 'sub',
  });

  @override
  _VideoPlayerScreenState createState() => _VideoPlayerScreenState();
}

class _VideoPlayerScreenState extends State<VideoPlayerScreen> {
  BetterPlayerController? _controller;
  StreamResponse? _streamData;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadStream();
  }

  Future<void> _loadStream() async {
    try {
      final response = await HiAnimeApiService.getStreamingLinks(
        episodeId: widget.episodeId,
        serverType: widget.serverType,
        includeProxy: true,
      );

      if (response.streams.isEmpty) {
        throw Exception('No streams available');
      }

      _streamData = response;
      _initializePlayer(response.streams.first);
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  void _initializePlayer(StreamData stream) {
    final source = stream.sources.first;
    
    // Use proxy URL if available, otherwise use direct URL with headers
    final videoUrl = source.proxyUrl != null
        ? '${HiAnimeApiService.baseUrl}${source.proxyUrl}'
        : source.file;

    // Headers only needed for direct URLs
    final headers = source.proxyUrl != null ? <String, String>{} : stream.headers;

    // Setup subtitles
    final subtitles = stream.subtitles.map((sub) {
      return BetterPlayerSubtitlesSource(
        type: BetterPlayerSubtitlesSourceType.network,
        urls: [sub.file],
        name: sub.label,
      );
    }).toList();

    final dataSource = BetterPlayerDataSource(
      BetterPlayerDataSourceType.network,
      videoUrl,
      headers: headers,
      subtitles: subtitles,
      videoFormat: BetterPlayerVideoFormat.hls,
    );

    _controller = BetterPlayerController(
      BetterPlayerConfiguration(
        autoPlay: true,
        aspectRatio: 16 / 9,
        fit: BoxFit.contain,
        controlsConfiguration: BetterPlayerControlsConfiguration(
          enableSkips: true,
          skipBackIcon: Icons.replay_10,
          skipForwardIcon: Icons.forward_10,
        ),
      ),
      betterPlayerDataSource: dataSource,
    );

    setState(() => _isLoading = false);
  }

  void _switchServer(StreamData stream) {
    _controller?.dispose();
    setState(() => _isLoading = true);
    _initializePlayer(stream);
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return Scaffold(
        body: Center(child: Text('Error: $_error')),
      );
    }

    if (_isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      backgroundColor: Colors.black,
      body: Column(
        children: [
          // Video Player
          AspectRatio(
            aspectRatio: 16 / 9,
            child: BetterPlayer(controller: _controller!),
          ),
          
          // Server Selection
          if (_streamData != null)
            Container(
              height: 50,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                itemCount: _streamData!.streams.length,
                itemBuilder: (context, index) {
                  final stream = _streamData!.streams[index];
                  return Padding(
                    padding: const EdgeInsets.all(8.0),
                    child: ElevatedButton(
                      onPressed: () => _switchServer(stream),
                      child: Text(stream.name),
                    ),
                  );
                },
              ),
            ),
            
          // Skip Intro/Outro Buttons
          if (_streamData?.streams.first.skips != null)
            _buildSkipButtons(_streamData!.streams.first.skips!),
        ],
      ),
    );
  }

  Widget _buildSkipButtons(SkipTimes skips) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        if (skips.intro != null)
          ElevatedButton(
            onPressed: () {
              _controller?.seekTo(Duration(seconds: skips.intro!.end));
            },
            child: const Text('Skip Intro'),
          ),
        const SizedBox(width: 16),
        if (skips.outro != null)
          ElevatedButton(
            onPressed: () {
              _controller?.seekTo(Duration(seconds: skips.outro!.end));
            },
            child: const Text('Skip Outro'),
          ),
      ],
    );
  }
}
```

### Option 2: Using video_player + chewie

```dart
import 'package:video_player/video_player.dart';
import 'package:chewie/chewie.dart';

class ChewieVideoPlayer extends StatefulWidget {
  final String episodeId;

  const ChewieVideoPlayer({required this.episodeId});

  @override
  _ChewieVideoPlayerState createState() => _ChewieVideoPlayerState();
}

class _ChewieVideoPlayerState extends State<ChewieVideoPlayer> {
  VideoPlayerController? _videoController;
  ChewieController? _chewieController;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _initPlayer();
  }

  Future<void> _initPlayer() async {
    try {
      final response = await HiAnimeApiService.getStreamingLinks(
        episodeId: widget.episodeId,
        includeProxy: true,
      );

      final stream = response.streams.first;
      final source = stream.sources.first;

      // Prefer proxy URL (no headers needed)
      final videoUrl = source.proxyUrl != null
          ? '${HiAnimeApiService.baseUrl}${source.proxyUrl}'
          : source.file;

      _videoController = VideoPlayerController.networkUrl(
        Uri.parse(videoUrl),
        httpHeaders: source.proxyUrl != null ? {} : stream.headers,
      );

      await _videoController!.initialize();

      _chewieController = ChewieController(
        videoPlayerController: _videoController!,
        autoPlay: true,
        aspectRatio: 16 / 9,
        allowFullScreen: true,
        allowMuting: true,
        showControls: true,
      );

      setState(() => _isLoading = false);
    } catch (e) {
      print('Error initializing player: $e');
    }
  }

  @override
  void dispose() {
    _videoController?.dispose();
    _chewieController?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    return Chewie(controller: _chewieController!);
  }
}
```

---

## 📱 Complete App Flow Example

```dart
// main.dart
void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Anime App',
      theme: ThemeData.dark(),
      home: const SearchScreen(),
    );
  }
}

// search_screen.dart
class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final _searchController = TextEditingController();
  List<SearchResult> _results = [];
  bool _isLoading = false;

  Future<void> _search() async {
    if (_searchController.text.isEmpty) return;
    
    setState(() => _isLoading = true);
    
    try {
      _results = await HiAnimeApiService.searchAnime(_searchController.text);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Search failed: $e')),
      );
    }
    
    setState(() => _isLoading = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Search Anime')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Search anime...',
                suffixIcon: IconButton(
                  icon: const Icon(Icons.search),
                  onPressed: _search,
                ),
              ),
              onSubmitted: (_) => _search(),
            ),
          ),
          if (_isLoading) const CircularProgressIndicator(),
          Expanded(
            child: ListView.builder(
              itemCount: _results.length,
              itemBuilder: (context, index) {
                final anime = _results[index];
                return ListTile(
                  leading: anime.poster != null
                      ? Image.network(anime.poster!, width: 50)
                      : null,
                  title: Text(anime.name),
                  subtitle: Text(anime.type ?? ''),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => EpisodeListScreen(animeSlug: anime.slug),
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

// episode_list_screen.dart  
class EpisodeListScreen extends StatefulWidget {
  final String animeSlug;

  const EpisodeListScreen({required this.animeSlug});

  @override
  State<EpisodeListScreen> createState() => _EpisodeListScreenState();
}

class _EpisodeListScreenState extends State<EpisodeListScreen> {
  List<Episode> _episodes = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadEpisodes();
  }

  Future<void> _loadEpisodes() async {
    try {
      _episodes = await HiAnimeApiService.getEpisodes(widget.animeSlug);
    } catch (e) {
      print('Error: $e');
    }
    setState(() => _isLoading = false);
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Episodes')),
      body: ListView.builder(
        itemCount: _episodes.length,
        itemBuilder: (context, index) {
          final episode = _episodes[index];
          return ListTile(
            title: Text('Episode ${episode.number}'),
            subtitle: episode.title != null ? Text(episode.title!) : null,
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => VideoPlayerScreen(episodeId: episode.id),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
```

---

## 🔑 Key Points

### When to use Direct URL vs Proxy URL

| Scenario | Use | Why |
|----------|-----|-----|
| Default | `proxy_url` | Works everywhere, no headers needed |
| Low latency needed | `file` + `headers` | Direct connection, faster |
| Cloudflare blocking | `proxy_url` | Bypasses protection |
| Production server | `proxy_url` | More reliable |

### URL Construction

```dart
// Direct URL (needs headers)
final directUrl = streamSource.file;
final headers = streamData.headers;

// Proxy URL (no headers needed)
final proxyUrl = '${baseUrl}${streamSource.proxyUrl}';
// Example: http://127.0.0.1:8000/api/proxy/m3u8?url=aHR0cHM6Ly...
```

### Error Handling Tips

```dart
try {
  // Try proxy URL first (most reliable)
  await playWithProxy(source.proxyUrl);
} catch (e) {
  // Fallback to direct URL with headers
  await playDirect(source.file, stream.headers);
}
```

---

## 📋 API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/search?keyword={query}` | GET | Search anime |
| `/api/anime/{slug}` | GET | Get anime details |
| `/api/episodes/{slug}` | GET | Get episode list |
| `/api/stream/{episode_id}` | GET | Get streaming URLs |
| `/api/proxy/m3u8?url={base64}` | GET | Proxy for m3u8 streams |

---

## 🚀 Production Checklist

- [ ] Change `baseUrl` to your production server
- [ ] Add error handling for network failures
- [ ] Implement retry logic for failed streams
- [ ] Add loading states and error UI
- [ ] Cache episode lists locally
- [ ] Handle app lifecycle (pause/resume video)
- [ ] Add quality selection UI
- [ ] Implement subtitle toggle
