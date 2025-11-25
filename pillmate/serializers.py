from rest_framework import serializers
from .models import Medicine, DoseLog, DailyDose, GuardianInfo


class DoseLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoseLog
        fields = ['id', 'taken_at', 'source']


class MedicineSerializer(serializers.ModelSerializer):
    # logs = DoseLogSerializer(many=True, read_only=True)

    class Meta:
        model = Medicine
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']

class DailyDoseSerializer(serializers.ModelSerializer):
    medicine = MedicineSerializer(read_only=True)

    class Meta:
        model = DailyDose
        fields = "__all__"

class GuardianInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuardianInfo
        fields = "__all__"