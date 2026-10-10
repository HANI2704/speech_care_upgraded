from django.urls import path
from . import views

app_name = 'practice'

urlpatterns = [
    path('', views.practice_home, name='home'),
    path('session/<int:text_id>/', views.practice_session, name='session'),
    path('analyze/', views.analyze_audio, name='analyze'),
    path('result/<int:session_id>/', views.session_result, name='result'),
    path('note/<int:session_id>/', views.add_therapist_note, name='add_note'),
]
