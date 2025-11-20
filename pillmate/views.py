from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import Medicine, DoseLog, DailyDose
from .serializers import MedicineSerializer, DailyDoseSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.contrib.auth.models import User


from django.utils import timezone
from datetime import date, timedelta



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
        dose.taken_at = datetime.now()
        dose.save()

        serializer = DailyDoseSerializer(dose)
        return Response(serializer.data, status=status.HTTP_200_OK)