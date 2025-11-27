from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from collections import defaultdict
from django.utils.timezone import make_aware

from pillmate.models import DailyDose, GuardianInfo  # ← 경로 너는 pillmate 앱임
from pillmate.services import send_missed_dose_email  # 서비스에 있으면 이 경로로 수정

class Command(BaseCommand):
    help = "Check missed doses for the last 2 days"

    def handle(self, *args, **options):
        self.stdout.write("=== CHECK MISSED DOSES START ===")
        self.check_missed_doses()
        self.stdout.write("=== CHECK MISSED DOSES END ===")

    def check_missed_doses(self):
        now = timezone.now()
        today = now.date()

        start_date = today - timedelta(days=2)
        end_date = today

        guardian = GuardianInfo.objects.first()
        if not guardian or not guardian.email:
            self.stdout.write("[MISSED_DOSE] 보호자 정보 없음 → skip")
            return

        self.stdout.write(f"[MISSED_DOSE] 날짜 범위: {start_date}~{end_date}")

        doses = DailyDose.objects.filter(
            date__range=[start_date, end_date]
        ).select_related("medicine")

        grouped = defaultdict(list)
        for dose in doses:
            grouped[dose.medicine].append(dose)

        for med, dose_list in grouped.items():
            self.stdout.write(f"\n--- 약 체크: {med.name} ---")

            if any(d.is_taken for d in dose_list):
                self.stdout.write("→ 지난 2일 중 복용 기록 있음 → skip")
                continue

            all_passed_time = True
            for d in dose_list:
                scheduled = make_aware(datetime.combine(d.date, med.alarm_time))
                if now < scheduled + timedelta(minutes=30):
                    all_passed_time = False
                    self.stdout.write(f"→ {d.date} 복용 예정시간이 아직 지나지 않음 → skip")
                    break

            if not all_passed_time:
                continue

            self.stdout.write("→ 2일 동안 한 번도 복용하지 않음! 이메일 발송")

            send_missed_dose_email(
                guardian_email=guardian.email,
                owner_name=guardian.owner_name,
                medicine_name=med.name,
                time=med.alarm_time,
            )

            self.stdout.write("→ 이메일 전송 완료")
