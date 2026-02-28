"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：media.py
"""

"""
Video media processing utilities.

This module provides utilities for video manipulation including splitting videos
based on timestamp information from JSON structures.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import subprocess
import json


def parse_timestamp(timestamp: str) -> float:
    """
    Parse timestamp string in format "MM:SS.mmm" to seconds.
    
    Args:
        timestamp: Time string in format "MM:SS.mmm" or "HH:MM:SS.mmm"
    
    Returns:
        Time in seconds as float
    
    Examples:
        >>> parse_timestamp("00:36.400")
        36.4
        >>> parse_timestamp("01:23.500")
        83.5
    """
    parts = timestamp.split(":")
    
    if len(parts) == 2:
        # Format: MM:SS.mmm
        minutes, seconds = parts
        hours = 0
    elif len(parts) == 3:
        # Format: HH:MM:SS.mmm
        hours, minutes, seconds = parts
    else:
        raise ValueError(f"Invalid timestamp format: {timestamp}")
    
    total_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    return total_seconds


def get_video_duration(video_path: str) -> float:
    """
    Get video duration in seconds using ffprobe.
    
    Args:
        video_path: Path to video file
    
    Returns:
        Duration in seconds
    """
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def split_video_by_segments(
    video_path: str,
    segments_json: List[Dict[str, Any]],
    output_dir: Optional[str] = None,
    output_prefix: str = "segment",
    use_copy: bool = False
) -> List[str]:
    """
    Split video into segments based on JSON structure with start/end times.
    
    The function will split the video according to the minimum duration between
    the video itself and the JSON timestamps. Any segments beyond the video
    duration will be ignored.
    
    Args:
        video_path: Path to the input video file
        segments_json: List of segment dictionaries containing 'start' and 'end' times
                       in format "MM:SS.mmm" or "HH:MM:SS.mmm"
        output_dir: Directory to save output segments (default: same as video)
        output_prefix: Prefix for output filenames (default: "segment")
        use_copy: If True, use stream copy (fast but may have black screens).
                  If False, re-encode video (slower but accurate, default)
    
    Returns:
        List of paths to generated segment files
    
    Example:
        >>> segments = [
        ...     {"start": "00:00.000", "end": "00:36.400", "text": "Opening"},
        ...     {"start": "00:36.400", "end": "00:40.560", "text": "Title"}
        ... ]
        >>> split_video_by_segments("video.mp4", segments)
        ['segment_001.mp4', 'segment_002.mp4']
    """
    video_path = Path(video_path)
    
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    # Get video duration
    video_duration = get_video_duration(str(video_path))
    
    # Set output directory
    if output_dir is None:
        output_dir = video_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    output_files = []
    
    for idx, segment in enumerate(segments_json, start=1):
        start_time_str = segment.get("start")
        end_time_str = segment.get("end")
        
        if not start_time_str or not end_time_str:
            print(f"Warning: Segment {idx} missing start or end time, skipping")
            continue
        
        start_time = parse_timestamp(start_time_str)
        end_time = parse_timestamp(end_time_str)
        
        # Skip if segment starts beyond video duration
        if start_time >= video_duration:
            print(f"Warning: Segment {idx} starts at {start_time}s, beyond video duration {video_duration}s, skipping")
            break
        
        # Clip end time to video duration
        if end_time > video_duration:
            print(f"Warning: Segment {idx} ends at {end_time}s, clipping to video duration {video_duration}s")
            end_time = video_duration
        
        # Calculate duration
        duration = end_time - start_time
        
        if duration <= 0:
            print(f"Warning: Segment {idx} has invalid duration {duration}s, skipping")
            continue
        
        # Generate output filename
        output_filename = f"{output_prefix}_{idx:03d}{video_path.suffix}"
        output_path = output_dir / output_filename
        
        # Use ffmpeg to extract segment
        # -ss before -i: fast seek (but less accurate)
        # -ss after -i: accurate seek (but slower)
        # We use accurate seeking to avoid black screens
        if use_copy:
            # Fast mode: stream copy (may have black screens at segment boundaries)
            cmd = [
                'ffmpeg',
                '-ss', str(start_time),
                '-i', str(video_path),
                '-t', str(duration),
                '-c', 'copy',
                '-avoid_negative_ts', 'make_zero',
                '-y',
                str(output_path)
            ]
        else:
            # Accurate mode: re-encode (slower but no black screens)
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-ss', str(start_time),
                '-t', str(duration),
                '-c:v', 'libx264',
                '-crf', '18',  # High quality
                '-preset', 'fast',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-y',
                str(output_path)
            ]
        
        try:
            print(f"Extracting segment {idx}: {start_time_str} -> {end_time_str} ({duration:.3f}s)")
            subprocess.run(cmd, capture_output=True, check=True)
            output_files.append(str(output_path))
            print(f"  ✓ Saved: {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error processing segment {idx}: {e.stderr.decode()}")
            continue
    
    return output_files


def split_video_from_json_file(
    video_path: str,
    json_path: str,
    output_dir: Optional[str] = None,
    output_prefix: str = "segment",
    use_copy: bool = False
) -> List[str]:
    """
    Split video based on segments defined in a JSON file.
    
    Args:
        video_path: Path to the input video file
        json_path: Path to JSON file containing segment definitions
        output_dir: Directory to save output segments (default: same as video)
        output_prefix: Prefix for output filenames (default: "segment")
        use_copy: If True, use stream copy (fast but may have black screens).
                  If False, re-encode video (slower but accurate, default)
    
    Returns:
        List of paths to generated segment files
    
    Example:
        >>> split_video_from_json_file("video.mp4", "segments.json")
        ['segment_001.mp4', 'segment_002.mp4']
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        segments_json = json.load(f)
    
    return split_video_by_segments(video_path, segments_json, output_dir, output_prefix, use_copy)


if __name__ == "__main__":
    # Example usage
    example_segments = [
        {
            "type": "narration",
            "start": "00:00.000",
            "end": "00:36.400",
            "text": "Opening segment",
            "speaker": None,
            "segment_title": "Opening"
        },
        {
            "type": "scene",
            "start": "00:36.400",
            "end": "00:40.560",
            "text": "Title card",
            "speaker": "Voiceover",
            "segment_title": "Title"
        }
    ]
    
    print("Example usage:")
    print("split_video_by_segments('input_video.mp4', segments_json)")
    print("split_video_from_json_file('input_video.mp4', 'segments.json')")
