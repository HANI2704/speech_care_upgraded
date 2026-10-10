from django.urls import path
from . import views

app_name = 'therapist'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('patient/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('patient/<int:patient_id>/feedback/', views.send_feedback, name='send_feedback'),
    # path('profile/', views.profile, name='therapist_profile'),
    path('profile/', views.profile, name='profile'),
    path('note/<int:session_id>/', views.save_note, name='save_note'),
    path('patient/<int:patient_id>/exercise-screenshots/', views.exercise_screenshots, name='exercise_screenshots'),
    path('exercises/manage/', views.manage_exercises, name='manage_exercises'),
]
