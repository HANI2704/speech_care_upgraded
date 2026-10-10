import json
import base64
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Max
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from datetime import timedelta
import json as json_module

from accounts.models import User, PatientProfile
from accounts.forms import PatientProfileForm
from practice.models import PracticeSession, TherapistFeedback
from facial.models import FacialExercise, PatientExerciseCompletion, FacialSession


def patient_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'patient':
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@patient_required
def dashboard(request):
    sessions      = PracticeSession.objects.filter(patient=request.user)
    total_sessions = sessions.count()
    avg_accuracy   = sessions.aggregate(avg=Avg('final_score'))['avg'] or 0
    last_session   = sessions.first()

    recent = list(sessions[:7])
    chart_labels = [s.created_at.strftime('%b %d') for s in reversed(recent)]
    chart_data   = [round(s.final_score, 1) for s in reversed(recent)]

    improvement = 0
    last5 = sessions[:5]
    prev5 = sessions[5:10]
    if last5.exists() and prev5.exists():
        last_avg = last5.aggregate(avg=Avg('final_score'))['avg'] or 0
        prev_avg = prev5.aggregate(avg=Avg('final_score'))['avg'] or 0
        improvement = round(last_avg - prev_avg, 1)

    unread_feedbacks = TherapistFeedback.objects.filter(patient=request.user, is_read=False)
    unread_count     = unread_feedbacks.count()
    profile          = getattr(request.user, 'patient_profile', None)

    avg_acc = round(avg_accuracy, 1)
    if profile:
        profile.check_and_upgrade_severity(avg_acc)

    context = {
        'total_sessions':  total_sessions,
        'avg_accuracy':    round(avg_accuracy, 1),
        'last_session':    last_session,
        'improvement':     improvement,
        'chart_labels':    json_module.dumps(chart_labels),
        'chart_data':      json_module.dumps(chart_data),
        'recent_sessions': sessions[:5],
        'unread_feedbacks': unread_feedbacks[:3],
        'unread_count':    unread_count,
        'profile':         profile,
    }
    return render(request, 'patient/dashboard.html', context)


@login_required
@patient_required
def progress(request):
    sessions         = PracticeSession.objects.filter(patient=request.user)
    thirty_days_ago  = timezone.now() - timedelta(days=30)
    daily_sessions   = sessions.filter(created_at__gte=thirty_days_ago)

    from django.db.models.functions import TruncDate
    daily_data = (daily_sessions
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(avg_score=Avg('final_score'), count=Count('id'))
        .order_by('date'))

    dates  = [str(d['date']) for d in daily_data]
    scores = [round(d['avg_score'], 1) for d in daily_data]

    avg_components = (sessions.aggregate(
        text=Avg('text_accuracy'), volume=Avg('volume_score'),
        stability=Avg('stability_score'), rate=Avg('speech_rate_score'),
        clarity=Avg('clarity_score'),
    ) if sessions.exists() else
        {'text':0,'volume':0,'stability':0,'rate':0,'clarity':0})

    facial_sessions = FacialSession.objects.filter(patient=request.user)[:10]
    profile         = getattr(request.user, 'patient_profile', None)

    context = {
        'sessions':      sessions,
        'total_sessions': sessions.count(),
        'avg_accuracy':  round(sessions.aggregate(avg=Avg('final_score'))['avg'] or 0, 1),
        'dates':         json_module.dumps(dates),
        'scores':        json_module.dumps(scores),
        'avg_text':      round(avg_components['text'] or 0, 1),
        'avg_volume':    round(avg_components['volume'] or 0, 1),
        'avg_stability': round(avg_components['stability'] or 0, 1),
        'avg_rate':      round(avg_components['rate'] or 0, 1),
        'avg_clarity':   round(avg_components['clarity'] or 0, 1),
        'radar_data':    json_module.dumps([
            round(avg_components['text'] or 0, 1),
            round(avg_components['volume'] or 0, 1),
            round(avg_components['stability'] or 0, 1),
            round(avg_components['rate'] or 0, 1),
            round(avg_components['clarity'] or 0, 1),
        ]),
        'facial_sessions': facial_sessions,
        'profile':         profile,
    }
    return render(request, 'patient/progress.html', context)


