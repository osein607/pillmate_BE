from django.core.mail import send_mail
from django.conf import settings

def send_missed_dose_email(guardian_email, owner_name, medicine_name, time):
    subject = f"[PillMate] {owner_name}님 약 미복용 알림"
    message = (
        f"{owner_name}님이 {time}에 복용해야 했던 약 '{medicine_name}'을(를)\n"
        f"아직 복용하지 않았습니다.\n"
        f"확인 부탁드립니다.\n\n"
        f"- PillMate"
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [guardian_email],
        fail_silently=False,
    )
