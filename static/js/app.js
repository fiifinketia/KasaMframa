// Kasa Mframa - Frontend JavaScript

class KasaMframeApp {
    constructor() {
        this.initializeEventListeners();
        this.loadModels();
    }

    initializeEventListeners() {
        // Form submission
        document.getElementById('synthesisForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.synthesizeSpeech();
        });

        // Model selection change
        document.getElementById('modelSelect').addEventListener('change', (e) => {
            this.onModelChange(e.target.value);
        });
    }

    async loadModels() {
        try {
            const response = await fetch('/api/models');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.populateModelSelect(data.models);
            } else {
                this.showAlert('Error loading models: ' + data.message, 'danger');
            }
        } catch (error) {
            console.error('Error loading models:', error);
            this.showAlert('Failed to load TTS models', 'danger');
        }
    }

    populateModelSelect(models) {
        const select = document.getElementById('modelSelect');
        
        // Clear existing options except the first
        while (select.children.length > 1) {
            select.removeChild(select.lastChild);
        }

        // Add model options
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.id;
            option.textContent = model.name;
            option.setAttribute('data-has-speakers', model.has_speakers);
            select.appendChild(option);
        });
    }

    async onModelChange(modelId) {
        const speakerSelect = document.getElementById('speakerSelect');
        
        if (!modelId) {
            speakerSelect.disabled = true;
            speakerSelect.innerHTML = '<option value="">Select a speaker...</option>';
            return;
        }

        const selectedOption = document.querySelector(`#modelSelect option[value="${modelId}"]`);
        const hasSpeakers = selectedOption?.getAttribute('data-has-speakers') === 'true';

        if (hasSpeakers) {
            try {
                const response = await fetch(`/api/speakers/${encodeURIComponent(modelId)}`);
                const data = await response.json();
                
                if (data.status === 'success') {
                    this.populateSpeakerSelect(data.speakers);
                    speakerSelect.disabled = false;
                } else {
                    console.error('Error loading speakers:', data.message);
                    speakerSelect.disabled = true;
                }
            } catch (error) {
                console.error('Error loading speakers:', error);
                speakerSelect.disabled = true;
            }
        } else {
            speakerSelect.disabled = true;
            speakerSelect.innerHTML = '<option value="">No speakers available</option>';
        }
    }

    populateSpeakerSelect(speakers) {
        const select = document.getElementById('speakerSelect');
        select.innerHTML = '<option value="">Default speaker</option>';
        
        speakers.forEach(speaker => {
            const option = document.createElement('option');
            option.value = speaker;
            option.textContent = speaker;
            select.appendChild(option);
        });
    }

    async synthesizeSpeech() {
        const text = document.getElementById('textInput').value.trim();
        const modelId = document.getElementById('modelSelect').value;
        const speaker = document.getElementById('speakerSelect').value;

        if (!text || !modelId) {
            this.showAlert('Please enter text and select a model', 'warning');
            return;
        }

        // Show loading state
        this.setLoadingState(true, 'Synthesizing speech...');
        this.hideResults();

        try {
            const response = await fetch('/api/synthesize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    model_id: modelId,
                    speaker: speaker || null
                })
            });

            const data = await response.json();

            if (data.status === 'success') {
                this.displayResults(data, text);
                this.showAlert('Speech synthesized successfully!', 'success');
            } else {
                this.showAlert('Synthesis failed: ' + data.message, 'danger');
            }
        } catch (error) {
            console.error('Synthesis error:', error);
            // this.showAlert('Network error during synthesis', 'danger');
        } finally {
            this.setLoadingState(false);
        }
    }

    displayResults(data, originalText) {
        // Show results card
        document.getElementById('resultsCard').style.display = 'block';

        // Set audio source
        const audioPlayer = document.getElementById('audioPlayer');
        audioPlayer.src = `/api/audio/${data.audio_id}`;

        // Display transcription
        document.getElementById('transcriptionText').textContent = data.transcription;

        // Display WER score
        const werPercentage = Math.round(data.wer_score * 100);
        const werProgressBar = document.getElementById('werProgressBar');
        const werBadge = document.getElementById('werBadge');
        const qualityBadge = document.getElementById('qualityBadge');

        // Update WER progress bar
        werProgressBar.style.width = `${werPercentage}%`;
        werBadge.textContent = `${werPercentage}%`;

        // Set color based on WER score
        werProgressBar.className = 'progress-bar';
        if (werPercentage <= 10) {
            werProgressBar.classList.add('bg-success');
            werBadge.className = 'badge bg-success fs-6';
        } else if (werPercentage <= 30) {
            werProgressBar.classList.add('bg-warning');
            werBadge.className = 'badge bg-warning fs-6';
        } else {
            werProgressBar.classList.add('bg-danger');
            werBadge.className = 'badge bg-danger fs-6';
        }

        // Update quality status
        if (data.threshold_exceeded) {
            qualityBadge.textContent = 'Poor Quality';
            qualityBadge.className = 'badge bg-danger fs-6';
        } else {
            qualityBadge.textContent = 'Good Quality';
            qualityBadge.className = 'badge bg-success fs-6';
        }

        // Scroll to results
        document.getElementById('resultsCard').scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
    }

    setLoadingState(isLoading, text = 'Processing...') {
        const loadingIndicator = document.getElementById('loadingIndicator');
        const synthesizeBtn = document.getElementById('synthesizeBtn');
        const loadingText = document.getElementById('loadingText');

        if (isLoading) {
            loadingIndicator.style.display = 'block';
            synthesizeBtn.disabled = true;
            synthesizeBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
            loadingText.textContent = text;
        } else {
            loadingIndicator.style.display = 'none';
            synthesizeBtn.disabled = false;
            synthesizeBtn.innerHTML = '<i class="fas fa-play me-2"></i>Synthesize Speech';
        }
    }

    hideResults() {
        document.getElementById('resultsCard').style.display = 'none';
    }

    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alertContainer');
        
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        alertContainer.appendChild(alertDiv);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 5000);
    }
}

// Download logs function
async function downloadLogs() {
    try {
        const response = await fetch('/api/logs/download');
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'poor_quality_samples.csv';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            const data = await response.json();
            app.showAlert('Download failed: ' + data.message, 'warning');
        }
    } catch (error) {
        console.error('Download error:', error);
        app.showAlert('Failed to download logs', 'danger');
    }
}

// Initialize app when DOM is loaded
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new KasaMframeApp();
});
