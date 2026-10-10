import re
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, PatientProfile, TherapistProfile

from django.conf import settings

def validate_indian_phone(phone):
    if not phone:
        return
    digits = re.sub(r'\D', '', phone)
    if len(digits) != 10:
        raise forms.ValidationError("Phone number must be exactly 10 digits.")
    if digits[0] not in '6789':
        raise forms.ValidationError("Phone number must start with 6, 7, 8, or 9.")


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-input'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-input'}))


class PatientRegistrationForm(UserCreationForm):
    first_name      = forms.CharField(max_length=50, required=True)
    last_name       = forms.CharField(max_length=50, required=True)
    email           = forms.EmailField(required=True)
    phone           = forms.CharField(max_length=10, required=False)
    age             = forms.IntegerField(required=False, min_value=1, max_value=120)
    gender          = forms.ChoiceField(choices=[('','Select'),('male','Male'),('female','Female'),('other','Other')])
    diagnosis       = forms.CharField(max_length=200, required=False)
    severity        = forms.ChoiceField(choices=[('','Select'),('mild','Mild'),('moderate','Moderate'),('severe','Severe')], required=False)
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model  = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'age', 'gender', 'password1', 'password2']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        validate_indian_phone(phone)
        return phone

    def clean_first_name(self):
        val = self.cleaned_data.get('first_name', '').strip()
        if not val.replace(' ', '').isalpha():
            raise forms.ValidationError("First name must contain only letters.")
        return val

    def clean_last_name(self):
        val = self.cleaned_data.get('last_name', '').strip()
        if not val.replace(' ', '').isalpha():
            raise forms.ValidationError("Last name must contain only letters.")
        return val

    def save(self, commit=True):
        user            = super().save(commit=False)
        user.role       = 'patient'
        user.first_name = self.cleaned_data['first_name']
        user.last_name  = self.cleaned_data['last_name']
        user.email      = self.cleaned_data['email']
        user.phone      = self.cleaned_data.get('phone', '')
        user.age        = self.cleaned_data.get('age')
        user.gender     = self.cleaned_data.get('gender', '')
        if self.cleaned_data.get('profile_picture'):
            user.profile_picture = self.cleaned_data['profile_picture']
        if commit:
            user.save()
            PatientProfile.objects.create(
                user      = user,
                diagnosis = self.cleaned_data.get('diagnosis', ''),
                severity  = self.cleaned_data.get('severity', ''),
            )

        return user


class TherapistRegistrationForm(UserCreationForm):
    first_name       = forms.CharField(max_length=50, required=True)
    last_name        = forms.CharField(max_length=50, required=True)
    email            = forms.EmailField(required=True)
    phone            = forms.CharField(max_length=10, required=False)
    specialization   = forms.CharField(max_length=200, required=False)
    qualification    = forms.CharField(max_length=200, required=False)
    license_number   = forms.CharField(max_length=50, required=False)
    years_experience = forms.IntegerField(required=False, initial=0, min_value=0, max_value=60)
    profile_picture  = forms.ImageField(required=False)

    class Meta:
        model  = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        validate_indian_phone(phone)
        return phone

    def clean_first_name(self):
        val = self.cleaned_data.get('first_name', '').strip()
        if not val.replace(' ', '').isalpha():
            raise forms.ValidationError("First name must contain only letters.")
        return val

    def clean_last_name(self):
        val = self.cleaned_data.get('last_name', '').strip()
        if not val.replace(' ', '').isalpha():
            raise forms.ValidationError("Last name must contain only letters.")
        return val

    def save(self, commit=True):
        user            = super().save(commit=False)
        user.role       = 'therapist'
        user.first_name = self.cleaned_data['first_name']
        user.last_name  = self.cleaned_data['last_name']
        user.email      = self.cleaned_data['email']
        user.phone      = self.cleaned_data.get('phone', '')
        if self.cleaned_data.get('profile_picture'):
            user.profile_picture = self.cleaned_data['profile_picture']
        if commit:
            user.save()
            TherapistProfile.objects.create(
                user             = user,
                specialization   = self.cleaned_data.get('specialization', ''),
                qualification    = self.cleaned_data.get('qualification', ''),
                license_number   = self.cleaned_data.get('license_number', ''),
                years_experience = self.cleaned_data.get('years_experience', 0) or 0,
            )

        return user


class PatientProfileForm(forms.ModelForm):
    first_name      = forms.CharField(max_length=50)
    last_name       = forms.CharField(max_length=50)
    email           = forms.EmailField()
    phone           = forms.CharField(max_length=10, required=False)
    age             = forms.IntegerField(required=False, min_value=1, max_value=120)
    gender          = forms.ChoiceField(choices=[('','Select'),('male','Male'),('female','Female'),('other','Other')], required=False)
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model   = PatientProfile
        fields  = ['diagnosis', 'severity', 'emergency_contact', 'emergency_phone', 'notes', 'date_of_birth']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        validate_indian_phone(phone)
        return phone

    def clean_emergency_phone(self):
        phone = self.cleaned_data.get('emergency_phone', '').strip()
        validate_indian_phone(phone)
        return phone

    def clean_first_name(self):
        val = self.cleaned_data.get('first_name', '').strip()
        if not val.replace(' ', '').isalpha():
            raise forms.ValidationError("First name must contain only letters.")
        return val

    def clean_last_name(self):
        val = self.cleaned_data.get('last_name', '').strip()
        if not val.replace(' ', '').isalpha():
            raise forms.ValidationError("Last name must contain only letters.")
        return val


class TherapistProfileForm(forms.ModelForm):
    first_name      = forms.CharField(max_length=50)
    last_name       = forms.CharField(max_length=50)
    email           = forms.EmailField()
    phone           = forms.CharField(max_length=10, required=False)
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model   = TherapistProfile
        fields  = ['specialization', 'qualification', 'license_number', 'years_experience', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        validate_indian_phone(phone)
        return phone

    def clean_first_name(self):
        val = self.cleaned_data.get('first_name', '').strip()
        if not val.replace(' ', '').isalpha():
            raise forms.ValidationError("First name must contain only letters.")
        return val

    def clean_last_name(self):
        val = self.cleaned_data.get('last_name', '').strip()
        if not val.replace(' ', '').isalpha():
            raise forms.ValidationError("Last name must contain only letters.")
        return val