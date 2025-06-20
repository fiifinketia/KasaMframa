import os
import logging
from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import tempfile
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///kasa_mframa.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Import services after app initialization
from tts_service import TTSService
from asr_service import ASRService
from evaluation import WERCalculator

# Initialize services
tts_service = TTSService()
asr_service = ASRService()
wer_calculator = WERCalculator()

@app.route('/')
def index():
    """Render the main interface"""
    try:
        available_models = tts_service.get_available_models()
        return render_template('index.html', models=available_models)
    except Exception as e:
        logger.error(f"Error loading models: {str(e)}")
        return render_template('index.html', models=[], error="Failed to load TTS models")

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get available TTS models"""
    try:
        models = tts_service.get_available_models()
        return jsonify({"status": "success", "models": models})
    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/speakers/<model_id>', methods=['GET'])
def get_speakers(model_id):
    """Get available speakers for a model"""
    try:
        speakers = tts_service.get_speakers(model_id)
        return jsonify({"status": "success", "speakers": speakers})
    except Exception as e:
        logger.error(f"Error fetching speakers for {model_id}: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/synthesize', methods=['POST'])
def synthesize():
    """Synthesize speech from text"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data or 'model_id' not in data:
            return jsonify({"status": "error", "message": "Missing required fields: text, model_id"}), 400
        
        text = data['text'].strip()
        model_id = data['model_id']
        speaker = data.get('speaker', None)
        
        if not text:
            return jsonify({"status": "error", "message": "Text cannot be empty"}), 400
        
        logger.info(f"Synthesizing text: '{text}' with model: {model_id}, speaker: {speaker}")
        
        # Generate unique filename
        audio_id = str(uuid.uuid4())
        audio_filename = f"{audio_id}.wav"
        audio_path = os.path.join(tempfile.gettempdir(), audio_filename)
        
        # Synthesize speech
        success = tts_service.synthesize(text, model_id, audio_path, speaker)
        
        if not success:
            return jsonify({"status": "error", "message": "Failed to synthesize speech"}), 500

        if False:
            # Transcribe the generated audio
            transcription = asr_service.transcribe(audio_path)
            
            if transcription is None:
                return jsonify({"status": "error", "message": "Failed to transcribe audio"}), 500
            
            # Calculate WER
            wer_score = wer_calculator.calculate_wer(text, transcription)
            
            # Log poor quality samples
            wer_threshold = float(os.environ.get('WER_THRESHOLD', '0.3'))
            if wer_score > wer_threshold:
                wer_calculator.log_poor_quality(text, transcription, wer_score, model_id, speaker)
        
        return jsonify({
            "status": "success",
            "audio_id": audio_id,
            "transcription": "None",
            "wer_score": 0,
            "threshold_exceeded": True
        })
        
    except Exception as e:
        logger.error(f"Error in synthesis: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/audio/<audio_id>')
def get_audio(audio_id):
    """Serve audio file"""
    try:
        audio_filename = f"{audio_id}.wav"
        audio_path = os.path.join(tempfile.gettempdir(), audio_filename)
        
        if not os.path.exists(audio_path):
            return jsonify({"status": "error", "message": "Audio file not found"}), 404
        
        return send_file(audio_path, mimetype='audio/wav')
        
    except Exception as e:
        logger.error(f"Error serving audio {audio_id}: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/logs/download')
def download_logs():
    """Download poor quality samples CSV"""
    try:
        csv_path = wer_calculator.get_csv_path()
        if not os.path.exists(csv_path):
            return jsonify({"status": "error", "message": "No log file found"}), 404
        
        return send_file(csv_path, as_attachment=True, download_name='poor_quality_samples.csv')
        
    except Exception as e:
        logger.error(f"Error downloading logs: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "message": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"status": "error", "message": "Internal server error"}), 500

with app.app_context():
    # Import models here so tables are created
    import models
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
