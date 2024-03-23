from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer
from .models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from .permissions import *


class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


@api_view(['POST'])
def logout_view(request):
    if request.method == 'POST':
        try:
            refresh_token = request.COOKIES.get('refresh_token')

            if refresh_token is None:
                raise AuthenticationFailed('Пользователь не аутентифицирован.')

            # Очистка куки с access и refresh токенами
            response = Response()
            response.delete_cookie('refresh_token')
            response.delete_cookie('access_token')

            # Удаление refresh токена из базы данных
            token = RefreshToken(refresh_token)
            token.blacklist()

            response.data = {
                'message': 'Вы успешно вышли из системы.'
            }

            return response

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_list(request):
    """
    Представление для получения списка студентов преподавателем.
    """
    if request.method == 'GET':
        # Проверяем, является ли пользователь преподавателем
        if request.user.role != 'Teacher':
            return Response({'message': 'У вас нет прав доступа'}, status=status.HTTP_403_FORBIDDEN)

        # Получаем всех студентов
        students = User.objects.filter(role='Student')
        serializer = UserSerializer(students, many=True)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacherOrReadOnly])
def list_student_groups(request):
    if request.method == 'GET':
        student_groups = User.objects.filter(
            role='Student').values_list('group', flat=True).distinct()

        return Response({'student_groups': student_groups}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def teachers_list(request):
    if request.method == 'GET':
        teachers = User.objects.filter(role='Teacher')
        serializer = UserSerializer(teachers, many=True)
        return Response(serializer.data)
