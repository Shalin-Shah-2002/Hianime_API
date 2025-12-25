# Flutter Download Integration Guide 📥

## API Endpoint for Downloads

**Base URL:** `https://your-api-url.com` (replace with your deployed API URL)

### Endpoint: GET `/api/download/{episode_id}`

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `episode_id` | string | ✅ Yes | - | Episode ID (e.g., "147365") |
| `server_type` | string | ❌ No | "sub" | "sub", "dub", or "all" |
| `quality` | string | ❌ No | "auto" | "auto", "1080p", "720p", "480p", "360p" |

---

## API Response Structure

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
      "proxy_url": "http://api.com/api/proxy/m3u8?url=...",
      "headers": {
        "Referer": "https://megacloud.blog/",
        "Origin": "https://megacloud.blog",
        "User-Agent": "Mozilla/5.0..."
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
  "recommended": {
    "method": "proxy_url",
    "reason": "Works without additional configuration"
  }
}
```

---

## Flutter Models

### download_response.dart
```dart
class DownloadResponse {
  final bool success;
  final String episodeId;
  final String serverType;
  final int totalOptions;
  final List<DownloadOption> downloadOptions;

  DownloadResponse({
    required this.success,
    required this.episodeId,
    required this.serverType,
    required this.totalOptions,
    required this.downloadOptions,
  });

  factory DownloadResponse.fromJson(Map<String, dynamic> json) {
    return DownloadResponse(
      success: json['success'] ?? false,
      episodeId: json['episode_id'] ?? '',
      serverType: json['server_type'] ?? 'sub',
      totalOptions: json['total_options'] ?? 0,
      downloadOptions: (json['download_options'] as List? ?? [])
          .map((e) => DownloadOption.fromJson(e))
          .toList(),
    );
  }
}

class DownloadOption {
  final String server;
  final String quality;
  final String type;
  final bool isM3u8;
  final String directUrl;
  final String proxyUrl;
  final Map<String, String> headers;
  final List<Subtitle> subtitles;

  DownloadOption({
    required this.server,
    required this.quality,
    required this.type,
    required this.isM3u8,
    required this.directUrl,
    required this.proxyUrl,
    required this.headers,
    required this.subtitles,
  });

  factory DownloadOption.fromJson(Map<String, dynamic> json) {
    return DownloadOption(
      server: json['server'] ?? '',
      quality: json['quality'] ?? 'auto',
      type: json['type'] ?? 'hls',
      isM3u8: json['is_m3u8'] ?? true,
      directUrl: json['direct_url'] ?? '',
      proxyUrl: json['proxy_url'] ?? '',
      headers: Map<String, String>.from(json['headers'] ?? {}),
      subtitles: (json['subtitles'] as List? ?? [])
          .map((e) => Subtitle.fromJson(e))
          .toList(),
    );
  }
}

class Subtitle {
  final String file;
  final String label;
  final String kind;

  Subtitle({
    required this.file,
    required this.label,
    required this.kind,
  });

  factory Subtitle.fromJson(Map<String, dynamic> json) {
    return Subtitle(
      file: json['file'] ?? '',
      label: json['label'] ?? 'Unknown',
      kind: json['kind'] ?? 'captions',
    );
  }
}
```

---

## Download Service

### download_service.dart
```dart
import 'dart:io';
import 'package:dio/dio.dart';
import 'package:path_provider/path_provider.dart';

class DownloadService {
  final Dio _dio = Dio();
  final String baseUrl;

  DownloadService({required this.baseUrl});

  /// Get download options for an episode
  Future<DownloadResponse> getDownloadLinks({
    required String episodeId,
    String serverType = 'sub',
    String quality = 'auto',
  }) async {
    try {
      final response = await _dio.get(
        '$baseUrl/api/download/$episodeId',
        queryParameters: {
          'server_type': serverType,
          'quality': quality,
        },
      );
      return DownloadResponse.fromJson(response.data);
    } catch (e) {
      throw Exception('Failed to get download links: $e');
    }
  }

  /// Download episode using proxy URL (RECOMMENDED - No headers needed!)
  Future<String> downloadEpisode({
    required String episodeId,
    required String fileName,
    String serverType = 'sub',
    int serverIndex = 0,
    Function(int received, int total)? onProgress,
    CancelToken? cancelToken,
  }) async {
    // 1. Get download links
    final downloadResponse = await getDownloadLinks(
      episodeId: episodeId,
      serverType: serverType,
    );

    if (!downloadResponse.success || downloadResponse.downloadOptions.isEmpty) {
      throw Exception('No download options available');
    }

    // 2. Get proxy URL (works without headers!)
    final option = downloadResponse.downloadOptions[serverIndex];
    final proxyUrl = option.proxyUrl;

    if (proxyUrl.isEmpty) {
      throw Exception('Proxy URL not available');
    }

    // 3. Get download directory
    final dir = await getApplicationDocumentsDirectory();
    final downloadDir = Directory('${dir.path}/Downloads');
    if (!await downloadDir.exists()) {
      await downloadDir.create(recursive: true);
    }

    final filePath = '${downloadDir.path}/$fileName.mp4';

    // 4. Download file
    await _dio.download(
      proxyUrl,
      filePath,
      onReceiveProgress: onProgress,
      cancelToken: cancelToken,
    );

    return filePath;
  }

