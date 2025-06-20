from app import db
from datetime import datetime

class SynthesisLog(db.Model):
    """Log synthesis requests for audit purposes"""
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    model_id = db.Column(db.String(256), nullable=False)
    speaker = db.Column(db.String(64), nullable=True)
    transcription = db.Column(db.Text, nullable=True)
    wer_score = db.Column(db.Float, nullable=True)
    audio_filename = db.Column(db.String(256), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SynthesisLog {self.id}: {self.model_id}>'
