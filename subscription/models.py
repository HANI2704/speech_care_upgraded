from django.db import models
from django.utils import timezone
from datetime import timedelta
from accounts.models import User


class TherapistSubscription(models.Model):
    STATUS_CHOICES = [
        ('trial', 'Free Trial'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    therapist = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    trial_start = models.DateTimeField(auto_now_add=True)
    trial_end = models.DateTimeField()
    subscription_start = models.DateTimeField(null=True, blank=True)
    subscription_end = models.DateTimeField(null=True, blank=True)
    plan_name = models.CharField(max_length=100, default='Basic')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.trial_end = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        now = timezone.now()
        if self.status == 'trial':
            return now <= self.trial_end
        elif self.status == 'active':
            return self.subscription_end and now <= self.subscription_end
        return False

    @property
    def days_remaining(self):
        now = timezone.now()
        if self.status == 'trial':
            delta = self.trial_end - now
            return max(0, delta.days)
        elif self.status == 'active' and self.subscription_end:
            delta = self.subscription_end - now
            return max(0, delta.days)
        return 0

    def __str__(self):
        return f"{self.therapist.get_full_name()} - {self.status}"
