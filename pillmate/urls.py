from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MedicineViewSet, arduino_confirm

router = DefaultRouter()
router.register('', MedicineViewSet, basename='medicine')

urlpatterns = [
    path('', include(router.urls)),
    path('arduino/confirm/', arduino_confirm, name='arduino_confirm'),
]
