import os
import logging
import sys
import glob

logger = logging.getLogger(__name__)

try:
    import torch
    import numpy as np
    import scipy.io.wavfile
    from transformers import pipeline, VitsModel, VitsTokenizer
    TORCH_AVAILABLE = True
    logger.info(f"PyTorch {torch.__version__} loaded successfully")
except ImportError as e:
    TORCH_AVAILABLE = False
    torch = None
    logger.warning(f"PyTorch not available: {e}")

# Try to import Coqui TTS
try:
    from TTS.api import TTS as CoquiTTS
    COQUI_AVAILABLE = True
except ImportError:
    COQUI_AVAILABLE = False
    CoquiTTS = None

logger = logging.getLogger(__name__)

class TTSService:
    """Text-to-Speech service supporting multiple model types"""
    
    def __init__(self):
        self.models = {}
        if TORCH_AVAILABLE:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"TTS Service initialized on device: {self.device}")
        else:
            self.device = "cpu"
            logger.warning("TTS Service initialized without PyTorch - using fallback mode")
        
        # Define available models
        self.available_models = {
            "facebook/mms-tts-aka": {
                "name": "Facebook MMS TTS Akan",
                "type": "transformers",
                "speakers": None
            },
            "hci-lab-dcug/ugtts-multispeaker-max40secs-total2hrs-sr22050-mms-aka-finetuned": {
                "name": "HCI Lab DCSUG Akan Finetuned",
                "type": "transformers", 
                # "speakers": ["IM", "speaker_1", "speaker_2"]
            },
            "hci-lab-dcug/ugtts-multispeaker-max40secs-total2hrs-sr22050-mms-swh-finetuned": {
                "name": "Swahili Finetuned",
                "type": "transformers",
                # "speakers": ["IM", "speaker_1", "speaker_2"]
            }
        }
        
        # Add Coqui TTS models if available
        if COQUI_AVAILABLE:
            self.available_models.update({
                "hci-lab-dcug/ugtts-multispeaker-max40secs-total2hrs-sr22050-mms-swh-finetuned": {
                    "name": "HCI Lab DCSUG Multispeaker",
                    "type": "coqui",
                    "model_path": "/tmp/ugtts-model/best_model.pth",
                    "config_path": "/tmp/ugtts-model/config.json",
                    "speakers": ["IM", "PT", "AN"]
                }
            })
    
    def get_available_models(self):
        """Return list of available models"""
        return [
            {
                "id": model_id,
                "name": model_info["name"],
                "has_speakers": model_info["speakers"] is not None
            }
            for model_id, model_info in self.available_models.items()
        ]
    
    def get_speakers(self, model_id):
        """Get available speakers for a model"""
        if model_id not in self.available_models:
            return []
        
        speakers = self.available_models[model_id]["speakers"]
        if speakers is None:
            return []
        
        return speakers
    
    def _load_model(self, model_id):
        """Load a TTS model"""
        if model_id in self.models:
            return self.models[model_id]
        
        try:
            logger.info(f"Loading TTS model: {model_id}")
            
            model_info = self.available_models.get(model_id)
            if not model_info:
                raise ValueError(f"Unknown model: {model_id}")
            
            if model_info["type"] == "transformers":
                if not TORCH_AVAILABLE:
                    raise ValueError("PyTorch not available for transformers models")
                # Use transformers pipeline
                synthesizer = pipeline(
                    "text-to-speech",
                    model=model_id,
                    device=0 if self.device == "cuda" else -1
                )
                self.models[model_id] = synthesizer
                logger.info(f"Successfully loaded model: {model_id}")
                return synthesizer
            elif model_info["type"] == "coqui":
                if not COQUI_AVAILABLE:
                    raise ValueError("Coqui TTS not available. Please install it first.")
                
                # Load Coqui TTS model
                model_path = model_info.get("model_path")
                config_path = model_info.get("config_path")
                
                if model_path and config_path and os.path.exists(model_path) and os.path.exists(config_path):
                    # Load from local files
                    synthesizer = CoquiTTS(model_path=model_path, config_path=config_path)
                else:
                    # Load from model name/path
                    model_name = model_id.replace("coqui://", "")
                    synthesizer = CoquiTTS(model_name)
                
                # Move to appropriate device
                if self.device == "cuda":
                    synthesizer = synthesizer.to("cuda")
                
                self.models[model_id] = synthesizer
                logger.info(f"Successfully loaded Coqui model: {model_id}")
                return synthesizer
            else:
                raise ValueError(f"Unsupported model type: {model_info['type']}")
                
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {str(e)}")
            raise
    
    def synthesize(self, text, model_id, output_path, speaker=None):
        """Synthesize speech from text"""
        try:
            model_info = self.available_models[model_id]
            logger.info(f"Synthesizing: '{text}' with model {model_id}, speaker: {speaker}")
            
            if model_info["type"] == "transformers":
                if not TORCH_AVAILABLE:
                    logger.error("Cannot synthesize with transformers - PyTorch not available")
                    return False
                    
                # Load model
                synthesizer = self._load_model(model_id)
                
                # Transformers pipeline synthesis
                synthesis_kwargs = {}
                if speaker and speaker != "default":
                    synthesis_kwargs["speaker_id"] = speaker
                
                speech = synthesizer(text, **synthesis_kwargs)
                
                # Save audio file
                import numpy as np
                import scipy.io.wavfile
                sample_rate = speech.get("sampling_rate", 22050)
                audio_data = speech["audio"]
                
                # Handle different audio data formats
                if isinstance(audio_data, list):
                    audio_data = np.array(audio_data)
                elif hasattr(audio_data, 'numpy'):
                    audio_data = audio_data.numpy()
                
                # Ensure audio data is in the right format
                if len(audio_data.shape) > 1:
                    audio_data = audio_data[0]  # Take first channel if stereo
                
                # Normalize audio data
                if audio_data.dtype != np.int16:
                    audio_data = (audio_data * 32767).astype(np.int16)
                
                # Save to file
                scipy.io.wavfile.write(output_path, sample_rate, audio_data)
                
            elif model_info["type"] == "coqui":
                if not COQUI_AVAILABLE:
                    logger.error("Cannot synthesize with Coqui - TTS not available")
                    return False
                    
                # Load model
                synthesizer = self._load_model(model_id)
                
                # Coqui TTS synthesis
                if speaker and speaker != "default":
                    synthesizer.tts_to_file(
                        text=text,
                        file_path=output_path,
                        speaker=speaker
                    )
                else:
                    synthesizer.tts_to_file(
                        text=text,
                        file_path=output_path
                    )
            else:
                # Generate simple test audio for unsupported model types
                logger.warning(f"Generating test audio for unsupported model type: {model_info['type']}")
                self._generate_test_audio(output_path)
            
            logger.info(f"Audio saved to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Synthesis failed: {str(e)}")
            return False
    
    def _generate_test_audio(self, output_path):
        """Generate simple test audio when ML libraries aren't available"""
        import struct
        import wave
        
        # Generate a simple tone (440 Hz sine wave for 2 seconds)
        sample_rate = 22050
        duration = 2.0
        num_samples = int(sample_rate * duration)
        
        # Create simple sine wave audio data
        audio_data = []
        frequency = 440.0
        for i in range(num_samples):
            t = float(i) / sample_rate
            import math
            sample = int(32767 * 0.3 * math.sin(2.0 * math.pi * frequency * t))
            audio_data.append(sample)
        
        # Save as WAV file
        with wave.open(output_path, 'w') as wav_file:
            wav_file.setnchannels(1)  # mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            
            # Pack audio data as 16-bit signed integers
            packed_data = struct.pack('<' + 'h' * len(audio_data), *audio_data)
            wav_file.writeframes(packed_data)
