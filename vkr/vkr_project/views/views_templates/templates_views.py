from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from ..forms import RegistrationForm
from django.contrib.auth import logout
from ..models import User
from django.http import JsonResponse
import requests


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
                return JsonResponse({'success': True})
            else:
                # Если сервер вернул ошибку, получаем JSON и обрабатываем сообщения об ошибках
                error_data = response.json()
                for field, errors in error_data.items():
                    error_messages[field] = ', '.join(errors)

        except requests.RequestException as e:
            # Если произошла ошибка при обращении к серверу, добавляем общее сообщение об ошибке
            error_messages['__all__'] = str(e)

    # Если метод запроса не POST или возникли ошибки, возвращаем страницу с формой регистрации
    return render(request, 'signup.html', {'error_messages': error_messages})


def login_view(request):
    message = None
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Перенаправление на главную страницу после успешного входа
                return redirect('home')
            else:
                message = "Неверное имя пользователя или пароль."
    else:
        form = AuthenticationForm(data=request.POST)
    return render(request, 'login.html', {'form': form, 'message': message})


def base_view(request):
    return render(request, 'base.html')


def home_view(request):
    return render(request, 'home.html')
