from django.urls import path
from . import views

app_name = 'patient'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('progress/', views.progress, name='progress'),
    path('reports/', views.reports, name='reports'),
    path('profile/', views.profile, name='profile'),
    path('exercises/', views.exercises, name='exercises'),
    path('exercises/complete/<int:exercise_id>/', views.complete_exercise, name='complete_exercise'),
    path('exercises/complete-with-screenshot/', views.complete_exercise_with_screenshot, name='complete_exercise_with_screenshot'),
    path('facial/', views.facial_analysis, name='facial_analysis'),
    path('facial/save/', views.save_facial_session, name='save_facial_session'),
]
