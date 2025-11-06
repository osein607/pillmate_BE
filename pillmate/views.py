from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Medicine, DoseLog
from .serializers import MedicineSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.contrib.auth.models import User


@extend_schema(tags = ["약 등록"])
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


    @action(detail=True, methods=['POST'])
    def mark_taken(self, request, pk=None):
        """사용자가 직접 복용 완료 처리"""
        try:
            medicine = self.get_object()
            medicine.is_taken_today = True
            medicine.save()
            DoseLog.objects.create(medicine=medicine, source='MANUAL')
            return Response({'message': '복용 완료로 표시됨'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
