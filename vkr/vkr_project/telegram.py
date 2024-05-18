from telegram import Bot, Update
from telegram.ext import *
import json
from django.http import JsonResponse
import requests
from django.views.decorators.csrf import csrf_exempt
import requests
from settings.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_USERNAME, ADMIN_TELEGRAM_CHAT_ID


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User


import os
import signal
import sys
from threading import Thread
import signal


def notify_server_start():
    bot_token = TELEGRAM_BOT_TOKEN
    chat_id = ADMIN_TELEGRAM_CHAT_ID
    message = "Сервер ИС запущен"

    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': message
    }

    response = requests.post(url, json=payload)

    if response.ok:
        print("Уведомление успешно отправлено.")
    else:
        print(f"Не удалось отправить уведомление. Ошибка: {response.text}")


def notify_server_stop(request):
    try:
        bot_token = TELEGRAM_BOT_TOKEN
        chat_id = ADMIN_TELEGRAM_CHAT_ID
        message = "Сервер ИС был приостановлен"

        url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        payload = {
            'chat_id': chat_id,
            'text': message
        }

        response = requests.post(url, json=payload)

        if response.ok:
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'error': f'Failed to send message to Telegram bot. Error message: {response.text}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


@csrf_exempt
def send_telegram_notification(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            chat_id = data.get('chat_id')
            message = data.get('message')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        if not chat_id or not message:
            return JsonResponse({'error': 'chat_id and message are required'}, status=400)

        # Отправляем запрос к Telegram Bot API для отправки сообщения
        url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
        params = {
            'chat_id': chat_id,
            'text': message
        }
        response = requests.post(url, json=params)

        # Проверяем успешность запроса и возвращаем результат
        if response.ok:
            return JsonResponse({'status': 'success'})
        else:
            error_message = response.json().get('description', 'Unknown error')
            return JsonResponse({'error': f'Failed to send message to Telegram bot. Error message: {error_message}'}, status=500)

    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    

def send_notification_via_telegram(chat_id, message):
    bot_token = TELEGRAM_BOT_TOKEN
    bot = Bot(token=bot_token)
    bot.send_message(chat_id=chat_id, text=message)

    
# --------------------------------------------------------------------------------------#

# Обработчик команды /start
def start(update, context):
    chat_id = update.message.chat_id
    message = f"Здравствуйте! Ваш chat ID: {chat_id}"
    update.message.reply_text(message)

def run_bot(TELEGRAM_BOT_TOKEN):
    from telegram.ext import Updater, CommandHandler

    # Инициализация ТГ бота
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Добавляем обработчик команды /start
    dp.add_handler(CommandHandler("start", start))

    # Запуск бота
    updater.start_polling()
    updater.idle()

# --------------------------------------------------------------------------------------#    
