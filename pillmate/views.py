from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.contrib.auth.models import User
from django.utils import timezone

from datetime import date, timedelta, datetime
from django.utils.timezone import make_aware
from collections import defaultdict

from .models import Medicine, DoseLog, DailyDose, GuardianInfo
from .serializers import MedicineSerializer, DailyDoseSerializer, GuardianInfoSerializer
from .services import send_missed_dose_email


@extend_schema(tags = ["약 등록"], summary= ["type: PRESCRIPTION | GENERAL | SUPPLEMENT", "time: BEFORE_MEAL | AFTER_MEAL"])
class MedicineViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = MedicineSerializer   

    def get_queryset(self):
        return Medicine.objects.order_by('-created_at')

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_anonymous:  # 로그인 안 되어 있으면 
            user = User.objects.first()  # 기본 유저로 대체 (테스트용)
        serializer.save(user=user)
        
    @action(detail=False, methods=["GET"], permission_classes=[AllowAny])
    def logs(self, request):
        """
        이번 달 날짜별 복용 현황 반환
        [
        {"date": "2025-11-01", "taken": 2, "missed": 1},
        {"date": "2025-11-02", "taken": 3, "missed": 0},
        ]
        """
        try:
            # 현재 날짜 기준
            today = timezone.localdate()

            # 쿼리 파라미터에서 month 받기
            month_str = request.query_params.get("month")
            month = int(month_str) if month_str else today.month
            year = today.year

            # 월의 첫날, 마지막날 구하기
            first_day = date(year, month, 1)
            last_day = (date(year + (month == 12), (month % 12) + 1, 1)
                        - timedelta(days=1))

            # 유저 (임시로 1)
            user_id = 1

            # 유저의 모든 DailyDose 조회
            doses = DailyDose.objects.filter(
                medicine__user_id=user_id,
                date__gte=first_day,
                date__lte=last_day
            )

            # 날짜별 집계
            data = []
            current = first_day

            while current <= last_day:
                day_doses = doses.filter(date=current)

                taken = day_doses.filter(is_taken=True).count()
                missed = day_doses.filter(is_taken=False).count()

                data.append({
                    "date": current.strftime("%Y-%m-%d"),
                    "taken": taken,
                    "missed": missed
                })

                current += timedelta(days=1)

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DailyDoseViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = DailyDose.objects.all()
    serializer_class = DailyDoseSerializer

    # /daily-dose/?date=2025-11-18
    def list(self, request, *args, **kwargs):
        date = request.query_params.get('date')
        if not date:
            return super().list(request, *args, **kwargs)

        queryset = DailyDose.objects.filter(date=date).select_related('medicine')
        serializer = DailyDoseSerializer(queryset, many=True)
        return Response(serializer.data)

    # PATCH /daily-dose/{id}/take/
    @action(detail=True, methods=['patch'])
    def take(self, request, pk=None):
        dose = self.get_object()
        dose.is_taken = True
        dose.taken_at = timezone.now()
        dose.save()

        serializer = DailyDoseSerializer(dose)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

##################################################################
# 보호자 알림

# /guardian/ 
@api_view(["GET"])
@permission_classes([AllowAny])
def get_guardian_info(request):
    info = GuardianInfo.objects.first()   # 테스트용 하나만 존재
    if not info:
        return Response({"data": None})
    return Response(GuardianInfoSerializer(info).data)

# /guardian/update/
@api_view(["POST"])
@permission_classes([AllowAny])
def update_guardian_info(request):
    info = GuardianInfo.objects.first()

    if not info:
        info = GuardianInfo.objects.create(
            owner_name=request.data.get("owner_name", "사용자"),
            owner_email=request.data.get("owner_email", "none@example.com")
        )

    serializer = GuardianInfoSerializer(info, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data)

def check_missed_doses():
    now = timezone.now()
    today = now.date()

    # 2일 범위 (오늘 포함)
    start_date = today - timedelta(days=2)
    end_date = today

    guardian = GuardianInfo.objects.first()
    if not guardian or not guardian.email:
        print("[MISSED_DOSE] 보호자 정보 없음 → skip")
        return

    print(f"[MISSED_DOSE] 날짜 범위: {start_date}~{end_date}")

    # DailyDose에서 해당 기간의 모든 기록 가져오기
    doses = DailyDose.objects.filter(
        date__range=[start_date, end_date]
    ).select_related("medicine")

    # 약별로 DailyDose 리스트 묶기
    grouped = defaultdict(list)
    for dose in doses:
        grouped[dose.medicine].append(dose)

    # 약별로 미복용 판단
    for med, dose_list in grouped.items():
        print(f"\n--- 약 체크: {med.name} ---")

        # 1) 2일 중 한 번이라도 복용했으면 PASS
        if any(d.is_taken for d in dose_list):
            print("→ 지난 2일 중 복용 기록 있음 → skip")
            continue

        # 2) 복용 예정 시간도 모두 지난 상태인지 확인
        all_passed_time = True
        for d in dose_list:
            scheduled = make_aware(datetime.combine(d.date, med.alarm_time))
            if now < scheduled + timedelta(minutes=30):
                all_passed_time = False
                print(f"→ {d.date} 복용 예정시간이 아직 지나지 않음 → skip")
                break

        if not all_passed_time:
            continue

        # 3) 최종적으로 2일 동안 복용 0회 → 이메일 1회 발송
        print("→ 2일 동안 한 번도 복용하지 않음! 이메일 발송")
        send_missed_dose_email(
            guardian_email=guardian.email,
            owner_name=guardian.owner_name,
            medicine_name=med.name,
            time=med.alarm_time,
        )

        print("→ 이메일 전송 완료")


@api_view(["GET"])
@permission_classes([AllowAny])
def check_missed(request):
    # check_missed_doses()
    return Response({"status": "done"})


########################################################################################
# 아두이노 로직

@api_view(["GET"])
@permission_classes([AllowAny])
def arduino_today_doses(request):
    today = timezone.localdate()

    # 오늘 날짜 DailyDose 가져오기
    doses = DailyDose.objects.filter(date=today).select_related("medicine")

    result = []
    for dose in doses:
        med = dose.medicine
        result.append({
            "medicine_id": med.id,
            "name": med.name,
            "alarm_time": med.alarm_time.strftime("%H:%M"),
            "is_taken": dose.is_taken,
        })

    return Response({
        "date": today,
        "doses": result
    })

@extend_schema(tags = ["아두이노->백엔드로 복용 완료 전송"])
@api_view(['POST'])
@permission_classes([AllowAny])  # 아두이노 접근 가능
def arduino_confirm(request):
    """아두이노 → 백엔드로 복용 완료 전송"""
    medicine_id = request.data.get('medicine_id')

    try:
        medicine = Medicine.objects.get(id=medicine_id)
        medicine.is_taken_today = True
        medicine.save()
        DoseLog.objects.create(medicine=medicine, source='ARDUINO')

        return Response({'message': '아두이노 복용 완료 반영됨'}, status=status.HTTP_200_OK)

    except Medicine.DoesNotExist:
        return Response({'error': '해당 약을 찾을 수 없음'}, status=status.HTTP_404_NOT_FOUND)