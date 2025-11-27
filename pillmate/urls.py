from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r"daily-dose", DailyDoseViewSet, basename="daily-dose")
router.register(r"", MedicineViewSet, basename='')

urlpatterns = [
    path("guardian/", get_guardian_info),
    path("guardian/update/", update_guardian_info),
    path("check_missed/", check_missed),
    path("arduino/today-dose/", arduino_today_doses),
    path('arduino/confirm/', arduino_confirm, name='arduino_confirm'),
    path('', include(router.urls)),


]

# /medicines/
# /medicines/{id}/
# /daily-dose/
# /daily-dose/{id}/
# /daily-dose/{id}/take/
# /daily-dose/?date=YYYY-MM-DD
# /guardian/
# /guardian/update/
# /arduino/confirm/
