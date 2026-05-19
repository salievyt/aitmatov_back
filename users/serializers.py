from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone', 'username', 'first_name', 'last_name',
            'avatar', 'avatar_url', 'role', 'class_level', 'school', 'is_active', 'is_staff', 'date_joined',
        ]
        read_only_fields = ['id', 'date_joined']

    def get_avatar_url(self, obj):
        request = self.context.get('request')
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return obj.avatar.url if obj.avatar else None


class UserProfileSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone', 'username', 'first_name', 'last_name',
            'avatar', 'avatar_url', 'role', 'class_level', 'school',
        ]
        read_only_fields = ['id', 'email', 'role']

    def get_avatar_url(self, obj):
        request = self.context.get('request')
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return obj.avatar.url if obj.avatar else None


class UserAdminUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone', 'first_name', 'last_name',
            'role', 'class_level', 'school', 'is_active', 'is_staff',
        ]
        read_only_fields = ['id', 'date_joined']

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['email', 'phone', 'username', 'first_name', 'last_name', 'password', 'password_confirm', 'role', 'class_level', 'school']

    def validate(self, data):
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Пароли не совпадают.'})
        return data

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
