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
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None   # 새로 생성인지 체크
        super().save(*args, **kwargs)

        # ⭐ DailyDose 자동 생성/수정/삭제 처리 시작 ⭐

        # 1) 기존 DailyDose 모두 불러오기
        existing = DailyDose.objects.filter(medicine=self)

        # 2) 기간(start_date ~ end_date) 기반으로 날짜 목록 생성
        delta = (self.end_date - self.start_date).days
        valid_dates = [self.start_date + timedelta(days=i) for i in range(delta + 1)]

        # 3) 기존 DailyDose 중에서 기간에서 벗어난 날짜 삭제
        for dose in existing:
            if dose.date not in valid_dates:
                dose.delete()

        # 4) 기간 내 날짜는 생성 또는 업데이트
        for d in valid_dates:
            dose, created = DailyDose.objects.get_or_create(
                medicine=self,
                date=d,
                defaults={"quantity": self.quantity}
            )
            if not created:
                # 기존 DailyDose라면 quantity 업데이트
                dose.quantity = self.quantity
                dose.save()

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
