from django.contrib import admin
from .models import PracticeText, PracticeSession, TherapistFeedback

admin.site.register(PracticeText)
admin.site.register(PracticeSession)
admin.site.register(TherapistFeedback)
