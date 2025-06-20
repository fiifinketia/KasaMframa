import os
import csv
import logging
from datetime import datetime
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
    import jiwer
    JIWER_AVAILABLE = True
except ImportError:
    JIWER_AVAILABLE = False
    jiwer = None

class WERCalculator:
    """Word Error Rate calculator and logger"""
    
    def __init__(self):
        self.csv_path = os.path.join(os.getcwd(), 'poor_quality_samples.csv')
        self._ensure_csv_exists()
    
    def _ensure_csv_exists(self):
        """Ensure CSV file exists with proper headers"""
        if not os.path.exists(self.csv_path):
            try:
                with open(self.csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['input_text', 'transcribed_text', 'wer_score', 'model_name', 'speaker', 'timestamp'])
                logger.info(f"Created CSV file: {self.csv_path}")
            except Exception as e:
                logger.error(f"Failed to create CSV file: {str(e)}")
    
    def calculate_wer(self, reference, hypothesis):
        """Calculate Word Error Rate between reference and hypothesis text"""
        try:
            if not reference or not hypothesis:
                return 1.0  # Maximum error if either text is empty
            
            # Clean texts
            reference = reference.strip().lower()
            hypothesis = hypothesis.strip().lower()
            
            if JIWER_AVAILABLE:
                # Calculate WER using jiwer
                wer = jiwer.wer(reference, hypothesis)
            else:
                # Simple word difference calculation when jiwer is not available
                ref_words = reference.split()
                hyp_words = hypothesis.split()
                
                if len(ref_words) == 0:
                    wer = 1.0 if len(hyp_words) > 0 else 0.0
                else:
                    # Count matching words (simple approximation)
                    matches = sum(1 for word in hyp_words if word in ref_words)
                    wer = 1.0 - (matches / len(ref_words))
                    wer = max(0.0, min(1.0, wer))  # Clamp between 0 and 1
            
            logger.debug(f"WER calculation - Reference: '{reference}', Hypothesis: '{hypothesis}', WER: {wer}")
            return wer
            
        except Exception as e:
            logger.error(f"WER calculation failed: {str(e)}")
            return 1.0  # Return maximum error on failure
    
    def log_poor_quality(self, input_text, transcribed_text, wer_score, model_name, speaker=None):
        """Log poor quality samples to CSV"""
        try:
            timestamp = datetime.now().isoformat()
            
            with open(self.csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    input_text,
                    transcribed_text,
                    wer_score,
                    model_name,
                    speaker or 'default',
                    timestamp
                ])
            
            logger.info(f"Logged poor quality sample - WER: {wer_score}, Model: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to log poor quality sample: {str(e)}")
    
    def get_csv_path(self):
        """Get path to CSV log file"""
        return self.csv_path
