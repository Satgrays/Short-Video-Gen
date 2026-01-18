"""
Script Controller
"""

import os
import re
import difflib
import json
import requests
import asyncio
import edge_tts
from groq import Groq
from dotenv import load_dotenv
from config.config import CONFIG

load_dotenv()

class ScriptController:
    def __init__(self):
        self.ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        self.groq_client = Groq(api_key=self.GROQ_API_KEY)
    
    def generate_script(self, system_content, user_content, model, script_path):
        """Generar script usando Groq"""
        try:
            completion = self.groq_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content}
                ]
            )
            script = completion.choices[0].message.content
            
            # LIMPIAR ANTES de guardar
            script = self.clean_script(script)
            
            # Ahora guardar el script limpio
            with open(script_path, 'w') as script_file:
                script_file.write(script)
            
            return script
            
        except Exception as e:
            print(f"Error generating script: {e}")
            return None

    def generate_audio(self, text, provider, audio_path):
        """Generar audio con múltiples providers"""
        
        provider = provider.lower()
        
        if provider == "elevenlabs":
            return self._generate_audio_elevenlabs(text, audio_path)
        elif provider == "edge" or provider == "edge-tts":
            return self._generate_audio_edge(text, audio_path)
        else:
            print(f"Unknown provider '{provider}', falling back to Edge TTS")
            return self._generate_audio_edge(text, audio_path)
    
    def _generate_audio_elevenlabs(self, text, audio_path):
        """Generar audio usando ElevenLabs"""
        elevenlabs_config = CONFIG.get("audio_settings", {}).get("elevenlabs", {})
        model_id = elevenlabs_config.get("model_id", "pNInz6obpgDQGcFmaJgB")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{model_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.ELEVENLABS_API_KEY
        }
        
        data = {
            "text": text,
            "model_id": elevenlabs_config.get("model", "eleven_monolingual_v1"),
            "voice_settings": elevenlabs_config.get("voice_settings", {
                "stability": 0.5, 
                "similarity_boost": 0.5
            })
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"ElevenLabs API error: {response.status_code} - {response.text}")
        
        CHUNK_SIZE = 1024
        with open(audio_path, 'wb') as audio_file:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    audio_file.write(chunk)
        
        print(f"Audio generated successfully with ElevenLabs at: {audio_path}")
    
    def _generate_audio_edge(self, text, audio_path):
        """Generar audio usando Edge TTS (gratis, ilimitado)"""
        
        # Obtener configuración de voz desde config o usar default
        edge_config = CONFIG.get("audio_settings", {}).get("edge", {})
        voice = edge_config.get("voice", "en-US-GuyNeural")
        rate = edge_config.get("rate", "+0%")
        pitch = edge_config.get("pitch", "+0Hz")
        
        # Normalizar caracteres problemáticos
        text = text.replace("'", "'")  # Apóstrofe tipográfico -> recto
        text = text.replace("'", "'")  # Otro apóstrofe tipográfico
        text = text.replace(""", '"')  # Comillas tipográficas
        text = text.replace(""", '"')
        text = text.replace("—", "-")  # Em dash
        text = text.replace("–", "-")  # En dash
        text = text.replace("…", "...")  # Puntos suspensivos
        
        print(f"Generating audio with Edge TTS (voice: {voice})...")
        
        async def _generate():
            communicate = edge_tts.Communicate(
                text, 
                voice,
                rate=rate,
                pitch=pitch
            )
            await communicate.save(audio_path)
        
        asyncio.run(_generate())
        
        print(f"Audio generated successfully with Edge TTS at: {audio_path}")

    def _prepare_text_for_tts(self, text):
        """Preparar texto para TTS normalizando caracteres problemáticos"""
        
        # Normalizar apóstrofes y comillas
        text = text.replace("'", "'")  # U+2019 -> U+0027
        text = text.replace("'", "'")  # U+2018 -> U+0027
        text = text.replace(""", '"')  # U+201C -> U+0022
        text = text.replace(""", '"')  # U+201D -> U+0022
        
        # Normalizar guiones
        text = text.replace("—", "-")
        text = text.replace("–", "-")
        
        # Normalizar puntos suspensivos
        text = text.replace("…", "...")
        
        return text

    def generate_transcript(self, audio_file, transcript_file_path):
        """Generar transcripción usando Groq Whisper API"""
        import os
        import json
        
        try:
            print(f"Transcribiendo audio: {audio_file}")
            
            with open(audio_file, "rb") as file:
                transcription = self.groq_client.audio.transcriptions.create(
                    file=(audio_file, file.read()),
                    model="whisper-large-v3-turbo",
                    response_format="verbose_json",
                    language="en",
                    timestamp_granularities=["word"]
                )
            
            print(f"Transcripción recibida de Groq")
            
            # Crear estructura igual que el test que funcionó
            result = {
                "segments": [],
                "text": transcription.text
            }
            
            # Procesar words
            if hasattr(transcription, 'words') and transcription.words:
                current_segment = {"words": []}
                for word_dict in transcription.words:
                    current_segment["words"].append({
                        "text": word_dict.get("word", ""),
                        "start": word_dict.get("start", 0),
                        "end": word_dict.get("end", 0)
                    })
                result["segments"].append(current_segment)
            else:
                print("Warning: No word-level timestamps available")
                result["segments"] = [{"words": [{"text": transcription.text, "start": 0, "end": 1}]}]
            
            # Asegurar que el directorio existe
            os.makedirs(os.path.dirname(transcript_file_path), exist_ok=True)
            
            # Guardar archivo
            with open(transcript_file_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            # Verificar que se guardó correctamente
            if os.path.exists(transcript_file_path):
                file_size = os.path.getsize(transcript_file_path)
                print(f"Transcript saved: {transcript_file_path} ({file_size} bytes)")
                
                # Verificar que se puede leer
                with open(transcript_file_path, 'r') as f:
                    test_read = json.load(f)
                print(f"File verified - {len(test_read.get('segments', []))} segments")
            else:
                print(f"ERROR: File was not created!")
                return None
            
            print(f"Transcript preview: {transcription.text[:200]}...")
            return result
            
        except Exception as e:
            print(f"Error generating transcript with Groq: {e}")
            import traceback
            traceback.print_exc()
            return None

    def verify_transcript(self, transcript_file, project_path, threshold=0.7):
        """Verificar similitud entre script y transcripción"""
        script_path = os.path.join(project_path, "script.txt")
        try:
            with open(script_path, 'r') as f:
                original_script = f.read().strip()
        except Exception as e:
            print("Script file not found for verification.")
            return None

        try:
            with open(transcript_file, 'r') as f:
                transcript_data = json.load(f)
        except Exception as e:
            print("Could not load transcript file for verification:", e)
            return None

        full_transcript = " ".join(
            word.get("text", "")
            for segment in transcript_data.get("segments", []) 
            for word in segment.get("words", [])
        ).strip()
        
        similarity = difflib.SequenceMatcher(None, original_script, full_transcript).ratio()
        print(f"Transcript similarity to original script: {similarity:.2f}")
        if similarity < threshold:
            print(f"Warning: Transcript similarity is below the threshold of {threshold}.")
        else:
            print("Transcript verification passed.")
        return similarity

    def clean_script(self, script):
        """Limpiar script de caracteres no deseados y formato"""
        
        # Remover títulos con ** (markdown bold)
        script = re.sub(r'\*\*.*?\*\*', '', script)
        
        # Remover asteriscos sueltos
        script = script.replace("*", "")
        
        # Remover contenido entre paréntesis
        script = re.sub(r'\([^)]*\)', '', script)
        
        # Remover headers markdown
        script = re.sub(r'^#+\s.*$', '', script, flags=re.MULTILINE)
        
        # Remover líneas vacías múltiples
        script = re.sub(r'\n\s*\n', '\n\n', script)
        
        # NORMALIZAR APÓSTROFES Y COMILLAS
        script = script.replace("'", "'")  # Apóstrofe tipográfico -> recto
        script = script.replace("'", "'")
        script = script.replace(""", '"')  # Comillas tipográficas -> rectas
        script = script.replace(""", '"')
        
        # Limpiar espacios
        script = script.strip()
        
        return script