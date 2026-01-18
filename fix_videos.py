"""
fix_videos.py - VERSIÓN CORREGIDA
Script para aplicar rotación física y corregir dimensiones
"""

import os
import subprocess
import json
from pathlib import Path
import sys

def get_video_metadata(video_path):
    """Obtener metadatos de un video"""
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 
        'stream=width,height,display_aspect_ratio,codec_name,r_frame_rate:stream_tags=rotate:stream_side_data=displaymatrix',
        '-of', 'json',
        video_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        if 'streams' in data and len(data['streams']) > 0:
            stream = data['streams'][0]
            
            width = stream.get('width', 0)
            height = stream.get('height', 0)
            rotation = stream.get('tags', {}).get('rotate', None)
            
            # Detectar display matrix rotation
            side_data = stream.get('side_data_list', [])
            displaymatrix_rotation = None
            for sd in side_data:
                if sd.get('side_data_type') == 'Display Matrix':
                    rot_str = sd.get('rotation', '0')
                    try:
                        displaymatrix_rotation = float(rot_str)
                    except:
                        pass
            
            return {
                'width': width,
                'height': height,
                'aspect': stream.get('display_aspect_ratio', 'N/A'),
                'codec': stream.get('codec_name', 'N/A'),
                'fps': stream.get('r_frame_rate', 'N/A'),
                'rotation': rotation,
                'displaymatrix': displaymatrix_rotation
            }
    except Exception as e:
        print(f"Error reading metadata: {e}")
    
    return None

def display_metadata(video_path, label="Video"):
    """Mostrar metadatos de un video de forma bonita"""
    metadata = get_video_metadata(video_path)
    
    if not metadata:
        print(f"  ❌ Could not read metadata")
        return metadata
    
    print(f"\n  📐 {label}:")
    print(f"    Dimensions: {metadata['width']}x{metadata['height']}")
    print(f"    Aspect: {metadata['aspect']}")
    print(f"    Codec: {metadata['codec']}")
    print(f"    FPS: {metadata['fps']}")
    
    has_rotation = False
    if metadata['rotation']:
        print(f"    Rotation tag: {metadata['rotation']}°")
        has_rotation = True
    
    if metadata['displaymatrix']:
        print(f"    Display matrix: {metadata['displaymatrix']}°")
        has_rotation = True
    
    if not has_rotation:
        print(f"    Rotation: None")
    
    # Determinar orientación
    if metadata['width'] > metadata['height']:
        orientation = "HORIZONTAL"
    elif metadata['height'] > metadata['width']:
        orientation = "VERTICAL"
    else:
        orientation = "SQUARE"
    
    print(f"    Orientation: {orientation}")
    
    if has_rotation:
        print(f"    ⚠️  Has rotation metadata - visual orientation differs")
    
    return metadata

def fix_video_metadata(input_path, output_dir=None, show_before_after=True):
    """Aplicar rotación física al video si es necesario"""
    input_path = Path(input_path)
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / input_path.name
    else:
        output_path = input_path.parent / f"fixed_{input_path.name}"
    
    if output_path.exists():
        print(f"⏭️  Skipping (already exists): {output_path.name}")
        return str(output_path)
    
    print(f"\n{'='*60}")
    print(f"Processing: {input_path.name}")
    
    # Obtener metadatos ANTES
    metadata_before = display_metadata(str(input_path), "BEFORE") if show_before_after else get_video_metadata(str(input_path))
    
    if not metadata_before:
        print(f"  ❌ Could not read video metadata")
        return None
    
    # Determinar si necesita rotación física
    needs_rotation = False
    transpose_value = None
    
    # Detectar rotación del display matrix (lo más confiable)
    if metadata_before['displaymatrix']:
        rotation = metadata_before['displaymatrix']
        print(f"\n  🔄 Detected display matrix rotation: {rotation}°")
        
        if rotation == -90 or rotation == 270:
            needs_rotation = True
            transpose_value = "2"  # 90° counter-clockwise
            print(f"  → Will apply 90° counter-clockwise rotation")
        elif rotation == 90 or rotation == -270:
            needs_rotation = True
            transpose_value = "1"  # 90° clockwise
            print(f"  → Will apply 90° clockwise rotation")
        elif abs(rotation) == 180:
            needs_rotation = True
            transpose_value = "2,transpose=2"  # 180°
            print(f"  → Will apply 180° rotation")
    
    # Construir comando ffmpeg
    if needs_rotation:
        print(f"  ⚙️  Applying physical rotation...")
        cmd = [
            'ffmpeg', '-i', str(input_path),
            '-vf', f'transpose={transpose_value}',  # Aplicar rotación física
            '-c:v', 'libx264',
            '-preset', 'ultrafast',  # Rápido
            '-crf', '23',
            '-c:a', 'copy',  # No re-encodear audio
            '-metadata:s:v:0', 'rotate=0',  # Remover metadata
            '-movflags', '+faststart',
            '-y', str(output_path)
        ]
    else:
        print(f"  ✓ No rotation needed, just copying...")
        cmd = [
            'ffmpeg', '-i', str(input_path),
            '-c', 'copy',
            '-metadata:s:v:0', 'rotate=0',
            '-movflags', '+faststart',
            '-y', str(output_path)
        ]
    
    try:
        print(f"  ⏳ Processing...")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Mostrar metadatos DESPUÉS
        if show_before_after:
            display_metadata(str(output_path), "AFTER")
        
        file_size = output_path.stat().st_size / (1024 * 1024)
        print(f"\n  ✅ Saved: {output_path.name}")
        print(f"  📦 File size: {file_size:.1f} MB")
        
        return str(output_path)
        
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Error:")
        print(e.stderr)
        return None

