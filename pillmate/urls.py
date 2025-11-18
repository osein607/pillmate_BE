from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MedicineViewSet, arduino_confirm, DailyDoseViewSet

router = DefaultRouter()
router.register(r"daily-dose", DailyDoseViewSet, basename="daily-dose")
router.register(r"", MedicineViewSet, basename='')

urlpatterns = [
    path('', include(router.urls)),
    path('arduino/confirm/', arduino_confirm, name='arduino_confirm'),
]

# /medicines/
# /medicines/{id}/
# /daily-dose/
# /daily-dose/{id}/
# /daily-dose/{id}/take/
# /daily-dose/?date=YYYY-MM-DD
# /arduino/confirm/
