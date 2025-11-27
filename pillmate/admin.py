from django.contrib import admin
from .models import Medicine, GuardianInfo
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
        })
    )

@admin.register(GuardianInfo)
class GuardianInfoAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "phone", "email", "owner_name", "owner_email")
    search_fields = ("name", "phone", "email", "owner_name", "owner_email")
