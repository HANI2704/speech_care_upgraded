# SpeechCare - Speech Therapy Platform
## Setup Instructions

### 1. Install Python & Dependencies

```bash
pip install Django==4.2 numpy Pillow
```

### 2. Navigate to project folder
```bash
cd speech_therapy
```

### 3. Run Migrations
```bash
python manage.py makemigrations accounts
python manage.py makemigrations practice
python manage.py migrate
```

### 4. Populate Sample Practice Texts
```bash
python populate_data.py
```

### 5. Create Admin User (optional)
```bash
python manage.py createsuperuser
```

### 6. Run Development Server
```bash
python manage.py runserver
```

### 7. Open Browser
```
http://127.0.0.1:8000/
```

---

## Project Structure

```
speech_therapy/
├── speech_therapy/      # Django settings, main URLs
├── accounts/            # User model, login, registration
├── practice/            # Speech practice, analysis engine
│   └── speech_engine.py # Core AI speech analysis
├── patient/             # Patient dashboard, progress, reports
├── therapist/           # Therapist dashboard, patient management
├── templates/           # All HTML templates (glassmorphism UI)
├── static/              # CSS, JS, images
├── requirements.txt
├── populate_data.py     # Sample data setup
└── manage.py
```

---

## Features

### 🎙️ Speech Analysis Engine (speech_engine.py)
Measures 5 parameters specially designed for paralysis patients:
1. **Text Accuracy** (40%) - Word-by-word matching using WER algorithm
2. **Voice Volume** (20%) - RMS energy to detect weak voice
3. **Voice Stability** (20%) - Frame-level jitter to detect tremors
4. **Speech Rate** (10%) - Words/second (therapy range: 0.7-2.5 wps)
5. **Speech Clarity** (10%) - Voiced vs silence ratio

### 👤 Patient Features
- Dashboard with progress chart
- Live microphone recording with waveform visualization
- Speech-to-text (browser Web Speech API)
- Detailed analysis after each session
- Progress tracking with radar chart
- Session history reports

### 👩‍⚕️ Therapist Features
- All patients overview with accuracy indicators
- Detailed patient view with all session history
- Add therapy notes to any session
- Progress charts per patient

### 🎨 UI
- Modern Glassmorphism design
- Fully responsive (mobile-friendly)
- Animated backgrounds
- Dark theme with purple/indigo gradient

---

## Roles
- **Patient**: Register → Practice → View progress
- **Therapist**: Register → View all patients → Add notes

## Important Notes

### Browser Mic Settings
The recording uses:
- `autoGainControl: false` — CRITICAL to measure real voice volume
- `noiseSuppression: false` — Real signal for stability analysis
- `sampleRate: 16000` — Optimal for speech

### Accuracy Logic
- If patient speaks slowly but clearly → lower speech rate score, higher text score
- If voice is trembling → lower stability score
- If voice is weak → lower volume score
- Silence/pauses detected → lower clarity score

This gives a real therapy-grade score, not just a text match percentage.

### user id : patelhani2024@gmail.com
### password : 123