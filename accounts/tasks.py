from datetime import timedelta

from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone


@shared_task
def send_welcome_email_task(user_id):
    user_model = get_user_model()
    try:
        user = user_model.objects.get(pk=user_id)
    except user_model.DoesNotExist:
        return f"Пользователь {user_id} не найден"

    send_mail(
        subject="Добро пожаловать!",
        message=f"Здравствуйте, {user.username}! Спасибо за регистрацию.",
        from_email=None,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return f"Приветственное письмо отправлено: {user.email}"


@shared_task
def clean_inactive_users_task(days=30):
    user_model = get_user_model()
    cutoff = timezone.now() - timedelta(days=days)
    inactive_users = user_model.objects.filter(is_active=False).filter(
        Q(last_login__lt=cutoff) | Q(last_login__isnull=True, date_joined__lt=cutoff)
    )
    count = inactive_users.count()
    inactive_users.delete()
    return f"Удалено неактивных пользователей: {count}"


@shared_task
def send_daily_admin_report_task():
    user_model = get_user_model()
    counts = {
        role: user_model.objects.filter(role=role).count()
        for role, _ in user_model.Role.choices
    }
    report = (
        "Статистика пользователей: "
        f"ADMIN={counts[user_model.Role.ADMIN]}, "
        f"MODERATOR={counts[user_model.Role.MODERATOR]}, "
        f"USER={counts[user_model.Role.USER]}"
    )
    print(report)
    return report
