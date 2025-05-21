from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для получения и обновления информации о пользователе"""
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_planfix_connected']
        read_only_fields = ['id', 'email', 'is_planfix_connected']


class UserRegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации новых пользователей"""
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'password2', 'first_name', 'last_name']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class PlanfixConnectSerializer(serializers.Serializer):
    """Сериализатор для подключения учетной записи Planfix"""
    
    planfix_token = serializers.CharField(required=True)
    planfix_id = serializers.CharField(required=True)