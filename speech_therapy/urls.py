from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect


def home_redirect(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'role'):
            if request.user.role == 'therapist':
                return redirect('therapist:dashboard')
            else:
                return redirect('patient:dashboard')
    return redirect('accounts:login')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_redirect, name='home'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('practice/', include('practice.urls', namespace='practice')),
    path('therapist/', include('therapist.urls', namespace='therapist')),
    path('patient/', include('patient.urls', namespace='patient')),
    path('subscription/', include('subscription.urls', namespace='subscription')),
# ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)