@login_required
@patient_required
def reports(request):
    sessions     = PracticeSession.objects.filter(patient=request.user)
    week_ago     = timezone.now() - timedelta(days=7)
    week_sessions = sessions.filter(created_at__gte=week_ago)

    feedbacks = TherapistFeedback.objects.filter(patient=request.user)
    feedbacks.filter(is_read=False).update(is_read=True)
    profile = getattr(request.user, 'patient_profile', None)

    context = {
        'sessions':      sessions[:20],
        'total_sessions': sessions.count(),
        'week_sessions': week_sessions.count(),
        'avg_accuracy':  round(sessions.aggregate(avg=Avg('final_score'))['avg'] or 0, 1),
        'best_score':    sessions.aggregate(best=Max('final_score'))['best'] or 0,
        'feedbacks':     feedbacks,
        'profile':       profile,
    }
    return render(request, 'patient/reports.html', context)


# @login_required
# @patient_required
# def profile(request):
#     user    = request.user
#     profile, _ = PatientProfile.objects.get_or_create(user=user)

#     if request.FILES.get('profile_picture'):
#         request.user.profile_picture = request.FILES.get('profile_picture')
#         request.user.save()
#         if form.is_valid():
#             user.first_name = form.cleaned_data.get('first_name', user.first_name)
#             user.last_name  = form.cleaned_data.get('last_name', user.last_name)
#             user.email      = form.cleaned_data.get('email', user.email)
#             user.phone      = form.cleaned_data.get('phone', user.phone)
#             user.age        = form.cleaned_data.get('age', user.age)
#             user.gender     = form.cleaned_data.get('gender', user.gender)
#             if form.cleaned_data.get('profile_picture'):
#                 user.profile_picture = form.cleaned_data['profile_picture']
#             user.save()
#             form.save()
#             from django.contrib import messages
#             messages.success(request, 'Profile updated!')
#             return redirect('patient:profile')
#     else:
#         form = PatientProfileForm(instance=profile, initial={
#             'first_name': user.first_name, 'last_name': user.last_name,
#             'email': user.email, 'phone': user.phone,
#             'age': user.age, 'gender': user.gender,
#         })
#     return render(request, 'patient/profile.html', {'form': form, 'profile': profile})

@login_required
@patient_required
def profile(request):
    user = request.user
    profile, _ = PatientProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        # USER FIELDS
        user.first_name = request.POST.get('first_name')
        user.last_name  = request.POST.get('last_name')
        user.email      = request.POST.get('email')
        user.phone      = request.POST.get('phone')
        user.age        = request.POST.get('age')
        user.gender     = request.POST.get('gender')

        # PROFILE FIELDS
        profile.diagnosis = request.POST.get('diagnosis')
        profile.severity  = request.POST.get('severity')
        profile.emergency_contact = request.POST.get('emergency_contact')
        profile.emergency_phone   = request.POST.get('emergency_phone')

        # PROFILE IMAGE
        if request.FILES.get('profile_picture'):
            user.profile_picture = request.FILES.get('profile_picture')

        # SAVE BOTH
        user.save()
        profile.save()

        from django.contrib import messages
        messages.success(request, 'Profile updated successfully!')

        return redirect('patient:profile')

    return render(request, 'patient/profile.html', {
        'user': user,
        'profile': profile
    })

@login_required
@patient_required
def exercises(request):
    profile  = getattr(request.user, 'patient_profile', None)
    severity = profile.severity if profile else 'mild'

    if severity == 'mild':
        recommended = FacialExercise.objects.filter(is_active=True, difficulty='easy')
    elif severity == 'moderate':
        recommended = FacialExercise.objects.filter(is_active=True, difficulty__in=['easy','medium'])
    else:
        recommended = FacialExercise.objects.filter(is_active=True)

    completions_today = PatientExerciseCompletion.objects.filter(
        patient=request.user, completed_at__date=timezone.now().date()
    )
    completed_exercise_ids = [c.exercise_id for c in completions_today]
    total_completed = PatientExerciseCompletion.objects.filter(patient=request.user).count()

    context = {
        'exercises':             recommended,
        'completed_exercise_ids': completed_exercise_ids,
        'total_completed':       total_completed,
        'profile':               profile,
        'severity':              severity,
    }
    return render(request, 'patient/exercises.html', context)


