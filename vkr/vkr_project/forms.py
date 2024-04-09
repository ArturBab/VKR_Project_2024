from django import forms
from .models import User
from django.core.exceptions import ValidationError


class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=100)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    name = forms.CharField(max_length=100)
    middle_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    role = forms.CharField(max_length=100)
    group = forms.CharField(max_length=100)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group'].required = False  # Поле группы необязательно

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError(
                "Пользователь с таким именем уже существует.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError(
                "Пользователь с таким адресом электронной почты уже существует.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        group = cleaned_data.get('group')
        if role == 'Teacher':
            cleaned_data['group'] = None  # Убираем группу для преподавателей
        elif role == 'Student' and not group:
            raise ValidationError("Для студента необходимо указать группу.")

        return cleaned_data

    def save(self):
        username = self.cleaned_data.get('username')
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        name = self.cleaned_data.get('name')
        middle_name = self.cleaned_data.get('middle_name')
        last_name = self.cleaned_data.get('last_name')
        role = self.cleaned_data.get('role')
        group = self.cleaned_data.get('group')

        if role == 'Teacher':
            group = None  # Убираем группу для преподавателей

        # Создаем нового пользователя
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            name=name,
            middle_name=middle_name,
            last_name=last_name,
            role=role,
            group=group
        )

        return user
