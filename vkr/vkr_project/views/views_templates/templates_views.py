from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from ..forms import RegistrationForm
from django.contrib.auth import logout
from ..models import User
import requests
from ..views.content_views import content_list
from django.contrib.auth.decorators import login_required
from rest_framework.authtoken.models import Token


def signup(request):
    error_messages = {}

    if request.method == 'POST':
        username = request.POST.get('username')
        name = request.POST.get('name')
        middle_name = request.POST.get('middle_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        group = request.POST.get('group')
        telegram_id = request.POST.get('telegram_id')

        try:
            response = requests.post('http://127.0.0.1:8000/api/register/', json={
                'username': username,
                'name': name,
                'middle_name': middle_name,
                'last_name': last_name,
                'email': email,
                'password': password,
                'role': role,
                'group': group,
                'telegram_id': telegram_id
            })
            if response.ok:
                return redirect('login')
            else:
                error_data = response.json()
                if isinstance(error_data, dict):
                    for key, value in error_data.items():
                        error_messages[key] = ', '.join(value)
                elif isinstance(error_data, list):
                    error_messages['__all__'] = ', '.join(error_data)

        except requests.RequestException as e:
            error_messages['__all__'] = str(e)

    # Если метод запроса не POST или возникли ошибки, возвращаем страницу с формой регистрации
    return render(request, 'signup.html', {'error_messages': error_messages})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            response = requests.post('http://127.0.0.1:8000/api/login/', json={
                'username': username,
                'password': password
            })

            if response.status_code == 200:
                # Успешно получен токен и данные пользователя
                access_token = response.json().get('access')
                refresh_token = response.json().get('refresh')

                # Получаем данные пользователя
                user_response = requests.get(
                    'http://127.0.0.1:8000/api/user/', headers={'Authorization': f'Bearer {access_token}'})
                user_data = user_response.json()

                # Передаем данные пользователя и устанавливаем куки в ответе
                response = render(request, 'home.html', {'user': user_data})
                response.set_cookie('access_token', access_token)
                response.set_cookie('refresh_token', refresh_token)

                return response

            elif response.status_code == 400:
                # Неправильные учетные данные
                error_message = "Неправильные учетные данные. Пожалуйста, попробуйте еще раз."
                return render(request, 'login.html', {'error_message': error_message})

            else:
                # Другие ошибки
                error_message = "Произошла ошибка. Пожалуйста, попробуйте еще раз."
                return render(request, 'login.html', {'error_message': error_message})

        except requests.RequestException as e:
            # Ошибка запроса к API
            error_message = f"Ошибка запроса к API: {str(e)}"
            return render(request, 'login.html', {'error_message': error_message})

    else:
        return render(request, 'login.html')


def base_view(request):
    return render(request, 'base.html')


@login_required
def home_view(request):
    user = request.user
    print(request.user)
    return render(request, 'home.html', {'user': user})


def display_content_list(request):
    # Получаем данные из API эндпоинта content_list
    response = content_list(request)

    # Проверяем, успешно ли получены данные
    if response.status_code == 200:
        # Если успешно, передаем данные на шаблон
        content_data = response.data
        return render(request, 'content_list.html', {'content_data': content_data})
    else:
        # Если произошла ошибка, выводим сообщение об ошибке на шаблон
        error_message = "Ошибка получения данных."
        return render(request, 'content_list.html', {'error_message': error_message})
