# Kasa Mframa - TTS Synthesis & ASR Evaluation System

## Overview

Kasa Mframa is a production-ready text-to-speech (TTS) synthesis and automatic speech recognition (ASR) evaluation system designed for African languages, particularly Akan and Swahili. The system provides both a REST API and a minimal web interface for synthesizing speech, transcribing audio, and evaluating model performance through Word Error Rate (WER) calculations.

## System Architecture

### Backend Architecture
- **Framework**: Flask web application with SQLAlchemy ORM
- **Language**: Python 3.11
- **Database**: SQLite (default) with PostgreSQL support configured
- **Deployment**: Gunicorn WSGI server with autoscaling capabilities
- **AI Models**: Transformers-based TTS models and Faster-Whisper for ASR

### Frontend Architecture
- **Technology**: HTML5, Bootstrap 5 (dark theme), vanilla JavaScript
- **Design**: Single-page application with REST API integration
- **Styling**: Custom CSS with modern dark theme and responsive design

## Key Components

### TTS Service (`tts_service.py`)
- Supports multiple TTS model types from Hugging Face
- Handles both single-speaker and multi-speaker models
- Uses CUDA when available, falls back to CPU
- Supported models include Facebook MMS TTS and HCI Lab fine-tuned models

### ASR Service (`asr_service.py`)
- Uses faster-whisper for speech recognition
- Default model: `fiifinketia/whisper-large-v3-turbo-akan`
- Lazy loading of models for memory efficiency
- Audio file transcription capabilities

### Evaluation System (`evaluation.py`)
- Word Error Rate (WER) calculation using jiwer library
- CSV logging for poor quality samples (WER threshold based)
- Performance monitoring and data collection for model improvement

### Data Models (`models.py`)
- `SynthesisLog`: Tracks synthesis requests, transcriptions, and WER scores
- Audit trail for all TTS operations
- Database schema supports PostgreSQL and SQLite

## Data Flow

1. **Text Input**: User enters text via web interface or API
2. **Model Selection**: Choose TTS model and speaker (if multi-speaker)
3. **Speech Synthesis**: TTS service generates audio file
4. **ASR Transcription**: Generated audio is transcribed back to text
5. **Evaluation**: WER score calculated between original and transcribed text
6. **Logging**: Results stored in database and poor samples logged to CSV
7. **Response**: Audio file, transcription, and WER score returned to user

## External Dependencies

### Core ML Libraries
- `transformers`: Hugging Face model support
- `faster-whisper`: Efficient speech recognition
- `torch`: PyTorch for model inference
- `jiwer`: WER calculation

### Web Framework
- `flask`: Web application framework
- `flask-sqlalchemy`: Database ORM
- `gunicorn`: Production WSGI server

### Audio Processing
- `scipy`: Audio file handling
- `numpy`: Numerical operations

### Database Support
- `psycopg2-binary`: PostgreSQL connector
- SQLite: Built-in Python support

## Deployment Strategy

### Environment Configuration
- **Development**: SQLite database, debug mode enabled
- **Production**: PostgreSQL database via `DATABASE_URL` environment variable
- **Scaling**: Autoscale deployment target on Replit
- **Security**: ProxyFix middleware for proper header handling

### Model Management
- Models loaded lazily to optimize memory usage
- CPU/GPU detection and automatic device selection
- Configurable model selection via environment variables

### Performance Optimizations
- Database connection pooling with pre-ping health checks
- Model caching to avoid repeated loading
- Efficient audio file handling with temporary storage

## Changelog
- June 20, 2025. Initial setup
- June 20, 2025. Added Coqui TTS support with bytlabs-io/coqui-ai-TTS integration

## User Preferences

Preferred communication style: Simple, everyday language.