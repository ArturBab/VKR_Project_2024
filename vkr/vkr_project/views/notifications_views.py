from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from ..serializers import NotificationSerializer
from ..models import User, Notification
import pytz
from django.utils import timezone


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_notification(request):
    if request.method == 'POST':
        # Получаем текущего пользователя (преподавателя)
        user = request.user

        # Проверяем, является ли пользователь преподавателем
        if not user.role == 'Teacher':
            return Response({'error': 'У вас нет разрешения на создание уведомлений.'}, status=status.HTTP_403_FORBIDDEN)

        # Получаем номер учебной группы из запроса
        group_educational = request.data.get('group_educational')

        # Проверяем наличие номера учебной группы
        if not group_educational:
            return Response({'error': 'Укажите учебную группу.'}, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем существование учебной группы в модели User
        if not User.objects.filter(role='Student', group=group_educational).exists():
            return Response({'error': 'Указанная учебная группа не существует.'}, status=status.HTTP_400_BAD_REQUEST)

        # Создаем данные для сериализатора уведомления
        notification_data = {
            # Используем текущего пользователя (преподавателя)
            'user': user.id,
            # Предполагается, что сообщение передается в запросе
            'message': request.data.get('message'),
        }

        # Добавляем учебную группу в данные уведомления, если она была предоставлена в запросе
        if group_educational:
            notification_data['group_educational'] = group_educational

        # Создаем сериализатор уведомления с данными из запроса
        serializer = NotificationSerializer(data=notification_data)
        if serializer.is_valid():
            # Сохраняем уведомление
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # В случае ошибки валидации возвращаем ошибку
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mark_group_notifications_as_read(request):
    if request.method == 'GET':
        # Получаем учебную группу текущего пользователя
        group_educational = request.user.group

        # Проверяем, указана ли учебная группа у текущего пользователя
        if not group_educational:
            return Response({'error': 'У текущего пользователя не указана учебная группа.'}, status=status.HTTP_400_BAD_REQUEST)

        # Получаем все уведомления для указанной учебной группы
        group_notifications = Notification.objects.filter(
            group_educational=group_educational)

        # Помечаем все уведомления для указанной учебной группы как прочитанные
        group_notifications.update(is_read=True)

        # Сериализуем уведомления в компактном формате
        notifications = []
        for notification in group_notifications:
            data = {
                'from': notification.user.username,
                'message': notification.message,
                'sent_at': notification.created_at.strftime('%d-%m-%Y, %H:%M')
            }
            notifications.append(data)

        # Сообщение о прочтении уведомлений
        message = f"Уведомления для учебной группы '{group_educational}' успешно прочитаны."

        return Response({'notifications': notifications, 'message': message})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def group_notification_status(request):
    if request.method == 'GET':
        # Получаем список учебных групп, для которых преподаватель отправлял уведомления
        group_educational_list = Notification.objects.filter(
            user=request.user).values_list('group_educational', flat=True).distinct()

        if not group_educational_list:
            return Response({'error': 'Преподаватель не отправил уведомлений ни одной учебной группе.'}, status=status.HTTP_400_BAD_REQUEST)

        # Получаем все уведомления для указанных учебных групп
        group_notifications = Notification.objects.filter(
            group_educational__in=group_educational_list)

        # Сериализуем уведомления для передачи данных о статусе просмотра
        notifications = []
        for notification in group_notifications:
            serializer = NotificationSerializer(notification)
            notifications.append(serializer.data)

        return Response({'notifications': notifications})
