from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from datetime import timedelta


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TherapistSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('trial', 'Free Trial'), ('active', 'Active'), ('expired', 'Expired'), ('cancelled', 'Cancelled')], default='trial', max_length=20)),
                ('trial_start', models.DateTimeField(auto_now_add=True)),
                ('trial_end', models.DateTimeField(default=django.utils.timezone.now)),
                ('subscription_start', models.DateTimeField(blank=True, null=True)),
                ('subscription_end', models.DateTimeField(blank=True, null=True)),
                ('plan_name', models.CharField(default='Basic', max_length=100)),
                ('amount_paid', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('notes', models.TextField(blank=True)),
                ('therapist', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
