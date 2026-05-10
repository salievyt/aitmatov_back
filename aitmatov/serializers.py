from rest_framework import serializers
from .models import AitmatovTheme


class AitmatovThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AitmatovTheme
        fields = ['id', 'name', 'slug', 'description', 'icon', 'order']
