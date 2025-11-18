from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta
from .models import Medicine, DailyDose

@receiver(post_save, sender=Medicine)
def create_daily_doses(sender, instance, created, **kwargs):
    if not created:
        return

    delta = (instance.end_date - instance.start_date).days
    for i in range(delta + 1):
        date = instance.start_date + timedelta(days=i)
        DailyDose.objects.get_or_create(
            medicine=instance,
            date=date,
            defaults={"quantity": instance.quantity}
        )
