import os
import logging
import sys
import glob


logger = logging.getLogger(__name__)

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    WhisperModel = None

class ASRService:
    """Automatic Speech Recognition service using faster-whisper"""
    
    def __init__(self):
        self.model = None
        self.model_name = os.environ.get('ASR_MODEL', 'fiifinketia/whisper-large-v3-turbo-akan')
        print(f"ASR Service initialized with model: {self.model_name}")
    
    def _load_model(self):
        """Load the ASR model"""
        if self.model is None:
            if not WHISPER_AVAILABLE:
                print("faster-whisper not available, using mock transcription")
                return None
            try:
                print(f"Loading ASR model: {self.model_name}")
                self.model = WhisperModel(self.model_name)
                print("ASR model loaded successfully")
            except Exception as e:
                print(f"Failed to load ASR model: {str(e)}")
                raise
        return self.model
    
    def transcribe(self, audio_path):
        """Transcribe audio file to text"""
        try:
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            # Load model
            model = self._load_model()
            
            if not WHISPER_AVAILABLE or model is None:
                # Return a placeholder transcription when real ASR is not available
                print("Using mock transcription - faster-whisper not available")
                return "Mock transcription output for testing purposes"
            
            print(f"Transcribing audio: {audio_path}")
            
            # Transcribe
            segments, info = model.transcribe(audio_path)
            
            # Combine all segments into one text
            transcription = ""
            for segment in segments:
                transcription += segment.text
            
            # Clean up transcription
            transcription = transcription.strip()
            
            print(f"Transcription completed: '{transcription}'")
            return transcription
            
        except Exception as e:
            print(f"Transcription failed: {str(e)}")
            return None