@csrf_exempt
@login_required
@patient_required
def complete_exercise_with_screenshot(request):
    """
    JSON POST endpoint.
    Receives:  exercise_id, screenshot (base64 PNG), facial metrics, score
    Saves:     PatientExerciseCompletion with screenshot file + metrics
    Returns:   JSON {success, completion_id}
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    try:
        data        = json_module.loads(request.body)
        exercise_id = data.get('exercise_id')
        screenshot_b64 = data.get('screenshot', '')
        score       = float(data.get('score', 0))
        smile       = float(data.get('smile', 0))
        jaw         = float(data.get('jaw', 0))
        lip         = float(data.get('lip', 0))
        muscle      = float(data.get('muscle', 0))
        weak_side   = data.get('weak_side', 'none')

        exercise = get_object_or_404(FacialExercise, id=exercise_id)

        completion = PatientExerciseCompletion(
            patient=request.user,
            exercise=exercise,
            score=score,
            accuracy_percentage=score,  # score already is accuracy %
            smile_at_completion=smile,
            jaw_at_completion=jaw,
            lip_at_completion=lip,
            muscle_at_completion=muscle,
            weak_side_at_completion=weak_side,
        )

        # ── Save screenshot as file ──────────────────────────────────────
        if screenshot_b64:
            from django.core.files.base import ContentFile
            # strip data-URL header if present
            if ',' in screenshot_b64:
                screenshot_b64 = screenshot_b64.split(',', 1)[1]
            img_bytes = base64.b64decode(screenshot_b64)
            filename  = (
                f"ex_{exercise_id}_"
                f"p{request.user.id}_"
                f"{timezone.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            completion.screenshot.save(filename, ContentFile(img_bytes), save=False)

        completion.save()

        return JsonResponse({
            'success':       True,
            'completion_id': completion.id,
            'has_screenshot': bool(completion.screenshot),
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@patient_required
def facial_analysis(request):
    facial_sessions = FacialSession.objects.filter(patient=request.user)
    avg_smile   = facial_sessions.aggregate(avg=Avg('smile_symmetry'))['avg'] or 0
    avg_jaw     = facial_sessions.aggregate(avg=Avg('jaw_opening'))['avg'] or 0
    avg_overall = facial_sessions.aggregate(avg=Avg('overall_score'))['avg'] or 0

    context = {
        'facial_sessions': facial_sessions[:10],
        'last_session':    facial_sessions.first(),
        'avg_smile':       round(avg_smile, 1),
        'avg_jaw':         round(avg_jaw, 1),
        'avg_overall':     round(avg_overall, 1),
        'total_sessions':  facial_sessions.count(),
    }
    return render(request, 'patient/facial_analysis.html', context)


@csrf_exempt
@require_POST
@login_required
@patient_required
def save_facial_session(request):
    try:
        data = json_module.loads(request.body)

        # Compute improvement vs last session
        last = FacialSession.objects.filter(patient=request.user).first()
        prev_score = last.overall_score if last else 0
        improvement = round(float(data.get('overall_score', 0)) - prev_score, 1)

        fs = FacialSession(
            patient=request.user,
            smile_symmetry=data.get('smile_symmetry', 0),
            lip_movement=data.get('lip_movement', 0),
            jaw_opening=data.get('jaw_opening', 0),
            eye_blink_rate=data.get('eye_blink_rate', 0),
            muscle_strength=data.get('muscle_strength', 0),
            weak_side=data.get('weak_side', 'none'),
            overall_score=data.get('overall_score', 0),
            suggested_reps=data.get('suggested_reps', 10),
            improvement_from_last=improvement,
            duration_seconds=data.get('duration_seconds', 0),
        )
        # Compute accuracy as weighted combination
        smile = float(data.get('smile_symmetry', 0))
        lip   = float(data.get('lip_movement', 0))
        jaw   = float(data.get('jaw_opening', 0))
        muscle= float(data.get('muscle_strength', 0))
        fs.accuracy_percentage = round(smile*0.35 + lip*0.25 + jaw*0.25 + muscle*0.15, 1)

        # Save screenshot if provided
        screenshot_b64 = data.get('screenshot', '')
        if screenshot_b64:
            from django.core.files.base import ContentFile
            if ',' in screenshot_b64:
                screenshot_b64 = screenshot_b64.split(',', 1)[1]
            try:
                img_bytes = base64.b64decode(screenshot_b64)
                filename = (
                    f"facial_p{request.user.id}_"
                    f"{timezone.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                )
                fs.screenshot.save(filename, ContentFile(img_bytes), save=False)
            except Exception:
                pass  # screenshot optional

        fs.save()
        return JsonResponse({'status': 'ok', 'session_id': fs.id,
                             'has_screenshot': bool(fs.screenshot),
                             'accuracy_percentage': fs.accuracy_percentage})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@patient_required
def complete_exercise(request, exercise_id):
    """Simple GET-based completion (fallback for non-JS)."""
    from django.contrib import messages
    exercise = get_object_or_404(FacialExercise, id=exercise_id)
    PatientExerciseCompletion.objects.create(
        patient=request.user,
        exercise=exercise,
        score=75,
        accuracy_percentage=75,
    )
    messages.success(request, f'"{exercise.title}" marked as complete!')
    return redirect('patient:exercises')