  /// Download with direct URL (requires headers)
  Future<String> downloadWithHeaders({
    required String episodeId,
    required String fileName,
    String serverType = 'sub',
    int serverIndex = 0,
    Function(int received, int total)? onProgress,
  }) async {
    final downloadResponse = await getDownloadLinks(
      episodeId: episodeId,
      serverType: serverType,
    );

    if (!downloadResponse.success || downloadResponse.downloadOptions.isEmpty) {
      throw Exception('No download options available');
    }

    final option = downloadResponse.downloadOptions[serverIndex];
    
    final dir = await getApplicationDocumentsDirectory();
    final filePath = '${dir.path}/Downloads/$fileName.mp4';

    await _dio.download(
      option.directUrl,
      filePath,
      options: Options(headers: option.headers),
      onReceiveProgress: onProgress,
    );

    return filePath;
  }

  /// Download subtitles
  Future<String?> downloadSubtitles({
    required DownloadOption option,
    required String fileName,
  }) async {
    if (option.subtitles.isEmpty) return null;

    final subtitle = option.subtitles.first;
    final dir = await getApplicationDocumentsDirectory();
    final filePath = '${dir.path}/Downloads/$fileName.vtt';

    await _dio.download(subtitle.file, filePath);
    return filePath;
  }
}
```

---

## Download Manager with Queue

### download_manager.dart
```dart
import 'dart:async';
import 'package:dio/dio.dart';

enum DownloadStatus { pending, downloading, completed, failed, cancelled }

class DownloadTask {
  final String id;
  final String episodeId;
  final String fileName;
  final String serverType;
  DownloadStatus status;
  double progress;
  String? filePath;
  String? error;
  CancelToken? cancelToken;

  DownloadTask({
    required this.id,
    required this.episodeId,
    required this.fileName,
    this.serverType = 'sub',
    this.status = DownloadStatus.pending,
    this.progress = 0,
    this.filePath,
    this.error,
  });
}

class DownloadManager {
  final DownloadService _downloadService;
  final List<DownloadTask> _queue = [];
  final _statusController = StreamController<DownloadTask>.broadcast();
  bool _isProcessing = false;

  DownloadManager({required DownloadService downloadService})
      : _downloadService = downloadService;

  Stream<DownloadTask> get statusStream => _statusController.stream;
  List<DownloadTask> get queue => List.unmodifiable(_queue);

  /// Add download to queue
  String addToQueue({
    required String episodeId,
    required String fileName,
    String serverType = 'sub',
  }) {
    final task = DownloadTask(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      episodeId: episodeId,
      fileName: fileName,
      serverType: serverType,
    );
    _queue.add(task);
    _statusController.add(task);
    _processQueue();
    return task.id;
  }

  /// Process download queue
  Future<void> _processQueue() async {
    if (_isProcessing) return;
    _isProcessing = true;

    while (_queue.any((t) => t.status == DownloadStatus.pending)) {
      final task = _queue.firstWhere((t) => t.status == DownloadStatus.pending);
      task.status = DownloadStatus.downloading;
      task.cancelToken = CancelToken();
      _statusController.add(task);

      try {
        final filePath = await _downloadService.downloadEpisode(
          episodeId: task.episodeId,
          fileName: task.fileName,
          serverType: task.serverType,
          cancelToken: task.cancelToken,
          onProgress: (received, total) {
            if (total > 0) {
              task.progress = received / total;
              _statusController.add(task);
            }
          },
        );

        task.status = DownloadStatus.completed;
        task.filePath = filePath;
        task.progress = 1.0;
      } on DioException catch (e) {
        if (e.type == DioExceptionType.cancel) {
          task.status = DownloadStatus.cancelled;
        } else {
          task.status = DownloadStatus.failed;
          task.error = e.message;
        }
      } catch (e) {
        task.status = DownloadStatus.failed;
        task.error = e.toString();
      }

      _statusController.add(task);
    }

    _isProcessing = false;
  }

  /// Cancel a download
  void cancelDownload(String taskId) {
    final task = _queue.firstWhere((t) => t.id == taskId);
    task.cancelToken?.cancel();
    task.status = DownloadStatus.cancelled;
    _statusController.add(task);
  }

