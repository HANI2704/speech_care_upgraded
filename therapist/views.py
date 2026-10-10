from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Max, Q
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
import json

from accounts.models import User, TherapistProfile, PatientProfile
from accounts.forms import TherapistProfileForm
from practice.models import PracticeSession, TherapistFeedback
from facial.models import PatientExerciseCompletion, FacialExercise
from subscription.models import TherapistSubscription


def therapist_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'therapist':
            return redirect('accounts:login')
        # Ensure subscription exists
        sub, created = TherapistSubscription.objects.get_or_create(therapist=request.user)
        if not sub.is_active:
            return redirect('subscription:expired')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@therapist_required
def dashboard(request):
    patients = User.objects.filter(role='patient')

    # Filter & Search
    severity_filter = request.GET.get('severity', '')
    name_filter = request.GET.get('name', '')
    min_acc = request.GET.get('min_acc', '')
    max_acc = request.GET.get('max_acc', '')

    patient_data = []
    for patient in patients:
        sessions = PracticeSession.objects.filter(patient=patient)
        avg = sessions.aggregate(avg=Avg('final_score'))['avg'] or 0
        avg = round(avg, 1)

        # Apply accuracy filter
        if min_acc and avg < float(min_acc):
            continue
        if max_acc and avg > float(max_acc):
            continue

        profile = getattr(patient, 'patient_profile', None)

        # Apply severity filter
        if severity_filter and profile and profile.severity != severity_filter:
            continue

        # Apply name filter
        if name_filter and name_filter.lower() not in patient.get_full_name().lower():
            continue

        last = sessions.first()
        unread_feedbacks = TherapistFeedback.objects.filter(patient=patient, is_read=False).count()

        patient_data.append({
            'user': patient,
            'total_sessions': sessions.count(),
            'avg_accuracy': avg,
            'last_practice': last.created_at if last else None,
            'profile': profile,
            'unread_feedbacks': unread_feedbacks,
        })

    total_sessions_today = PracticeSession.objects.filter(
        created_at__date=timezone.now().date()
    ).count()

    subscription = getattr(request.user, 'subscription', None)

    context = {
        'patient_data': patient_data,
        'total_patients': len(patient_data),
        'total_sessions_today': total_sessions_today,
        'severity_filter': severity_filter,
        'name_filter': name_filter,
        'min_acc': min_acc,
        'max_acc': max_acc,
        'subscription': subscription,
    }
    return render(request, 'therapist/dashboard.html', context)


@login_required
@therapist_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(User, id=patient_id, role='patient')
    sessions = PracticeSession.objects.filter(patient=patient)
    profile = getattr(patient, 'patient_profile', None)
    feedbacks = TherapistFeedback.objects.filter(patient=patient)

    # Chart data
    recent = list(sessions[:15])
    chart_labels = [s.created_at.strftime('%b %d %H:%M') for s in reversed(recent)]
    chart_data = [round(s.final_score, 1) for s in reversed(recent)]

    avg_components = sessions.aggregate(
        text=Avg('text_accuracy'),
        volume=Avg('volume_score'),
        stability=Avg('stability_score'),
        rate=Avg('speech_rate_score'),
        clarity=Avg('clarity_score'),
    )

    avg_accuracy = round(sessions.aggregate(avg=Avg('final_score'))['avg'] or 0, 1)

    # Auto severity check
    upgraded = False
    if profile:
        upgraded = profile.check_and_upgrade_severity(avg_accuracy)

    # Exercise completion summary
    from facial.models import PatientExerciseCompletion as PEC
    exercise_completions = PEC.objects.filter(patient=patient).select_related('exercise').order_by('-completed_at')[:6]
    screenshots_count = PEC.objects.filter(patient=patient).exclude(screenshot='').exclude(screenshot__isnull=True).count()

    context = {
        'patient': patient,
        'profile': profile,
        'sessions': sessions,
        'feedbacks': feedbacks,
        'total_sessions': sessions.count(),
        'avg_accuracy': avg_accuracy,
        'best_score': sessions.aggregate(best=Max('final_score'))['best'] or 0,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'avg_text': round(avg_components['text'] or 0, 1),
        'avg_volume': round(avg_components['volume'] or 0, 1),
        'avg_stability': round(avg_components['stability'] or 0, 1),
        'avg_rate': round(avg_components['rate'] or 0, 1),
        'avg_clarity': round(avg_components['clarity'] or 0, 1),
        'radar_data': json.dumps([
            round(avg_components['text'] or 0, 1),
            round(avg_components['volume'] or 0, 1),
            round(avg_components['stability'] or 0, 1),
            round(avg_components['rate'] or 0, 1),
            round(avg_components['clarity'] or 0, 1),
        ]),
        'severity_upgraded': upgraded,
        'exercise_completions': exercise_completions,
        'screenshots_count': screenshots_count,
    }
    return render(request, 'therapist/patient_detail.html', context)


@login_required
@therapist_required
def profile(request):
    user = request.user
    profile = user.therapist_profile

    if request.method == 'POST':
        form = TherapistProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            user.first_name = form.cleaned_data.get('first_name', user.first_name)
            user.last_name = form.cleaned_data.get('last_name', user.last_name)
            user.email = form.cleaned_data.get('email', user.email)
            user.phone = form.cleaned_data.get('phone', user.phone)
            if request.FILES.get('profile_picture'):
                user.profile_picture = request.FILES['profile_picture']
            user.save()
            form.save()

            # ✅ Save TherapistProfile fields
            form.save()
            
            from django.contrib import messages
            messages.success(request, 'Profile updated successfully!')
            return redirect('therapist:profile')
    else:
        form = TherapistProfileForm(instance=profile, initial={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone': user.phone,
        })

    subscription = getattr(user, 'subscription', None)
    return render(request, 'therapist/profile.html', {'form': form,'profile': profile, 'subscription': subscription})


