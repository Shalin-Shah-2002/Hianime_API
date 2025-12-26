#!/usr/bin/env python3
"""
Fast MP4 Download Test Script
Uses the improved FFmpeg-based download API
"""

import httpx
import time
import sys
import os

def download_episode(episode_id="94736", output_path=None, quality="best"):
    """Download an episode with progress display"""
    
    if output_path is None:
        output_path = f"/Users/shalinshah/Downloads/episode_{episode_id}.mp4"
    
    print("🎬 Ultra Fast MP4 Download")
    print("=" * 50)
    print(f"Episode ID: {episode_id}")
    print(f"Quality: {quality}")
    print(f"Output: {output_path}")
    print("=" * 50)
    
    url = f"http://localhost:8000/api/download/mp4/{episode_id}?quality={quality}"
    
    start_time = time.time()
    total_bytes = 0
    
    try:
        # Use longer timeout since FFmpeg needs time to process
        with httpx.Client(timeout=httpx.Timeout(900.0, connect=60.0)) as client:
            print("\n📡 Connecting to server (FFmpeg is downloading)...")
            print("⏳ Please wait - FFmpeg downloads directly from source...")
            
            with client.stream('GET', url) as response:
                if response.status_code != 200:
                    error_text = response.read().decode('utf-8', errors='ignore')
                    print(f"❌ Error: HTTP {response.status_code}")
                    print(f"Details: {error_text[:500]}")
                    return
                
                # Get content length if available
                content_length = response.headers.get('content-length')
                if content_length:
                    print(f"📦 Expected size: {int(content_length)/1024/1024:.2f} MB")
                
                print("✅ Download started! Receiving data...\n")
                
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_bytes(chunk_size=1048576):  # 1MB chunks
                        f.write(chunk)
                        total_bytes += len(chunk)
                        
                        # Calculate stats
                        mb = total_bytes / (1024 * 1024)
                        elapsed = time.time() - start_time
                        speed = mb / elapsed if elapsed > 0 else 0
                        
                        # Print progress
                        sys.stdout.write(
                            f"\r📥 Downloaded: {mb:.2f} MB | "
                            f"Speed: {speed:.2f} MB/s | "
                            f"Time: {elapsed:.1f}s"
                        )
                        sys.stdout.flush()
        
        # Final stats
        elapsed = time.time() - start_time
        mb = total_bytes / (1024 * 1024)
        
        print("\n\n" + "=" * 50)
        print("✅ DOWNLOAD COMPLETE!")
        print("=" * 50)
        print(f"📁 File: {output_path}")
        print(f"📊 Size: {mb:.2f} MB")
        print(f"⏱️  Time: {elapsed:.1f} seconds")
        if elapsed > 0:
            print(f"🚀 Speed: {mb/elapsed:.2f} MB/s")
        
        # Verify the file is a valid MP4
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            with open(output_path, 'rb') as f:
                header = f.read(12)
                # Check for ftyp box (MP4 signature)
                if b'ftyp' in header:
                    print("✅ Valid MP4 file!")
                else:
                    print("⚠️  File may not be a valid MP4")
        
    except httpx.TimeoutException:
        print("\n\n❌ Timeout! The download took too long.")
        print("Try again or use a different episode.")
    except httpx.ConnectError:
        print("\n\n❌ Could not connect to server!")
        print("Make sure the API server is running: python api.py")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Parse arguments
    episode_id = "94736"  # Default: Road of Naruto
    quality = "best"
    
    if len(sys.argv) > 1:
        episode_id = sys.argv[1]
    if len(sys.argv) > 2:
        quality = sys.argv[2]
    
    print(f"\nUsage: python test_download.py [episode_id] [quality]")
    print(f"Quality options: best, 1080, 720, 480, 360\n")
    
    download_episode(episode_id, quality=quality)
