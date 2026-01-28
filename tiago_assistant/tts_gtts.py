# tts_gtts.py - VERSION GOOGLE TTS avec pygame

from gtts import gTTS
import os
import tempfile
import time
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("⚠️  pygame non installé, utilisation de playsound basique")


class TTS:
    def __init__(self, lang: str = 'fr', slow: bool = False):
        """
        TTS utilisant Google Text-to-Speech (meilleure qualité).
        
        Args:
            lang: Langue ('fr' pour français, 'en' pour anglais)
            slow: Si True, parle lentement
        """
        self.lang = lang
        self.slow = slow
        
        if PYGAME_AVAILABLE:
            pygame.mixer.init()
            print(f"🔊 TTS Google activé avec pygame (langue: {lang})")
        else:
            print(f"🔊 TTS Google activé (langue: {lang})")

    def say(self, text: str) -> None:
        """Prononce le texte donné"""
        if not text or len(text.strip()) == 0:
            return
        
        try:
            # Détection automatique de la langue
            lang = self._detect_language(text)
            
            # Génération audio avec gTTS
            tts = gTTS(text=text, lang=lang, slow=self.slow)
            
            # Sauvegarde temporaire
            temp_file = tempfile.mktemp(suffix='.mp3')
            tts.save(temp_file)
            
            # Lecture audio
            if PYGAME_AVAILABLE:
                self._play_with_pygame(temp_file)
            else:
                self._play_basic(temp_file)
            
            # Nettoyage
            try:
                os.unlink(temp_file)
            except:
                pass
            
        except Exception as e:
            print(f"❌ Erreur TTS: {e}")
    
    def _play_with_pygame(self, filepath: str):
        """Joue l'audio avec pygame (méthode silencieuse)"""
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()
        
        # Attendre la fin de la lecture
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        
        pygame.mixer.music.unload()
    
    def _play_basic(self, filepath: str):
        """Méthode de secours sans pygame"""
        import platform
        system = platform.system()
        
        if system == "Windows":
            # Utilise PowerShell pour jouer sans ouvrir de fenêtre
            os.system(f'powershell -c "(New-Object Media.SoundPlayer \'{filepath}\').PlaySync();"')
        elif system == "Darwin":  # macOS
            os.system(f'afplay "{filepath}"')
        else:  # Linux
            os.system(f'mpg123 -q "{filepath}"')
    
    def _detect_language(self, text: str) -> str:
        """Détecte si le texte est en anglais ou français"""
        english_words = ['the', 'and', 'you', 'are', 'have', 'this', 'that', 'with', 'from', 'what', 'your']
        
        text_lower = text.lower()
        english_count = sum(1 for word in english_words if f' {word} ' in f' {text_lower} ')
        
        if english_count >= 2:
            return 'en'
        return 'fr'