@login_required
@therapist_required
def save_note(request, session_id):
    if request.method == 'POST':
        session = get_object_or_404(PracticeSession, id=session_id)
        session.therapist_notes = request.POST.get('note', '')
        session.therapist = request.user
        session.save()
        from django.contrib import messages
        messages.success(request, 'Note saved!')
    return redirect('therapist:patient_detail', patient_id=session.patient.id)


@login_required
@therapist_required
def send_feedback(request, patient_id):
    """Send manual therapist feedback to patient."""
    if request.method == 'POST':
        patient = get_object_or_404(User, id=patient_id, role='patient')
        feedback_text = request.POST.get('feedback_text', '').strip()
        rating = request.POST.get('rating', 3)
        session_id = request.POST.get('session_id')
        session = None
        if session_id:
            session = PracticeSession.objects.filter(id=session_id).first()

        if feedback_text:
            TherapistFeedback.objects.create(
                therapist=request.user,
                patient=patient,
                session=session,
                feedback_text=feedback_text,
                rating=rating,
            )
            # Email notification to patient
            if patient.email:
                try:
                    from accounts.email_utils import send_feedback_notification_email
                    send_feedback_notification_email(patient, request.user, feedback_text, int(rating))
                except Exception:
                    pass
            from django.contrib import messages
            messages.success(request, f'Feedback sent to {patient.get_full_name()}!')

    return redirect('therapist:patient_detail', patient_id=patient_id)


@login_required
@therapist_required
def exercise_screenshots(request, patient_id):
    """Gallery of all exercise completions with real-time screenshots for a patient."""
    patient = get_object_or_404(User, id=patient_id, role='patient')

    # Optional exercise filter
    exercise_filter = request.GET.get('exercise', '')
    completions = PatientExerciseCompletion.objects.filter(
        patient=patient
    ).select_related('exercise').order_by('-completed_at')

    if exercise_filter:
        completions = completions.filter(exercise_id=exercise_filter)

    # Only completions that have a screenshot
    with_screenshots = completions.exclude(screenshot='').exclude(screenshot__isnull=True)
    all_exercises = FacialExercise.objects.filter(is_active=True)

    # Per-exercise summary stats
    exercise_stats = []
    for ex in all_exercises:
        ex_completions = completions.filter(exercise=ex)
        if ex_completions.exists():
            from django.db.models import Avg
            avg_score = ex_completions.aggregate(avg=Avg('score'))['avg'] or 0
            last = ex_completions.first()
            exercise_stats.append({
                'exercise': ex,
                'count': ex_completions.count(),
                'avg_score': round(avg_score, 1),
                'last_done': last.completed_at,
                'has_screenshots': ex_completions.exclude(screenshot='').exclude(screenshot__isnull=True).count(),
            })

    # Facial session screenshots
    from facial.models import FacialSession
    facial_sessions_with_shots = FacialSession.objects.filter(
        patient=patient
    ).exclude(screenshot='').exclude(screenshot__isnull=True).order_by('-session_date')[:30]

    context = {
        'patient': patient,
        'completions': completions[:60],
        'with_screenshots': with_screenshots[:60],
        'all_exercises': all_exercises,
        'exercise_filter': exercise_filter,
        'exercise_stats': exercise_stats,
        'total_completions': completions.count(),
        'total_with_screenshots': with_screenshots.count(),
        'facial_sessions_with_shots': facial_sessions_with_shots,
    }
    return render(request, 'therapist/exercise_screenshots.html', context)


@login_required
@therapist_required
def manage_exercises(request):
    """List, add and edit facial exercises with direct video upload."""
    exercises = FacialExercise.objects.all().order_by('category', 'difficulty')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            ex = FacialExercise(
                title       = request.POST.get('title', '').strip(),
                description = request.POST.get('description', '').strip(),
                category    = request.POST.get('category', 'smile'),
                difficulty  = request.POST.get('difficulty', 'easy'),
                duration_seconds = int(request.POST.get('duration_seconds', 30)),
                repetitions = int(request.POST.get('repetitions', 10)),
                is_active   = True,
            )
            if request.FILES.get('video_file'):
                ex.video_file = request.FILES['video_file']
            ex.save()
            from django.contrib import messages
            messages.success(request, f'Exercise "{ex.title}" added successfully.')
            return redirect('therapist:manage_exercises')

        elif action == 'delete':
            ex_id = request.POST.get('exercise_id')
            FacialExercise.objects.filter(id=ex_id).delete()
            from django.contrib import messages
            messages.success(request, 'Exercise deleted.')
            return redirect('therapist:manage_exercises')

        elif action == 'toggle':
            ex_id = request.POST.get('exercise_id')
            ex = get_object_or_404(FacialExercise, id=ex_id)
            ex.is_active = not ex.is_active
            ex.save()
            return redirect('therapist:manage_exercises')

    return render(request, 'therapist/manage_exercises.html', {'exercises': exercises})
