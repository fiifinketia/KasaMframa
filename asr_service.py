import os
import logging
import sys
import glob

# Setup environment for nix packages
nix_packages = []
try:
    import subprocess
    result = subprocess.run(['ls', '/nix/store'], capture_output=True, text=True)
    store_dirs = result.stdout.strip().split('\n')
    
    for pkg_name in ['torch', 'numpy', 'scipy']:
        matching_dirs = [d for d in store_dirs if f'python311-{pkg_name}' in d]
        if matching_dirs:
            pkg_path = f"/nix/store/{matching_dirs[0]}/lib/python3.11/site-packages"
            if os.path.exists(pkg_path) and pkg_path not in sys.path:
                sys.path.insert(0, pkg_path)
                nix_packages.append(pkg_name)
except Exception:
    pass

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
        logger.info(f"ASR Service initialized with model: {self.model_name}")
    
    def _load_model(self):
        """Load the ASR model"""
        if self.model is None:
            if not WHISPER_AVAILABLE:
                logger.warning("faster-whisper not available, using mock transcription")
                return None
            try:
                logger.info(f"Loading ASR model: {self.model_name}")
                self.model = WhisperModel(self.model_name)
                logger.info("ASR model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load ASR model: {str(e)}")
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
                logger.warning("Using mock transcription - faster-whisper not available")
                return "Mock transcription output for testing purposes"
            
            logger.info(f"Transcribing audio: {audio_path}")
            
            # Transcribe
            segments, info = model.transcribe(audio_path)
            
            # Combine all segments into one text
            transcription = ""
            for segment in segments:
                transcription += segment.text
            
            # Clean up transcription
            transcription = transcription.strip()
            
            logger.info(f"Transcription completed: '{transcription}'")
            return transcription
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            return None
