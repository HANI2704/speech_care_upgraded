import json
import base64
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages

from .models import PracticeText, PracticeSession
from .speech_engine import analyze_speech
from accounts.models import User


def patient_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'patient':
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@patient_required
def practice_home(request):
    category   = request.GET.get('category', '')
    difficulty = request.GET.get('difficulty', '')
    texts = PracticeText.objects.filter(is_active=True)
    if category:   texts = texts.filter(category=category)
    if difficulty: texts = texts.filter(difficulty=difficulty)

    recent_sessions = PracticeSession.objects.filter(patient=request.user)[:5]
    return render(request, 'practice/home.html', {
        'texts': texts,
        'recent_sessions': recent_sessions,
        'categories': PracticeText.CATEGORY_CHOICES,
        'difficulties': PracticeText.DIFFICULTY_CHOICES,
        'selected_category': category,
        'selected_difficulty': difficulty,
    })


@login_required
@patient_required
def practice_session(request, text_id):
    practice_text = get_object_or_404(PracticeText, id=text_id, is_active=True)
    return render(request, 'practice/session.html', {'practice_text': practice_text})


@csrf_exempt
@require_POST
def analyze_audio(request):
    """
    API endpoint: receive audio blob + spoken text + optional facial_data,
    run speech analysis, save FacialSession if facial_data present, return results.
    """
    if not request.user.is_authenticated or request.user.role != 'patient':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        data         = json.loads(request.body)
        text_id      = data.get('text_id')
        spoken_text  = data.get('spoken_text', '')
        audio_base64 = data.get('audio_data', '')
        sample_rate  = data.get('sample_rate', 16000)
        facial_data  = data.get('facial_data', None)   # NEW
        practice_screenshot_b64 = data.get('practice_screenshot', '')

        practice_text = get_object_or_404(PracticeText, id=text_id)

        # Decode audio
        if audio_base64:
            audio_bytes = base64.b64decode(audio_base64)
        else:
            audio_bytes = bytes(sample_rate * 2)  # 1 s silence

        # Run speech analysis
        results = analyze_speech(
            audio_data_bytes=audio_bytes,
            reference_text=practice_text.content,
            spoken_text=spoken_text,
            sample_rate=sample_rate,
        )

        # Save PracticeSession
        session = PracticeSession.objects.create(
            patient=request.user,
            practice_text=practice_text,
            display_text=practice_text.content,
            spoken_text=spoken_text,
            text_accuracy=results['text_accuracy'],
            volume_score=results['volume_score'],
            stability_score=results['stability_score'],
            speech_rate_score=results['speech_rate_score'],
            clarity_score=results['clarity_score'],
            final_score=results['final_score'],
            rms_energy=results['rms_energy'],
            pitch_std=results['pitch_std'],
            words_per_second=results['words_per_second'],
            duration_seconds=results['duration_seconds'],
            word_error_rate=results['word_error_rate'],
            missing_words=results['missing_words'],
            extra_words=results['extra_words'],
        )

        # ── Save FacialSession if facial data was captured ──────────────
        facial_session_id = None
        facial_overall    = None
        if facial_data and isinstance(facial_data, dict):
            try:
                from facial.models import FacialSession
                from django.db.models import Avg

                # Compute improvement vs last session
                last = FacialSession.objects.filter(patient=request.user).first()
                prev_score = last.overall_score if last else 0
                improvement = round(
                    float(facial_data.get('overall_score', 0)) - prev_score, 1
                )

                fs = FacialSession.objects.create(
                    patient=request.user,
                    smile_symmetry=facial_data.get('smile_symmetry', 0),
                    lip_movement=facial_data.get('lip_movement', 0),
                    jaw_opening=facial_data.get('jaw_opening', 0),
                    eye_blink_rate=facial_data.get('eye_blink_rate', 0),
                    muscle_strength=facial_data.get('muscle_strength', 0),
                    weak_side=facial_data.get('weak_side', 'none'),
                    overall_score=facial_data.get('overall_score', 0),
                    suggested_reps=facial_data.get('suggested_reps', 10),
                    improvement_from_last=improvement,
                    duration_seconds=facial_data.get('duration_seconds', 0),
                    accuracy_percentage=round(
                        float(facial_data.get('smile_symmetry', 0))*0.35 +
                        float(facial_data.get('lip_movement', 0))*0.25 +
                        float(facial_data.get('jaw_opening', 0))*0.25 +
                        float(facial_data.get('muscle_strength', 0))*0.15, 1
                    ),
                    notes=f"Captured during practice session #{session.id}",
                )
                # Save practice screenshot if provided
                if practice_screenshot_b64:
                    import base64 as b64mod
                    from django.core.files.base import ContentFile
                    try:
                        shot = practice_screenshot_b64
                        if ',' in shot:
                            shot = shot.split(',', 1)[1]
                        img_bytes = b64mod.b64decode(shot)
                        fname = f"practice_p{request.user.id}_s{session.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                        fs.screenshot.save(fname, ContentFile(img_bytes), save=True)
                    except Exception:
                        pass
                facial_session_id = fs.id
                facial_overall    = fs.overall_score
            except Exception as fe:
                pass  # facial save is optional — don't break speech result

        # Auto-check severity upgrade
        try:
            from accounts.models import PatientProfile
            from django.db.models import Avg
            profile = PatientProfile.objects.get(user=request.user)
            avg_acc = PracticeSession.objects.filter(patient=request.user).aggregate(
                avg=Avg('final_score')
            )['avg'] or 0
            profile.check_and_upgrade_severity(round(avg_acc, 1))
        except Exception:
            pass

        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'results': results,
            'facial_session_id': facial_session_id,
            'facial_overall': facial_overall,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def session_result(request, session_id):
    session = get_object_or_404(PracticeSession, id=session_id)
    if request.user.role == 'patient' and session.patient != request.user:
        return redirect('patient:dashboard')

    # Try to fetch matching facial session (same patient, closest in time)
    facial_session = None
    try:
        from facial.models import FacialSession
        facial_session = FacialSession.objects.filter(
            patient=session.patient,
            notes__contains=f"practice session #{session.id}"
        ).first()
    except Exception:
        pass

    return render(request, 'practice/result.html', {
        'session': session,
        'facial_session': facial_session,
    })


@login_required
def add_therapist_note(request, session_id):
    if request.user.role != 'therapist':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    session = get_object_or_404(PracticeSession, id=session_id)
    if request.method == 'POST':
        session.therapist_notes = request.POST.get('note', '')
        session.therapist = request.user
        session.save()
        messages.success(request, 'Note saved successfully.')
    return redirect('therapist:patient_detail', patient_id=session.patient.id)
