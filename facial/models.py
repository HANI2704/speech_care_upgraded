from django.db import models
from accounts.models import User
from django.core.exceptions import ValidationError


def validate_video_duration(value):
    """Ensure uploaded video is at most 60 seconds. Basic size check as proxy."""
    # Max ~50MB for a 1 min video at reasonable quality
    if value.size > 52_428_800:
        raise ValidationError("Video file too large. Max size is 50 MB (≈ 1 min).")


class FacialSession(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='facial_sessions')
    session_date = models.DateTimeField(auto_now_add=True)

    smile_symmetry  = models.FloatField(default=0)
    lip_movement    = models.FloatField(default=0)
    jaw_opening     = models.FloatField(default=0)
    eye_blink_rate  = models.FloatField(default=0)
    muscle_strength = models.FloatField(default=0)
    weak_side       = models.CharField(max_length=10, blank=True,
                          choices=[('left','Left'),('right','Right'),('none','None')])
    overall_score   = models.FloatField(default=0)
    # Store computed accuracy percentage (0-100)
    accuracy_percentage = models.FloatField(default=0, help_text="Overall accuracy % after practice")
    suggested_reps  = models.PositiveIntegerField(default=10)
    improvement_from_last = models.FloatField(default=0)
    notes           = models.TextField(blank=True)
    duration_seconds= models.FloatField(default=0)

    # Real-time screenshot captured during session
    screenshot = models.ImageField(
        upload_to='facial_screenshots/',
        blank=True, null=True,
        help_text="Webcam snapshot captured during facial session"
    )

    class Meta:
        ordering = ['-session_date']

    def __str__(self):
        return f"{self.patient.get_full_name()} - Facial {self.session_date.strftime('%Y-%m-%d')}"

    @property
    def computed_accuracy(self):
        """Return a weighted accuracy percentage."""
        return round(
            self.smile_symmetry * 0.35 +
            self.lip_movement   * 0.25 +
            self.jaw_opening    * 0.25 +
            self.muscle_strength* 0.15,
            1
        )


class FacialExercise(models.Model):
    CATEGORY_CHOICES = [
        ('smile',   'Smile Training'),
        ('lip',     'Lip Exercises'),
        ('jaw',     'Jaw Exercises'),
        ('eye',     'Eye Exercises'),
        ('tongue',  'Tongue Exercises'),
    ]
    DIFFICULTY_CHOICES = [
        ('easy',   'Easy'),
        ('medium', 'Medium'),
        ('hard',   'Hard'),
    ]
    title            = models.CharField(max_length=200)
    description      = models.TextField()
    category         = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    difficulty       = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='easy')
    duration_seconds = models.PositiveIntegerField(default=30)
    repetitions      = models.PositiveIntegerField(default=10)
    # Direct video file upload — max 1 minute, no YouTube links
    video_file       = models.FileField(
        upload_to='exercise_videos/',
        blank=True, null=True,
        validators=[validate_video_duration],
        help_text="Upload a reference video (max 1 minute / 50 MB). MP4 recommended."
    )
    # Keep video_url for backward-compat but prefer video_file
    video_url        = models.URLField(blank=True)
    is_active        = models.BooleanField(default=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def has_video(self):
        return bool(self.video_file)


class PatientExerciseCompletion(models.Model):
    """Stores one completed exercise set, including a webcam screenshot."""
    patient      = models.ForeignKey(User, on_delete=models.CASCADE,
                       related_name='exercise_completions')
    exercise     = models.ForeignKey(FacialExercise, on_delete=models.CASCADE,
                       related_name='completions')
    completed_at = models.DateTimeField(auto_now_add=True)
    score        = models.FloatField(default=0)
    accuracy_percentage = models.FloatField(default=0)

    # Real-time webcam screenshot
    screenshot   = models.ImageField(
                       upload_to='exercise_screenshots/',
                       blank=True, null=True,
                       help_text="Webcam snapshot taken at moment of completion"
                   )
    # Facial metrics at completion moment
    smile_at_completion   = models.FloatField(default=0)
    jaw_at_completion     = models.FloatField(default=0)
    lip_at_completion     = models.FloatField(default=0)
    muscle_at_completion  = models.FloatField(default=0)
    weak_side_at_completion = models.CharField(max_length=10, default='none')

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.patient.get_full_name()} — {self.exercise.title} @ {self.completed_at:%Y-%m-%d %H:%M}"
