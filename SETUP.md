# SpeechCare — Setup & Features Guide

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install "Django>=4.2,<5.0" mysqlclient Pillow
# Optional for audio analysis:
pip install numpy scipy
# Optional for advanced facial analysis:
pip install mediapipe opencv-python
```

### 2. Configure Database
```sql
CREATE DATABASE speech_care_db CHARACTER SET utf8mb4;
```

### 3. Configure Email (Required for Registration Emails)
```bash
cp .env.example .env
# Edit .env with your Gmail address and App Password
```

**Gmail App Password Setup:**
1. Enable 2-Step Verification on your Google account
2. Go to: Google Account → Security → App Passwords
3. Create an App Password → choose "Mail"
4. Paste the 16-char code as EMAIL_HOST_PASSWORD in .env

> If email credentials are not set, emails print to Django console (dev fallback).

### 4. Run Migrations
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## ✨ New Features Added

### 🎤 Practice Page — Microphone + Camera Together
- Both mic and camera activate simultaneously on "Start Session"
- Patient reads displayed text aloud while camera tracks facial movements
- A screenshot is captured when session ends and saved to FacialSession

### 🧠 Facial Analysis — Accuracy Percentage Saved
- `accuracy_percentage` field now computed and stored in database
- Weighted formula: Smile×35% + Lip×25% + Jaw×25% + Muscle×15%
- Shown in session history table as a dedicated column
- Separate from "Overall Score" to distinguish practice accuracy

### 🏋️ Exercise Page — Direct Video Upload (No YouTube)
- Therapists upload MP4/MOV/WebM videos directly (max 1 minute)
- Native HTML5 video player — works offline, no external dependencies
- Old YouTube URL field retained for backward compat but video_file takes priority

### 📧 Email — Fixed & Working
- Settings now auto-load from .env file (no need to export manually)
- Welcome emails sent on patient and therapist registration
- Feedback emails sent when therapist submits feedback
- Console fallback with helpful setup warning when not configured

### 👨‍⚕️ Therapist: Manage Exercises Page
- New sidebar link: "Manage Exercises"
- Add exercises with direct video upload
- Delete / toggle active status inline
- Preview uploaded videos right in the admin table

---

## Environment Variables (.env file)

```
DB_NAME=speech_care_db
DB_USER=root
DB_PASSWORD=your_password
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=you@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx
```
