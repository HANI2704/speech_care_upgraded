from django.contrib import admin
from .models import FacialExercise, FacialSession, PatientExerciseCompletion


@admin.register(FacialExercise)
class FacialExerciseAdmin(admin.ModelAdmin):
    list_display  = ('title', 'category', 'difficulty', 'repetitions', 'duration_seconds', 'has_video', 'is_active')
    list_filter   = ('category', 'difficulty', 'is_active')
    search_fields = ('title', 'description')
    fieldsets = (
        (None, {'fields': ('title', 'description', 'category', 'difficulty', 'is_active')}),
        ('Timing', {'fields': ('duration_seconds', 'repetitions')}),
        ('Reference Video (upload directly, max 1 minute)', {'fields': ('video_file',)}),
    )

    def has_video(self, obj):
        return bool(obj.video_file)
    has_video.boolean = True
    has_video.short_description = 'Has Video'


@admin.register(FacialSession)
class FacialSessionAdmin(admin.ModelAdmin):
    list_display  = ('patient', 'session_date', 'overall_score', 'accuracy_percentage', 'weak_side', 'duration_seconds')
    list_filter   = ('weak_side',)
    search_fields = ('patient__username', 'patient__first_name')
    readonly_fields = ('session_date', 'accuracy_percentage')


@admin.register(PatientExerciseCompletion)
class PatientExerciseCompletionAdmin(admin.ModelAdmin):
    list_display  = ('patient', 'exercise', 'completed_at', 'score', 'accuracy_percentage')
    list_filter   = ('exercise__category',)
    search_fields = ('patient__username',)
