from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('therapist', 'Therapist'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    phone = models.CharField(max_length=10, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True, choices=[('male','Male'),('female','Female'),('other','Other')])
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"


class PatientProfile(models.Model):
    SEVERITY_CHOICES = [
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    diagnosis = models.CharField(max_length=200, blank=True, help_text="e.g., Stroke, Parkinson's, Aphasia")
    severity = models.CharField(max_length=20, default='mild', choices=SEVERITY_CHOICES)
    assigned_therapist = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='patients'
    )
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=10, blank=True)
    notes = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    severity_upgraded_at = models.DateTimeField(null=True, blank=True)
    speech_accuracy_for_upgrade = models.FloatField(default=0)

    def __str__(self):
        return f"Patient: {self.user.get_full_name()}"

    def check_and_upgrade_severity(self, current_avg_accuracy):
        UPGRADE_THRESHOLDS = {'mild': 65.0, 'moderate': 80.0}
        SEVERITY_PROGRESSION = {'mild': 'moderate', 'moderate': 'severe'}
        threshold = UPGRADE_THRESHOLDS.get(self.severity)
        if threshold and current_avg_accuracy >= threshold:
            self.severity = SEVERITY_PROGRESSION[self.severity]
            self.severity_upgraded_at = timezone.now()
            self.speech_accuracy_for_upgrade = current_avg_accuracy
            self.save()
            return True
        return False


class TherapistProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='therapist_profile')
    specialization = models.CharField(max_length=200, blank=True, default='')
    qualification = models.CharField(max_length=200, blank=True, default='')
    license_number = models.CharField(max_length=50, blank=True, default='')
    years_experience = models.PositiveIntegerField(default=0)
    bio = models.TextField(blank=True, default='')

    def __str__(self):
        return f"Therapist: {self.user.get_full_name()}"