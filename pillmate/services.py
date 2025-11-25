from django.core.mail import send_mail
from django.conf import settings

def send_missed_dose_email(guardian_email, owner_name, medicine_name, time):
    subject = f"[PillMate] {owner_name}님 최근 2일간 미복용 알림"

    message = (
        f"{owner_name}님이 최근 2일 동안 복용해야 했던 약 '{medicine_name}'을(를)\n"
        f"단 한 번도 복용하지 않은 것으로 확인되었습니다.\n\n"
        f"복용 시간은 {time.strftime('%H:%M')} 입니다.\n"
        f"건강 관리를 위해 확인 부탁드립니다.\n\n"
        f"- PillMate"
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [guardian_email],
        fail_silently=False,
    )

