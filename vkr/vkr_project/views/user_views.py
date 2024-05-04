from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from ..serializers import UserSerializer
from ..models import User
from rest_framework.decorators import api_view, permission_classes
from ..permissions import *
from django.views.decorators.http import require_POST
from django.shortcuts import redirect
from django.contrib.auth import logout as django_logout
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView


class RegisterAPIView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": "Registration successful"}, status=status.HTTP_201_CREATED)
        else:
            errors = serializer.errors
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            # Успешно получен токен, добавим его в куки
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')

            # Устанавливаем access токен в куки
            response.set_cookie(key='access_token',
                                value=access_token, httponly=True)
            # Устанавливаем refresh токен в куки
            response.set_cookie(key='refresh_token',
                                value=refresh_token, httponly=True)

        return response


class LogoutAPIView(APIView):
    def post(self, request):
        # Удаляем куки с токенами
        response = Response()
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        response.data = {'message': 'Successfully logged out.'}
        return response


class CurrentUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'middle_name': user.middle_name,
            'last_name': user.last_name,
            'role': user.role
        })


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
