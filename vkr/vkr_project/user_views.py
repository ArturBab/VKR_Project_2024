from django.db import IntegrityError
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from .serializers import UserSerializer
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework import status
from .models import User
import jwt
import datetime


@api_view(['POST'])
def register_view(request):
    if request.method == 'POST':
        try:
            data = request.data.copy()
            password = data.pop('password', None)
            user = User.objects.create(**data)
            if password is not None:
                user.set_password(password)
                user.save()
            serializer = UserSerializer(user)
            return Response({'message': 'Вы были успешно зарегистрированы в систему.', 'user': serializer.data}, status=status.HTTP_201_CREATED)

        except IntegrityError as e:
            if 'UNIQUE constraint failed: vkr_project_user.username' in str(e):
                error_message = 'Такое имя пользователя уже существует.'
            elif 'UNIQUE constraint failed: vkr_project_user.email' in str(e):
                error_message = 'Такая почта уже существует.'
            else:
                error_message = 'Произошла ошибка при регистрации пользователя.'
            return Response({'error': error_message}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login_view(request):
    if request.method == 'POST':
        try:
            username = request.data['username']
            password = request.data['password']

            user = User.objects.filter(username=username).first()

            if user is None:
                raise AuthenticationFailed('Данный пользователь не найден.')

            if not user.check_password(password):
                raise AuthenticationFailed('Пароль не верный.')

            payload = {
                'id': user.id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
                'iat': datetime.datetime.utcnow()
            }

            token = jwt.encode(payload, 'secret',
                               algorithm='HS256').decode('utf-8')

            response = Response()

            response.set_cookie(key='jwt', value=token, httponly=True)
            response.data = {
                'message': 'Вы успешно авторизовались.',
                'jwt': token
            }

            return response

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def user_view(request):
    if request.method == 'GET':
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('Вы не были авторизованы')

        try:
            payload = jwt.decode(token, 'secret', algorithm=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Вы не были авторизованы')

        user = User.objects.filter(id=payload['id']).first()
        serializer = UserSerializer(user)

        return Response(serializer.data)


@api_view(['POST'])
def logout_view(request):
    response = Response()
    response.delete_cookie('jwt')
    response.data = {
        'message': 'Вы вышли из системы.'
    }
    return response