  /// Remove completed/failed/cancelled tasks
  void clearCompleted() {
    _queue.removeWhere((t) =>
        t.status == DownloadStatus.completed ||
        t.status == DownloadStatus.failed ||
        t.status == DownloadStatus.cancelled);
  }

  void dispose() {
    _statusController.close();
  }
}
```

---

## UI Widget Example

### download_button.dart
```dart
import 'package:flutter/material.dart';

class DownloadButton extends StatefulWidget {
  final String episodeId;
  final String episodeName;
  final DownloadManager downloadManager;

  const DownloadButton({
    super.key,
    required this.episodeId,
    required this.episodeName,
    required this.downloadManager,
  });

  @override
  State<DownloadButton> createState() => _DownloadButtonState();
}

class _DownloadButtonState extends State<DownloadButton> {
  String? _taskId;
  DownloadStatus _status = DownloadStatus.pending;
  double _progress = 0;

  @override
  void initState() {
    super.initState();
    widget.downloadManager.statusStream.listen((task) {
      if (task.id == _taskId) {
        setState(() {
          _status = task.status;
          _progress = task.progress;
        });
      }
    });
  }

  void _startDownload() {
    final taskId = widget.downloadManager.addToQueue(
      episodeId: widget.episodeId,
      fileName: widget.episodeName,
      serverType: 'sub',
    );
    setState(() {
      _taskId = taskId;
      _status = DownloadStatus.pending;
    });
  }

  @override
  Widget build(BuildContext context) {
    switch (_status) {
      case DownloadStatus.pending:
        return IconButton(
          icon: const Icon(Icons.download),
          onPressed: _startDownload,
        );
      case DownloadStatus.downloading:
        return Stack(
          alignment: Alignment.center,
          children: [
            CircularProgressIndicator(value: _progress),
            Text('${(_progress * 100).toInt()}%',
                style: const TextStyle(fontSize: 10)),
          ],
        );
      case DownloadStatus.completed:
        return const Icon(Icons.check_circle, color: Colors.green);
      case DownloadStatus.failed:
        return IconButton(
          icon: const Icon(Icons.error, color: Colors.red),
          onPressed: _startDownload, // Retry
        );
      case DownloadStatus.cancelled:
        return IconButton(
          icon: const Icon(Icons.refresh),
          onPressed: _startDownload,
        );
    }
  }
}
```

---

## Quick Start Usage

```dart
void main() async {
  // Initialize
  final downloadService = DownloadService(
    baseUrl: 'https://your-api-url.com',
  );
  final downloadManager = DownloadManager(
    downloadService: downloadService,
  );

  // Download One Piece Episode 1147
  final taskId = downloadManager.addToQueue(
    episodeId: '147365',
    fileName: 'OnePiece_EP1147',
    serverType: 'sub',
  );

  // Listen to progress
  downloadManager.statusStream.listen((task) {
    print('${task.fileName}: ${(task.progress * 100).toInt()}% - ${task.status}');
  });
}
```

---

## Required Dependencies

Add to `pubspec.yaml`:
```yaml
dependencies:
  dio: ^5.4.0
  path_provider: ^2.1.2
```

---

## Key Points

| Feature | Implementation |
|---------|----------------|
| **No Headers Needed** | Use `proxy_url` - headers handled by API server |
| **Multiple Servers** | HD-1, HD-2, HD-3 options available |
| **SUB/DUB Support** | Pass `serverType: 'sub'` or `'dub'` |
| **Progress Tracking** | Use `onProgress` callback |
| **Cancel Downloads** | Use `CancelToken` |
| **Subtitles** | Available in response, download separately |

---

## Flow Diagram

```
┌─────────────────┐
│  User taps      │
│  Download       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GET /api/       │
│ download/{id}   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Get proxy_url   │
│ from response   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ dio.download()  │
│ with proxy_url  │
│ (no headers!)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Save to device  │
│ storage         │
└─────────────────┘
```

---

## AI Prompt for Implementation

Copy this prompt to have AI implement the download feature in your Flutter app:

```
I need to implement a video download feature in my Flutter app. 

API Endpoint: GET /api/download/{episode_id}?server_type=sub

The API returns download_options array with:
- proxy_url: Use this directly (no headers needed)
- direct_url: Requires headers from response
- subtitles: Array of subtitle files

Requirements:
1. Create DownloadResponse and DownloadOption models
2. Create DownloadService with dio for API calls and file downloads
3. Create DownloadManager with queue support, progress tracking, cancel support
4. Create DownloadButton widget showing download progress
5. Use proxy_url (no headers needed) for simplest implementation
6. Support background downloads
7. Save files to app documents directory

Dependencies needed: dio, path_provider

Please implement these classes following the structure in FLUTTER_DOWNLOAD_INTEGRATION.md
```

---

**Happy Downloading! 🎬📥**
