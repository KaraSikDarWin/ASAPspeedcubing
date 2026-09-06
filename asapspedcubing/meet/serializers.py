from rest_framework import serializers
from .models import Competitors, Discipline, RoundsOfDiscipline, Results

class ResultsSerializer(serializers.ModelSerializer):
    competitor = serializers.StringRelatedField()

    class Meta:
        model = Results
        fields = [
            'competitor', 'attempt_1', 'attempt_2', 'attempt_3',
            'attempt_4', 'attempt_5', 'average', 'best'
        ]