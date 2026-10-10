from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, PatientProfile, TherapistProfile

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role']
    list_filter = ['role']
    fieldsets = UserAdmin.fieldsets + (
        ('Extra', {'fields': ('role', 'phone', 'age', 'gender', 'profile_picture')}),
    )

admin.site.register(PatientProfile)
admin.site.register(TherapistProfile)
