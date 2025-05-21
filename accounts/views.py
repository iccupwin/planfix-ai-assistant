from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, UserRegisterSerializer, PlanfixConnectSerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """
    API для регистрации новых пользователей
    """
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "token": token.key
        }, status=status.HTTP_201_CREATED)


class CustomAuthToken(ObtainAuthToken):
    """
    API для аутентификации пользователей и получения токена
    """
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_planfix_connected': user.is_planfix_connected
        })


class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    API для получения и обновления данных пользователя
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class ConnectPlanfixView(APIView):
    """
    API для подключения учетной записи Planfix
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = PlanfixConnectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.planfix_id = serializer.validated_data['planfix_id']
        user.planfix_token = serializer.validated_data['planfix_token']
        user.is_planfix_connected = True
        user.save()
        
        return Response({
            'status': 'success',
            'message': 'Planfix account successfully connected',
            'is_planfix_connected': True
        }, status=status.HTTP_200_OK)


class DisconnectPlanfixView(APIView):
    """
    API для отключения учетной записи Planfix
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        user = request.user
        user.planfix_id = None
        user.planfix_token = None
        user.is_planfix_connected = False
        user.save()
        
        return Response({
            'status': 'success',
            'message': 'Planfix account successfully disconnected',
            'is_planfix_connected': False
        }, status=status.HTTP_200_OK)