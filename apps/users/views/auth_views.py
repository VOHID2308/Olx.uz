"""
Autentifikatsiya views - Telegram login, token refresh, logout
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema

from apps.users.serializers import TelegramLoginSerializer, UserSerializer

User = get_user_model()


class TelegramLoginView(APIView):
    """
    Telegram orqali login yoki ro'yxatdan o'tish.
    Agar foydalanuvchi mavjud bo'lsa - token qaytaradi.
    Agar mavjud bo'lmasa - yangi user yaratib token qaytaradi.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        request=TelegramLoginSerializer,
        responses={200: UserSerializer},
        summary="Telegram orqali login/ro'yxatdan o'tish",
        tags=['Authentication']
    )
    def post(self, request):
        serializer = TelegramLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        telegram_id = data['telegram_id']

        try:
            user = User.objects.get(telegram_id=telegram_id)
            # Mavjud user - ma'lumotlarini yangilash
            user.first_name = data['first_name']
            user.last_name = data.get('last_name', '')
            user.username = data['username']
            user.save(update_fields=['first_name', 'last_name', 'username'])
            created = False
        except User.DoesNotExist:
            # Yangi user yaratish
            user = User.objects.create_user(
                telegram_id=telegram_id,
                username=data['username'],
                first_name=data['first_name'],
                last_name=data.get('last_name', ''),
                role='customer'
            )
            created = True

        # JWT token yaratish
        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
            'created': created
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Chiqish - refresh tokenni blacklist ga qo'shish
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Tizimdan chiqish",
        tags=['Authentication']
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token taqdim etilmagan'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Muvaffaqiyatli chiqildi'}, status=status.HTTP_200_OK)
        except TokenError:
            return Response(
                {'error': 'Token noto\'g\'ri yoki muddati o\'tgan'},
                status=status.HTTP_400_BAD_REQUEST
            )