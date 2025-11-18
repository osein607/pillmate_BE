from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta

class Medicine(models.Model):
    TYPE_CHOICES = [
        ('PRESCRIPTION', '처방약'),
        ('GENERAL', '일반약'),
        ('SUPPLEMENT', '건강보조제'),
    ]

    TIME_CHOICES = [
        ('BEFORE_MEAL', '식전 복용'),
        ('AFTER_MEAL', '식후 30분'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medicines')
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    quantity = models.PositiveIntegerField(default=1)
    start_date = models.DateField()
    end_date = models.DateField()
    time = models.CharField(max_length=20, choices=TIME_CHOICES)
    alarm_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

class DailyDose(models.Model):
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE,
        related_name="daily_doses"
    )
    date = models.DateField()
    quantity = models.PositiveIntegerField(default=1)
    is_taken = models.BooleanField(default=False)
    taken_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('medicine', 'date')
        ordering = ['date']

    def __str__(self):
        return f"{self.medicine.name} - {self.date}"


class DoseLog(models.Model):
    SOURCE_CHOICES = [
        ('ARDUINO', '아두이노 감지'),
        ('MANUAL', '사용자 입력'),
    ]

    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='logs')
    taken_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='ARDUINO')

    def __str__(self):
        return f"{self.medicine.name} - {self.taken_at.strftime('%Y-%m-%d %H:%M')}"

# 아두이노 통신 관련
class Device(models.Model):
    device_id = models.CharField(unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class MedicineLog(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    medicine = models.CharField(max_length=200)
    taken = models.BooleanField()
    timestamp = models.DateTimeField()
