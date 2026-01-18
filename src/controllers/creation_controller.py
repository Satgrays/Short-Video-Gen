"""
Creation Controller
"""

import os
import random
import glob
import json
import numpy as np
import textwrap
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
from config.config import CONFIG

video_height = CONFIG.get("video_settings", {}).get("height", 1920)

class CreationController:
    """
    def load_data(self, project_path):
        transcript_file_path = os.path.join(project_path, 'script.txt')
        video_details_path = os.path.join(project_path, 'details.json')
        audio_path = os.path.join(project_path, 'audio.mp3')
        
        with open(transcript_file_path, 'r') as transcript_file:
            self.caption_data = json.load(transcript_file)
        
        with open(video_details_path, 'r') as video_details_file:
            self.video_details = json.load(video_details_file)
        
        self.audio = AudioFileClip(audio_path)
    """
    
    def create_video_with_project_path(self, project_path):
        # Cargar datos una sola vez
        transcript_path = os.path.join(project_path, "transcript.json")
        video_details_path = os.path.join(project_path, "details.json")
        audio_path = os.path.join(project_path, "audio.mp3")
        
        print(f"Loading transcript from: {transcript_path}")
        
        with open(transcript_path, 'r', encoding='utf-8') as transcript_file:
            transcript = json.load(transcript_file)
        
        with open(video_details_path, 'r', encoding='utf-8') as video_details_file:
            video_details = json.load(video_details_file)
        
        audio = AudioFileClip(audio_path)
        
        # Elegir video de fondo
        video_path = self.choose_background_video(audio)
        
        # Guardar audio para usar en trim_video
        self.audio = audio
        
        # Recortar video
        video = self.trim_video_to_audio_duration(video_path)
        
        # Crear subtítulos
        text_clips = self.create_text_clips(transcript)

        # DEBUG - AGREGAR ESTAS LÍNEAS:
        print(f"═══ DEBUG TEXT CLIPS ═══")
        print(f"Total text clips created: {len(text_clips)}")
        if len(text_clips) > 0:
            print(f"First clip starts at: {text_clips[0].start}s")
            print(f"First clip duration: {text_clips[0].duration}s")
        else:
            print("⚠️  NO TEXT CLIPS CREATED!")

        final_video = CompositeVideoClip([video] + text_clips)
        
        # Crear título
        title = video_details.get('video_title', 'UNTITLED')
        max_width_chars = CONFIG.get("fallbacks", {}).get("max_title_width_chars", 17)
        wrapped_title = textwrap.fill(title.upper(), width=max_width_chars)
        
        raw_title_duration = CONFIG.get("video_settings", {}).get("title_duration", 10)
        title_duration = min(raw_title_duration, audio.duration)
        
        title_text_clip = (
            TextClip(
                wrapped_title, 
                fontsize=CONFIG.get("video_settings", {}).get("title_fontsize", 120), 
                color='black', 
                font=CONFIG.get("fonts", {}).get("title", "fonts/PassionOne-Bold.ttf"),
                bg_color="white", 
                stroke_color='white', 
                stroke_width=5, 
                align='center'
            )
            .set_position(tuple(CONFIG.get("video_settings", {}).get("title_position", ["center", 250])))
            .set_duration(title_duration)
        )
        
        final_video = CompositeVideoClip([final_video, title_text_clip])
        
        final_video_path = os.path.join(project_path, "final_video.mp4")
        
        final_video = final_video.set_audio(audio)
        
        print("Rendering final video...")
        print(f"Video dimensions: {final_video.w}x{final_video.h}")
        print(f"Video duration: {final_video.duration}")
        print(f"Number of text clips: {len(text_clips)}")
        if len(text_clips) > 0:
            print(f"First text clip: '{text_clips[0].txt}' at {text_clips[0].start}s for {text_clips[0].duration}s")
        
        final_video.write_videofile(
            final_video_path,
            codec="libx264",
            audio_codec="aac",  
            fps=30, 
            threads=8,
            preset="ultrafast",
            ffmpeg_params=["-movflags", "+faststart"]
        )
        
        print(f"Final video with captions saved at: {final_video_path}")
    
    def create_text_clips(self, transcript):
        text_clips = []
        min_duration = CONFIG.get("fallbacks", {}).get("min_text_clip_duration", 0.1)
        buffer_duration = CONFIG.get("fallbacks", {}).get("buffer_duration", 0.1)
        text_clip_config = CONFIG.get("text_clip_settings", {})
        
        # Posición fija para subtítulos (parte inferior)
        subtitle_y_position = video_height - 900  # Ajusta este valor según necesites
        
        for segment in transcript.get('segments', []):
            words = segment.get('words', [])
            for i, word_data in enumerate(words):
                word = word_data.get('text', '')
                start_time = word_data.get('start', 0)
                
                if i < len(words) - 1:
                    next_word = words[i + 1]
                    max_duration = next_word.get('start', start_time) - start_time
                    if max_duration <= 0.01:
                        duration = min_duration
                        next_word['start'] = next_word.get('start', 0) + buffer_duration
                    else:
                        duration = max(word_data.get('end', start_time) - start_time, min_duration)
                        duration = min(duration, max_duration)
                else:
                    duration = max(word_data.get('end', start_time) - start_time, min_duration)
                    duration = min(duration, CONFIG.get("fallbacks", {}).get("max_text_clip_duration", 5))
                
                txt_clip = (TextClip(
                                word.upper(), 
                                fontsize=text_clip_config.get("fontsize", 120), 
                                color=text_clip_config.get("color", 'white'), 
                                font=text_clip_config.get("font", 'fonts/PassionOne-Bold.ttf'),
                                stroke_color=text_clip_config.get("stroke_color", "black"), 
                                stroke_width=text_clip_config.get("stroke_width", 8)
                        )
                        .set_position(lambda t: ('center', subtitle_y_position + 15 * np.sin(2 * np.pi * t)))
                        .set_start(start_time)
                        .set_duration(duration)
                        .crossfadein(text_clip_config.get("crossfade_duration", 0.035))
                        )
                text_clips.append(txt_clip)
        
        return text_clips
        
        
    def trim_video_to_audio_duration(self, video_path):
        video = VideoFileClip(video_path, audio=False, fps_source='fps')
        
        print(f"Video loaded - Dimensions reported: {video.w}x{video.h}")
        
        # Si MoviePy lee las dimensiones al revés (1596x720 pero debería ser 720x1596)
        # FORZAR las dimensiones correctas
        if video.w > video.h:
            print(f"Dimensions are inverted, swapping them...")
            # Forzar a MoviePy a usar las dimensiones correctas
            # Esto NO rota el video, solo le dice a MoviePy cómo interpretarlo
            video.size = (video.h, video.w)  # Intercambiar width y height
            print(f"Corrected dimensions: {video.w}x{video.h}")
        
        target_width = CONFIG.get("video_settings", {}).get("width", 1080)
        target_height = CONFIG.get("video_settings", {}).get("height", 1920)
        
        print(f"Target dimensions: {target_width}x{target_height}")
        
        # Ahora calcular aspect ratios con dimensiones corregidas
        video_aspect = video.w / video.h
        target_aspect = target_width / target_height
        
        print(f"Aspect ratios - Video: {video_aspect:.3f}, Target: {target_aspect:.3f}")
        
        # Resize
        if video_aspect > target_aspect:
            new_height = target_height
            new_width = int(video_aspect * new_height)
        else:
            new_width = target_width
            new_height = int(new_width / video_aspect)
        
        print(f"Resizing to: {new_width}x{new_height}")
        video = video.resize(newsize=(new_width, new_height))
        
        # Crop al centro
        x_center = video.w / 2
        y_center = video.h / 2
        
        video = video.crop(
            x1=x_center - target_width / 2,
            y1=y_center - target_height / 2,
            x2=x_center + target_width / 2,
            y2=y_center + target_height / 2
        )
        
        print(f"Final dimensions: {video.w}x{video.h}")
        
        audio_duration = self.audio.duration
        if video.duration > audio_duration:
            video = video.subclip(0, audio_duration)
        
        return video
    
    def choose_background_video(self, audio):
        audio_duration = audio.duration
        video_dir = CONFIG.get("videos_dir", "videos")
        video_files = glob.glob(os.path.join(video_dir, "*.mp4"))
        if not video_files:
            raise FileNotFoundError(f"No mp4 files found in the '{video_dir}' directory.")
        
        valid_videos = []
        longest_video = None
        longest_duration = 0.0
        
        for video in video_files:
            try:
                clip = VideoFileClip(video)
                duration = clip.duration
                clip.close() 
                if duration >= audio_duration:
                    valid_videos.append(video)
                if duration > longest_duration:
                    longest_duration = duration
                    longest_video = video
            except Exception as e:
                print(f"Error processing video {video}: {e}")
        
        if valid_videos:
            return random.choice(valid_videos)
        if longest_video:
            return longest_video
        raise ValueError("No valid background video was found.") 