def check_video(video_path):
    """Solo ver metadatos sin modificar"""
    print(f"\n{'='*60}")
    print(f"Video: {Path(video_path).name}")
    print(f"{'='*60}")
    
    display_metadata(video_path, "METADATA")
    print()

def check_directory(directory, pattern="*.mp4"):
    """Ver metadatos de todos los videos en un directorio"""
    directory = Path(directory)
    
    if not directory.exists():
        print(f"❌ Directory not found: {directory}")
        return
    
    video_files = list(directory.glob(pattern))
    
    if not video_files:
        print(f"❌ No {pattern} files found in {directory}")
        return
    
    print(f"\n{'='*60}")
    print(f"Found {len(video_files)} video(s) in {directory}")
    print(f"{'='*60}")
    
    for video_file in video_files:
        check_video(str(video_file))

def fix_all_videos(input_dir, output_dir=None, pattern="*.mp4"):
    """Arreglar todos los videos en un directorio"""
    input_dir = Path(input_dir)
    
    if not input_dir.exists():
        print(f"❌ Directory not found: {input_dir}")
        return
    
    video_files = [
        f for f in input_dir.glob(pattern) 
        if not f.name.startswith('fixed_')
    ]
    
    if not video_files:
        print(f"❌ No {pattern} files found in {input_dir}")
        return
    
    print(f"\n{'='*60}")
    print(f"Found {len(video_files)} video(s) to process")
    print(f"Mode: Apply physical rotation when needed")
    print(f"{'='*60}")
    
    fixed_videos = []
    failed_videos = []
    
    for i, video_file in enumerate(video_files, 1):
        print(f"\n[{i}/{len(video_files)}]")
        try:
            result = fix_video_metadata(video_file, output_dir)
            if result:
                fixed_videos.append(result)
            else:
                failed_videos.append(str(video_file))
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")
            failed_videos.append(str(video_file))
    
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successfully fixed: {len(fixed_videos)}")
    print(f"❌ Failed: {len(failed_videos)}")
    
    if fixed_videos:
        print(f"\nFixed videos:")
        for video in fixed_videos:
            print(f"  ✓ {Path(video).name}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python fix_videos.py check <video_file|directory>    # Ver metadatos")
        print("  python fix_videos.py fix <directory> [output_dir]    # Arreglar videos")
        print("\nExamples:")
        print("  python fix_videos.py check videos/my_video.mp4")
        print("  python fix_videos.py check videos/")
        print("  python fix_videos.py fix videos/")
        print("  python fix_videos.py fix videos/ videos_fixed/")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "check":
        if len(sys.argv) < 3:
            print("❌ Please specify a video file or directory")
            sys.exit(1)
        
        path = Path(sys.argv[2])
        
        if path.is_file():
            check_video(str(path))
        elif path.is_dir():
            check_directory(path)
        else:
            print(f"❌ Not found: {path}")
    
    elif command == "fix":
        if len(sys.argv) < 3:
            print("❌ Please specify an input directory")
            sys.exit(1)
        
        input_dir = sys.argv[2]
        output_dir = sys.argv[3] if len(sys.argv) > 3 else None
        
        fix_all_videos(input_dir, output_dir)
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'check' or 'fix'")
        sys.exit(1)