from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from ..serializers import NotificationSerializer
from ..models import User, Notification, NotificationReadByStudent
from ..telegram import send_notification_via_telegram, ADMIN_TELEGRAM_CHAT_ID


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

            send_notification_via_telegram(chat_id=ADMIN_TELEGRAM_CHAT_ID, message=request.data.get('message'))

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # В случае ошибки валидации возвращаем ошибку
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_as_read_via_bot(request):
    if request.method == 'POST':
        # Получаем данные из запроса, например, идентификатор уведомления
        notification_id = request.data.get('notification_id')

        # Находим уведомление в базе данных
        notification = Notification.objects.get(id=notification_id)

        # Помечаем уведомление как прочитанное
        notification.is_read = True
        notification.save()

        # Возвращаем подтверждение об успешном обновлении статуса
        return Response({'message': 'Статус уведомления успешно обновлен.'})





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
        # Получаем уведомления текущего пользователя (преподавателя)
        notifications = request.user.notifications.all()

        # Сериализуем уведомления вместе с информацией о студентах, которые прочитали каждое уведомление
        notifications_data = []
        for notification in notifications:
            data = {
                'id': notification.id,
                'user': notification.user.username,
                'message': notification.message,
                'created_at': notification.created_at.strftime('%d-%m-%Y, %H:%M'),
                'is_read': notification.is_read,
                'group_educational': notification.group_educational,
                'read_by_students': [
                    {
                        'student': read_by_student.student.username,
                        'read_status': 'Read' if read_by_student.is_read else 'Not Read'
                    }
                    for read_by_student in notification.read_by_students.all()
                ]
            }
            notifications_data.append(data)

        return Response({'notifications': notifications_data})
