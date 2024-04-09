from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from ..forms import RegistrationForm
from ..models import User


def register(request):
    message = None
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            role = cleaned_data.get('role')
            group = cleaned_data.get('group')
            if role == 'Teacher':
                cleaned_data.pop('group', None)
            elif role == 'Student' and not group:
                form.add_error('group', "Для студента необходимо указать группу.")
                return render(request, 'registration.html', {'form': form, 'message': message})
            
            user = User.objects.create_user(**cleaned_data)  # Создаем пользователя
            message = "Регистрация прошла успешно"
            return redirect('home')  # Перенаправление на страницу успешной регистрации
    else:
        form = RegistrationForm()
    return render(request, 'registration.html', {'form': form, 'message': message})


def base_view(request):
    return render(request, 'base.html')

def home_view(request):
    return render(request, 'home.html')
