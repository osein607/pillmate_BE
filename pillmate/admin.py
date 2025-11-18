from django.contrib import admin
from .models import Medicine
@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    fieldsets = (
        ("기본 정보", {
            "fields": ("user", "name", "type")
        }),
        ("복약 설정", {
            "fields": ("quantity", "time", "alarm_time")
        }),
        ("복약 기간", {
            "fields": ("start_date", "end_date")
        }),
        ("기타", {
            "fields": ("is_taken_today",)
        }),
    )
