from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import TherapistSubscription


@login_required
def expired(request):
    subscription = getattr(request.user, 'subscription', None)
    return render(request, 'subscription/expired.html', {'subscription': subscription})


@login_required
def activate(request):
    """Activate paid subscription (demo - in production integrate payment gateway)."""
    if request.method == 'POST':
        plan = request.POST.get('plan', 'Basic')
        duration_days = int(request.POST.get('duration_days', 30))
        sub, _ = TherapistSubscription.objects.get_or_create(therapist=request.user)
        sub.status = 'active'
        sub.subscription_start = timezone.now()
        sub.subscription_end = timezone.now() + timezone.timedelta(days=duration_days)
        sub.plan_name = plan
        sub.amount_paid = 999 if duration_days == 30 else 2499
        sub.save()
        from django.contrib import messages
        messages.success(request, f'Subscription activated! Valid for {duration_days} days.')
        return redirect('therapist:dashboard')
    context = {
        'basic_features': [
            'Unlimited Patients',
            'Feedback System',
            'Patient Reports',
            'Session Notes',
            '30 Days Access',
        ],
        'pro_features': [
            'Everything in Basic',
            'AI Facial Analysis',
            'Advanced Reports',
            'Priority Support',
            '90 Days Access',
        ],
    }
    return render(request, 'subscription/activate.html', context)
