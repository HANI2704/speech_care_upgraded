from django.db import models
from accounts.models import User


class PracticeText(models.Model):
    CATEGORY_CHOICES = [
        ('vowels', 'Vowel Sounds'),
        ('consonants', 'Consonant Sounds'),
        ('words', 'Simple Words'),
        ('sentences', 'Short Sentences'),
        ('paragraphs', 'Paragraphs'),
        ('tongue_twisters', 'Tongue Twisters'),
    ]
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='sentences')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='easy')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class PracticeSession(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='practice_sessions')
    practice_text = models.ForeignKey(PracticeText, on_delete=models.SET_NULL, null=True)
    display_text = models.TextField()
    spoken_text = models.TextField(blank=True)

    text_accuracy = models.FloatField(default=0)
    volume_score = models.FloatField(default=0)
    stability_score = models.FloatField(default=0)
    speech_rate_score = models.FloatField(default=0)
    clarity_score = models.FloatField(default=0)
    final_score = models.FloatField(default=0)

    rms_energy = models.FloatField(default=0)
    pitch_std = models.FloatField(default=0)
    words_per_second = models.FloatField(default=0)
    duration_seconds = models.FloatField(default=0)
    missing_words = models.TextField(blank=True)
    extra_words = models.TextField(blank=True)
    word_error_rate = models.FloatField(default=0)

    therapist_notes = models.TextField(blank=True)
    therapist = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_sessions'
    )

    audio_file = models.FileField(upload_to='audio/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.created_at.strftime('%Y-%m-%d %H:%M')} - {self.final_score:.1f}%"


class TherapistFeedback(models.Model):
    """Manual therapist feedback for patients — stored permanently in reports."""
    therapist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_feedbacks')
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_feedbacks')
    session = models.ForeignKey(
        PracticeSession, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedbacks'
    )
    feedback_text = models.TextField()
    rating = models.PositiveIntegerField(default=3, choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback from {self.therapist.get_full_name()} to {self.patient.get_full_name()}"
