from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages

from .forms import PatientRegistrationForm, TherapistRegistrationForm, PatientProfileForm, TherapistProfileForm
from .models import PatientProfile, TherapistProfile


def login_view(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user) 
    if request.method == 'POST':
        username = request.POST.get('username', '').strip() 
        password = request.POST.get('password', '') 
        user = authenticate( request, username=username, password=password ) 
        if user: login(request, user) 
        return redirect_by_role(user) 
    else: messages.error(request, 'Invalid username or password.') 
    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


def register_patient(request):
    if request.method == 'POST': 
        form = PatientRegistrationForm(request.POST)

        if form.is_valid(): 
            user = form.save()
            # Create PatientProfile with default severity = mild 
            PatientProfile.objects.get_or_create(user=user)

            # Login patient 
            login(request, user)
            messages.success( request,
                     f'Welcome, {user.get_full_name() or user.username}!' 
                    )
            return redirect('patient:dashboard')
    else: 
        form = PatientRegistrationForm()
    return render( request, 'accounts/register_patient.html', {'form': form} )


def register_therapist(request):
    if request.method == 'POST':
        form = TherapistRegistrationForm(request.POST)


        if form.is_valid():
            user = form.save()

            # Create TherapistProfile
            TherapistProfile.objects.get_or_create(user=user)

            # Auto-create 30-day trial subscription
            from subscription.models import TherapistSubscription

            TherapistSubscription.objects.get_or_create(
                therapist=user
            )

            # Login therapist
            login(request, user)

            messages.success(
                request,
                f'Welcome, Dr. {user.get_full_name() or user.username}! '
                f'Your 30-day free trial has started.'
            )

            return redirect('therapist:dashboard')

    else:
        form = TherapistRegistrationForm()

    # IMPORTANT:
    # This return is required for GET requests
    # and also when the form is invalid.
    return render(
        request,
        'accounts/register_therapist.html',
        {'form': form}
    )

def redirect_by_role(user): 
    if user.role == 'therapist': 
        return redirect('therapist:dashboard') 
    return redirect('patient:dashboard')